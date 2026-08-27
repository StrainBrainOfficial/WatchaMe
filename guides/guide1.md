Every section here is a numbered procedure. Run the steps in order; each one is a command to type or a control to click. Lines marked **Check** tell you what success looks like — if you do not see it, stop there rather than continuing.

Start at Part 1 if you have never set up GitHub on this machine. If `gh auth status` already reports you as logged in, skip to Part 2. **Prefer not to use a terminal at all?** Appendix D is the same work done entirely in a web browser.

**First time through, read Parts 1 to 4 in order and stop there:**

```
1  GitHub setup      account, tools, sign in
2  Configure         name the repository
3  Choose add-ons    decide what it carries      <- do this BEFORE publishing
4  Publish           push it live, verify the URLs
   then Book Two     install on the device       <- last, and only once the above is done
```

Parts 5 to 9 are for afterwards: removing an add-on, changing the Toolbox, moving the repository, and checking its health. You do not need them on a first run.

Background and troubleshooting live in the appendices, so the procedures stay short.

# Part 1 — GitHub setup

**Where:** terminal on your computer, plus a browser for 1.1 and the sign-in approval in 1.4. Skip this part entirely if you are using the browser-only route in Appendix D.

Do this once per machine.

**1.1 Create a GitHub account** — skip if you have one.

Go to **github.com/signup** and register. Your username becomes part of every URL your devices fetch from, so pick one you are willing to keep.

**1.2 Install the tools.**

*macOS (Homebrew):*

```
brew install git gh
```

*Debian / Ubuntu:*

```
sudo apt update && sudo apt install git gh python3
```

*Windows:*

```
winget install Git.Git GitHub.cli Python.Python.3.12
```

**Check:** all three report a version.

```
python3 --version     # need 3.8 or newer
git --version
gh --version
```

**1.3 Tell git who you are.** Commits fail or land under the wrong name without this.

```
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
```

**Check:**

```
git config --global user.name && git config --global user.email
```

> Use the email attached to your GitHub account, or commits will not be linked to your profile. GitHub also offers a `@users.noreply.github.com` address if you would rather not publish a real one.

**1.4 Sign in to GitHub from the terminal.**

```
gh auth login
```

It asks four questions. The answers:

| Prompt | Answer |
|---|---|
| What account do you want to log into? | **GitHub.com** |
| What is your preferred protocol for Git operations? | **HTTPS** |
| Authenticate Git with your GitHub credentials? | **Yes** |
| How would you like to authenticate? | **Login with a web browser** |

It then shows a one-time code. Copy it, press Enter, and your browser opens; paste the code and approve. The token is stored in your system credential store.

**Check:**

```
gh auth status
```

You want `Logged in to github.com account YOURNAME` and a token with the `repo`, `read:org` and `gist` scopes.

> **Headless machine, or no browser?** Create a personal access token (classic) at **github.com/settings/tokens** with the `repo`, `read:org` and `gist` scopes, then pipe it in: `gh auth login --with-token < token.txt`.

**1.5 Get the repository onto this machine.**

If you already have the directory, just note where it is. Otherwise clone it:

```
git clone https://github.com/YOURNAME/YOURREPO.git ~/Dev/kodi-repo
```

Starting from scratch instead? Copy the repository files into a new directory and:

```
cd ~/Dev/kodi-repo && git init -b main
```

\pagebreak

# Part 2 — Configure the repository

**Where:** terminal and a text editor. No browser.

**2.1 Open the repository directory.**

```
cd ~/Dev/kodi-repo
```

**2.2 Set your identity.** Open `repo.config.json` and set these four fields. Record them in the worksheet (Book Three) as you go — the install URL in Part 3 is built from them.

| Field | Set it to |
|---|---|
| `github_user` | Your GitHub username or org, exactly as it appears in URLs — the **Owner** field on GitHub's create page |
| `github_repo` | The repository name, matching the **Repository name** field exactly, capitals included |
| `repo_name` | The display name shown in Kodi. Anything readable. |
| `provider` | Your name, shown as the author |

Leave `repo_id`, `branch`, `hosting` and `keep_versions` alone unless Part 7 applies.

**2.3 Build.**

```
python3 scripts/build_repo.py
```

