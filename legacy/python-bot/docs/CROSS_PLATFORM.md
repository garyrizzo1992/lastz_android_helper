# Linux and macOS runtime

The LastZ bot uses the same Python application on Linux and macOS. Host setup
only needs to provide Python, Android platform-tools (`adb`), Tesseract, and the
Python packages in `requirements-runtime.txt` (`requirements.txt` includes it).

Python 3.13 is used by deployment and CI. Keeping the same minor version
reduces differences between development and production.

## Runtime configuration

The bot accepts these environment variables:

| Variable | Purpose | Default |
| --- | --- | --- |
| `LASTZ_ADB_PATH` | Absolute ADB executable path | `adb` from `PATH` |
| `LASTZ_TESSERACT_PATH` | Absolute Tesseract executable path | `tesseract` from `PATH` |
| `LASTZ_DATA_DIR` | Parent for logs, traces, and persistent state | Repository root |
| `LASTZ_LOG_DIR` | Override the log directory | `$LASTZ_DATA_DIR/logs` |
| `LASTZ_DEBUG_DIR` | Override screenshots and trace images | `$LASTZ_DATA_DIR/debug` |
| `LASTZ_STATUS_FILE` | Override the persistent action-status file | `$LASTZ_DATA_DIR/runtime/action_status.json` |
| `LASTZ_ENV_FILE` | Environment file read by `scripts/run_bot.sh` | Repository `.env` |
| `LASTZ_PYTHON` | Python used by `scripts/run_bot.sh` | Repository `.venv/bin/python` |

Relative override paths are resolved from the repository root. Template images
are always resolved from the repository, so the service working directory does
not affect image loading.

## Host setup

On Debian or Raspberry Pi OS:

```bash
sudo apt-get install android-tools-adb tesseract-ocr python3-venv
```

On Apple Silicon macOS:

```bash
brew install python@3.12 android-platform-tools tesseract
```

Create the environment and install Python packages:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-runtime.txt
```

Connect and authorize the Android phone, then verify the complete host setup:

```bash
adb devices -l
scripts/run_bot.sh --preflight
```

Start the bot with `scripts/run_bot.sh`. The same script is suitable as the
systemd `ExecStart` command on Linux or the `ProgramArguments` command in a
macOS LaunchAgent wrapper.

The launcher force-syncs tracked files to `origin/main` on every start, matching
the Raspberry Pi deployment. It preserves untracked files such as `.env`. Set
`LASTZ_GIT_SYNC=false` to skip this behaviour, or use `LASTZ_GIT_REMOTE` and
`LASTZ_GIT_BRANCH` to select a different remote or branch.

The launcher installs the pinned bot dependencies when the requirements checksum
or Python version changes. `--preflight` skips both Git sync and dependency
installation. See [macOS Ansible deployment](ANSIBLE_MACOS.md) for automatic
login startup, external state migration, secrets, and log rotation.
