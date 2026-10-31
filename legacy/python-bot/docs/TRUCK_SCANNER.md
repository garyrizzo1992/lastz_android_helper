# Standalone Go truck scanner

Runs against the **local USB Android phone on this Windows PC**, independently
of the Python production bot. No connection to the Mac, automatic attacks,
Plunder/Fight taps or purchase confirmations.

## Rules

| Universal Orange Hero Fragment icons | Action |
| --- | --- |
| 0–1 | Skip; no power OCR |
| Exactly 2 | Share to **World chat, regardless of power**, then continue |
| 3+ and power below 440,000,000 | Windows sound alert; save evidence; stop with truck open |
| 3+ and power 440,000,000 or higher | Share to **World chat**, then continue |

Fragments are separate icons at the start of the cargo row, not quantities.
The scanner resets to the start and verifies counts on two frames. Power OCR
fits the white text tightly and uses different segmentation modes, rather
than repeated scales of one model. It requires agreeing readings and
independent-frame verification for an alert. Conflicting power readings on
opposite sides of the alert limit are rejected. A real 522.17M screen is kept
as a regression against the former leading-5-to-9 OCR confusion.
Transient count differences are rechecked for up to five observations; two
consecutive agreeing counts are required. Persistent uncertainty stops safely
with an explicit error, not a qualifying-match sound.
Two-fragment shares have no power limit; readable power is used only for
identity/World-chat receipt verification, never as a sharing threshold.

## Build once

From the LastZ repository root, with Go installed:

```powershell
go build -C tools/truck-scanner -o ../../bin/truck-scanner.exe .
```

Standard-library Go only: **no Python, OpenCV or CGO**. The executable still
needs bundled ADB, templates/config and Tesseract. The local binary is ignored
by Git; rebuild after source updates. Windows CI also publishes a build artifact.

## Run

Connect and authorize one USB phone; open **Others' Trucks**. From the repository root:

```powershell
.\bin\truck-scanner.exe
```

From the `scripts` folder:

```powershell
..\bin\truck-scanner.exe
```

Search runs **until found by default**. Ctrl+C stops. Do not run competing
scanners or other automation controlling the same phone.

```powershell
.\bin\truck-scanner.exe --max-refreshes 0  # Current list only
.\bin\truck-scanner.exe --max-refreshes 3  # Three refreshes maximum
.\bin\truck-scanner.exe --capture          # Screenshot only, no taps
.\bin\truck-scanner.exe --test-sound
.\bin\truck-scanner.exe --inspect-current  # Process the open truck
```

`--inspect-current` is actionable: it may share two-fragment trucks to World.
Use `--capture` for read-only inspection. Override defaults with `--serial`,
`--adb`, `--tesseract`, `--config`, `--output` and `--share-state`.

## Safe World sharing

1. Verify exactly two icons and open the truck's Share control.
2. Locate the **World globe icon**, then the unique share button aligned with
   it. Confirm the adjacent World label. No fixed World row/position is used.
   Menu opening is polled for up to five observations; an animation or an
   unreadable decorative Share title alone cannot block a valid World row.
3. Handle a second confirmation only after recognizing its World globe and
   World label; choose the gold Share control, not Cancel or another channel.
4. Require a success toast or a matching World chat card. If the toast is
   missed, check World chat and restore the truck list afterwards.

Attempts are saved before sending in ignored
`runtime/truck-scanner/world-shares.json`. Stable owner/power-header identity
avoids duplicate posts as truck coordinates move. Pending/uncertain/verified
attempts are not blindly re-sent for 24 hours. Reconcile uncertain outcomes
using saved evidence; never erase the ledger just to retry a send.
A short global interval limits sharing bursts.
Small text-rendering variations are tolerated using packed owner masks;
approximate duplicate matching still requires the same state and exact power.

Set `share_two_fragments_world` to `false` in `config/truck_scanner.json` to
disable two-fragment sharing. Set `share_high_power_fragments_world` to `false`
to disable 3+ fragment shares at/above the power limit. Both are enabled by default.

## Calibration, evidence and tests

Current calibration: Samsung S23 Ultra, **720×1544**. Truck positions come from
body/cab templates and grade-colour checks. Other resolutions fail safely.
The top dice Refresh was observed replacing the list without a purchase dialog.
Ambiguous controls, unreadable candidate power and unexpected screens stop.
Use the unarmed example config when calibrating another layout.

Evidence stays under `runtime/truck-scanner/`. `last-truck.png` is overwritten
to avoid screenshot growth during long searches; match/share evidence and the
ledger are retained. Nothing is sent to Discord.

```powershell
go test -C tools/truck-scanner ./...
go vet -C tools/truck-scanner ./...
```

Tests cover boundaries, any-power two-fragment sharing, World-icon-relative
targeting, separate icons, screenshot fixtures and durable state. The previous
Python scanner was removed after the Go replacement built and was live-tested.
