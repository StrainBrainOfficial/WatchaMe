This book documents the repository in this directory: what each file does, how the build pipeline works, and how to run it. It assumes the repo exists — it is an operations manual, not a from-scratch tutorial.

The design decision behind it: **this is a repository, not a build.** A build is a snapshot of somebody's `userdata` and `addons` folders. It cannot update itself, reinstalling it wipes your configuration, and it breaks on every Kodi release. A repository is the mechanism Kodi natively polls, so every add-on inside it updates individually, forever. The one-click convenience people actually want from a build is provided by an add-on *inside* the repository — the Toolbox — which installs the whole curated set in one pass. Book Two covers using it.

# Part 0 — How a Kodi repository works

Four moving parts.

| Piece | What it is | Where |
|---|---|---|
| Add-on zip | An add-on folder, zipped, named `id-version.zip` | `docs/zips/<id>/` |
| Index | `addons.xml` — every add-on's `addon.xml` concatenated | `docs/addons.xml` |
| Checksum | MD5 of the index | `docs/addons.xml.md5` |
| Repository add-on | A tiny add-on holding the URLs to the three above | `docs/repository.kodikit.zip` |

The update loop:

1. Kodi periodically downloads `addons.xml.md5`. It is 32 bytes, so this is cheap.
2. If that hash differs from last time, it downloads the full `addons.xml`.
3. It compares each `version=` against what is installed.
4. Anything newer is downloaded from `docs/zips/` and installed.

So automatic updates reduce to one rule: **when an add-on changes, its version must increase and the index must be regenerated.** `scripts/build_repo.py` does both, and CI runs it daily.

> **The most common failure in any Kodi repo.** Files change but `version=` does not. Kodi concludes it is already current and never downloads the change. Nothing in the logs looks wrong. The builder here avoids this for mirrored add-ons by reading the version from upstream's own `addon.xml`, but for local add-ons in `src/` you must bump it yourself.

# Part 1 — Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.8+ | Runs the builder. No third-party packages except Pillow for artwork. |
| Git + a GitHub account | The repo must be public — Kodi has no credential handling worth using. |
| Network access | The builder calls the GitHub API and `mirrors.kodi.tv`. |
| Kodi 21 (Omega) or 22 (Piers) | What the dependency checker validates against. |

\pagebreak

# Part 2 — Layout

```
kodi-repo/
├── addons.json            THE CURATED LIST - what to mirror and what to install
├── repo.config.json       Repo identity: name, ids, GitHub target, hosting
├── scripts/
│   ├── build_repo.py      Sync mirrors, package, build repo addon, write index
│   ├── check_deps.py      Verify every <import> resolves. Hard-fails CI.
│   └── make_art.py        Regenerate icon.png / fanart.png (needs Pillow)
├── src/
│   └── script.kodikit.toolbox/   The one-click installer + maintenance addon
├── assets/                Committed icon and fanart
├── docs/                  PUBLISHED TREE - the only part Kodi ever reads
│   ├── addons.xml         GENERATED index
│   ├── addons.xml.md5     GENERATED checksum; the update trigger
│   ├── index.html         GENERATED landing page
│   ├── repository.kodikit.zip     Stable-URL copy of the repo addon
│   └── zips/<id>/<id>-<version>.zip (+ .md5)
└── guides/                This documentation
```

## What you edit versus what is generated

Confusing these is the classic mistake. Everything under `docs/` is regenerated on every build; hand-edits are lost, and editing `addons.xml` directly breaks the checksum and invalidates the whole repository.

| Path | Who writes it | Edit by hand? |
|---|---|---|
| `addons.json`, `repo.config.json` | You | **Yes — this is the control surface** |
| `src/**` | You | Yes |
| `scripts/**` | You | Rarely |
| `docs/**` | `build_repo.py` | **Never** |

`docs/` is committed even though it is generated, because that is what GitHub serves to Kodi. That is the whole delivery mechanism.

## Why `docs/`

The published tree is called `docs/` because GitHub Pages can serve a `/docs` folder directly. It works identically over raw URLs without Pages enabled, which is the current default — see Part 7.

# Part 3 — Configuration

Everything about the repo's identity lives in `repo.config.json`:

| Field | Current value | What it controls |
|---|---|---|
| `repo_id` | `repository.kodikit` | Add-on ID of the repository itself. Globally unique, permanent. |
| `repo_name` | `KodiKit` | Display name in Kodi's UI. Cosmetic. |
| `repo_version` | `1.0.0` | Bump when the repo add-on's own URLs or metadata change. |
| `provider` | `StrainBrainOfficial` | Shown as the author. Cosmetic. |
| `github_user` / `github_repo` | `StrainBrainOfficial` / `kodi-repo` | **Baked into every URL.** Must match where you actually push. |
| `branch` | `main` | Branch the URLs point at. |
| `hosting` | `raw` | `raw` or `pages` — see Part 7. |
| `keep_versions` | `2` | Old zips retained per add-on. |
| `toolbox_id` | `script.kodikit.toolbox` | Which local add-on the Toolbox is. |

**Renaming the repo:** edit `repo_id`, `repo_name`, `github_user`, `github_repo`, then rebuild. To rename the Toolbox too, rename `src/script.kodikit.toolbox/`, update the `id` in its `addon.xml`, and update `toolbox_id`.

> `github_user` and `github_repo` are concatenated into the URLs inside the repository add-on, which then ships to every device. Getting them wrong yields a repository that installs cleanly and then finds nothing — with no useful error. Push to exactly the path configured here.

\pagebreak

# Part 4 — What is in the curated set

The set is deliberately tools and utilities only. No streaming or scraper add-ons: those are what get repositories taken down, and they break every few weeks. This one is built to still work in a year untouched.

Add-ons reach a device by one of three routes, and the distinction matters:

**1. Mirrored here (3).** Packaged into this repo because Kodi's official repo does not carry them. Re-synced from upstream daily.

| ID | What it does |
|---|---|
| `service.subtitles.a4ksubtitles` | Multi-source subtitle search — OpenSubtitles, Addic7ed, Podnapisi, SubDL, SubSource |
| `script.black.bars.never` | Detects and removes black bars during playback, **including hardcoded ones** |
| `script.service.janitor` | Deletes watched video files on a schedule to reclaim disk |

**2. Installed from Kodi's official repo (17).** The Toolbox installs these *by ID*, so they stay on the official update channel — which is where you want them. Includes `inputstream.adaptive`, `inputstream.ffmpegdirect`, `script.trakt`, `service.upnext`, `script.kodi.loguploader`, `plugin.video.youtube`, and optional entries like `skin.copacetic`, `script.plexmod` and `pvr.iptvsimple`.

**3. From a vendor's own repo (2).** Listed in the README, not installed automatically, because they resolve dependencies the official repo cannot: TheMovieDb Helper 6.x and Jellyfin for Kodi.

> **Why route 2 exists.** Mirroring an add-on that Kodi's official repo already carries would fork it onto your update channel and make you responsible for tracking it. Installing by ID keeps it on the maintainer's channel. Only mirror what is genuinely unavailable.

# Part 5 — Adding or removing an add-on

One entry in `addons.json`:

```
{
  "id": "script.example",
  "name": "Example",
  "category": "tools",
  "why": "What it does and why it earned a slot.",
  "github": "owner/repo",
  "track": "release"
}
```

| Field | Meaning |
|---|---|
| `id` | The add-on ID. Must match the `id=` in its own `addon.xml`. |
| `why` | Prose. Forces a justification for every slot; it also ends up in the README. |
| `github` | `owner/repo` — omit for an add-on installed from the official repo by ID. |
| `track` | `release` (newest published release, falling back to the default branch) or `branch` (always the branch head). |
| `ref` | Pin to a specific branch, e.g. `"ref": "matrix"`. |
| `optional` | `true` leaves it unticked in the Toolbox's multi-select. |

The builder locates the add-on inside the downloaded tarball by **scanning for an `addon.xml` whose `id` matches**, so it copes with any upstream repo layout — nested folders, differently named directories, monorepos. You do not repack anything by hand.

To remove one, delete its entry and rebuild. Its zips stay in `docs/zips/` until pruned; installed copies on devices remain but stop receiving updates.

\pagebreak

# Part 6 — The build pipeline

```
python3 scripts/build_repo.py && python3 scripts/check_deps.py
```

