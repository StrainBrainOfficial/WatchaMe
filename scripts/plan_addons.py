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
    wanted = []
    for n, line in enumerate(WISHLIST.read_text().splitlines(), 1):
        line = line.split("#")[0].strip()
        if not line:
            continue
        parts = line.split()
        addon_id = parts[0]
        optional = "optional" in [p.lower() for p in parts[1:]]
        slug = next((p for p in parts[1:] if "/" in p), None)
        if not re.match(r"^[a-z0-9._-]+$", addon_id):
            print("  ! line %d: '%s' does not look like an add-on id" % (n, addon_id),
                  file=sys.stderr)
            continue
        wanted.append({"id": addon_id, "slug": slug, "optional": optional})
    return wanted


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="write entries into addons.json and bump the toolbox version")
    args = ap.parse_args()

    wanted = read_wishlist()
    if not wanted:
        sys.exit("wishlist is empty -- add some add-on ids to %s" % WISHLIST.name)

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
        if addon_id in official:
            entry = collections.OrderedDict([
                ("id", addon_id), ("name", addon_id.split(".")[-1].title()),
                ("category", "tools"), ("why", "TODO: one sentence on why this earned a slot."),
            ])
            if item["optional"]:
                entry["optional"] = True
            plan.append(("official", entry))
            print("  ok  %-42s official  (installed by id)" % addon_id)
        elif item["slug"]:
            entry = collections.OrderedDict([
                ("id", addon_id), ("name", addon_id.split(".")[-1].title()),
                ("category", "tools"), ("why", "TODO: one sentence on why this earned a slot."),
                ("github", item["slug"]), ("track", "release"),
            ])
            if item["optional"]:
                entry["optional"] = True
            plan.append(("mirror", entry))
            print("  ok  %-42s mirror    (from %s)" % (addon_id, item["slug"]))
        else:
            blocked.append(addon_id)
            print("  !!  %-42s NOT in the official repo, and no owner/repo given" % addon_id)

    if blocked:
        print("\nAdd a GitHub slug for these in %s, e.g." % WISHLIST.name)
        for addon_id in blocked:
            print("    %s   owner/repo" % addon_id)

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
