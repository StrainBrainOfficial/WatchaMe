This book provisions a Fire TV Stick using the repository from Book One. The target is the **Fire TV Stick 4K (2018, model E9L29Y)** — 1.7 GHz quad-core, 1.5 GB RAM, 8 GB storage, Android 7.1+, running Kodi 21.1. Guidance for the 1 GB gen 1/2 sticks is noted where it differs.

There is no snapshot build here, deliberately. Appendix B explains why, and covers making one anyway if your situation genuinely calls for it.

# Part 1 — The hardware budget

| | Stick gen 1 (2014) | Stick gen 2 (2016) | **Stick 4K (2018)** | Stick Lite / 3rd gen |
|---|---|---|---|---|
| Model | W87CUN | LY73PR | **E9L29Y** | — |
| RAM | 1 GB | 1 GB | **1.5 GB** | 1 GB |
| Storage | 8 GB (~5 usable) | 8 GB (~5 usable) | **8 GB (~5 usable)** | 8 GB |
| CPU | Dual-core 1.0 GHz | Quad-core 1.3 GHz | **Quad-core 1.7 GHz** | Quad-core 1.7 GHz |
| Android base | 5.1 | 5.1 | **7.1+** | 9 |
| Realistic Kodi ceiling | 19–20 | 20 | **21+** | 21+ |

Fire OS reserves 350–450 MB for itself. Kodi with Estuary is roughly 250–300 MB. That leaves about **250 MB of headroom** on a 1 GB stick and closer to **700 MB** on the 4K. Every add-on running a background service eats into it.

| Metric | 1 GB sticks | **Stick 4K** | Unacceptable |
|---|---|---|---|
| `.kodi/` on disk | under 350 MB | under 500 MB | over 900 MB |
| Cold start | under 25 s | under 18 s | over 45 s |
| Idle RAM (PSS) | under 420 MB | under 600 MB | thrashing / restarts |
| Background services | 4 or fewer | 6 or fewer | 10 or more |

**Storage, not RAM, is the binding constraint on the 4K.** The extra 512 MB buys real room for services, but the flash is the same 8 GB, and the texture cache grows without limit until something caps it. That is what the artwork resolution settings in Appendix A are for.

> **Version matching matters more than version chasing.** Kodi 21.1 on the stick and Kodi 21.1 as the reference is the easy case. On gen 1/2 sticks (Android 5.1) the ceiling is Kodi 20 — check kodi.tv/download for the current `armeabi-v7a` minimum before committing, since it rises with each release.

# Part 2 — What goes on the box

The curated set from Book One, Part 4, minus what this hardware cannot afford.

**Install:** the repository, the Toolbox, `inputstream.adaptive`, `inputstream.ffmpegdirect`, `service.subtitles.a4ksubtitles`, `script.black.bars.never`, `service.upnext`, `script.kodi.loguploader`, and `plugin.video.youtube`.

**Consider:** `script.trakt` if you want watched-state sync — it is a background service, but a light one. `script.service.janitor` only if the stick stores local recordings, which it usually does not. `service.vpn.manager` is in the repository and unticked by default — on this hardware, and with Surfshark specifically, it is the wrong route; see the VPN decision in Part 4.

**Leave out on a stick:**

| Component | Cost |
|---|---|
| `skin.copacetic` and any third-party skin | 40–150 MB plus slower menus. Estuary is the lightest maintained skin. |
| `script.plexmod` | Only with a Plex server; library sync is the heaviest recurring cost in the set |
| `pvr.iptvsimple` | Only with an M3U subscription; costs startup work otherwise |
| `script.extendedinfo`, `script.embuary.*` | Skin and metadata helpers that scrape in the background |
| Multiple subtitle services | Each is a service; one is enough |

The Toolbox leaves optional entries unticked by default, so the shortest path is: accept the defaults, then untick the skin.

\pagebreak

# Part 3 — Install Kodi on the stick

**1. Enable sideloading.** Settings → My Fire TV → Developer Options → *Apps from Unknown Sources* → On. On newer Fire OS you may need to click the Fire TV Stick build number seven times first to reveal Developer Options.

**2. Install Kodi.** Either the Downloader app, or ADB from your machine:

```
adb connect FIRESTICK-IP:5555
adb install -r kodi-21.1-Omega-armeabi-v7a.apk
```

The stick is 32-bit ARM: use the **`armeabi-v7a`** APK, not `arm64-v8a`.

**3. Launch Kodi once and quit.** This creates the profile directory.

# Part 4 — The provisioning run

Follow Book One, Part 10 exactly. Condensed, with the choices for this device:

| # | Step | This device |
|---|---|---|
| 1 | Unknown sources → On | |
| 2 | Updates → Install updates automatically | **Do not skip.** This is what makes the stick maintenance-free. |
| 3 | Add file source | The URL from Book One, Part 7, named `kodikit` |
| 4 | Install `repository.kodikit.zip` | From the source you just added |
| 5 | Install **KodiKit Toolbox** from the repository | |
| 6 | Toolbox → **Install curated add-ons** | Untick the skin and any optional entry from Part 2 |
| 7 | **Set up the VPN** | Surfshark's Fire TV app, not the Kodi add-on — see the section below. Mandatory decision; do it before step 9. |
| 8 | Toolbox → **Apply streaming cache tuning** | Choose **Fire TV Stick**. Restart when prompted. |
| 9 | Settings → Player → Language → subtitle service | Set a4kSubtitles as the default — it does nothing until you do |
| 10 | Toolbox → **Clean up caches** | Clears install debris |

The tuning profile in step 7 writes a 40 MB buffer plus the artwork caps and dirty-region redraw described in Appendix A. Do not use *Balanced* here: its 64 MB buffer becomes roughly 192 MB resident, which does not fit alongside Fire OS on 1.5 GB.

## The VPN decision (step 7)

Your primary VPN is **Surfshark**, and that settles how this step goes on a Fire TV Stick: use Surfshark's own Fire TV app, not the Kodi add-on.

Two independent reasons, either one sufficient:

1. **Fire OS.** VPN Manager works by executing an OpenVPN binary and raising a tunnel from inside Kodi. On Android and Fire OS an ordinary app cannot control the system VPN, so the add-on generally cannot establish one on this hardware.
2. **Provider coverage.** VPN Manager 7.0.3 bundles connection profiles for NordVPN, ExpressVPN and Private Internet Access. **Surfshark is not among them.** Using it with Surfshark means the *User Defined* route: downloading `.ovpn` config files and importing them by hand.

### The route to use

