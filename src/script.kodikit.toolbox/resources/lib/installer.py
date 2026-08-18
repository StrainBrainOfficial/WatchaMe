"""Bulk-install the curated add-on set."""
import json
import os

import xbmc
import xbmcaddon
import xbmcgui

from .common import NAME, confirm, log, notify

ADDON = xbmcaddon.Addon()


def _manifest():
    manifest_path = os.path.join(
        xbmcaddon.Addon().getAddonInfo("path"), "resources", "addons.json")
    try:
        with open(manifest_path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError) as exc:
        log("cannot read bundled manifest: %s" % exc, xbmc.LOGERROR)
        return {}


def _installed(addon_id):
    return xbmc.getCondVisibility("System.HasAddon(%s)" % addon_id) == 1


def _catalogue():
    """Flatten the manifest into display rows, mirrors first."""
    manifest = _manifest()
    rows = []
    for source in ("mirror", "official"):
        for entry in manifest.get(source, []):
            rows.append({
                "id": entry["id"],
                "name": entry.get("name", entry["id"]),
                "category": entry.get("category", "other"),
                "why": entry.get("why", ""),
                "optional": bool(entry.get("optional")),
                "installed": _installed(entry["id"]),
            })
    rows.sort(key=lambda r: (r["optional"], r["category"], r["name"].lower()))
    return rows


def run():
    rows = _catalogue()
    if not rows:
        notify("Add-on list unavailable", xbmcgui.NOTIFICATION_ERROR)
        return

    pending = [r for r in rows if not r["installed"]]
    if not pending:
        notify("Everything in the list is already installed")
        return

    labels = []
    for row in pending:
        tag = "[COLOR grey](optional)[/COLOR] " if row["optional"] else ""
        labels.append("%s%s  [COLOR grey]- %s[/COLOR]" % (tag, row["name"], row["category"]))

    # Preselect the non-optional ones: that is the "recommended build".
    preselect = [i for i, row in enumerate(pending) if not row["optional"]]
    picked = xbmcgui.Dialog().multiselect(
        "Select add-ons to install (%d already present)" % (len(rows) - len(pending)),
        labels, preselect=preselect)
    if not picked:
        return

    chosen = [pending[i] for i in picked]
    if not confirm(NAME,
                   "Install %d add-on(s)?\nKodi will ask you to confirm each one." % len(chosen),
                   yes="Install"):
        return

    progress = xbmcgui.DialogProgress()
    progress.create(NAME, "Installing...")
    done, failed = [], []
    for index, row in enumerate(chosen):
        if progress.iscanceled():
            break
        progress.update(int(index * 100 / len(chosen)), "%s" % row["name"])
        try:
            # Blocking form: returns once the install dialog is dismissed.
            xbmc.executebuiltin("InstallAddon(%s)" % row["id"], True)
        except Exception as exc:  # pragma: no cover - Kodi runtime only
            log("install failed for %s: %s" % (row["id"], exc), xbmc.LOGERROR)
        (done if _installed(row["id"]) else failed).append(row["name"])
    progress.close()

    summary = ["[B]Installed (%d)[/B]" % len(done)] + ["  %s" % n for n in done]
    if failed:
        summary += ["", "[B]Not installed (%d)[/B]" % len(failed)] + ["  %s" % n for n in failed]
        summary += ["", "Skipped or declined add-ons can be installed again at any time."]
    xbmcgui.Dialog().textviewer("%s - install summary" % NAME, "\n".join(summary))
