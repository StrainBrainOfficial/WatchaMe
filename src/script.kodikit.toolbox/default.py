"""KodiKit Toolbox - entry point."""
import sys

import xbmcaddon
import xbmcgui

from resources.lib import installer, maintenance, tweaks

ADDON = xbmcaddon.Addon()
NAME = ADDON.getAddonInfo("name")

MENU = [
    ("Install curated add-ons", installer.run),
    ("Storage report", maintenance.report),
    ("Clean up caches", maintenance.run),
    ("Apply streaming cache tuning", tweaks.run),
    ("Clean video/music library", maintenance.clean_library),
]


def main():
    # Allow direct invocation, e.g. RunScript(script.kodikit.toolbox,cleanup)
    if len(sys.argv) > 1:
        shortcut = {
            "install": installer.run,
            "report": maintenance.report,
            "cleanup": maintenance.run,
            "tweaks": tweaks.run,
            "library": maintenance.clean_library,
        }.get(sys.argv[1].lower())
        if shortcut:
            shortcut()
            return

    while True:
        choice = xbmcgui.Dialog().select(NAME, [label for label, _ in MENU])
        if choice < 0:
            return
        MENU[choice][1]()


if __name__ == "__main__":
    main()