**Check:** the last two lines report the add-on count, an md5, and the URL it will serve from. That URL must contain your `github_user` and `github_repo` from 2.2.

**2.4 Check dependencies.**

```
python3 scripts/check_deps.py
```

**Check:** `all dependencies resolve`. If not, go to Appendix C.

**2.5 Commit.**

```
git add -A && git commit -m "Configure repository identity"
```

# Part 3 — Choose your add-ons

**Where:** terminal and a text editor. No browser.

This is where you decide what your repository carries. Do it before you publish, and again whenever you want to change the set.

You fill in one file and run one command. The whole part is:

```
1  edit addons.wishlist.txt          list what you want
2  python3 scripts/plan_addons.py    check it
3  ...fix anything it flags
4  python3 scripts/plan_addons.py --apply
5  ...write a "why" for each new entry
6  build, check, push
```

**3.1 List what you want.** Open **`addons.wishlist.txt`** in the repository root. It ships with 22 blank slots, each holding two placeholders:

```
REPLACE_ID_01    REPLACE_SOURCE_01
REPLACE_ID_02    REPLACE_SOURCE_02
```

Overwrite them in place. Replace `REPLACE_ID_nn` with the add-on's id, and `REPLACE_SOURCE_nn` with where it comes from — or **delete that word entirely** if the add-on is in Kodi's official repository:

```
script.trakt
service.subtitles.a4ksubtitles   a4k-openproject/a4kSubtitles
script.skinvariables             https://raw.githubusercontent.com/owner/repo/master/omega/zips
script.plexmod                                                        optional
```

Slots you have not touched are ignored, so fill in as many as you need and leave the rest — the planner reports how many are still blank. Need more than 22? Copy a slot line.

| Field | Required | Meaning |
|---|---|---|
| add-on id | **Yes** | The real id, not the display name. Find it in the add-on's own `addon.xml`, or as the folder name under `~/.kodi/addons/`. |
| source | Only sometimes | Where it comes from. Needed for anything **not** in Kodi's official repository — you do not have to know which those are; step 3.2 tells you. One of the three forms below. |
| `optional` | No | Leaves the entry **unticked** in the Toolbox picker. Use it for anything needing credentials, a subscription, or extra hardware. |

Everything after a `#` is a comment, so the instructions already in the file can stay.

The source is one of three forms, and you will need one for every add-on that Kodi does not ship itself:

| Form | Use when | Example |
|---|---|---|
| `owner/repo` | It lives on GitHub | `a4k-openproject/a4kSubtitles` |
| `https://…/zips` | It is served by another Kodi repository — the directory holding that repo's `addons.xml` | `https://raw.githubusercontent.com/owner/repo/master/omega/zips` |
| `https://…/x-1.2.3.zip` | All you have is a fixed zip | `https://host/plugin.video.x-1.2.3.zip` |

Prefer the first two. Both track the newest version automatically; a fixed zip only changes when that URL's contents change.

> **You know the repositories but not the add-on ids?** Paste their URLs into **`addons.repos.txt`**, one per line, and run:
>
> `python3 scripts/plan_addons.py --discover`
>
> It visits each one and prints every add-on served, with the source path already formatted for the wishlist — copy the lines you want. Any URL shape works: a landing page, a directory listing, a repository zip, or a folder holding an `addons.xml`. It follows nested indexes too, since vendor repos routinely split add-ons across per-Kodi-version directories, and keeps the newest version when one appears in several.
>
> To check a single repository without editing the file, pass it directly: `python3 scripts/plan_addons.py --discover https://that-repo/`

**3.2 Check the list.**

```
python3 scripts/plan_addons.py
```

It reads your wishlist, checks every id against Kodi's official Omega and Piers indexes, and prints one line each:

```
  --  service.subtitles.a4ksubtitles    already in addons.json
  ok  script.trakt                      official  (installed by id)
  ok  plugin.video.example              mirror    (github owner/repo)
  ok  script.fromvendor                 mirror    (kodi repo)
  ok  script.pinned                     mirror    (fixed zip)
  !!  script.something                  NOT in the official repo, and no source given
```

