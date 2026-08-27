Every section here is a numbered procedure. Run the steps in order; each one is a command to type or a control to click. Lines marked **Check** tell you what success looks like — if you do not see it, stop there rather than continuing.

Background and troubleshooting live in the appendices, so the procedures stay short.

# Part 1 — First-time setup

Do this once, on the machine where you will maintain the repository.

**1.1 Verify your tools.**

```
python3 --version     # need 3.8 or newer
git --version
gh --version          # optional, only for Part 2
```

**1.2 Open the repository directory.**

```
cd ~/Dev/kodi-repo
```

**1.3 Set your identity.** Open `repo.config.json` and set these four fields:

| Field | Set it to |
|---|---|
| `github_user` | Your GitHub username or org, exactly as it appears in URLs |
| `github_repo` | The repository name you will push to |
| `repo_name` | The display name shown in Kodi. Anything readable. |
| `provider` | Your name, shown as the author |

Leave `repo_id`, `branch`, `hosting` and `keep_versions` alone unless Part 6 applies.

**1.4 Build.**

```
python3 scripts/build_repo.py
```

**Check:** the last two lines report the add-on count, an md5, and the URL it will serve from. That URL must contain your `github_user` and `github_repo` from step 1.3.

**1.5 Check dependencies.**

```
python3 scripts/check_deps.py
```

**Check:** `all dependencies resolve`. If not, go to Appendix C.

**1.6 Commit.**

```
git add -A && git commit -m "Configure repository identity"
```

# Part 2 — Publish to GitHub

Do this once. After it, everything is automatic.

**2.1 Sign in to GitHub.**

```
gh auth login
```

**2.2 Create the repository.** It must be public — Kodi cannot authenticate.

```
gh repo create YOURNAME/YOURREPO --public --source=. --remote=origin
```

**2.3 Push.**

```
git push -u origin main
```

**2.4 Wait for the build.**

```
gh run watch
```

**Check:** the run completes green. If it fails, read the log — it is running the same two commands you ran in 1.4 and 1.5.

**2.5 Verify what Kodi will see.** Three URLs must respond correctly.

```
BASE=https://raw.githubusercontent.com/YOURNAME/YOURREPO/main/docs
curl -sI  $BASE/addons.xml     | head -1     # expect: HTTP/2 200
curl -s   $BASE/addons.xml.md5               # expect: 32 hex characters, nothing else
curl -sI  $BASE/repository.kodikit.zip | head -1   # expect: HTTP/2 200
```

**Check:** all three as described. A 404 on the first two means step 1.3 does not match where you actually pushed.

**2.6 Write down the install URL.** This is what you type into Kodi in Book Two:

```
https://raw.githubusercontent.com/YOURNAME/YOURREPO/main/docs
```

\pagebreak

# Part 3 — Add an add-on

The repeatable procedure. Six steps.

**3.1 Find the add-on's ID.** Not its display name. Any one of:

| Source | Where to look |
|---|---|
| Its GitHub repo | `addon.xml` → the `id=` attribute of the root `<addon>` element |
| An installed copy | The folder name under `~/.kodi/addons/`, e.g. `script.trakt/` |
| Kodi | Add-ons → the add-on → Information |

**3.2 Decide which section it goes in.** Run this, with your IDs in the `probe` list:

```
python3 - <<'EOF'
import gzip, re, urllib.request
url = "https://mirrors.kodi.tv/addons/omega/addons.xml.gz"
req = urllib.request.Request(url, headers={"User-Agent": "kodikit"})
raw = gzip.decompress(urllib.request.urlopen(req, timeout=60).read()).decode("utf-8", "replace")
ids = set(re.findall(r'<addon\s+id="([^"]+)"', raw))
for probe in ["script.trakt", "service.vpn.manager"]:
    print("%-34s %s" % (probe, "IN official" if probe in ids else "NOT in official"))
EOF
```

| Result | Section | Why |
|---|---|---|
| `IN official` | `official` | Installed by ID; stays on the maintainer's update channel |
| `NOT in official` | `mirror` | Packaged into your repo from its GitHub source |
| Installs only from a vendor's own repo | `external` | Documented, never auto-installed — see Appendix A |

**3.3 Add the entry to `addons.json`.** Copy the matching shape.

For `mirror`:

```
{
  "id": "service.vpn.manager",
  "name": "VPN Manager for OpenVPN",
  "category": "privacy",
  "why": "One sentence on what it does and why it earned a slot.",
  "github": "Zomboided/service.vpn.manager",
  "track": "release",
  "optional": true
}
```

