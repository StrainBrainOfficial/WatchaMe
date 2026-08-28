#!/usr/bin/env python3
"""
Build the Kodi repository.

  1. Resolve the latest upstream version of every mirrored addon.
  2. Download + repackage it as a Kodi-shaped zip (<id>/addon.xml at the root).
  3. Package every locally-authored addon in src/.
  4. Generate the repository addon itself.
  5. Regenerate addons.xml + addons.xml.md5 and the landing page.

Idempotent: a version already present in docs/zips is skipped, so running this
daily costs almost nothing and only produces a diff when upstream actually moved.
"""

import gzip
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ZIPS = DOCS / "zips"
SRC = ROOT / "src"

SKIP_NAMES = {".git", ".github", "__pycache__", ".idea", ".vscode", ".pytest_cache"}
SKIP_SUFFIX = {".pyc", ".pyo", ".pyd"}

# GitHub hard-rejects any single file over 100 MB, and the zips are served
# straight out of the repo, so anything near that ceiling can never be pushed.
MAX_ZIP_MB = 95


class ZipTooLarge(Exception):
    pass


# ---------------------------------------------------------------- helpers

def log(msg):
    print(msg, flush=True)


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def base_url(cfg):
    user, repo, branch = cfg["github_user"], cfg["github_repo"], cfg.get("branch", "main")
    if cfg.get("hosting") == "pages":
        return f"https://{user}.github.io/{repo}"
    return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/docs"


def api(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "kodi-repo-builder",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "kodi-repo-builder"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=300) as resp:
        return resp.read()


def version_key(version):
    """Kodi-ish version ordering: numeric-aware, digits sort above text."""
    parts = re.split(r"[.\-+~]", version or "0")
    key = []
    for part in parts:
        for chunk in re.findall(r"\d+|\D+", part):
            key.append((1, int(chunk), "") if chunk.isdigit() else (0, 0, chunk))
    return key


# ---------------------------------------------------------------- packaging

def iter_files(folder):
    for path in sorted(Path(folder).rglob("*")):
        if any(part in SKIP_NAMES for part in path.parts):
            continue
        if path.suffix in SKIP_SUFFIX:
            continue
        if path.is_file():
            yield path


def read_addon_xml(folder):
    xml_path = Path(folder) / "addon.xml"
    if not xml_path.is_file():
        return None, None
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError:
        return None, None
    return root.get("id"), root.get("version")


def find_addon_dir(tree_root, addon_id):
    """Locate the folder holding this addon's addon.xml anywhere in an extracted tree."""
    candidates = []
    for xml_path in Path(tree_root).rglob("addon.xml"):
        if any(part in SKIP_NAMES for part in xml_path.parts):
            continue
        found_id, _ = read_addon_xml(xml_path.parent)
        if found_id == addon_id:
            candidates.append(xml_path.parent)
    if not candidates:
        return None
    # Shallowest match wins (avoids picking a vendored copy under lib/).
    return sorted(candidates, key=lambda p: len(p.parts))[0]


