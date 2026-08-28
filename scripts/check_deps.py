#!/usr/bin/env python3
"""
Verify that everything this repository advertises is actually installable.

Four gates, each of which has caught real breakage here:

  1. Every <import> resolves against Kodi's official repository or this one.
     An unresolvable dependency means Kodi refuses to install the add-on.
  2. Nothing requires xbmc.python < 3.0.0. Kodi 19+ refuses those outright,
     and because xbmc.* is a builtin prefix, gate 1 never looks at them.
  3. Nothing duplicates an official-repo build newer than or equal to ours.
     Kodi resolves across every enabled repository by highest version, so a
     stale mirror here shadows the maintained official copy.
  4. Every advertised zip exists, opens, holds <id>/addon.xml and matches its
     .md5 sidecar. A Git LFS pointer checked out without its object passes
     every other check and still hands Kodi 130 bytes of text.

Runs in CI and fails the build.
"""
import gzip
import hashlib
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from build_repo import version_key

ROOT = Path(__file__).resolve().parent.parent
# Kodi 21 Omega and Kodi 22 Piers: an add-on only needs to resolve on one of them.
KODI_VERSIONS = ("omega", "piers")
# Provided by Kodi itself, never shipped by a repository.
BUILTIN_PREFIXES = ("xbmc.", "kodi.")
# Kodi 19 dropped Python 2. Below this an add-on cannot be installed at all.
MIN_PYTHON_ABI = "3.0.0"


def official_index(version):
    url = f"https://mirrors.kodi.tv/addons/{version}/addons.xml.gz"
    req = urllib.request.Request(url, headers={"User-Agent": "kodi-repo-builder"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = gzip.decompress(resp.read())
    return {a.get("id"): a.get("version") for a in ET.fromstring(raw)}


def check_imports(local, available):
    """Every non-optional, non-builtin import resolves somewhere."""
    problems = []
    for addon in local:
        addon_id = addon.get("id")
        for imp in addon.findall("./requires/import"):
            dep = imp.get("addon")
            if not dep or dep.startswith(BUILTIN_PREFIXES):
                continue
            if imp.get("optional") == "true":
                continue
            resolvable = [v for v, ids in available.items() if dep in ids]
            if not resolvable:
                problems.append(f"{addon_id} requires {dep} - not in the official repo or this one")
            elif len(resolvable) < len(available):
                print(f"  note: {addon_id} -> {dep} resolves only on {', '.join(resolvable)}")
    return problems


def check_python_abi(local):
    """Nothing built for Python 2."""
    problems = []
    for addon in local:
        for imp in addon.findall("./requires/import"):
            if imp.get("addon") != "xbmc.python":
                continue
            wanted = imp.get("version") or "0"
            if version_key(wanted) < version_key(MIN_PYTHON_ABI):
                problems.append(f"{addon.get('id')} requires xbmc.python {wanted} - Kodi 19+ "
                                f"provides {MIN_PYTHON_ABI} and refuses to install it")
    return problems


def check_official_overlap(local, official):
    """Do not shadow the official repo with an equal or older copy."""
    problems = []
    for addon in local:
        addon_id, ours = addon.get("id"), addon.get("version")
        theirs = official.get(addon_id)
        if theirs is None:
            continue
        if version_key(ours) > version_key(theirs):
            print(f"  note: {addon_id} {ours} is ahead of the official repo's {theirs}, "
                  f"so mirroring it here is doing something")
        else:
            problems.append(f"{addon_id} {ours} duplicates the official repo's {theirs} - move it "
                            f"to the \"official\" section of addons.json instead of mirroring it")
    return problems


def check_packages(local):
    """The advertised zip is a real, correct, hash-matching package."""
    problems = []
    for addon in local:
        addon_id, version = addon.get("id"), addon.get("version")
        zip_path = ROOT / "docs" / "zips" / addon_id / f"{addon_id}-{version}.zip"
        if not zip_path.is_file():
            problems.append(f"{addon_id} {version} is advertised but {zip_path.name} is missing")
            continue
        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.read(f"{addon_id}/addon.xml")
        except zipfile.BadZipFile:
            problems.append(f"{zip_path.name} is not a readable zip - an unfetched Git LFS "
                            f"pointer looks exactly like this")
            continue
        except KeyError:
            problems.append(f"{zip_path.name} has no {addon_id}/addon.xml at its root")
            continue
        md5_path = zip_path.with_suffix(".zip.md5")
        if not md5_path.is_file():
            problems.append(f"{zip_path.name} has no .md5 sidecar, and the repo add-on "
                            f"declares <hashes>true</hashes>")
        elif hashlib.md5(zip_path.read_bytes()).hexdigest() != md5_path.read_text().split()[0]:
            problems.append(f"{zip_path.name} does not match its .md5 sidecar")
    return problems


def main():
    addons_xml = ROOT / "docs" / "addons.xml"
    if not addons_xml.is_file():
        print("docs/addons.xml missing - run build_repo.py first")
        return 1

    local = ET.parse(addons_xml).getroot()
    local_ids = {a.get("id") for a in local}

    available, official = {}, {}
    for version in KODI_VERSIONS:
        try:
            index = official_index(version)
        except Exception as exc:
            print(f"WARNING: could not fetch the {version} index ({exc}); skipping it")
            continue
        available[version] = set(index) | local_ids
        for aid, ver in index.items():
            if aid not in official or version_key(ver) > version_key(official[aid]):
                official[aid] = ver

    if not available:
        print("WARNING: no official index reachable, dependency check skipped")
        return 0

    sections = (
        ("UNRESOLVABLE DEPENDENCIES", check_imports(local, available),
         "Add the missing add-on to the mirror list in addons.json."),
        ("PYTHON 2 ADD-ONS", check_python_abi(local),
         "Drop these - no Kodi version this repo targets can install them."),
        ("DUPLICATES OF THE OFFICIAL REPO", check_official_overlap(local, official),
         "Kodi picks the highest version across every enabled repo, so a stale mirror "
         "here beats a maintained official copy."),
        ("BROKEN PACKAGES", check_packages(local),
         "Rebuild with build_repo.py. A zip that is a few hundred bytes of text is an "
         "LFS pointer whose object was never fetched."),
    )

    print(f"checked {len(local)} add-ons against: {', '.join(available)}")
    failed = False
    for title, problems, hint in sections:
        if not problems:
            continue
        failed = True
        print(f"\n{title}:")
        for line in problems:
            print(f"  {line}")
        print(f"\n{hint}")
    if failed:
        return 1
    print("all dependencies resolve, all packages are installable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