| Marker | Meaning | Do |
|---|---|---|
| `--` | Already carried | Nothing |
| `ok … official` | Kodi ships it; it will be installed by id and stay on its maintainer's update channel | Nothing |
| `ok … mirror` | Not in Kodi's repo; it will be packaged into yours from the source you gave — the bracket says which | Nothing |
| `!!` | Not in Kodi's repo, and you gave no source | Step 3.3 |

**3.2b What the planner does about duplicates and versions.** Scanning several repositories routinely turns up the same add-on in more than one of them, at different versions. Paste both lines and the planner does not guess:

```
  script.example listed 2 times:
      KEEP v2.2.2        https://…/nexusrepo/zips
      drop v1.9.0        https://…/omega/zips
```

It asks each source what version it currently advertises and keeps the newest, showing what it dropped. If a source advertises nothing it prints `v?` and is only kept when nothing better exists.

**Staying up to date afterwards is automatic**, and does not depend on what the versions were today:

| Source | What the daily sync does |
|---|---|
| `repo_url` | Re-reads that repository's index and takes whatever it now advertises |
| `github` with `track: release` | Takes the newest published release |
| `zip_url` | Pinned — only changes if that URL's contents change |

So the version you see at this step is not baked in. The first two track upstream on their own; only a fixed zip stands still, which is why it is the last resort.

The planner also flags two things worth acting on. **Library and resource add-ons** (`script.module.*`, `resource.*`) are installed automatically by Kodi as dependencies — listing them yourself is usually unnecessary. And **a long list** gets a warning: every add-on you carry is packaged into your repository, appears in the Toolbox picker, and is checked daily, so a catalogue of everything a repository happens to serve is worse than a short list you actually use.

**3.3 Resolve anything marked `!!`.** The add-on has to come from somewhere. Add one of the three source forms to that line:

```
script.something   owner/repo
script.something   https://that-repo/omega/zips
script.something   https://host/script.something-1.2.3.zip
```

If it is on GitHub, searching for the exact add-on id usually finds it — most Kodi add-ons use their id as the repository name. If it comes from a vendor's Kodi repository, run `--discover` against that repository and copy the line it prints. Re-run 3.2 until no `!!` lines remain.

If the add-on has no GitHub repository at all and installs only from a vendor's own Kodi repository, it belongs in the `external` section instead. Add it by hand using the `external` shape at the end of this part, and it is documented rather than installed.

**3.4 Apply.**

```
python3 scripts/plan_addons.py --apply
```

This changes two files:

- **`addons.json`** — your entries are appended to the right sections.
- **`src/script.watchame.toolbox/addon.xml`** — the Toolbox's version is bumped for you.

> The version bump is not cosmetic. The curated list ships *inside* the Toolbox, so without it the published index is byte-identical and **no device ever fetches your new list**, while every build reports success. The planner does it so you cannot forget; `build_repo.py` refuses to finish if it is ever missed.

**3.5 Write a `why` for each new entry.** The planner leaves a placeholder:

```
"why": "TODO: one sentence on why this earned a slot."
```

Open `addons.json` and replace every `TODO`. This text ends up in the README and is the only record of why an add-on is there.

`name` and `category` you can normally leave alone — the planner reads them from the add-on's own metadata: Kodi's official index for `official` entries, the repository's `addons.xml` for `repo_url` entries, and the `addon.xml` at the GitHub repo root otherwise. Only add-ons no index carries fall back to a name derived from the id. Both fields show in the Toolbox picker, so they are worth a glance.

**3.6 Build and check.**

```
python3 scripts/build_repo.py && python3 scripts/check_deps.py
```

**Check:** the build ends with an add-on count and an md5, and the dependency check says `all dependencies resolve`.

If it reports an unresolvable import, that add-on needs a dependency nobody publishes — move it to the `external` section (see the end of this part) rather than shipping something that cannot install.

**3.7 Commit and push.**

```
git add -A && git commit -m "Add <what you added>" && git push
```

Skip the push if you have not done Part 4 yet; just commit and carry on.

**3.8 Confirm it landed.**

```
grep -o 'id="[^"]*" name="[^"]*" version="[^"]*"' docs/addons.xml
```

**Check:** every add-on you added appears with a version. On a device, Toolbox → *Install curated add-ons* shows the new entries, unticked if you marked them `optional`.

## Writing entries by hand

