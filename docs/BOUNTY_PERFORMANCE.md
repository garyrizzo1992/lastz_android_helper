# Bounty search performance investigation

2026-10-29, Europe/Malta. Requested diagnosis of extremely low FPS during bounty search. Work resumed after switching Codex to Full Access. No agents, scan restart, account change, gameplay input, APK installation or production source changes in this investigation.

## Measured evidence

Phone f7c5e6fe, OnionRing92 UID2059765822000064, PID4652/start8058934. Fresh state confirmed clear World scene2/modal0. No AutomationController, MaintenanceController, PhoneCheck or injector was running before the isolated probe. The idle helper app was present.

The saved bounty-group job has completed start40/end64/nextState65/complete:true. Its final result is4717 bounty observations,0 shares,0 attacks. Observations include repeated records; this is not4717 unique bounties. No job was restarted.

Read-only SurfaceFlinger timing sample on the actual game SurfaceView:127 frames, average30.13 FPS, median frame33.33ms, p95 frame50.07ms. This sample is with the worker stopped, not a measurement of the user's earlier severe slowdown. Thermal service reported status0 in the initial inspection; this does not rule out earlier throttling.

An isolated getter-only diagnostic then measured:

| Operation | Result |
| --- | --- |
| Bounty snapshot, first call including template initialization |540.36ms,73 bounty records |
| Bounty snapshot, warm |373.58ms,73 records |
| Bounty snapshot, warm |430.28ms,73 records |
| Aggregate memory reads over those three snapshots |208885 reads,5024138 bytes |
| Aggregate state snapshots |3 calls,316.44ms total |
| Aggregate focus checks |2 calls,208.87ms total; included within snapshot work, do not add again |
| Field-cache counters |20 hits,10409 misses; investigate table population/cache churn before attributing a specific cause |
| World geometry, first call |97 graphics inspected,16 blockers,41ms inside Unity render callback |
| World geometry, repeat |97 graphics inspected,16 blockers,33ms inside Unity render callback |

Both geometry receipts explicitly have inputDispatched:false. The diagnostic guard allowed only inspect/map-region. No map gesture, click, share or attack was sent. DeviceInput was closed and its injector detached at the end.

Evidence (ignored local runtime files): runtime/helper-build/bounty-fps-readonly.json and bounty-performance-profile.jsonl. Reproducible local diagnostic sources: bounty_fps_readonly.py, BountyPerformanceCheck.java, prepare_bounty_profile.py and run_bounty_profile.py. The modified agent exists only in the diagnostic artifact; it adds timing/graphic-count fields, with no production source/APK changes. Diagnostic device folder: /data/local/tmp/lastz-bounty-profile-1793302906. Existing phone-check and installed assets were not overwritten.

## What this explains

AutomationController.moveMap reads a complete BountyReader snapshot BEFORE and AFTER movement. Its caller then immediately calls scanBounties, which takes another complete snapshot. Whenever the list is nonempty, scanBounties takes yet another complete snapshot to consider restoring the scan position, even if no eligible bounty was opened. Thus an ordinary move over a nonempty area incurs FOUR full bounty snapshots, before any additional per-target work.

On this sampled area that represents roughly1.5â€“2.2seconds of snapshot work alone per move (an estimate from the measured samples, not an instrumented full-cycle duration). DeviceInput.mapMove separately waits800ms after its gesture. The gesture emits20 movement updates on30ms timers plus its initial120ms delay; actual cadence can be slower due to scheduling/guards. These deliberate delays and redundant reads explain low search throughput and stop/start map motion. They are distinct from rendering FPS.

unityMapRegion enumerates all active UI Graphics and measures blockers synchronously in SendWillRenderCanvases. The measured33â€“41ms callback can cause a short frame hitch. It does not by itself establish a sustained severe FPS collapse. Bounty memory reads execute in the external diagnostic/controller process; their duration must not be presented as time spent blocking Unity's render thread.

## Next optimization, if requested

