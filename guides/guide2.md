One continuous procedure, steps 1 to 34, taking a Fire TV Stick from factory state to a finished, self-updating Kodi box. Target hardware: **Fire TV Stick 4K (2018, model E9L29Y)** — 1.5 GB RAM, 8 GB storage, Android 7.1+, Kodi 21.1. Notes for the 1 GB gen 1/2 sticks appear where they differ.

Allow about 30 minutes. Lines marked **Check** tell you what success looks like.

**Before you start, have these ready:**

- The install URL from Book One, step 2.6
- Your Surfshark login
- The Kodi `armeabi-v7a` APK for your version, or the Downloader app
- Optional but recommended: ADB on your computer, for the verification steps

\pagebreak

# Stage A — Prepare the stick (steps 1–5)

**1.** On the stick: Settings → My Fire TV → About → click **Fire TV Stick** seven times to reveal Developer Options.

**2.** Settings → My Fire TV → Developer Options → **Apps from Unknown Sources → On**.

**3.** *(Optional, for the verification steps)* Same menu → **ADB debugging → On**.

**4.** Settings → My Fire TV → About → Network → note the **IP address**.

**5.** *(Optional)* From your computer:

```
adb connect STICK-IP:5555
```

**Check:** `connected to STICK-IP:5555`. Accept the prompt on the TV if one appears.

# Stage B — Install Kodi (steps 6–8)

**6.** Install Kodi, by either route:

*Downloader app:* open Downloader on the stick, enter the Kodi download URL for the **armeabi-v7a** build, install when it downloads.

*ADB from your computer:*

```
adb install -r kodi-21.1-Omega-armeabi-v7a.apk
```

> Use **armeabi-v7a**, not arm64-v8a. The stick is 32-bit ARM; the wrong APK simply fails to install.

**7.** Launch Kodi once, let it reach the home screen, then quit it. This creates the profile directory.

**8.** Skip Kodi's setup wizard if offered. Leave the skin as Estuary.

# Stage C — Set up Surfshark (steps 9–13)

Do this **before** any sign-in inside Kodi. Sign-ins bind to the address that completed them, so doing this later means redoing them.

**9.** On the stick: Amazon appstore → search **Surfshark** → install.

**10.** Open Surfshark, sign in, connect to a location.

**11.** In Surfshark's settings, enable **auto-connect on startup**, so a reboot cannot silently drop protection.

**12.** *(Optional)* Set **Bypasser** if you want specific apps outside the tunnel.

**13.** Verify the tunnel at OS level — the app's own UI is not proof:

```
adb shell ip addr show tun0
```

**Check:** a `tun0` interface exists with an IP. If it does not, the stick is not tunnelling no matter what the app displays.

> **Do not use the VPN Manager add-on on this device.** It raises an OpenVPN tunnel from inside Kodi, which an ordinary Android app cannot do on Fire OS. It also bundles profiles for NordVPN, ExpressVPN and PIA only — not Surfshark. It stays in the repository, unticked, for Linux and LibreELEC boxes; Appendix C covers using it with Surfshark there.

\pagebreak

# Stage D — Install the repository (steps 14–20)

**14.** Kodi → Settings (gear) → System → Add-ons → **Unknown sources → On**. Accept the warning.

**15.** Settings → Add-ons → Updates → **Install updates automatically**.

> Step 15 goes before any add-on exists so every one inherits it. This single setting is what makes the stick maintenance-free.

**16.** Settings → File manager → **Add source** → `<None>`.

**17.** Type the install URL from Book One, step 2.6:

```
https://raw.githubusercontent.com/YOURNAME/YOURREPO/main/docs
```

**18.** Name it `kodikit` → OK.

**19.** Kodi → Add-ons → **Install from zip file** → `kodikit` → `repository.kodikit.zip`.

**Check:** a notification confirms the repository add-on installed.

**20.** Add-ons → **Install from repository** → KodiKit → Program add-ons → **KodiKit Toolbox** → Install.

**Check:** the Toolbox appears under Add-ons → Program add-ons.

> If step 19 fails, the URL in step 17 is wrong. Re-run Book One step 2.5 from your computer.

# Stage E — Install the add-ons (steps 21–23)

**21.** Open **KodiKit Toolbox** → **Install curated add-ons**.

**22.** In the picker, untick anything you do not want. For this stick:

| Untick | Reason |
|---|---|
| `skin.copacetic` | 40–150 MB and slower menus; Estuary is lighter |
| `script.plexmod` | Only useful with a Plex server |
| `pvr.iptvsimple` | Only useful with an IPTV M3U subscription |
| `service.vpn.manager` | Wrong route on Fire OS — Stage C already covered it |
| `script.service.janitor` | Only if the stick stores local recordings |