The planner exists so you do not have to, but the entries are plain JSON and you can add them directly. `addons.template.json` in the repository root holds all three shapes ready to paste.

`addons.json` has three sections. An entry goes in exactly one.

**`mirror`** — packaged into your repo from GitHub:

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

**`official`** — installed by id from Kodi's own repo. No `github`, no `track`:

```
{
  "id": "script.trakt",
  "name": "Trakt",
  "category": "tracking",
  "why": "Scrobbling, watched-state sync and lists across devices."
}
```

**`external`** — documented, never auto-installed. No `id`; a vendor `url` and the add-ons it provides:

```
{
  "name": "TheMovieDb Helper (6.x)",
  "why": "Hard-requires script.module.pil, which no official repo ships.",
  "url": "https://jurialmunkey.github.io/repository.jurialmunkey/",
  "addons": ["plugin.video.themoviedb.helper", "script.skinvariables"]
}
```

| Field | Sections | Meaning |
|---|---|---|
| `id` | mirror, official | Must match the add-on's own `addon.xml` exactly |
| `name` | all | Display name in the Toolbox picker |
| `category` | mirror, official | Groups and sorts the picker. In use: `subtitles`, `playback`, `tracking`, `tools`, `interface`, `privacy`. |
| `why` | all | Your justification. Ends up in the README. |
| `github` | mirror | `owner/repo`. One of `github`, `repo_url` or `zip_url` is required. |
| `repo_url` | mirror | Directory holding another Kodi repo's `addons.xml`; the newest version is taken automatically |
| `zip_url` | mirror | A fixed zip URL. Pinned — only changes when that URL's contents change. |
| `datadir` | mirror | Optional, with `repo_url`. Where that repository keeps its zips, when it is not the same folder as its `addons.xml`. Symptom of needing it: the version resolves but the download fails. |
| `track` | mirror | With `github`: `release` (newest release, falling back to branch head) or `branch` |
| `ref` | mirror | Pin a branch, e.g. `"ref": "matrix"` |
| `optional` | mirror, official | `true` leaves it unticked in the picker |

Adding entries by hand means **bumping the Toolbox version yourself** (step 3.4 explains why), then continuing from 3.6.

# Part 4 — Publish to GitHub

**Where:** terminal, except 3.5 which is a browser setting.

Do this once. After it, everything is automatic.

**4.1 Point the local repository at GitHub.** It must be public — Kodi cannot authenticate. Which route depends on whether the repository exists yet.

**Route A — it does not exist yet.** One command creates it and wires up the remote:

```
gh repo create YOURNAME/YOURREPO --public --source=. --remote=origin
```

`YOURNAME` is the owner and `YOURREPO` the repository name — the same two values as `github_user` and `github_repo` in 2.2. It adds no README, .gitignore or license, which is what you want: any of them creates an initial commit and turns your first push into a merge.

**Route B — you already created it in the browser** (Appendix D.1, or github.com/new). Do not run the command above; it will fail. Just add the remote:

```
git remote add origin https://github.com/YOURNAME/YOURREPO.git
```

**Check either route:**

```
git remote -v
```

Both lines must show your repository's URL.

> **`GraphQL: Name already exists on this account (createRepository)`** means the repository is already there — you are on Route B. Nothing is broken and nothing was changed; add the remote and carry on to 3.2.
>
> **`remote origin already exists`** means the remote is set already. Confirm it points where you expect with `git remote -v`, or repoint it: `git remote set-url origin URL`.

**4.2 Push.**

```
git push -u origin main
```

**Check:** no authentication prompt. If you get one, redo 1.4.

**4.3 Wait for the build.**

```
gh run watch
```

**Check:** the run completes green. If it fails, read the log — it is running the same two commands you ran in 2.3 and 2.4.

> **No run appears at all?** That is normal on the very first push. The workflow filters on changed paths, and GitHub often skips that filter when a branch is created rather than updated. Start one by hand and carry on:
>
> `gh workflow run sync.yml && gh run watch`

**4.4 Verify what Kodi will see.** Replace `YOURNAME` and `YOURREPO` in the first line, then paste the whole block.