def make_zip(addon_dir, addon_id, version, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{addon_id}-{version}.zip"
    tmp_path = zip_path.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in iter_files(addon_dir):
            arcname = Path(addon_id) / file_path.relative_to(addon_dir)
            # Fixed timestamp so unchanged content produces a byte-identical zip.
            info = zipfile.ZipInfo(str(arcname), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, file_path.read_bytes())
    tmp_path.replace(zip_path)
    size_mb = zip_path.stat().st_size / 1024 / 1024
    if size_mb > MAX_ZIP_MB:
        zip_path.unlink(missing_ok=True)
        raise ZipTooLarge(f"{zip_path.name} is {size_mb:.0f} MB, over the {MAX_ZIP_MB} MB limit")
    digest = hashlib.md5(zip_path.read_bytes()).hexdigest()
    (out_dir / f"{addon_id}-{version}.zip.md5").write_text(digest + "\n", encoding="utf-8")
    return zip_path


def prune(out_dir, addon_id, keep):
    zips = sorted(
        out_dir.glob(f"{addon_id}-*.zip"),
        key=lambda p: version_key(p.stem[len(addon_id) + 1:]),
        reverse=True,
    )
    for stale in zips[keep:]:
        stale.unlink(missing_ok=True)
        stale.with_suffix(".zip.md5").unlink(missing_ok=True)
        log(f"      pruned {stale.name}")


# ---------------------------------------------------------------- upstream sync

def resolve_upstream(entry):
    """Return (tarball_url, label) for the newest upstream state."""
    slug = entry["github"]
    track = entry.get("track", "release")
    if track == "release":
        try:
            rel = api(f"https://api.github.com/repos/{slug}/releases/latest")
            if rel.get("tarball_url"):
                return rel["tarball_url"], rel.get("tag_name", "latest")
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
            log(f"      no published release, falling back to branch head")
    meta = api(f"https://api.github.com/repos/{slug}")
    branch = entry.get("ref") or meta.get("default_branch", "master")
    return f"https://api.github.com/repos/{slug}/tarball/{branch}", f"{branch}@head"


def _extract_tarball(blob, tmp):
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        # Refuse path traversal in the upstream archive.
        members = [m for m in tar.getmembers()
                   if not (m.name.startswith("/") or ".." in Path(m.name).parts)]
        tar.extractall(tmp, members=members)


def _extract_zip(blob, tmp):
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        members = [n for n in zf.namelist()
                   if not (n.startswith("/") or ".." in Path(n).parts)]
        zf.extractall(tmp, members=members)


def kodi_repo_version(entry, addon_id):
    """Newest version of addon_id advertised by another Kodi repository."""
    base = entry["repo_url"].rstrip("/")
    index = None
    for name in ("addons.xml", "addons.xml.gz"):
        try:
            raw = download(f"{base}/{name}")
            index = gzip.decompress(raw) if name.endswith(".gz") else raw
            break
        except Exception:
            continue
    if index is None:
        raise RuntimeError(f"no addons.xml under {base}")
    root = ET.fromstring(index.decode("utf-8-sig", "replace"))
    versions = [a.get("version") for a in root.findall("addon") if a.get("id") == addon_id]
    if not versions:
        raise RuntimeError(f"{addon_id} is not served by {base}")
    return max(versions, key=version_key)


def sync_mirror(entry, keep):
    addon_id = entry["id"]
    source = entry.get("github") or entry.get("repo_url") or entry.get("zip_url")
    if not source:
        log(f"  - {addon_id}: no github, repo_url or zip_url, skipped")
        return None
    log(f"  - {addon_id}  ({source})")

    # A Kodi repository advertises versions up front, so we can skip the
    # download entirely when we already hold the newest one.
    if entry.get("repo_url"):
        try:
            version = kodi_repo_version(entry, addon_id)
        except Exception as exc:
            log(f"      SKIP: {exc}")
            return None
        log(f"      upstream: {version}")
        if (ZIPS / addon_id / f"{addon_id}-{version}.zip").exists():
            log(f"      already current at {version}")
            prune(ZIPS / addon_id, addon_id, keep)
            return version
        datadir = (entry.get("datadir") or entry["repo_url"]).rstrip("/")
        url, is_zip = f"{datadir}/{addon_id}/{addon_id}-{version}.zip", True
    elif entry.get("zip_url"):
        url, is_zip = entry["zip_url"], True
        log(f"      upstream: fixed zip url")
    else:
        try:
            url, label = resolve_upstream(entry)
        except Exception as exc:
            log(f"      SKIP: could not resolve upstream: {exc}")
            return None
        is_zip = False
        log(f"      upstream: {label}")

    try:
        blob = download(url)
    except Exception as exc:
        log(f"      SKIP: download failed: {exc}")
        return None

    with tempfile.TemporaryDirectory() as tmp:
        try:
            _extract_zip(blob, tmp) if is_zip else _extract_tarball(blob, tmp)
        except Exception as exc:
            log(f"      SKIP: bad archive: {exc}")
            return None

        addon_dir = find_addon_dir(tmp, addon_id)
        if addon_dir is None:
            log(f"      SKIP: no addon.xml with id={addon_id} in the archive")
            return None

        _, version = read_addon_xml(addon_dir)
        if not version:
            log(f"      SKIP: addon.xml has no version")
            return None

        out_dir = ZIPS / addon_id
        zip_path = out_dir / f"{addon_id}-{version}.zip"
        if zip_path.exists():
            log(f"      already current at {version}")
        else:
            try:
                make_zip(addon_dir, addon_id, version, out_dir)
            except ZipTooLarge as exc:
                log(f"      SKIP: {exc}")
                return None
            log(f"      packaged {version}  <-- UPDATED")
        prune(out_dir, addon_id, keep)
        return version


# ---------------------------------------------------------------- repo addon

REPO_ADDON_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<addon id="{repo_id}" name="{repo_name}" version="{repo_version}" provider-name="{provider}">
  <extension point="xbmc.addon.repository" name="{repo_name}">
    <dir>
      <info compressed="false">{base}/addons.xml</info>
      <checksum>{base}/addons.xml.md5</checksum>
      <datadir zip="true">{base}/zips</datadir>
      <hashes>true</hashes>
    </dir>
  </extension>
  <extension point="xbmc.addon.metadata">
    <summary lang="en_gb">{summary}</summary>
    <description lang="en_gb">{description}</description>
    <platform>all</platform>
    <license>GPL-3.0-or-later</license>
    <source>https://github.com/{user}/{gh_repo}</source>
    <assets>
      <icon>icon.png</icon>
      <fanart>fanart.png</fanart>
    </assets>
  </extension>
</addon>
"""


def build_repo_addon(cfg):
    repo_id = cfg["repo_id"]
    staging = ROOT / ".build" / repo_id
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    (staging / "addon.xml").write_text(REPO_ADDON_XML.format(
        repo_id=repo_id,
        repo_name=cfg["repo_name"],
        repo_version=cfg["repo_version"],
        provider=cfg["provider"],
        base=base_url(cfg),
        summary=cfg["summary"],
        description=cfg["description"],
        user=cfg["github_user"],
        gh_repo=cfg["github_repo"],
    ), encoding="utf-8")

    for art in ("icon.png", "fanart.png"):
        source = ROOT / "assets" / art
        if source.is_file():
            shutil.copy2(source, staging / art)

    out_dir = ZIPS / repo_id
    make_zip(staging, repo_id, cfg["repo_version"], out_dir)
    prune(out_dir, repo_id, cfg.get("keep_versions", 2))
    # Stable download URL for the one-time "install from zip" step.
    shutil.copy2(out_dir / f"{repo_id}-{cfg['repo_version']}.zip", DOCS / f"{repo_id}.zip")
    log(f"  - {repo_id} {cfg['repo_version']} (+ stable docs/{repo_id}.zip)")
    return cfg["repo_version"]


STALE_LOCAL = []


def build_local_addons(cfg):
    built = {}
    if not SRC.is_dir():
        return built
    for addon_dir in sorted(p for p in SRC.iterdir() if p.is_dir()):
        addon_id, version = read_addon_xml(addon_dir)
        if not addon_id:
            log(f"  - {addon_dir.name}: no valid addon.xml, skipped")
            continue
        if addon_id == cfg.get("toolbox_id"):
            # The toolbox ships a copy of the curated list, so editing
            # addons.json at the repo root is the single source of truth.
            (addon_dir / "resources").mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / "addons.json", addon_dir / "resources" / "addons.json")
        out_dir = ZIPS / addon_id
        zip_path = out_dir / f"{addon_id}-{version}.zip"
        existing = zip_path.read_bytes() if zip_path.exists() else None
        make_zip(addon_dir, addon_id, version, out_dir)
        changed = existing != zip_path.read_bytes()
        prune(out_dir, addon_id, cfg.get("keep_versions", 2))
        # Zips are byte-reproducible, so changed bytes at an unchanged version
        # means the content moved without the version moving. Kodi keys updates
        # off the version in addons.xml, so no device would ever fetch this.
        stale = existing is not None and changed
        log(f"  - {addon_id} {version}"
            + ("  <-- CONTENT CHANGED, VERSION NOT BUMPED" if stale
               else "  <-- UPDATED" if changed else ""))
        if stale:
            STALE_LOCAL.append((addon_id, version))
        built[addon_id] = version
    return built


# ---------------------------------------------------------------- index

def collect_latest():
    """For every addon folder in zips/, return (id, version, addon.xml root) of the newest zip."""
    entries = []
    if not ZIPS.is_dir():
        return entries
    for addon_dir in sorted(p for p in ZIPS.iterdir() if p.is_dir()):
        addon_id = addon_dir.name
        zips = sorted(
            addon_dir.glob(f"{addon_id}-*.zip"),
            key=lambda p: version_key(p.stem[len(addon_id) + 1:]),
            reverse=True,
        )
        if not zips:
            continue
        size_mb = zips[0].stat().st_size / 1024 / 1024
        if size_mb > MAX_ZIP_MB:
            log(f"  ! {zips[0].name} is {size_mb:.0f} MB, over the {MAX_ZIP_MB} MB limit, skipped")
            continue
        try:
            with zipfile.ZipFile(zips[0]) as zf:
                raw = zf.read(f"{addon_id}/addon.xml")
        except KeyError:
            log(f"  ! {zips[0].name} has no {addon_id}/addon.xml, skipped")
            continue
        except zipfile.BadZipFile:
            # A Git LFS pointer checked out without the object looks exactly
            # like this. Advertising it would hand Kodi a 130-byte "zip".
            log(f"  ! {zips[0].name} is not a readable zip, skipped")
            continue
        try:
            root = ET.fromstring(raw)
        except ET.ParseError:
            log(f"  ! {zips[0].name} has unparseable addon.xml, skipped")
            continue
        entries.append((addon_id, root.get("version"), root))
    return entries


def write_addons_xml(entries):
    lines = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', "<addons>"]
    for _, _, root in entries:
        body = ET.tostring(root, encoding="unicode").strip()
        lines.extend("    " + line for line in body.splitlines())
    lines.append("</addons>")
    payload = "\n".join(lines) + "\n"
    (DOCS / "addons.xml").write_text(payload, encoding="utf-8")
    digest = hashlib.md5(payload.encode("utf-8")).hexdigest()
    (DOCS / "addons.xml.md5").write_text(digest + "\n", encoding="utf-8")
    return digest


def write_index(cfg, entries):
    base = base_url(cfg)
    # GitHub Pages runs Jekyll unless this exists, which is slow over a few
    # hundred zip folders and drops any path beginning with an underscore.
    (DOCS / ".nojekyll").touch()
    rows = "\n".join(
        f"      <tr><td><code>{aid}</code></td><td>{ver}</td>"
        f'<td><a href="zips/{aid}/{aid}-{ver}.zip">zip</a></td></tr>'
        for aid, ver, _ in entries
    )
    (DOCS / "index.html").write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{cfg['repo_name']} - Kodi repository</title>
<style>
  body{{font:16px/1.6 system-ui,sans-serif;max-width:52rem;margin:3rem auto;padding:0 1.25rem;
       background:#14161a;color:#e6e8ec}}
  a{{color:#8ab4ff}} code{{background:#22262e;padding:.15em .4em;border-radius:4px}}
  table{{border-collapse:collapse;width:100%;margin-top:1rem}}
  td,th{{text-align:left;padding:.45rem .6rem;border-bottom:1px solid #2b303a}}
  .box{{background:#1c1f26;border:1px solid #2b303a;border-radius:8px;padding:1rem 1.25rem}}
</style></head><body>
<h1>{cfg['repo_name']}</h1>
<p>{cfg['summary']}</p>
<div class="box">
  <p><strong>Install:</strong> add this as a file source in Kodi, then install the repo zip.</p>
  <p><code>{base}/</code></p>
  <p>Or download <a href="{cfg['repo_id']}.zip">{cfg['repo_id']}.zip</a> and use
     <em>Add-ons &rarr; Install from zip file</em>.</p>
</div>
<h2>Addons served ({len(entries)})</h2>
<table><tr><th>ID</th><th>Version</th><th>Download</th></tr>
{rows}
</table>
<p><a href="addons.xml">addons.xml</a> &middot; <a href="addons.xml.md5">addons.xml.md5</a></p>
</body></html>
""", encoding="utf-8")


