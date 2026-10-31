# Bot bounty monitor

Started 2026-10-29, Europe/Malta. User explicitly requested starting bounty sharing to trucks on the bot, leaving it running and checking periodically for improvements.

- Installed helper0.24; settings/history/checkpoint hashes preserved (deploy-024-before/after.txt).
- Active OnionRing92 UID2059765822000064, PID11076/start4412219; do not switch accounts.
- Running mode bounties-group, saved states40–64, dryfalse, resume defaulttrue. No truck scanner or attack mode.
- Startup: state40 exact nonexistent-state message recognized; skipped and advanced to state41. No shares/attacks reported yet.
- Monitor heartbeat ID: monitor-bot-bounty-sharing, active every15minutes in this chat. Read logs/ledger/checkpoint only while the worker runs; do not inject, replace assets or hot-install.
- On normal completion of range, report and end the monitor; do not start another range. Honor any later user stop. Disconnection/account change must not trigger account switching or automatic restart.
- Progress source: /data/user/0/dev.codex.lastzhelper/files/last-run.txt and bounty-group-progress.json. Receipts: world-shares.json keys group-bounty:<room>:<uuid>, pinned room custom_vip_2028198887000064_1793214114, owner Gaarix. No plunder, no note, only completed available12/15.

## Improvements to observe

1. Whether consecutive discontinued states are reliably recognized and skipped (old message must clear before the next search).
2. Navigation/zoom/movement stalls and time spent per state; investigate using concrete log timings before changing behavior.
3. Whether group share confirmations and receipts match exact bounty UUID/coordinates/room with empty note.
4. Whether virtualized group row reveal or repeat prevention causes unexpected stops. Never retry uncertain sends.

No broad tuning is justified yet; preserve the direct blue Share route for truck sharing and Gaarix-only attack guard. No agents.

## 2026-10-29 01:11 Europe/Malta check

Healthy run advanced from40 to51 (checkpoint nextState51, completefalse),1401 observations,shared0,attacked0. No group-bounty attempt/receipt records yet and no result/error termination. Fresh read-only state probe confirmed the same OnionRing92 UID/PID/start; worker remains active. No input, injection, asset overwrite, install or restart performed. Left scanning running.

Observability improvement for a later stopped-worker update: current scanned counts include repeated records and lack per-state eligible/unfinished/exhausted/duplicate counters. With1401 observations but no sends, unique/eligibility breakdowns would explain coverage and filtering without weakening eligibility. Prepare only when useful; do not change the active worker or assume a fault from zero shares.

## 2026-10-29 01:26 Europe/Malta check

ADB read of the app log failed. Checking device connectivity; no game input, restart, account switch or deployment attempted. Last confirmed healthy position was state51 at01:11. Cannot infer current game progress or completion without a fresh log.

Confirmed: adb devices lists no connected devices; f7c5e6fe not found. Monitoring cannot read the phone until it reconnects. The Android worker may still run independently; its present status is unknown. Keep the heartbeat for reconnection checks, do not restart scanning automatically, and avoid repeated unchanged disconnect notifications.