```
BASE=https://raw.githubusercontent.com/YOURNAME/YOURREPO/main/docs
curl -sI  $BASE/addons.xml     | head -1            # expect: HTTP/2 200
curl -s   $BASE/addons.xml.md5                      # expect: 32 hex characters, nothing else
curl -sI  $BASE/repository.watchame.zip | head -1    # expect: HTTP/2 200
```

**Check:** all three as described. A 404 on the first two means 2.2 does not match where you actually pushed.

**4.5 Confirm Actions can write back.** *(Browser.)* The sync job commits the regenerated `docs/` to your repository, so it needs write permission. On a repo you own, Actions are enabled automatically — the "enable workflows" prompt only appears on forks — but the write permission is a separate setting that will fail the job if it is wrong.

Open the repository on github.com → **Settings** → **Actions** → **General** → scroll to **Workflow permissions** → select **Read and write permissions** → Save.

**Check:** the **Sync repository** workflow appears under the Actions tab, and the run from 3.3 shows a commit step that succeeded. A `403` or `permission denied` on the push step means this setting is still read-only.

> **A green run does not prove this is right.** If nothing changed upstream, the job has nothing to commit and never exercises the permission — it goes green either way, and you find out weeks later when the first real update fails. Check the setting directly instead:
>
> `gh api repos/OWNER/REPO/actions/permissions/workflow --jq .default_workflow_permissions`
>
> It must print `write`. To set it without leaving the terminal:
>
> `gh api -X PUT repos/OWNER/REPO/actions/permissions/workflow -f default_workflow_permissions=write`

**4.6 Write down the install URL.** This is what you type into Kodi in Book Two, step 17:

```
https://raw.githubusercontent.com/YOURNAME/YOURREPO/main/docs
```

> **No `gh`?** Create the repository at **github.com/new** — public, no README, no .gitignore — then: `git remote add origin https://github.com/YOURNAME/YOURREPO.git && git push -u origin main`. When git asks for a password, paste a personal access token; GitHub stopped accepting account passwords for this in 2021.

\pagebreak

# Part 5 — Remove an add-on

**Where:** terminal and a text editor.

**5.1** Delete its entry from `addons.json`.

**5.2** Bump the Toolbox version in `src/script.watchame.toolbox/addon.xml`.

**5.3** Build and push:

```
python3 scripts/build_repo.py && python3 scripts/check_deps.py
git add -A && git commit -m "Remove <addon-id>" && git push
```

**Check:** `grep '<addon id="<addon-id>"' docs/addons.xml` returns nothing.

> Copies already installed on devices keep working but stop receiving updates. A repository cannot retract an add-on — to remove it from a device, uninstall it there.

# Part 6 — Change the Toolbox itself

**Where:** terminal and a text editor.

**6.1** Edit the code under `src/script.watchame.toolbox/`.

**6.2** Bump the version in its `addon.xml` — patch for a fix, minor for new behaviour.

**6.3** Build, check, push:

```
python3 scripts/build_repo.py && python3 scripts/check_deps.py
git add -A && git commit -m "Toolbox: <what changed>" && git push
```

# Part 7 — Change the repository's identity or URLs

**Where:** terminal and a text editor, then each device.

Only when moving the repo or renaming it.

**7.1** Edit `repo.config.json`: `github_user`, `github_repo`, `branch`, or `hosting`.

**7.2** Bump `repo_version` in the same file.

**7.3** Build and push as in 6.3.

**7.4** Reinstall the repository zip on **every device.** The old URLs are baked into the copy they already have.

> Because of 7.4, get `github_user` and `github_repo` right in Part 2 and leave them alone.

# Part 8 — Daily operation

**Where:** nowhere — it runs itself.

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

# Part 9 — Health check

**Where:** terminal, plus the device for 9.6.

Run after any push, or whenever something looks wrong.

**9.1 The index lists what you expect.**

```
grep -o 'id="[^"]*" name="[^"]*" version="[^"]*"' docs/addons.xml
```

**9.2 A specific add-on is present.**

```
grep -o 'id="service.vpn.manager"[^>]*version="[^"]*"' docs/addons.xml
```

**9.3 Its zip is Kodi-shaped** — `<id>/addon.xml` must be at the root:

```
unzip -l docs/zips/service.vpn.manager/*.zip | head -5
```

**9.4 The Toolbox carries the current list.**

