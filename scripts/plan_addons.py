#!/usr/bin/env python3
"""Turn addons.wishlist.txt into addons.json entries.

Checks each wanted add-on against Kodi's official repository, decides whether
it belongs in the 'official' or 'mirror' section, and prints entries ready to
paste. With --apply it writes them into addons.json and bumps the toolbox
version for you (without which no device would ever see the change).
"""
import argparse
import collections
import gzip
import json
import pathlib
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
WISHLIST = ROOT / "addons.wishlist.txt"
REPOS = ROOT / "addons.repos.txt"
MANIFEST = ROOT / "addons.json"
CONFIG = ROOT / "repo.config.json"
KODI_VERSIONS = ("omega", "piers")


def official_ids():
    ids = set()
    for version in KODI_VERSIONS:
        url = "https://mirrors.kodi.tv/addons/%s/addons.xml.gz" % version
        req = urllib.request.Request(url, headers={"User-Agent": "watchame-planner"})
        try:
            raw = gzip.decompress(urllib.request.urlopen(req, timeout=60).read())
        except Exception as exc:
            print("  ! could not read the %s index (%s)" % (version, exc), file=sys.stderr)
            continue
        ids |= set(re.findall(r'<addon\s+id="([^"]+)"', raw.decode("utf-8", "replace")))
    return ids


def read_wishlist():
    if not WISHLIST.is_file():
        sys.exit("no %s -- create it and list what you want" % WISHLIST.name)
    wanted, untouched = [], 0
    for n, line in enumerate(WISHLIST.read_text().splitlines(), 1):
        line = line.split("#")[0].strip()
        if not line:
            continue
        # Slots still holding their placeholders are simply not filled in yet.
        if "REPLACE_ID_" in line:
            untouched += 1
            continue
        line = " ".join(w for w in line.split() if not w.startswith("REPLACE_SOURCE_"))
        parts = line.split()
        addon_id = parts[0]
        rest = [p for p in parts[1:] if p.lower() != "optional"]
        optional = len(rest) != len(parts) - 1
        if not re.match(r"^[a-z0-9._-]+$", addon_id):
            print("  ! line %d: '%s' does not look like an add-on id" % (n, addon_id),
                  file=sys.stderr)
            continue
        source = rest[0] if rest else None
        kind = None
        if source:
            if "://" in source:
                kind = "zip_url" if source.lower().endswith(".zip") else "repo_url"
            elif "/" in source:
                kind = "github"
            else:
                print("  ! line %d: '%s' is not a slug, repo url or zip url"
                      % (n, source), file=sys.stderr)
                continue
        wanted.append({"id": addon_id, "source": source, "kind": kind,
                       "optional": optional})
    if untouched:
        print("(%d slot%s still blank -- ignored)\n"
              % (untouched, "" if untouched == 1 else "s"))
    return wanted



def _find_repo_zip(page_url):
    """A repo landing page is usually an index listing repository.*.zip."""
    import urllib.parse
    try:
        req = urllib.request.Request(page_url, headers={"User-Agent": "watchame-planner"})
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    except Exception:
        return None
    links = re.findall(r'href=["\']([^"\']+\.zip)["\']', html, re.I)
    if not links:
        return None
    # Prefer an actual repository add-on, and the newest of them.
    repo_links = [l for l in links if "repository" in l.lower()] or links
    repo_links.sort(key=_vkey)
    return urllib.parse.urljoin(page_url if page_url.endswith("/") else page_url + "/",
                                repo_links[-1])


def _vkey(v):
    return [int(n) for n in re.findall(r"\d+", v or "0")]


