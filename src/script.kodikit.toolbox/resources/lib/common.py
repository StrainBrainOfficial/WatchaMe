"""Shared helpers for the toolbox."""
import os

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

ADDON = xbmcaddon.Addon()
NAME = ADDON.getAddonInfo("name")


def path(special):
    return xbmcvfs.translatePath(special)


def notify(message, icon=xbmcgui.NOTIFICATION_INFO, ms=5000):
    xbmcgui.Dialog().notification(NAME, message, icon, ms)


def confirm(heading, message, yes="Continue", no="Cancel"):
    return xbmcgui.Dialog().yesno(heading, message, nolabel=no, yeslabel=yes)


def log(message, level=xbmc.LOGINFO):
    xbmc.log("[%s] %s" % (NAME, message), level)


def human(size):
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return "%.1f %s" % (value, unit)
        value /= 1024


def tree_size(target):
    """Bytes used by a file or directory, ignoring anything unreadable."""
    if not os.path.exists(target):
        return 0
    if os.path.isfile(target):
        try:
            return os.path.getsize(target)
        except OSError:
            return 0
    total = 0
    for root, _dirs, files in os.walk(target, onerror=lambda e: None):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                continue
    return total