```
python3 -c "import zipfile,json,glob; z=sorted(glob.glob('docs/zips/script.watchame.toolbox/*.zip'))[-1]; \
m=json.loads(zipfile.ZipFile(z).read('script.watchame.toolbox/resources/addons.json')); \
print(sorted(e['id'] for s in ('mirror','official') for e in m[s]))"
```

**9.5 The live URLs still respond.** Re-run 4.4.

**9.6 On a device:** Toolbox → Install curated add-ons. New entries appear in the picker, unticked if you marked them `optional`.

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
| `addons.wishlist.txt` | **Fill this in** — what you want the repo to carry | **Yes** |
| `addons.repos.txt` | **Paste URLs here** — repositories to scan with `--discover` | **Yes** |
| `addons.template.json` | Copy-paste entry templates; never read by the build | Reference |
| `scripts/plan_addons.py` | Turns the wishlist into `addons.json` entries | Rarely |
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
| `gh auth login` opens no browser | Headless machine | Use the token method in the 1.4 note |
| `git push` asks for a password | Not authenticated, or using a password | Redo 1.4, or paste a personal access token |
| `Name already exists on this account` | The repository was already created, probably in the browser | Skip to 4.1 Route B |
| `destination path already exists and is not an empty directory` | Cloning on top of the local repository you already have | Do not clone. Use 4.1 Route B to attach it to GitHub. |
| Commits show the wrong author | `user.email` not your GitHub address | Redo 1.3 |
| Build stops: `content changed without a version bump` | The working case, caught | Bump the version in `src/<addon>/addon.xml`, rebuild |
| `check_deps` reports an unresolvable import | A dependency nobody publishes | Move the add-on to `external` and document the vendor repo |
| Mirror sync: `no published release, falling back to branch head` | Upstream publishes no releases | Normal. Set `"track": "branch"` to make it explicit. |
| Mirror sync: add-on not found in the tarball | `id` does not match upstream's `addon.xml` | Correct the `id` |
| Mirror sync: version resolves, then `download failed` | That repo serves zips from a different path than its index | Add a `datadir` to the entry |
| Mirror sync fails after an upstream rename | Default branch changed | Set `"ref"` explicitly |
| Actions run but the commit step fails `403` | Workflow permissions set to read-only | Do 4.5 |
| Actions never run at all | Workflows disabled (usual on a fork) | Actions tab → enable them |
| Kodi: "Could not connect to repository" | `github_user`/`github_repo` wrong, or repo private | Re-run 4.4; confirm the repo is public |
| Kodi: repository installs but lists nothing | Index empty, or checksum stale | Re-run 2.3; never hand-edit `docs/` |
| Kodi: "Failed to install add-on" | Zip name does not match `id-version.zip` | Re-run 2.3; the builder names them |
| Kodi: "Dependency not met" | Unresolvable `<import>` | Run 2.4 |
| An add-on never updates on one device | Per-add-on auto-update set to Never | Add-on info → Auto-update → On |
| Updates appear only after a restart | Normal 24-hour poll cycle | Force a check on the device, or wait |

\pagebreak

# Appendix D — The browser-only route

Everything in Parts 2 to 7 can be done in a web browser, without a terminal, because **the build runs on GitHub rather than on your machine.** You edit a file, GitHub rebuilds the repository and commits the result, and your devices pick it up. This appendix is the parallel path.

## D.1 Getting the files onto GitHub

This is the one step where the browser is clumsy — 49 files, 27 MB. Two ways:

**Route A — seed once, then never touch a terminal again.** Have someone run the single `git push` from Part 3, or do it yourself once. Everything from D.2 onward is pure browser. This is the recommended route.

**Route B — no terminal at all.**

1. Go to **github.com/new**. The *Create a new repository* page has two sections; set every field as below, then click **Create repository**.

| Section | Field | Set it to | Why |
|---|---|---|---|
| 1 General | **Owner** | Your account or org, e.g. `StrainBrainOfficial` | This becomes `github_user` in `repo.config.json` and appears in every URL your devices fetch |
| 1 General | **Repository name** | Whatever you like, e.g. `WatchaMe` | Must match `github_repo` in `repo.config.json` **exactly**, including capitals |
| 1 General | **Description** | Optional, anything | Cosmetic; shown on the repo page only |
| 2 Configuration | **Choose visibility** | **Public** | Kodi fetches over plain HTTPS and cannot authenticate. A private repo is unreachable by your devices. |
| 2 Configuration | **Add README** | **Off** | |
| 2 Configuration | **Add .gitignore** | **No .gitignore** | |
| 2 Configuration | **Add license** | **No license** | |