Leave ticked: InputStream Adaptive and FFmpeg Direct, a4kSubtitles, Black Bars Never, Up Next, Logfile Uploader, YouTube.

**23.** Confirm and let it run.

**Check:** the Toolbox reports what installed. Anything already present is skipped automatically.

# Stage F — Configure (steps 24–30)

**24.** Toolbox → **Apply streaming cache tuning** → select **Fire TV Stick** → Write → **Restart** when prompted.

> Do not pick *Balanced* here. Its 64 MB buffer becomes roughly 192 MB resident, which does not fit alongside Fire OS on 1.5 GB. On a 1 GB gen 1/2 stick, pick *Low memory* instead.

**25.** Settings → Player → Language → **Default TV show service** and **Default movie service** → set both to **a4kSubtitles**.

> Subtitles do nothing until this is set. It is the single most common "it's broken" report.

**26.** Settings → Player → Videos → **Allow hardware acceleration – MediaCodec (Surface) → On**.

**27.** Same screen → **Allow hardware acceleration – MediaCodec → Off** (redundant with Surface, costs memory).

**28.** Same screen → **Adjust display refresh rate → On start/stop**; **Sync playback to display → Off**; **Enable HQ scalers → 0%**.

**29.** Settings → Interface → **Show RSS news feeds → Off**. Settings → Media → General → **Show media flags → Off**.

**30.** Settings → Services → Control → **Allow remote control via HTTP → On**, port 8080.

> Step 30 is what makes remote diagnosis possible later without touching the device.

\pagebreak

# Stage G — Verify (steps 31–34)

**31.** Reboot the stick, then leave Kodi sitting on the home screen for a minute.

**32.** Check memory and disk from your computer:

```
adb shell dumpsys meminfo org.xbmc.kodi | grep 'TOTAL PSS'
adb shell du -sh /sdcard/Android/data/org.xbmc.kodi/files/.kodi
```

**Check:** against the targets below.

| Metric | Stick 4K | 1 GB sticks |
|---|---|---|
| TOTAL PSS idle | under 600 MB | under 420 MB |
| `.kodi/` on disk | under 500 MB | under 350 MB |
| Cold start | under 18 s | under 25 s |
| Background services | 6 or fewer | 4 or fewer |

**33.** Confirm auto-update really is set:

```
adb shell "grep addonupdates \
  /sdcard/Android/data/org.xbmc.kodi/files/.kodi/userdata/guisettings.xml"
```

**Check:** the value is `0`. If it is `1` or `2`, redo step 15.

**34.** Play something for a minute. Press `Ctrl`+`Shift`+`O` (or hold Select on the remote → the codec overlay) and confirm no dropped frames.

**Done.** The stick now updates itself. Every add-on tracks its own upstream through the repository, with no further action.

# After setup — routine maintenance

| When | Do |
|---|---|
| Monthly | Toolbox → **Storage report** |
| When storage looks bad | Toolbox → **Clean up caches** |
| Occasionally | Toolbox → **Clean video/music library** |
| After adding an add-on | Re-run step 32 to catch a heavy background service |

Artwork re-downloads as you browse after a cache clean. That is expected; the first few minutes feel slower.

# Troubleshooting

| Symptom | Fix |
|---|---|
| Kodi APK will not install | Wrong architecture — use `armeabi-v7a` |
| Step 19 fails | URL in step 17 is wrong; re-run Book One step 2.5 |
| Repository installs but lists nothing | Book One, Appendix C |
| Subtitles never appear | Step 25 not done |
| Buffering on 1080p or 4K | Redo step 24 and pick **Fire TV Stick** |
| Stutter on high-bitrate video | Step 26 — MediaCodec (Surface) is off |
| Black screen with audio | Step 27 — disable the non-Surface MediaCodec option |
| Very slow menus | A third-party skin got installed; switch back to Estuary |
| Out of space within weeks | Toolbox → Clean up caches; confirm step 24 was applied |
| Add-ons never update | Step 33 returns something other than `0` |
| Surfshark shows connected but traffic is not tunnelled | Step 13 shows no `tun0`; reconnect in the app |
| Everything is slow on a gen 1/2 stick | 1 GHz dual-core is the limit — cut the add-on count, expect 1080p only |

\pagebreak

# Appendix A — The hardware