# ---------------------------------------------------------------- main

def main():
    cfg = load_json(ROOT / "repo.config.json")
    manifest = load_json(ROOT / "addons.json")
    keep = cfg.get("keep_versions", 2)
    DOCS.mkdir(parents=True, exist_ok=True)
    ZIPS.mkdir(parents=True, exist_ok=True)

    log("== syncing mirrored addons from upstream")
    failures = []
    for entry in manifest.get("mirror", []):
        if sync_mirror(entry, keep) is None:
            failures.append(entry["id"])

    log("\n== packaging local addons")
    build_local_addons(cfg)

    log("\n== building repository addon")
    build_repo_addon(cfg)

    log("\n== regenerating index")
    entries = collect_latest()
    digest = write_addons_xml(entries)
    write_index(cfg, entries)
    shutil.rmtree(ROOT / ".build", ignore_errors=True)

    log(f"\naddons.xml: {len(entries)} addons, md5 {digest}")
    log(f"serving from: {base_url(cfg)}")
    if failures:
        log(f"\nWARNING: {len(failures)} mirror(s) failed and kept their previous zip: "
            + ", ".join(failures))
    if STALE_LOCAL:
        log("\nERROR: content changed without a version bump:")
        for addon_id, version in STALE_LOCAL:
            log(f"  {addon_id} is still {version}; devices on {version} will keep "
                f"the old copy because addons.xml is unchanged.")
        log("Bump the version in src/<addon>/addon.xml and rebuild.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