> **Why all three must be off.** Any one of them creates an initial commit, so the repository is no longer empty. The **uploading an existing file** shortcut in step 2 disappears, and a later `git push` is rejected until you merge or force. Leave them off and the repository starts clean.

2. On the empty repository page, click **uploading an existing file**.
3. Drag the whole project folder onto the page. Wait for all 49 files to list.
4. Type a commit message and click **Commit changes**.
5. **Check the `.github/workflows/` folder arrived.** Hidden folders sometimes do not survive a drag from Finder or Explorer. If it is missing: **Add file → Create new file**, type the path `.github/workflows/sync.yml` — typing slashes creates the folders — paste the workflow contents, and commit.

Nothing in the repository exceeds GitHub's 25 MB web-upload limit.

## D.2 Set the workflow permission

**Settings** → **Actions** → **General** → scroll to **Workflow permissions** → **Read and write permissions** → **Save**.

Without this the build runs and then fails at the final commit with a `403`. It is the same as step 4.5.

## D.3 Set your identity

1. Click **`repo.config.json`** in the file list.
2. Click the **pencil** icon (*Edit this file*).
3. Set `github_user`, `github_repo`, `repo_name` and `provider` as in step 2.2.
4. Scroll down, click **Commit changes**.

The commit triggers a build automatically, because the workflow watches `repo.config.json`.

## D.4 Run or watch the build

The workflow runs on any commit touching `addons.json`, `repo.config.json`, `src/` or `scripts/`, and daily at 05:15 UTC. To run it by hand:

**Actions** tab → **Sync repository** in the left sidebar → **Run workflow** button → **Run workflow**.

**Check:** the run appears with a green tick. Click it to read the log — it is the same output as the terminal commands in 2.3 and 2.4.

A red cross reading `content changed without a version bump` means D.6 was done without D.7.

## D.5 Verify what Kodi will see

Open these three in a browser tab, substituting your values:

```
https://raw.githubusercontent.com/YOURNAME/YOURREPO/main/docs/addons.xml
https://raw.githubusercontent.com/YOURNAME/YOURREPO/main/docs/addons.xml.md5
https://raw.githubusercontent.com/YOURNAME/YOURREPO/main/docs/repository.watchame.zip
```

**Check:** the first shows XML listing your add-ons; the second shows a single 32-character hash; the third downloads a file. A **404** on any means the values in D.3 do not match the repository's actual address.

The third URL is also the one you enter in Book Two, step 17 — minus the filename.

## D.6 Add or remove an add-on

1. Click **`addons.template.json`** and copy the block you need — Part 3's *Writing entries by hand* section explains which, and D.8 covers deciding `official` versus `mirror` without a terminal.
2. Click **`addons.json`** → **pencil** → paste your entry into the matching section → **Commit changes**.

## D.7 Bump the Toolbox version — the step that matters

1. Navigate to **`src`** → **`script.watchame.toolbox`** → **`addon.xml`**.
2. Click the **pencil**.
3. Increase the version, e.g. `version="1.2.1"` → `version="1.2.2"`.
4. **Commit changes.**

Do D.6 and D.7 as two commits or one, but never D.6 alone: the curated list ships inside the Toolbox, so without a version bump no device ever fetches your change. The build will stop with a red cross if you forget.

## D.8 Deciding `official` versus `mirror` without a terminal

Step 3.2 runs the planner, which queries Kodi's official index for you. Without a terminal you cannot run it, so check on the device instead:

**Add-ons → Install from repository → Kodi Add-on repository →** browse the category and look for the add-on by name.

Found there, it goes in `official`. Not found, it goes in `mirror`.

## D.9 What you give up

Only local testing. Running the build on your own machine catches a mistake in seconds; via the browser you find out when the Actions run goes red a minute later. The checks are identical either way — `build_repo.py` and `check_deps.py` run in both places, so nothing broken reaches a device.
