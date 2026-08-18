#!/usr/bin/env python3
"""
Verify every <import> in this repo resolves against Kodi's official repository
or against this repo itself. An unresolvable dependency means Kodi refuses to
install the add-on, so this runs in CI and fails the build.
"""
import gzip
import io
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Kodi 21 Omega and Kodi 22 Piers: an add-on only needs to resolve on one of them.
KODI_VERSIONS = ("omega", "piers")
# Provided by Kodi itself, never shipped by a repository.
BUILTIN_PREFIXES = ("xbmc.", "kodi.")


def official_index(version):
    url = f"https://mirrors.kodi.tv/addons/{version}/addons.xml.gz"
    req = urllib.request.Request(url, headers={"User-Agent": "kodi-repo-builder"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = gzip.decompress(resp.read())
    return {a.get("id") for a in ET.fromstring(raw)}


def main():
    addons_xml = ROOT / "docs" / "addons.xml"
    if not addons_xml.is_file():
        print("docs/addons.xml missing - run build_repo.py first")
        return 1

    local = ET.parse(addons_xml).getroot()
    local_ids = {a.get("id") for a in local}

    available = {}
    for version in KODI_VERSIONS:
        try:
            available[version] = official_index(version) | local_ids
        except Exception as exc:
            print(f"WARNING: could not fetch the {version} index ({exc}); skipping it")

    if not available:
        print("WARNING: no official index reachable, dependency check skipped")
        return 0

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
                problems.append((addon_id, dep))
            elif len(resolvable) < len(available):
                print(f"  note: {addon_id} -> {dep} resolves only on "
                      f"{', '.join(resolvable)}")

    print(f"checked {len(local)} add-ons against: {', '.join(available)}")
    if problems:
        print("\nUNRESOLVABLE DEPENDENCIES:")
        for addon_id, dep in problems:
            print(f"  {addon_id} requires {dep} - not in the official repo or this one")
        print("\nAdd the missing add-on to the mirror list in addons.json.")
        return 1
    print("all dependencies resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