| # | Step |
|---|---|
| 1 | On the stick: Amazon appstore → install the **Surfshark** app |
| 2 | Sign in and connect. Enable **auto-connect on startup** so a reboot does not silently drop protection. |
| 3 | Optionally set **Bypasser** (Surfshark's split tunnelling) if you want specific apps outside the tunnel |
| 4 | Verify the tunnel is actually up — see below |
| 5 | Only then do any account sign-ins inside Kodi |

Step 5 is the ordering that matters. Device-code and OAuth flows bind a session to the address that completed them, so signing in before the tunnel is up means redoing it later.

This route is strictly better than the add-on on this device: it covers **everything on the stick**, not just Kodi.

### Verifying the tunnel

The Surfshark app reports connected, but confirm it at the OS level:

```
# A VPN tunnel interface should exist while connected
adb shell ip addr show tun0

# And Android should report an active VPN transport
adb shell dumpsys connectivity | grep -i -m5 vpn
```

If `tun0` does not exist, the app is not actually tunnelling regardless of what its UI says.

### When VPN Manager is still worth ticking

Tick it in the Toolbox picker only if you also run Kodi on **Linux, LibreELEC or Windows**, where it can execute OpenVPN properly, and you want the same curated set everywhere. For Surfshark there:

- In VPN Manager settings choose **User Defined** as the provider.
- Get the `.ovpn` files from Surfshark's manual-setup page and import them via VPN Manager's *import wizard*.
- Authenticate with Surfshark's **manual-setup service credentials** from your account dashboard — these are a separate username and password, **not** your Surfshark login. Using the account email/password here is the usual reason a manual OpenVPN connection fails.

If you decide against a VPN entirely, that is a legitimate answer — just make it deliberately, and before the sign-ins.

## Playback settings

The Toolbox does not touch these; set them once by hand.

| Setting | Value | Why |
|---|---|---|
| Player → Videos → Allow hardware acceleration – **MediaCodec (Surface)** | On | Hardware decode. Without it 1080p stutters and 4K is hopeless. |
| Allow hardware acceleration – MediaCodec | Off | Redundant with Surface, costs memory |
| Adjust display refresh rate | On start/stop | Prevents judder |
| Sync playback to display | Off | Expensive on a weak CPU |
| Enable HQ scalers | 0% | Pure CPU cost, no visible benefit here |

## Interface settings

| Setting | Value |
|---|---|
| Interface → Skin | Estuary |
| Show RSS news feeds | Off |
| Startup → Perform on startup | Home screen |
| Media → General → Show media flags | Off |
| Services → Control → Allow remote control via HTTP | On, port 8080 |

Leaving the web server on is what makes everything in Part 5 possible without touching the device.

\pagebreak

# Part 5 — Verifying

Run these after a reboot, idle at the home screen.

```
# Memory
adb shell dumpsys meminfo org.xbmc.kodi | grep -E 'TOTAL PSS|TOTAL RSS'

# Installed size
adb shell du -sh /sdcard/Android/data/org.xbmc.kodi/files/.kodi

# Where the space actually went
adb shell "du -m /sdcard/Android/data/org.xbmc.kodi/files/.kodi/* \
  /sdcard/Android/data/org.xbmc.kodi/files/.kodi/userdata/* | sort -rn | head"

# Which services started
adb shell "grep -i 'service.*started\|Starting service' \
  /sdcard/Android/data/org.xbmc.kodi/files/.kodi/temp/kodi.log | tail -20"

# Confirm auto-update really is on
adb shell "grep addonupdates \
  /sdcard/Android/data/org.xbmc.kodi/files/.kodi/userdata/guisettings.xml"
```

| Check | Pass on the Stick 4K |
|---|---|
| TOTAL PSS idle | under 600 MB |
| `.kodi/` size | under 500 MB |
| Cold start | under 18 s |
| Services started | 6 or fewer |
| `general.addonupdates` | `0` |
| 1080p / 4K playback | no dropped frames (`Ctrl`+`Shift`+`O` overlay) |

A high PSS is almost always one background service. Disable them one at a time and re-measure — that is far faster than guessing.

The Toolbox's **Storage report** gives the same picture from the sofa, with no ADB, and changes nothing when you run it.

# Part 6 — Keeping it small

A stick that starts at 300 MB reaches 900 MB in six months if nothing prunes it. The texture cache is nearly always the cause.

| Task | Frequency | How |
|---|---|---|
| Storage report | Monthly | Toolbox → Storage report |
| Clean up caches | When the report looks bad | Toolbox → Clean up caches |
| Clean library | Occasionally | Toolbox → Clean video/music library |
| Re-measure idle RAM | After adding an add-on | Catch a heavy service immediately |

Clearing thumbnails and the texture DB means artwork re-downloads as you browse. That is the point — but the first few minutes afterwards feel slower.

# Part 7 — Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Buffering on 1080p or 4K | Cache profile too large for the device | Toolbox → tuning → **Fire TV Stick** |
| Stutter on high-bitrate video | Hardware decode off | MediaCodec (Surface) → On |
| Black screen with audio | MediaCodec conflict | Disable the non-Surface MediaCodec option |
| Very slow menus | Third-party skin or scraping widgets | Estuary; remove widgets |
| Out of space within weeks | Texture cache growth | Clean up caches; confirm the artwork caps are in `advancedsettings.xml` |
| Subtitles never appear | Default service not set | Settings → Player → Language → a4kSubtitles |
| Add-ons never update | `general.addonupdates` not `0` | Set it; check the per-add-on override too |
| Kodi APK will not install | Wrong architecture | Use `armeabi-v7a` |
| Everything is slow on gen 1/2 | 1 GHz dual-core is the limit | Cut the add-on count; expect 1080p only. Not applicable to the 4K. |

\pagebreak

# Appendix A — What the Fire TV Stick profile writes

Toolbox → Apply streaming cache tuning → Fire TV Stick produces this at `userdata/advancedsettings.xml`, backing up any existing file with a timestamp first:

```
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<advancedsettings>
  <cache>
    <!-- 1 = buffer all internet filesystems to memory -->
    <buffermode>1</buffermode>
    <memorysize>41943040</memorysize>
    <readfactor>4</readfactor>
  </cache>

  <!-- Redraw only changed screen regions; a large win on weak GPUs. -->
  <gui>
    <algorithmdirtyregions>3</algorithmdirtyregions>
  </gui>

  <!-- Cap cached artwork. The highest-leverage setting for storage on a
       stick: the flash is 8 GB no matter how much RAM the model has. -->
  <imageres>540</imageres>
  <fanartres>720</fanartres>

  <!-- Fail fast on dead sources instead of hanging the UI. -->
  <network>
    <curlclienttimeout>20</curlclienttimeout>
    <curllowspeedtime>15</curllowspeedtime>
  </network>
</advancedsettings>
```

Why these numbers:

- **`memorysize` 40 MB.** Kodi allocates roughly **three times** the configured value, so this is ~120 MB resident. The *Low memory* profile (20 MB → ~60 MB) suits 1 GB sticks; *Balanced* (64 MB → ~192 MB) is for a box with real RAM to spare.
- **`imageres` / `fanartres`.** Dropping fanart from 1080 to 720 more than halves texture cache growth, and on a stick feeding a TV that upscales anyway the difference is invisible. This is the single most effective setting against the 8 GB flash filling up.
- **`algorithmdirtyregions` 3.** Redraw only what changed. Meaningful on this GPU.
- **Network timeouts.** Without them a dead source hangs the UI rather than failing.

Cache settings only take effect after a restart, which the Toolbox offers.

Legacy note: pre-Kodi 18 guides use `<network><cachemembuffersize>` and `<readbufferfactor>`. Those names still parse but are deprecated — the `<cache>` block above is current.

# Appendix B — Why there is no snapshot build

The original goal here was a "build": a packaged `userdata` + `addons` snapshot installed by a wizard. That is the wrong shape for this, for four reasons:

1. **A build cannot update itself.** The add-ons inside it are sideloaded, belong to no repository, and therefore never receive updates. Book One's entire machinery exists to avoid exactly this.
2. **Reinstalling wipes your configuration.** Updating a build means replacing `userdata`, taking your settings with it.
3. **Builds rot on Kodi releases.** A profile built on one major version does not restore cleanly onto another; settings move and the add-on database schema changes.
4. **Builds leak credentials.** `userdata/addon_data/` holds API keys, tokens and account logins. Packaging it wholesale ships your accounts to everyone who installs it.

The Toolbox provides the part people actually want from a build — one action, whole set installed, sensible settings applied — while every add-on stays individually updatable on its own channel. A fresh stick reaches a finished state in about five minutes with Part 4, and stays current afterwards with no further attention.

## If you genuinely need one

Cloning many identical devices, or a box with no reliable network, are real reasons. In that case:

```
cd ~/.kodi
zip -qr ~/mybuild-1.0.0.zip addons userdata \
  -x 'addons/packages/*' 'userdata/Database/*' 'userdata/Thumbnails/*' \
     '*/__pycache__/*' '*.pyc' '*.log' 'temp/*'
```

Exclude `Database/` and `Thumbnails/` — both rebuild themselves and are most of the size. **Audit `addon_data/` for credentials before sharing it:**

```
grep -rilE 'token|apikey|api_key|password|secret|user' ~/.kodi/userdata/addon_data/
```

Restore by extracting over `.kodi/` with Kodi **force-stopped**, not merely backgrounded — Kodi rewrites `guisettings.xml` on exit and will overwrite the restored settings otherwise:

```
adb push mybuild-1.0.0.zip /sdcard/Download/
adb shell "cd /sdcard/Android/data/org.xbmc.kodi/files/.kodi && \
  unzip -o /sdcard/Download/mybuild-1.0.0.zip"
adb shell am force-stop org.xbmc.kodi
```

Even then, install the repository afterwards so the cloned devices resume receiving updates.
