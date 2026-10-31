# LastZ bot

ADB-based automation for four Last Z Android accounts on a USB-connected phone.
The same application runs on Windows, Linux and macOS. Game interaction uses
OpenCV templates, OCR and verified navigation; runtime state is stored separately
from application code.

## Repository contents

| Path | Purpose |
| --- | --- |
| `main_scrcpy.py`, `bot/` | Application entry point and feature workflows |
| `status_store.py`, `workflow_result.py` | Persistent status and workflow outcomes |
| `images/` | Game detection templates |
| `tests/` | Unit, workflow and sanitized screenshot regressions |
| `ansible/`, `.github/workflows/` | Deployment configuration and CI |
| `scripts/run_bot.sh` | Required Linux/macOS service launcher |
| `scripts/scrcpy_crop_screenshot.py` | Screenshot cropping utility |
| `tools/truck-scanner/` | Standalone Go USB truck scanner, Windows sound alert and World sharing |
| `LastZRemotePhone/` | Windows remote-phone launcher with Mac bot pause/resume |
| `Pause-Bot.ps1`, `Resume-Bot.ps1` | Windows controls for the Mac bot service over SSH |
| `scrcpy/` | Bundled Windows ADB executable and its two required DLLs |
| `docs/` | Architecture, deployment and feature documentation |

No standalone debug, web-store, log-reader or validation scripts are maintained.
The truck scanner, two bot-control scripts and `LastZRemotePhone/` are explicitly requested exceptions;
see its [usage instructions](LastZRemotePhone/README.md).
Generated logs, screenshots, bytecode and runtime state are excluded from Git.
Historical versions of removed files remain available in Git history.

For the standalone purple/yellow truck finder (3+ Universal Orange Hero
Fragment icons, power below 440M), see [Truck scanner](docs/TRUCK_SCANNER.md).

## Pause or resume the Mac bot from Windows

Run either command from this folder:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Pause-Bot.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Resume-Bot.ps1
```

The scripts use `garyrizzo@192.168.1.10` and your existing
`$env:USERPROFILE\.ssh\id_ed25519` key. Override `-MacHost`, `-MacUser` or
`-IdentityFile` if needed. The Mac must already be in SSH known_hosts.
Pause stops the current bot using `launchctl bootout`. Resume loads the agent
again and confirms that the service is running. Neither script changes the
service's enabled/disabled settings; normal login/reboot startup is preserved.
Both commands can be
repeated; resuming an already running service does not kill its current work.
Close an active LastZ remote-phone session before resuming to avoid competing
controls on the handset. Pausing also stops shield monitoring and alerts.

## Development and checks

Install Python 3.13, ADB and Tesseract, then:

```sh
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
python main_scrcpy.py --preflight
```

`requirements.txt` includes the pinned runtime requirements for compatibility.
See [runtime setup](docs/CROSS_PLATFORM.md), [architecture](docs/ARCHITECTURE.md)
and [macOS deployment](docs/ANSIBLE_MACOS.md). Do not run a second bot against
the phone while the normal service is using it.

[Weekly shield activation and evidence](docs/SHIELDS.md) are implemented but
disarmed pending an approved live activation/replacement test.

## Android helper migration

See [functionality inventory and migration roadmap](../../docs/PYTHON_TO_ANDROID_MIGRATION_PLAN.md) for moving the Python maintenance workflows into the on-device helper. Current implementation handoff: [NEXT_SESSION.md](../../docs/NEXT_SESSION.md).
