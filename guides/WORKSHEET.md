# Worksheet

Fill this in as you follow the guide. Every blank is used by a numbered step, and the step is named beside it.

## 1. Your values

Fill these in once, in Book One, Part 1.

| What | Used by | Your value |
|---|---|---|
| GitHub username or org | 2.2 `github_user` | |
| Repository name | 2.2 `github_repo` | |
| Repository display name | 2.2 `repo_name` | |
| Provider / author name | 2.2 `provider` | |
| **Install URL** | 3.6, and Book Two step 17 | `https://raw.githubusercontent.com/______/______/main/docs` |
| Fire TV Stick IP address | Book Two steps 4, 5 | |
| Kodi version on the stick | Book Two step 6 | |

## 2. Add-ons you want

One row per add-on. Fill the first two columns, run the probe in step 4.2, then complete the rest.

| Display name | Add-on ID | Probe result | Section | `optional`? | Added |
|---|---|---|---|---|---|
| | | IN / NOT in official | mirror / official / external | yes / no | [ ] |
| | | | | | [ ] |
| | | | | | [ ] |
| | | | | | [ ] |
| | | | | | [ ] |
| | | | | | [ ] |
| | | | | | [ ] |
| | | | | | [ ] |

Reminder: after adding entries, **bump the Toolbox version** (step 4.4) or no device will ever see them.

## 3. Book One checklist

**Part 1 — GitHub setup** *(once per machine; skip if `gh auth status` already shows you logged in)*

- [ ] 1.1 GitHub account exists
- [ ] 1.2 `git`, `gh` and `python3` installed, all reporting a version
- [ ] 1.3 `git config --global user.name` and `user.email` set
- [ ] 1.4 `gh auth login` done; `gh auth status` shows *Logged in*
- [ ] 1.5 Repository directory on this machine

**Part 2 — Configure the repository**

- [ ] 2.1 In the repository directory
- [ ] 2.2 Four identity fields set in `repo.config.json`
- [ ] 2.3 `build_repo.py` ran; served-from URL matches your values
- [ ] 2.4 `check_deps.py` says *all dependencies resolve*
- [ ] 2.5 Committed

**Part 3 — Publish**

- [ ] 3.1 Repository created, public
- [ ] 3.2 Pushed, with no authentication prompt
- [ ] 3.3 Actions run green
- [ ] 3.4 All three URLs verified (200 / 32-char hash / 200)
- [ ] 3.5 Workflows enabled in the Actions tab
- [ ] 3.6 Install URL written into section 1 above

## 4. Book Two checklist

- [ ] **Stage A** (1–5) Developer options on, unknown sources on, IP noted
- [ ] **Stage B** (6–8) Kodi installed (`armeabi-v7a`), launched once, quit
- [ ] **Stage C** (9–13) Surfshark installed, auto-connect on, `tun0` confirmed
- [ ] **Stage D** (14–20) Auto-update set *before* add-ons, source added, repository and Toolbox installed
- [ ] **Stage E** (21–23) Curated add-ons installed, unwanted entries unticked
- [ ] **Stage F** (24–30) Cache profile applied, subtitle default set, MediaCodec Surface on
- [ ] **Stage G** (31–34) Rebooted, memory and disk within targets, `addonupdates` = `0`, playback clean

## 5. Measured results

From Book Two, step 32. Compare against the targets in the same step.

| Metric | Target (Stick 4K) | Measured |
|---|---|---|
| TOTAL PSS idle | under 600 MB | |
| `.kodi/` on disk | under 500 MB | |
| Cold start | under 18 s | |
| Background services | 6 or fewer | |
| `general.addonupdates` | `0` | |