1. Pass the just-verified post-move snapshot into scanBounties instead of immediately reading it again. Preserve server/LOD/zoom checks and per-target fresh identity/availability checks before input/sharing.
2. Only consider restoring the scan origin if the scan actually navigated to a bounty. Do not enumerate the entire point population just to check camera position. Revalidate current state before any required movement.
3. Profile allViewPoints size, row enumeration and field-cache behavior. TruckDiscoveryProbe.rows currently scans hash slots twice using many tiny /proc reads; investigate a bounded bulk-read implementation with table-layout/version validation and meaningful fixtures before changing this shared reader.
4. Add bounded phase timings for snapshot, geometry, gesture and settle to distinguish scan speed from frame stalls. Preserve UID/process/focus/STOP checks; do not improve speed by removing guards or reusing stale coordinates.
5. Measure a bounded bot map-movement sample and SurfaceFlinger cadence before/after an optimization. Do not restart the completed40â€“64 sharing job implicitly. Keep any future release/settings preservation separate from this diagnosis.

This was the initial diagnosis. The live reproduction and deployed fix below supersede its previously unconfirmed FPS conclusion. Redundant Java snapshots have not been optimized in this change.

## Live reproduction and fix: installed0.32

The user started a new live bounties-group run over states10â€“64. A second performance probe correctly refused to start alongside that worker. Read-only SurfaceFlinger evidence then confirmed15.07FPS, median33.42ms/p95 183.05ms, while the worker was active. A thread sample showed the game's Android UI thread using90.3% of one CPU core versus UnityMain12.9%. This is actual rendering degradation during a scan, not merely slow scanning. Preserved evidence: bounty-fps-active-before032.json.

Stopped that worker using the helper's ordinary Stop action, waited for cleanup, retained start10/end64/nextState16/complete:false. The last result explicitly confirms stopped:true. No uncertain share was retried or ledger cleared. The isolated probe then performed exactly two opposite map drags on the expected bot, with no shares/attacks/account switch.

The native input agent's `field()` linearly traversed Lua hash tables for every account/map guard at each movement step, synchronously on Android's UI thread. Baseline east/west gestures each ran46account checks and23map checks and took4516/4483ms inside the agent (4732/4695ms including external checks/receipt handling). Account checks alone totaled2357/2398ms; map timing includes nested account time, so do not add the two timing columns.

Added `cachedLuaStringField` in input-agent-tail.js. A cache exists only for one request and holds up to128 hash-slot LOCATIONS. Every hit revalidates the current table node pointer/hash size/key tag/key string/non-nil value and rereads the live value. Layout changes invalidate/retry; instability/unknown fields fail closed. No account/focus/scene/STOP checks or gesture steps were removed. Numeric-ID lookup remains unchanged. No cached account values or screen coordinates.

With the fix, the same east/west test retained46account/23map checks and took1089/1118ms inside the agent (1405/1534ms externally). Account time dropped to74/113ms; map time113/136ms includes nested account work. Ordinary metadata-based geometry is retained. Evidence: bounty-movement-before.jsonl and bounty-movement-after.jsonl. Areas had slightly different bounty populations, but the gesture guard counts and scene/account were identical; this is not a controlled claim about every map/location.

157 cache regression checks cover reading a changed UID value, node-table replacement, relocated/deleted fields, changed key tags/hash size, reused addresses, rehash during lookup, bounded instability retries, bounded cache size and reduced warm lookup work. Full helper validation passes all existing suites plus these checks; see bounty-fps-validation.txt. Signed release0.32 built/installed successfully. All9 XML/JSON settings/history/checkpoint files matched SHA256 before/after install. Baselines bounty-fps032-{before,after}-persistent.json and install/build logs. Old agent assets retained; active new immutable agent c217441d91c3a342b30bd0712d9af1bfc92227bf0660225f66299974447e38d6.

Resumed the same bounties-group run with start10/end64/resume:true, on OnionRing92 UID2059765822000064. Initial post-install sample during navigation measured27.80FPS/p9566.50ms. A subsequent active map-scanning sample measured27.50FPS/p9550.43ms, while state16 advanced to182observations/0shares/0attacks. Evidence bounty-fps-active-after032.json, compared with bounty-fps-active-before032.json (15.07FPS/p95183.05ms). These are short live samples, not a guarantee of FPS on every state/device. Left the job running. Do not run another controller, inject diagnostics or replace/install assets while this job runs.
