# Last Z Android Helper

On-device Android overlay bot for Last Z. Java provides the app, floating controls and task orchestration; read-only runtime metadata and guarded native UI geometry drive game actions. Root/Magisk and the pinned game runtime are required.

Start with [the current handoff](docs/CURRENT_HANDOFF.md), then [remaining implementation work](docs/ANDROID_BOT_REMAINING_PLAN.md) and [the full parity contract](docs/ANDROID_BOT_PARITY_HANDOFF.md). The latest installed release and the latest source can differ; the handoff records both. Moving repositories does not start or deploy a bot.

## Layout

- `tools/last-z-helper/`: Android app, native agent integration, policies, tests and build scripts.
- `docs/`: Android feature investigations, migration plans, checkpoints and historical handoffs.
- `legacy/python-bot/`: frozen Python/Go reference and compatibility changes used for migration. Not a second automatically running controller.
- `runtime/`: ignored local evidence, build caches, signing key, rooting files and phone backups.
- `bin/`: ignored signed APKs and rollback artifacts.
- `scrcpy/`: ignored local Android platform tools.

## Build and validate

Use Java 17, Android SDK platform 35/build-tools 35.0.1, Python 3, Node.js and PowerShell. Set `JAVA_HOME` and `LASTZ_ANDROID_SDK` when needed.

```powershell
python tools/last-z-helper/fetch_assets.py
powershell -ExecutionPolicy Bypass -File tools/last-z-helper/validate.ps1
powershell -ExecutionPolicy Bypass -File tools/last-z-helper/build.ps1
```

On macOS/Linux, set `JAVA_HOME`, `LASTZ_ANDROID_SDK` and put Node.js on `PATH`, then use:

```sh
python3 tools/last-z-helper/fetch_assets.py
python3 tools/last-z-helper/validate.py
```

The portable validator builds DEX and runs the Windows suite inventory, all JavaScript guard tests, Python tests and the cross-process recovery suites.

Optional rooted-device checks, after stopping every controller:

```sh
python3 tools/last-z-helper/validate_android_fixtures.py --serial YOUR_DEVICE_SERIAL
```

This explicit-device command builds and runs isolated filesystem and process-ownership fixtures. It refuses an active controller or requested bot run, uses no game input/memory and does not replace installed app assets. Its private report stays under ignored `runtime/helper-build`. The detach fixture holds the shared controller lock and uses an owned shell that expires within30seconds even if its parent disconnects.
 `build.py` defaults to DEX only. To package an APK, pass `--apk --keystore /private/path/to/existing-key.jks` with `LASTZ_KEYSTORE_PASSWORD` set in the environment. It never generates a replacement key or installs the app. Keep the original signer when updating an existing installation.

The APK is written to `bin/last-z-helper.apk`. Installation is separate; use an explicitly selected ADB device and preserve settings, histories and the existing signing key. A fresh clone does not contain the private signing key needed to upgrade an existing installation. Build scripts retain their existing test-key behavior for new installations; do not generate a replacement key for an installed helper.

Copy the Android platform tools into `scrcpy/` for the existing Windows device utilities. The transferred local checkout already contains its dependencies and private build material. None of the private runtime, signing keys, backups, device logs or APKs are published by this repository.

## Operation

Opening the helper shows floating controls. Run bot rotates explicitly selected accounts and performs enabled, due maintenance. Trucks and World-map bounty finding remain separate manual modes. Preview and STOP remain independent controls. See the current handoff for verified features and pending work; full Python parity is not complete.
