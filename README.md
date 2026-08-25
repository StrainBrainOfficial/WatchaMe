# KodiKit — a curated, self-updating Kodi repository

A lightweight curated repository of high-quality Kodi tools: subtitles, Trakt scrobbling, black-bar removal, metadata, maintenance and cleanup utilities. Mirrors are refreshed automatically from upstream every day.

**Everything here is a tool or utility.** No streaming/scraper add-ons, no piracy
sources — those are what get repositories taken down and what breaks every few
weeks. This repo is built to still work in a year without you touching it.

---

## Repository or "build"? Read this first.

A **build** is a snapshot of someone's entire `userdata` + `addons` folder,
installed by a wizard. It cannot update itself. The only way to "update" a build
is to wipe your configuration and reinstall it, which is why builds rot, break on
every Kodi release, and lose your settings.

A **repository** is the mechanism Kodi natively polls for updates. Add it once and
every add-on inside it updates itself forever, individually, with no wizard.

So: **this is a repository**, and the one-click convenience people actually want
from a build is provided by an add-on inside it — **script.kodikit.toolbox** — which
installs the whole curated set in one pass and handles cleanup and tuning.
One-zip install, no snapshot, nothing to reinstall later.

---

## Install

1. In Kodi: **Settings → System → Add-ons** → enable **Unknown sources**.
2. **Settings → File manager → Add source**, and enter:

   ```
   https://raw.githubusercontent.com/StrainBrainOfficial/kodi-repo/main/docs/
   ```

   Name it `kodikit`.
3. **Add-ons → Install from zip file** → `kodikit` →
   `repository.kodikit.zip`
4. **Add-ons → Install from repository → KodiKit** → install
   **KodiKit Toolbox**.
5. Open the Toolbox → **Install curated add-ons** → confirm.

Direct zip link: `https://raw.githubusercontent.com/StrainBrainOfficial/kodi-repo/main/docs/repository.kodikit.zip`

---

## The Toolbox add-on

| Action | What it does |
|---|---|
| Install curated add-ons | Multi-select install of the whole list below. Already-installed add-ons are filtered out; optional ones are unticked by default. |
| Storage report | Shows exactly how much each cache is costing you, changing nothing. |
| Clean up caches | Package cache, temp files, thumbnails, texture DB, logs 7+ days old. Pick per item, see sizes first. Never touches media or settings. |
| Apply streaming cache tuning | Writes `advancedsettings.xml` from a device profile — Fire TV Stick, low-memory, balanced or large. The two constrained profiles also cap cached artwork resolution, enable dirty-region redraw and shorten network timeouts. Backs up any existing file with a timestamp first. |
| Clean video/music library | Removes library entries whose files are gone. Deletes no media. |

It can also be driven directly, e.g. from a keymap or another script:

```
RunScript(script.kodikit.toolbox,cleanup)
```

Valid arguments: `install`, `report`, `cleanup`, `tweaks`, `library`.

---

## What's included

### Mirrored in this repo (3)

Packaged here because the official Kodi repo doesn't carry them. Re-synced from
upstream daily.