`build_repo.py` runs four stages:

**1. Sync mirrored add-ons.** For each `github` entry, ask the GitHub API for the newest release (or branch head), download the tarball, find the add-on folder, and repackage it as a Kodi-shaped zip with `<id>/addon.xml` at the root. Versions already present are skipped, so a quiet day produces no output and no commit.

**2. Package local add-ons.** Everything in `src/` is zipped at the version in its `addon.xml`. **This is where you must have bumped the version yourself** — the builder packages what it is told.

**3. Build the repository add-on.** Generates `addon.xml` from `repo.config.json`, zips it into `docs/zips/`, and writes a stable copy at `docs/repository.kodikit.zip` so the install URL never changes with version.

**4. Regenerate the index.** Collects the newest zip per add-on, concatenates their `addon.xml` bodies into `docs/addons.xml`, writes the MD5, prunes to `keep_versions`, and regenerates `docs/index.html`.

Zips are written with **fixed timestamps**, so identical content produces byte-identical output. Without this, every run would produce a different zip and CI would commit noise daily.

## The dependency checker

`check_deps.py` fetches Kodi's official `addons.xml.gz` for **Omega and Piers**, unions it with this repo's own IDs, and verifies every non-optional `<import>` in the index resolves against at least one. It **fails the build** if not.

```
checked 5 add-ons against: omega, piers
all dependencies resolve
```

This is not ceremony. An unresolvable dependency makes Kodi refuse to install the add-on, and the failure appears on the user's device, not in your build. It has already earned its place: TheMovieDb Helper 6.x hard-requires `script.module.pil`, a compiled Pillow module **no official Kodi repo ships**. Mirroring it would have shipped an add-on that cannot install. The checker caught it, so 6.x is documented under the vendor-repo route and the dependency-clean 5.x is in the one-click list instead.

If the official index is unreachable the check warns and passes rather than blocking on a network failure.

# Part 7 — Publishing

Two hosting modes, set by `hosting` in `repo.config.json`.

| Mode | URL form | Notes |
|---|---|---|
| `raw` (current) | `raw.githubusercontent.com/USER/REPO/main/docs` | Works immediately after push, no setup. ~5 min cache. |
| `pages` | `USER.github.io/REPO` | Better caching. Requires enabling Pages for `/docs`. |

Switching modes changes the URLs baked into the repository add-on, so **existing users must reinstall the repo zip once.** Choose before distributing.

Verify after pushing:

```
curl -sI https://raw.githubusercontent.com/USER/REPO/main/docs/addons.xml | head -1
curl -s  https://raw.githubusercontent.com/USER/REPO/main/docs/addons.xml.md5
```

The first must return `200`; the second a bare 32-character hex string.

# Part 8 — Automation

`.github/workflows/sync.yml` runs daily at 05:15 UTC, on manual dispatch, and on pushes that touch `addons.json`, `repo.config.json`, `src/`, `scripts/`, or the workflow itself.

It runs the builder, then the dependency checker, and commits `docs/` back to the branch only if something changed. A `concurrency` group prevents overlapping runs from fighting over the same commit.

The full unattended chain:

```
upstream publishes  ->  05:15 UTC sync job packages the new version
                    ->  check_deps.py verifies it can actually install
                    ->  docs/ committed, addons.xml.md5 changes
                    ->  Kodi notices within 24h and installs silently
```

Worst case is about 48 hours from upstream release to device.

\pagebreak

# Part 9 — Making sure updates actually land

Three things must line up.

**Kodi must be set to auto-update.** Settings → Add-ons → Updates → *Install updates automatically*. In `guisettings.xml` this is `general.addonupdates` = `0` (`1` notifies, `2` never). There is also a per-add-on override in Add-on info → Auto-update; if one was ever set to Never, the global setting will not rescue it.

**The version must increase.** Kodi only moves upward. Re-uploading a zip with the same version does nothing regardless of content, and lowering a version to force a change does nothing either. A broken release is fixed with a **higher** patch version, never a re-upload.

**The checksum must change.** That is what Kodi polls. The builder handles it; the only way to break it is editing `docs/addons.xml` by hand afterwards.

To force an immediate check on a device: Add-ons → My add-ons → select the repository → Check for updates. Remotely, toggling the repository off and on forces a re-scan on the next cycle:

```
curl -s -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled",
       "params":{"addonid":"repository.kodikit","enabled":true}}' \
  http://DEVICE-IP:8080/jsonrpc
```

If an update does not land, `kodi.log` is definitive:

```
adb shell "grep -i 'repository.kodikit\|CRepository' \
  /sdcard/Android/data/org.xbmc.kodi/files/.kodi/temp/kodi.log | tail -40"
```

`CRepository::FetchIndex` failures point at URLs or checksums; "no update available" against a bumped version points at a stale index.

# Part 10 — Installing on a device, in order

Order is part of the procedure, not a detail. Four rules drive it:

| Rule | Consequence |
|---|---|
| Config files are read at startup | `advancedsettings.xml` must exist before Kodi is used |
| InputStream add-ons underpin playback | They come before anything that plays video |
| Declared dependencies resolve automatically | Never hand-install `script.module.*` |
| Services claim defaults on first run | Subtitles must be in place before you set the default |

**Phase A — Foundation**

| # | Step |
|---|---|
| 1 | Install Kodi, launch once, quit |
| 2 | Settings → System → Add-ons → **Unknown sources → On** |
| 3 | Settings → Add-ons → Updates → **Install updates automatically** |
| 4 | Settings → File manager → Add source → the URL from Part 7, named `kodikit` |
| 5 | Add-ons → Install from zip file → `kodikit` → `repository.kodikit.zip` |
| 6 | Add-ons → Install from repository → KodiKit → install **KodiKit Toolbox** |

Step 3 goes before any add-on exists so every one inherits it. Step 5 matters more than it looks: an add-on sideloaded from a loose zip belongs to no repository, so Kodi has nowhere to check for updates and it stays at its installed version forever.

**Phase B — The Toolbox does the rest**

Open the Toolbox → **Install curated add-ons**. It multi-selects the whole set, filters out anything already installed, and leaves optional entries unticked. Kodi resolves each add-on's declared dependencies automatically and in the right order, which is why there is no manual InputStream step here — installing the parents pulls them.

**Phase C — Tune and finish**

| # | Step |
|---|---|
| 7 | Toolbox → **Apply streaming cache tuning** → pick your device profile → restart |
| 8 | Set the subtitle default: Settings → Player → Language → a4kSubtitles. **An unset default is why "subtitles don't work".** |
| 9 | Toolbox → **Clean up caches** to clear install debris |
| 10 | Optional: enable Settings → Services → Control → Allow remote control via HTTP, for remote diagnosis |

That is the whole deployment. Book Two applies it to a Fire TV Stick with device-specific numbers.

\pagebreak

# Part 11 — Maintenance

| Task | When | How |
|---|---|---|
| Add or drop a curated add-on | Any time | Edit `addons.json`, push. CI rebuilds. |
| Change the Toolbox | Any time | Edit `src/`, **bump its `addon.xml` version**, push |
| Change repo identity or URLs | Rarely | Edit `repo.config.json`, bump `repo_version`, and have users reinstall the repo zip |
| Regenerate artwork | Rarely | `python3 scripts/make_art.py` (needs Pillow) |
| Check upstream health | Monthly | Read the sync job's log for skipped or failed mirrors |

# Part 12 — Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| "Could not connect to repository" | `github_user`/`github_repo` wrong, or repo private | `curl` the URL; confirm 200 and public |
| Repository installs, shows no add-ons | Index empty or checksum stale | Re-run the builder; never hand-edit `docs/` |
| "Failed to install add-on" | Zip name does not match `id-version.zip` | Re-run the builder; it names them |
| "Dependency not met" | Unresolvable `<import>` | Run `check_deps.py`; mirror the missing module |
| Add-on installs, never updates | Version not bumped | Bump it in `addon.xml` and rebuild |
| One add-on never updates | Per-add-on auto-update set to Never | Add-on info → Auto-update → On |
| CI commits every day with no real change | Zip timestamps not fixed | Already handled here; do not remove the fixed-timestamp logic |
| Sync job fails on one add-on | Upstream renamed a release or branch | Set `ref` explicitly in `addons.json` |
| Updates only appear after a restart | Normal 24h poll cycle | Force a check, or accept the cadence |