def discover(url, seen=None):
    """List the add-ons a Kodi repository serves, following nested indexes."""
    import io, zipfile
    url = url.strip()
    bases = []
    if not url.lower().endswith(".zip"):
        # A bare base may serve addons.xml directly, or it may be the landing
        # page you would paste into Kodi -- an index listing a repository zip.
        probe = url.rstrip("/") + "/addons.xml"
        try:
            req = urllib.request.Request(probe, headers={"User-Agent": "watchame-planner"})
            urllib.request.urlopen(req, timeout=30).read(1)
        except Exception:
            zip_url = _find_repo_zip(url)
            if zip_url:
                print("  (landing page -- following %s)\n" % zip_url.rsplit("/", 1)[-1])
                url = zip_url
    if url.lower().endswith(".zip"):
        req = urllib.request.Request(url, headers={"User-Agent": "watchame-planner"})
        blob = urllib.request.urlopen(req, timeout=60).read()
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            name = next(n for n in zf.namelist() if n.endswith("addon.xml"))
            root = ET.fromstring(zf.read(name))
        for d in root.iter("dir"):
            el = d.find("info")
            if el is not None and el.text:
                bases.append(el.text.strip())
        el = root.find(".//info")
        if not bases and el is not None and el.text:
            bases.append(el.text.strip())
    else:
        bases.append(url.rstrip("/") + "/addons.xml")

    visited, found, queue = set(), {}, list(bases)
    while queue:
        index_url = queue.pop(0)
        if index_url in visited:
            continue
        visited.add(index_url)
        try:
            req = urllib.request.Request(index_url, headers={"User-Agent": "watchame-planner"})
            raw = urllib.request.urlopen(req, timeout=60).read()
            if index_url.endswith(".gz"):
                raw = gzip.decompress(raw)
            root = ET.fromstring(raw.decode("utf-8-sig", "replace"))
        except Exception as exc:
            print("  ! %s: %s" % (index_url, exc), file=sys.stderr)
            continue
        base = index_url.rsplit("/", 1)[0]
        for addon in root.findall("addon"):
            aid, ver = addon.get("id"), addon.get("version")
            if aid.startswith("repository."):
                # A repository entry points at the index that holds the real add-ons.
                for el in addon.iter("info"):
                    if el.text:
                        queue.append(el.text.strip())
                continue
            prev = found.get(aid)
            if prev is None or _vkey(ver) > _vkey(prev[0]):
                found[aid] = (ver, base)

    if not found:
        print("no add-ons found -- the repository's own index url did not "
              "respond (see the ! line above, if any)")
        return 1
    print("%d add-on(s) served -- paste the lines you want into %s:\n"
          % (len(found), WISHLIST.name))
    for aid in sorted(found):
        ver, base = found[aid]
        note = ""
        if seen is not None:
            if aid in seen and seen[aid] != base:
                note = "   # ALSO served by an earlier repo -- pick one"
            seen.setdefault(aid, base)
        print("%-46s %s        # v%s%s" % (aid, base, ver, note))
    return 0


def advertised_version(item):
    """Version a source currently offers, or None when it cannot be known cheaply."""
    if item["kind"] != "repo_url":
        return None
    base = item["source"].rstrip("/")
    for name in ("addons.xml", "addons.xml.gz"):
        try:
            req = urllib.request.Request(f"{base}/{name}",
                                         headers={"User-Agent": "watchame-planner"})
            raw = urllib.request.urlopen(req, timeout=45).read()
            if name.endswith(".gz"):
                raw = gzip.decompress(raw)
            root = ET.fromstring(raw.decode("utf-8-sig", "replace"))
            vs = [a.get("version") for a in root.findall("addon")
                  if a.get("id") == item["id"]]
            return max(vs, key=_vkey) if vs else None
        except Exception:
            continue
    return None