| | Stick gen 1 (2014) | Stick gen 2 (2016) | **Stick 4K (2018)** | Stick Lite / 3rd gen |
|---|---|---|---|---|
| Model | W87CUN | LY73PR | **E9L29Y** | — |
| RAM | 1 GB | 1 GB | **1.5 GB** | 1 GB |
| Storage | 8 GB (~5 usable) | 8 GB (~5 usable) | **8 GB (~5 usable)** | 8 GB |
| CPU | Dual-core 1.0 GHz | Quad-core 1.3 GHz | **Quad-core 1.7 GHz** | Quad-core 1.7 GHz |
| Android base | 5.1 | 5.1 | **7.1+** | 9 |
| Realistic Kodi ceiling | 19–20 | 20 | **21+** | 21+ |

Fire OS reserves 350–450 MB. Kodi with Estuary is 250–300 MB. That leaves roughly 250 MB of headroom on a 1 GB stick and 700 MB on the 4K.

**Storage, not RAM, is the binding constraint on the 4K.** The extra 512 MB buys room for services, but the flash is the same 8 GB and the texture cache grows without limit until something caps it — which is what step 24 does.

On gen 1/2 sticks (Android 5.1) the practical Kodi ceiling is 20; check kodi.tv/download for the current `armeabi-v7a` minimum, as it rises with each release.

# Appendix B — What step 24 writes

Toolbox → cache tuning → Fire TV Stick produces `userdata/advancedsettings.xml`, backing up any existing file with a timestamp first:

```
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<advancedsettings>
  <cache>
    <buffermode>1</buffermode>
    <memorysize>41943040</memorysize>
    <readfactor>4</readfactor>
  </cache>
  <gui>
    <algorithmdirtyregions>3</algorithmdirtyregions>
  </gui>
  <imageres>540</imageres>
  <fanartres>720</fanartres>
  <network>
    <curlclienttimeout>20</curlclienttimeout>
    <curllowspeedtime>15</curllowspeedtime>
  </network>
</advancedsettings>
```

- **`memorysize` 40 MB.** Kodi allocates roughly three times the configured value, so this is ~120 MB resident. *Low memory* (20 MB → ~60 MB) suits 1 GB sticks; *Balanced* (64 MB → ~192 MB) needs a box with real RAM.
- **`imageres` / `fanartres`.** Dropping fanart from 1080 to 720 more than halves texture cache growth, and on a TV that upscales anyway the difference is invisible. This is the most effective single setting against the 8 GB flash filling.
- **`algorithmdirtyregions` 3.** Redraw only what changed.
- **Network timeouts.** A dead source fails instead of hanging the UI.

Cache settings take effect only after the restart in step 24.

# Appendix C — VPN Manager with Surfshark, on a non-Android box

Only relevant on Linux, LibreELEC or Windows, where an add-on can execute OpenVPN.

1. Toolbox → Install curated add-ons → tick **VPN Manager for OpenVPN**.
2. VPN Manager → settings → provider → **User Defined**.
3. Download Surfshark's `.ovpn` config files from their manual-setup page.
4. Import them with VPN Manager's import wizard.
5. Authenticate with Surfshark's **manual-setup service credentials** from your account dashboard — a separate username and password, **not** your Surfshark login.

Step 5 is the usual failure: the account email and password do not work for manual OpenVPN.

# Appendix D — Why there is no snapshot build

The original goal was a "build" — a packaged `userdata` + `addons` snapshot installed by a wizard. That shape is wrong here for four reasons:

1. **It cannot update itself.** Add-ons inside a build are sideloaded, belong to no repository, and never receive updates.
2. **Reinstalling wipes your configuration**, because updating means replacing `userdata`.
3. **Builds rot across Kodi releases** — settings move and the add-on database schema changes.
4. **Builds leak credentials.** `userdata/addon_data/` holds API keys and account logins; packaging it ships your accounts to everyone who installs it.

Stages D–F deliver what people actually want from a build — one action, whole set installed, sensible settings — while every add-on stays individually updatable.

**If you genuinely need one** (cloning many identical sticks, or no reliable network):

```
cd ~/.kodi
zip -qr ~/mybuild-1.0.0.zip addons userdata \
  -x 'addons/packages/*' 'userdata/Database/*' 'userdata/Thumbnails/*' \
     '*/__pycache__/*' '*.pyc' '*.log' 'temp/*'
grep -rilE 'token|apikey|password|secret' ~/.kodi/userdata/addon_data/
```

Review whatever that `grep` lists before sharing the zip. Restore by extracting over `.kodi/` with Kodi **force-stopped** — it rewrites `guisettings.xml` on exit and will otherwise overwrite what you restored:

```
adb shell am force-stop org.xbmc.kodi
adb push mybuild-1.0.0.zip /sdcard/Download/
adb shell "cd /sdcard/Android/data/org.xbmc.kodi/files/.kodi && \
  unzip -o /sdcard/Download/mybuild-1.0.0.zip"
```

Install the repository afterwards so the cloned devices resume receiving updates.
