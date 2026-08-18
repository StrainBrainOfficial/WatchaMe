"""Cleanup and reporting. Nothing here deletes media or user settings."""
import os
import shutil
import time

import xbmc
import xbmcgui

from .common import NAME, confirm, human, log, notify, path, tree_size

# Kodi keeps the running log open; removing it mid-session breaks logging.
KEEP_IN_TEMP = (".log", ".old.log")


def _packages():
    return path("special://home/addons/packages")


def _temp():
    return path("special://temp")


def _thumbnails():
    return path("special://profile/Thumbnails")


def _textures_db():
    db_dir = path("special://profile/Database")
    if not os.path.isdir(db_dir):
        return None
    for name in sorted(os.listdir(db_dir), reverse=True):
        if name.startswith("Textures") and name.endswith(".db"):
            return os.path.join(db_dir, name)
    return None


def _old_logs(days=7):
    """Rotated/uploaded logs older than `days`, excluding the live kodi.log."""
    log_dir = path("special://logpath")
    cutoff = time.time() - days * 86400
    found = []
    if not os.path.isdir(log_dir):
        return found
    for name in os.listdir(log_dir):
        full = os.path.join(log_dir, name)
        if not os.path.isfile(full):
            continue
        if name in ("kodi.log", "kodi_crashlog.log"):
            continue
        if not name.endswith((".log", ".old.log", ".dmp")):
            continue
        try:
            if os.path.getmtime(full) < cutoff:
                found.append(full)
        except OSError:
            continue
    return found


def _temp_targets():
    """Everything under special://temp except the live logs."""
    root = _temp()
    targets = []
    if not os.path.isdir(root):
        return targets
    for name in os.listdir(root):
        if name.endswith(KEEP_IN_TEMP):
            continue
        targets.append(os.path.join(root, name))
    return targets


def _remove(target):
    """Delete a file or tree. Returns bytes freed (0 if it could not be removed)."""
    size = tree_size(target)
    try:
        if os.path.isdir(target) and not os.path.islink(target):
            shutil.rmtree(target, ignore_errors=False)
        else:
            os.remove(target)
    except OSError as exc:
        log("could not remove %s: %s" % (target, exc), xbmc.LOGWARNING)
        return 0
    return size


def _tasks():
    """(label, targets, needs_restart) for each cleanup job."""
    textures = _textures_db()
    return [
        ("Add-on install packages", [_packages()], False),
        ("Temporary files", _temp_targets(), False),
        ("Thumbnail cache", [_thumbnails()], True),
        ("Texture database", [textures] if textures else [], True),
        ("Old log files (7+ days)", _old_logs(), False),
    ]


def report():
    """Show what each cleanup task would reclaim, without touching anything."""
    lines = []
    total = 0
    for label, targets, _restart in _tasks():
        size = sum(tree_size(t) for t in targets if t)
        total += size
        count = len([t for t in targets if t and os.path.exists(t)])
        lines.append("[B]%s[/B]  %s  (%d item%s)"
                     % (label, human(size), count, "" if count == 1 else "s"))
    lines.append("")
    lines.append("[B]Reclaimable total: %s[/B]" % human(total))
    xbmcgui.Dialog().textviewer("%s - storage report" % NAME, "\n".join(lines))


def run():
    """Let the user pick cleanup tasks, then run them."""
    tasks = [t for t in _tasks() if any(x and os.path.exists(x) for x in t[1])]
    if not tasks:
        notify("Nothing to clean")
        return

    labels = ["%s  (%s)" % (label, human(sum(tree_size(t) for t in targets)))
              for label, targets, _ in tasks]
    picked = xbmcgui.Dialog().multiselect("Select what to clean", labels,
                                          preselect=list(range(len(tasks))))
    if not picked:
        return

    chosen = [tasks[i] for i in picked]
    if not confirm(NAME, "Delete the selected caches?\nMedia files and settings are not touched.",
                   yes="Clean"):
        return

    progress = xbmcgui.DialogProgress()
    progress.create(NAME, "Cleaning...")
    freed = 0
    restart = False
    for index, (label, targets, needs_restart) in enumerate(chosen):
        if progress.iscanceled():
            break
        progress.update(int(index * 100 / len(chosen)), label)
        before = freed
        for target in targets:
            if target:
                freed += _remove(target)
        if needs_restart and freed > before:
            restart = True
    progress.close()

    # Kodi recreates these on demand; leaving them missing is fine, but the
    # packages folder is expected to exist by the addon installer.
    try:
        os.makedirs(_packages(), exist_ok=True)
    except OSError:
        pass

    notify("Reclaimed %s" % human(freed))
    if restart:
        if confirm(NAME, "Thumbnail/texture cache cleared.\nRestart Kodi now to rebuild it?",
                   yes="Restart", no="Later"):
            xbmc.executebuiltin("RestartApp")


def clean_library():
    """Remove entries whose files no longer exist."""
    options = ["Video library", "Music library", "Both"]
    choice = xbmcgui.Dialog().select("Clean which library?", options)
    if choice < 0:
        return
    if not confirm(NAME, "Remove library entries whose files are missing?\n"
                         "This does not delete any media.", yes="Clean"):
        return
    if choice in (0, 2):
        xbmc.executebuiltin("CleanLibrary(video)")
    if choice in (1, 2):
        xbmc.executebuiltin("CleanLibrary(music)")
    notify("Library clean started")
