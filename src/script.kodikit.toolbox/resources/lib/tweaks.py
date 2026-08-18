"""Write a conservative advancedsettings.xml for smoother streaming."""
import os
import shutil
import time

import xbmc
import xbmcgui

from .common import NAME, confirm, log, notify, path

# Kodi allocates roughly 3x memorysize, so keep the per-profile figure modest.
PROFILES = [
    ("Low memory  (~20 MB buffer, for old boxes)", 20 * 1024 * 1024, 4),
    ("Balanced  (~64 MB buffer, recommended)", 64 * 1024 * 1024, 8),
    ("Large  (~128 MB buffer, 4 GB+ RAM)", 128 * 1024 * 1024, 20),
]

TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<advancedsettings>
  <cache>
    <!-- 1 = buffer all internet filesystems to memory -->
    <buffermode>1</buffermode>
    <memorysize>{memorysize}</memorysize>
    <readfactor>{readfactor}</readfactor>
  </cache>
</advancedsettings>
"""


def _target():
    return os.path.join(path("special://profile"), "advancedsettings.xml")


def run():
    choice = xbmcgui.Dialog().select("Streaming cache profile", [p[0] for p in PROFILES])
    if choice < 0:
        return
    label, memorysize, readfactor = PROFILES[choice]
    target = _target()

    message = "Write advancedsettings.xml with the '%s' profile?" % label.split("  ")[0]
    if os.path.exists(target):
        message += "\n\nYour existing file will be backed up first."
    if not confirm(NAME, message, yes="Write"):
        return

    backup = None
    if os.path.exists(target):
        backup = "%s.%s.bak" % (target, time.strftime("%Y%m%d-%H%M%S"))
        try:
            shutil.copy2(target, backup)
        except OSError as exc:
            log("backup failed: %s" % exc, xbmc.LOGERROR)
            notify("Could not back up existing file", xbmcgui.NOTIFICATION_ERROR)
            return

    try:
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(TEMPLATE.format(memorysize=memorysize, readfactor=readfactor))
    except OSError as exc:
        log("write failed: %s" % exc, xbmc.LOGERROR)
        notify("Could not write advancedsettings.xml", xbmcgui.NOTIFICATION_ERROR)
        return

    detail = "Backed up to:\n%s\n\n" % os.path.basename(backup) if backup else ""
    if confirm(NAME, "%sCache settings only take effect after a restart.\nRestart Kodi now?"
               % detail, yes="Restart", no="Later"):
        xbmc.executebuiltin("RestartApp")