| ID | Add-on | Why it's here | Upstream |
|---|---|---|---|
| `service.subtitles.a4ksubtitles` | a4kSubtitles | Multi-source subtitle search (OpenSubtitles, Addic7ed, Podnapisi, SubDL, SubSource) in one addon. Not in the official repo. | [a4k-openproject/a4kSubtitles](https://github.com/a4k-openproject/a4kSubtitles) |
| `script.black.bars.never` | BlackBarsNever | Detects and removes black bars, including hardcoded ones, during playback. | [osumoclement/script.black.bars.never](https://github.com/osumoclement/script.black.bars.never) |
| `script.service.janitor` | Janitor | Deletes watched video files on a schedule to reclaim disk. Not in the official repo. | [Anthirian/script.filecleaner](https://github.com/Anthirian/script.filecleaner) |

### Installed from Kodi's official repo (17)

The Toolbox installs these by ID — they stay on the official update channel,
which is where you want them.

| ID | Add-on | Type | What it does |
|---|---|---|---|
| `script.trakt` | Trakt | tracking | Scrobbling, watched-state sync and lists across devices. |
| `service.upnext` | Up Next | playback | Netflix-style auto-play of the next episode. |
| `script.globalsearch` | Global Search | tools | Search the whole library and addons from one dialog. |
| `script.skinshortcuts` | Skin Shortcuts | skinning | Menu customisation; required by most good skins. |
| `script.keymap` | Keymap Editor | tools | Remap remote and keyboard buttons from the GUI. |
| `script.cu.lrclyrics` | CU LRC Lyrics | music | Synced lyrics during music playback. |
| `script.extendedinfo` | ExtendedInfo Script | metadata | Deep cast, similar-title and trailer browsing. |
| `script.embuary.helper` | Embuary Helper | skinning | Widget and skin helper used by many modern skins. |
| `script.embuary.info` | Embuary Info | metadata | Rich info dialogs for movies, shows and people. |
| `inputstream.adaptive` | InputStream Adaptive | playback | DASH/HLS/Smooth playback; required by most streaming addons. |
| `inputstream.ffmpegdirect` | InputStream FFmpegDirect | playback | Timeshift and better handling of live streams. |
| `plugin.video.youtube` | YouTube | video | The maintained YouTube client. |
| `script.kodi.loguploader` | Kodi Logfile Uploader | tools | One-click log upload when you need support. |
| `plugin.program.autocompletion` | Autocompletion | tools | Search suggestions in Kodi's on-screen keyboard. |
| `skin.copacetic` | Copacetic | skin | Fast, clean, actively maintained modern skin. *(optional)* |
| `script.plexmod` | Plex for Kodi | library | Plex media server integration. *(optional)* |
| `pvr.iptvsimple` | PVR IPTV Simple Client | pvr | Play your own M3U playlists as live TV channels. *(optional)* |

### Better from the vendor's own repo

**TheMovieDb Helper (6.x)** — Newer than the official repo's 5.x, but hard-requires script.module.pil, a compiled module no official repo ships. Upstream's own repo resolves it.  
Repo: <https://jurialmunkey.github.io/repository.jurialmunkey/>  
Provides: `plugin.video.themoviedb.helper`, `script.skinvariables`, `skin.arctic.horizon.2`

**Jellyfin for Kodi** — Generates its addon.xml at release time and publishes an auto-updating repo.  
Repo: <https://repo.jellyfin.org/files/client/kodi/>  
Provides: `plugin.video.jellyfin`

---

## How it stays up to date

`.github/workflows/sync.yml` runs daily (and on every push):

1. `scripts/build_repo.py` asks GitHub for each mirrored add-on's newest release,
   downloads it, and repackages it as a Kodi-shaped zip (`<id>/addon.xml` at the
   root). Versions already present are skipped, so a quiet day produces no commit.
2. `scripts/check_deps.py` verifies **every `<import>` in the repo resolves**
   against Kodi's Omega and Piers indexes or against this repo. This is a hard
   failure — it exists because an unresolvable dependency makes Kodi refuse to
   install the add-on, and it already caught one real case (see below).
3. If anything changed, the workflow commits `docs/` back to the branch. Kodi
   picks it up on its next check.

Zips are written with fixed timestamps, so identical content produces an
identical zip and no spurious commits.

### One thing worth knowing

TheMovieDb Helper 6.x hard-requires `script.module.pil`, a compiled Pillow module
that **no official Kodi repo ships** for Omega or Piers. Mirroring 6.x here would
have shipped an add-on that cannot install. The dependency checker caught it, so
6.x is listed under the vendor repo above and the dependency-clean official 5.x
build is in the one-click list instead.

---

## Making it yours

Everything is driven by two files.

**Add an add-on to mirror** — one entry in `addons.json`:

```json
{
  "id": "script.example",
  "name": "Example",
  "category": "tools",
  "why": "What it does and why it earned a slot.",
  "github": "owner/repo",
  "track": "release"
}
```

`track` is `release` (newest published release, falling back to the default
branch) or `branch` (always the branch head). Use `"ref": "somebranch"` to pin
one. The builder finds the add-on folder by scanning the archive for an
`addon.xml` whose `id` matches, so it copes with any repo layout. Add
`"optional": true` to leave it unticked in the Toolbox.

**Rename the repo** — edit `repo.config.json` (`repo_id`, `repo_name`,
`github_user`, `github_repo`), then rebuild. To rename the Toolbox as well,
rename `src/script.kodikit.toolbox/`, update its `addon.xml` id, and update
`toolbox_id` in the config.

**Host on GitHub Pages instead of raw URLs** — set `"hosting": "pages"` in
`repo.config.json`, enable Pages for the `/docs` folder, and rebuild. Pages
caches better; raw URLs need no setup. Note that changing this changes the URLs
baked into the repo zip, so existing users must reinstall the repo zip once.

**Build locally:**

```bash
python3 scripts/build_repo.py && python3 scripts/check_deps.py
```

`scripts/make_art.py` regenerates the icon and fanart; it needs Pillow, which is
why the artwork is committed rather than built in CI.

---

## Licensing

The mirrored add-ons are GPL and are redistributed unmodified, with their
licences and source intact — which is exactly what the GPL is for. Each entry in
`addons.json` records its upstream so provenance is always traceable. The
scripts and the Toolbox add-on in this repo are GPL-3.0-or-later.
