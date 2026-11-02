# Car Code Reader — handoff / context

Paste or point Claude Code at this file when you open the project, so it knows the full state
without re-explaining. Last updated 2026-11-01. Current version: **2.30**.

## What this is

An OBD-II car diagnostic app. Reads/clears trouble codes (engine, ABS, airbag, transmission),
shows live sensor data, smog-readiness, heavy-duty (J1939) trucks, and 1995-and-older blink codes.
Two codebases:

- **Desktop (Mac + Windows):** Python 3 + Tkinter, one shared source, packaged with PyInstaller.
  Repo: `HughWinstanley/car-code-reader` (this repo).
- **iOS:** separate Swift/SwiftUI app on the Mac at `~/Documents/car-code-reader-ios/ios`
  (`CarCodeReader.xcodeproj`). A copy also exists under `ios/` in this repo.

## Repo layout (desktop)

- `app/` — the app's Python modules (these are what the in-app updater replaces):
  `car_code_reader.py` (UI), `obd_core.py` (ELM327/OBD), `dtc_database.py`, `icons.py` (vector icons),
  `icon_render.py` (anti-aliased icon rendering via Pillow), `vehicles.py`, `j1939.py`, `obd1.py`,
  `maker_codes.py`, `updater.py`, plus others, and `icon.png`.
- `source/start.py` — the frozen entry point (NOT updatable; sets DPI awareness, loads the newest
  app copy). `source/version.py`, `source/mac/`, `source/windows/`.
- `.github/workflows/build-mac.yml`, `build-windows.yml` — CI that builds and publishes.
- `release.json` — version + sha256 of each updatable file (the self-updater reads this).

## How releases / updates work

- Bump `"version"` in `release.json` (and the sha256 of any `app/*.py` you changed), push to `main`.
  Push also needs `source/version.py` set to the same version.
- CI builds the Windows `.exe` (onefile) and Mac `.app` (in a DMG) and publishes them to GitHub
  Releases tagged `win-v<version>` / `mac-v<version>`.
- The app self-updates from inside (Help → Check for updates): `updater.py` fetches the `app/*`
  files from `raw.githubusercontent.com/<repo>/main` by sha256 into a per-user folder; `start.py`
  loads that newer copy. **The frozen `start.py` and bundled libraries (Pillow, pyserial) can NOT
  be delivered by the updater — those only change by downloading a fresh build.**

## Open items / TODO

1. **Make the Mac app open on *other* Macs (the big one).** The build is ad-hoc signed, which only
   opens reliably on the Mac that built it. We confirmed the real blocker is Gatekeeper refusing a
   non-notarized app — clearing quarantine / running the binary directly did not fix it on the 2nd Mac.
   The fix is **notarization**, and the pipeline is already built into `build-mac.yml` (signs with a
   Developer ID, notarizes, staples — falls back to ad-hoc when the cert secrets aren't set).
   **What's needed:** an Apple Developer ID certificate + 5 GitHub secrets. Full steps in
   `source/mac/NOTARIZATION.md`. **Constraint:** the user's Apple ID is under 18, so an *adult on the
   Company Six Services LLC Apple Developer account* must create the certificate.

2. **Windows fullscreen layout.** When the window is maximized, the content stays left-aligned with
   empty space on the right instead of filling/centering. Not yet fixed. It's in
   `app/car_code_reader.py` (the `tile_grid` / page layout packs with `anchor="w"`); needs the content
   centered or capped-width-centered on wide windows. Deliverable via the updater once done.

3. **iOS signing (seen in Xcode just now).** Project signs with "Hugh Winstanley (Personal Team)".
   Warnings: Debug config has **no bundle identifier** (set `PRODUCT_BUNDLE_IDENTIFIER`); Release uses
   `com.carcodereader.CarCodeReader` but shows "Communication with Apple failed". TestFlight / proper
   distribution also needs the adult-authorized Apple Developer account (same under-18 constraint).

## Recent work (most recent first)

- Added Mac Developer ID signing + notarization pipeline (ad-hoc fallback) — `source/mac/NOTARIZATION.md`.
- Added a Mac `Open Car Code Reader.command` that clears the quarantine flag (cert-free workaround;
  did not get past the 2nd Mac's Gatekeeper, which is why notarization is needed).
- Anti-aliased icons: `icon_render.py` runs the existing `icons.py` drawing through a Pillow canvas at
  4x and downsamples (fixes jagged/"pixely" icons on Windows at native DPI). Pillow is bundled in both
  builds.
- Windows fixes: Per-Monitor-V2 DPI awareness (crisp rendering); fixed a crash where scanned codes
  didn't show (`%-I` time format is not portable to Windows — build the 12-hour time manually); made
  the UI update pump resilient so one failing callback can't freeze the app.

## Hard rule (do not violate)

**Never add car-key / immobilizer programming to the app.** It was requested and refused earlier —
it's a car-theft enabler. Keep it out.

## Quick dev notes

- Smoke-test the desktop app headlessly on Linux: `xvfb-run python3 <harness>` driving
  `car_code_reader.App`. Pillow + `python3-pil.imagetk` needed for `icon_render`.
- `gh` works for releases via the REST API (`gh api repos/.../releases/...`); GraphQL and the Actions
  log blob storage are blocked in some environments, so fetch logs/assets via REST.