For `official` — no `github`, no `track`:

```
{
  "id": "script.trakt",
  "name": "Trakt",
  "category": "tracking",
  "why": "Scrobbling, watched-state sync and lists across devices."
}
```

For `external` — different shape entirely: no `id`, a vendor `url`, and the add-ons it provides:

```
{
  "name": "TheMovieDb Helper (6.x)",
  "why": "Hard-requires script.module.pil, which no official repo ships.",
  "url": "https://jurialmunkey.github.io/repository.jurialmunkey/",
  "addons": ["plugin.video.themoviedb.helper", "script.skinvariables"]
}
```

Field reference:

| Field | Sections | Meaning |
|---|---|---|
| `id` | mirror, official | Must match the add-on's own `addon.xml` exactly |
| `name` | all | Display name in the Toolbox picker |
| `category` | mirror, official | Groups and sorts the picker. In use: `subtitles`, `playback`, `tracking`, `tools`, `interface`, `privacy`. |
| `why` | all | Your justification. Ends up in the README. |
| `github` | mirror | `owner/repo` |
| `track` | mirror | `release` (newest release, falling back to branch head) or `branch` |
| `ref` | mirror | Pin a branch, e.g. `"ref": "matrix"` |
| `optional` | mirror, official | `true` leaves it **unticked** in the picker |

**3.4 Bump the Toolbox version.** Open `src/script.kodikit.toolbox/addon.xml` and increase the patch number, e.g. `1.2.1` → `1.2.2`.

> **Do not skip this.** The curated list ships *inside* the Toolbox. Change the list without changing the version and the published index stays byte-identical, so no device ever fetches your new list — while the build looks completely successful. `build_repo.py` now refuses to finish in that state and names the stale add-on.

**3.5 Build and check.**

```
python3 scripts/build_repo.py && python3 scripts/check_deps.py
```

**Check:** exit code 0, and `all dependencies resolve`. If the build stops with `content changed without a version bump`, you missed 3.4.

**3.6 Push.**

```
git add -A && git commit -m "Add <addon-id>" && git push
```

**Check:** run the verification in Part 8.

\pagebreak

# Part 4 — Remove an add-on

**4.1** Delete its entry from `addons.json`.

**4.2** Bump the Toolbox version in `src/script.kodikit.toolbox/addon.xml`.

**4.3** Build and push:

```
python3 scripts/build_repo.py && python3 scripts/check_deps.py
git add -A && git commit -m "Remove <addon-id>" && git push
```

**Check:** `grep '<addon id="<addon-id>"' docs/addons.xml` returns nothing.

> Copies already installed on devices keep working but stop receiving updates. A repository cannot retract an add-on — to remove it from a device, uninstall it there.

# Part 5 — Change the Toolbox itself

**5.1** Edit the code under `src/script.kodikit.toolbox/`.

**5.2** Bump the version in its `addon.xml` — patch for a fix, minor for new behaviour.

**5.3** Build, check, push:

```
python3 scripts/build_repo.py && python3 scripts/check_deps.py
git add -A && git commit -m "Toolbox: <what changed>" && git push
```

# Part 6 — Change the repository's identity or URLs

Only when moving the repo or renaming it.

**6.1** Edit `repo.config.json`: `github_user`, `github_repo`, `branch`, or `hosting`.

**6.2** Bump `repo_version` in the same file.

**6.3** Build and push as in 5.3.

**6.4** Reinstall the repository zip on **every device.** The old URLs are baked into the copy they already have.

> Because of 6.4, get `github_user` and `github_repo` right in Part 1 and leave them alone.

# Part 7 — Daily operation

Nothing to do. For reference, the scheduled job at 05:15 UTC:

1. Checks each mirrored add-on's upstream for a newer release.
2. Repackages anything that moved.
3. Runs the dependency check; a failure stops the commit.
4. Commits the regenerated `docs/` only if something changed.

Devices poll roughly every 24 hours, so worst case is about 48 hours from an upstream release to your stick.

To force a run now:

```
gh workflow run sync.yml && gh run watch
```

\pagebreak

# Part 8 — Health check

Run after any push, or whenever something looks wrong.

**8.1 The index lists what you expect.**

```
grep -o 'id="[^"]*" name="[^"]*" version="[^"]*"' docs/addons.xml
```

**8.2 A specific add-on is present.**

```
grep -o 'id="service.vpn.manager"[^>]*version="[^"]*"' docs/addons.xml
```