def resolve_duplicates(wanted):
    """One entry per add-on id, keeping the source offering the newest version."""
    by_id = collections.OrderedDict()
    for item in wanted:
        by_id.setdefault(item["id"], []).append(item)

    dupes = {k: v for k, v in by_id.items() if len(v) > 1}
    if dupes:
        print("%d add-on(s) listed more than once -- checking which source is newest\n"
              % len(dupes))

    resolved = []
    for addon_id, items in by_id.items():
        if len(items) == 1:
            resolved.append(items[0])
            continue
        scored = []
        for it in items:
            ver = advertised_version(it)
            scored.append((_vkey(ver) if ver else [-1], ver, it))
        scored.sort(key=lambda t: t[0], reverse=True)
        best_key, best_ver, best = scored[0]
        print("  %s listed %d times:" % (addon_id, len(items)))
        for key, ver, it in scored:
            mark = "KEEP" if it is best else "drop"
            where = it["source"] or "official"
            print("      %-4s v%-12s %s" % (mark, ver or "?", where))
        if best_ver is None:
            print("      (no version advertised -- kept the first listed)")
        resolved.append(best)
    if dupes:
        print()
    return resolved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="write entries into addons.json and bump the toolbox version")
    ap.add_argument("--discover", metavar="URL", nargs="*",
                    help="list what Kodi repositories serve. With no URL, reads "
                         "addons.repos.txt; otherwise takes them on the command line.")
    args = ap.parse_args()

    if args.discover is not None:
        urls = args.discover
        if not urls:
            if not REPOS.is_file():
                sys.exit("no %s -- create it and paste your repository urls in"
                         % REPOS.name)
            raw_lines = [l.split("#")[0].strip()
                         for l in REPOS.read_text().splitlines()]
            raw_lines = [u for u in raw_lines if u]
            blank = sum(1 for u in raw_lines if "REPLACE_WITH_REPO_URL" in u)
            urls = [u for u in raw_lines if "REPLACE_WITH_REPO_URL" not in u]
            if blank:
                print("(%d empty slot%s in %s -- ignored)"
                      % (blank, "" if blank == 1 else "s", REPOS.name))
            if not urls:
                sys.exit("Nothing pasted yet. Replace the REPLACE_WITH_REPO_URL "
                         "slots in %s with your repository urls." % REPOS.name)
            print("reading %d repository url(s) from %s\n" % (len(urls), REPOS.name))
        rc, seen = 0, {}
        for n, url in enumerate(urls):
            if n:
                print()
            print("=" * 78)
            print("  %s" % url)
            print("=" * 78)
            rc |= discover(url, seen)
        if len(urls) > 1:
            print("\n%d add-on(s) found across %d repositories."
                  % (len(seen), len(urls)))
        return rc

    wanted = read_wishlist()
    if wanted:
        wanted = resolve_duplicates(wanted)
        noise = [w["id"] for w in wanted
                 if w["id"].startswith(("script.module.", "resource."))]
        if noise:
            print("%d of these are library or resource add-ons: %s%s" %
                  (len(noise), ", ".join(noise[:4]),
                   " ..." if len(noise) > 4 else ""))
            print("Kodi installs those automatically as dependencies. Listing them "
                  "is usually unnecessary -- remove them unless you know you need "
                  "your own copy.\n")
        if len(wanted) > 40:
            print("%d add-ons listed. That is a lot to carry: every one is packaged "
                  "into your repository, shows in the Toolbox picker, and is checked "
                  "daily. Consider trimming to what you will actually use.\n"
                  % len(wanted))
    if not wanted:
        sys.exit("Nothing filled in yet. Overwrite the REPLACE_ placeholders in %s"
                 % WISHLIST.name)

    manifest = json.loads(MANIFEST.read_text(), object_pairs_hook=collections.OrderedDict)
    have = {e["id"] for s in ("mirror", "official") for e in manifest[s] if "id" in e}

    print("checking %d add-on(s) against Kodi's official repository\n" % len(wanted))
    official = official_ids()

    plan, blocked = [], []
    for item in wanted:
        addon_id = item["id"]
        if addon_id in have:
            print("  --  %-42s already in addons.json" % addon_id)
            continue
        if addon_id in official and not item["kind"]:
            entry = collections.OrderedDict([
                ("id", addon_id), ("name", addon_id.split(".")[-1].title()),
                ("category", "tools"), ("why", "TODO: one sentence on why this earned a slot."),
            ])
            if item["optional"]:
                entry["optional"] = True
            plan.append(("official", entry))
            print("  ok  %-42s official  (installed by id)" % addon_id)
        elif item["kind"]:
            entry = collections.OrderedDict([
                ("id", addon_id), ("name", addon_id.split(".")[-1].title()),
                ("category", "tools"), ("why", "TODO: one sentence on why this earned a slot."),
            ])
            if item["kind"] == "github":
                entry["github"] = item["source"]
                entry["track"] = "release"
                origin = "github %s" % item["source"]
            elif item["kind"] == "repo_url":
                entry["repo_url"] = item["source"].rstrip("/")
                origin = "kodi repo"
            else:
                entry["zip_url"] = item["source"]
                origin = "fixed zip"
            if item["optional"]:
                entry["optional"] = True
            plan.append(("mirror", entry))
            print("  ok  %-42s mirror    (%s)" % (addon_id, origin))
        else:
            blocked.append(addon_id)
            print("  !!  %-42s NOT in the official repo, and no source given" % addon_id)

    if blocked:
        print("\nAdd a source for these in %s -- one of:" % WISHLIST.name)
        for addon_id in blocked:
            print("    %s   owner/repo" % addon_id)
            print("    %s   https://host/path/zips        (another Kodi repo)" % addon_id)
            print("    %s   https://host/addon-1.2.3.zip  (a fixed zip)" % addon_id)
            break
        if len(blocked) > 1:
            print("    ... and %d more" % (len(blocked) - 1))
        print("\nNot sure what a repository serves?  "
              "python3 scripts/plan_addons.py --discover <repo url or repo zip url>")

    if not plan:
        print("\nnothing new to add")
        return 1 if blocked else 0

    if not args.apply:
        print("\n--- entries (re-run with --apply to write them in) ---")
        for section, entry in plan:
            print("\n%s:" % section)
            print(json.dumps(entry, indent=2))
        print("\nEdit each \"why\" before committing -- it ends up in the README.")
        return 1 if blocked else 0

    for section, entry in plan:
        manifest[section].append(entry)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")

    cfg = json.loads(CONFIG.read_text())
    addon_xml = ROOT / "src" / cfg["toolbox_id"] / "addon.xml"
    text = addon_xml.read_text()
    version = ET.fromstring(text).get("version")
    parts = version.split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    new_version = ".".join(parts)
    addon_xml.write_text(text.replace('version="%s"' % version,
                                      'version="%s"' % new_version, 1))

    print("\nwrote %d entr(ies) to addons.json" % len(plan))
    print("bumped %s %s -> %s" % (cfg["toolbox_id"], version, new_version))
    print("\nNext:")
    print("  1. edit the \"why\" fields in addons.json")
    print("  2. python3 scripts/build_repo.py && python3 scripts/check_deps.py")
    print("  3. git add -A && git commit -m 'Add add-ons' && git push")
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