**8.3 Its zip is Kodi-shaped** — `<id>/addon.xml` must be at the root:

```
unzip -l docs/zips/service.vpn.manager/*.zip | head -5
```

**8.4 The Toolbox carries the current list.**

```
python3 -c "import zipfile,json,glob; z=sorted(glob.glob('docs/zips/script.kodikit.toolbox/*.zip'))[-1]; \
m=json.loads(zipfile.ZipFile(z).read('script.kodikit.toolbox/resources/addons.json')); \
print(sorted(e['id'] for s in ('mirror','official') for e in m[s]))"
```

**8.5 The live URLs still respond.** Re-run 2.5.

**8.6 On a device:** Toolbox → Install curated add-ons. New entries appear in the picker, unticked if you marked them `optional`.

# Appendix A — How it works

**The update loop.** Kodi downloads `addons.xml.md5` (32 bytes) on a ~24 hour cycle. If that hash changed, it downloads `addons.xml`, compares every `version=` against what is installed, and downloads anything newer from `docs/zips/`. So an update happens **only** when a version number increases. Re-uploading a zip at the same version does nothing; lowering a version does nothing. A broken release is fixed with a higher patch version, never a re-upload.

**The three routes.** `official` keeps an add-on on its maintainer's update channel — mirroring something Kodi already ships would fork it onto your channel and make you responsible for tracking it. `mirror` is for add-ons genuinely unavailable elsewhere. `external` is for add-ons whose dependencies nobody publishes: TheMovieDb Helper 6.x hard-requires `script.module.pil`, a compiled Pillow build no official repo ships, so mirroring it would deliver an add-on that cannot install.

**What the builder does.** Syncs mirrors from upstream; packages everything in `src/` at the version in its `addon.xml`; generates the repository add-on from `repo.config.json`; regenerates the index, checksum, `index.html`, and prunes old zips. Zips use fixed timestamps, so identical content produces identical bytes — otherwise CI would commit noise daily.

**What the dependency checker does.** Fetches Kodi's official index for Omega and Piers, unions it with your own IDs, and verifies every non-optional `<import>` resolves. It fails the build rather than letting a device discover the problem.

**Where the add-on ID appears.** Folder name in `docs/zips/`, zip filename, folder at the root inside the zip, and the `id=` in `addon.xml`. Kodi builds its download URL from the ID and version in the index, so any mismatch is a 404 that surfaces as "failed to install". The builder derives all four from one source, which is why you never rename zips by hand.

# Appendix B — File map

| Path | Purpose | Edit? |
|---|---|---|
| `addons.json` | The curated list | **Yes — this is the control surface** |
| `repo.config.json` | Repo identity, hosting, versions | Yes |
| `src/` | Add-ons you maintain | Yes |
| `scripts/build_repo.py` | The builder | Rarely |
| `scripts/check_deps.py` | Dependency validation | Rarely |
| `scripts/make_art.py` | Regenerates icon/fanart (needs Pillow) | Rarely |
| `assets/` | Committed icon and fanart | Rarely |
| `docs/` | **Published tree — what Kodi downloads** | **Never by hand** |
| `guides/` | This document's source | Yes |

# Appendix C — Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Build stops: `content changed without a version bump` | The working case, caught | Bump the version in `src/<addon>/addon.xml`, rebuild |
| `check_deps` reports an unresolvable import | A dependency nobody publishes | Move the add-on to `external` and document the vendor repo |
| Mirror sync: `no published release, falling back to branch head` | Upstream publishes no releases | Normal. Set `"track": "branch"` to make it explicit. |
| Mirror sync: add-on not found in the tarball | `id` does not match upstream's `addon.xml` | Correct the `id` |
| Mirror sync fails after an upstream rename | Default branch changed | Set `"ref"` explicitly |
| Kodi: "Could not connect to repository" | `github_user`/`github_repo` wrong, or repo private | Re-run 2.5; confirm the repo is public |
| Kodi: repository installs but lists nothing | Index empty, or checksum stale | Re-run 1.4; never hand-edit `docs/` |
| Kodi: "Failed to install add-on" | Zip name does not match `id-version.zip` | Re-run 1.4; the builder names them |
| Kodi: "Dependency not met" | Unresolvable `<import>` | Run 1.5 |
| An add-on never updates on one device | Per-add-on auto-update set to Never | Add-on info → Auto-update → On |
| Updates appear only after a restart | Normal 24-hour poll cycle | Force a check on the device, or wait |
