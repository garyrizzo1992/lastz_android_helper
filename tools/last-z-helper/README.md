# Last Z Helper — 0.38 candidate

Installed phone release remains 0.37. The 0.38 source groups available maintenance under **Maintenance rotation**: set up registered games, choose accounts and tasks, preview one round, then run automatic game-to-game maintenance until STOP. Opening the helper immediately shows floating controls. Trucks and World-map bounty finding stay separate. Do not call 0.38 phone-verified yet: setup identified five games, but full round/startup UI testing was interrupted by an unexpected phone reboot. See [rotation implementation and test checkpoint](../../docs/MAINTENANCE_ROTATION_PLAN.md) and [current handoff](../../docs/CURRENT_HANDOFF.md).

Rotation includes VIP, Alliance Help/Gifts, completed troops and finished Wanted rewards only. Other Python features still require migration; chest remains quarantined. The sections below include historical release details; the unified Trucks group / World Chat selector described in the current handoff supersedes old destination-specific button names.

Release 0.30 adds memory-only Mail coverage diagnostics, deferred instrumentation for Wanted/finished-troop no-work paths, a mandatory compatible-session gate, and clearer failed-geometry status. Diagnostic screenshots default off (`phone_check.py --screenshot` opts in); World-share PNG evidence requires `diagnosticScreenshots:true`. Exact metadata receipts and duplicate ledgers remain authoritative. Attack screenshots are unchanged.

Maintenance controls include VIP free rewards, Alliance Help, Alliance Gifts, Collect finished troops and Collect Wanted rewards. Mail remains diagnostic-only with partial coverage; no Mail claim button. Chest collection remains disabled while its historical uncertain attempt is reconciled. See `docs/CURRENT_HANDOFF.md` for validation and continuation status.




Rooted Android helper for the pinned Last Z 1.250.731 (3161) runtime, with ARM64 phone and x86_64 LDPlayer injectors. Gameplay metadata is read from memory; UI geometry uses Unity getters, and actions use Android/Unity input. It runs on the device without desktop Python, OpenCV, Tesseract, or a Frida server.



Truck group sharing uses the initial big blue **Share** button directly, then the **trucks** group. It never uses Plunder or map preview. Plunder/Fight input is restricted to explicit Attack3+ on Gaarix mode, on Gaarix, with preview off.

Both main and floating controls offer **Bounties to World** and **Bounties to trucks group**. Eligibility remains completed available12/15-box bounties, empty note, no plunder. Each destination has independent duplicate history and resume checkpoints. The group destination is the same verified Gaarix-owned trucks room used for truck tiles. Group bounty server-receipt validation remains unverified until a qualifying target is available.

## Choose a truck mode



| Button | Eligibility | Action |

| --- | --- | --- |

| Share 3+ to trucks group | Purple/yellow, 3+ separate orange-fragment reward slots, exact power strictly below the configured limit | Share the native truck tile to the trucks group with an empty note |

| Attack 3+ on Gaarix | Same rewards/power rule; the currently active character must be Gaarix | Attack and return to the list |

| Share 2+ to World | Purple/yellow, 2+ slots at any known power | Share only the truck tile to World; it already shows power |



These modes are mutually exclusive. Send does not attack or post to World; Attack ignores other trucks; World never attacks. All truck modes refresh continuously until STOP, subject to the existing unexpected-dialog and unchanged-refresh guards. The power limit defaults to **440 million**; equality is excluded from Send/Attack. Skip state applies only to World shares. Counts mean separate reward slots, not a stack's quantity.



Gaarix is pinned to verified UID `2028198887000064`. Attack requires his active character; group scanning retains the scanning-account requirement. Group delivery is pinned to his user-created **trucks** room `custom_vip_2028198887000064_1793214114`, its owner UID and exact rendered label. Another room with the same name is rejected. World mode may run on any active character.



## Active window only



Open the intended game or Parallel Space clone and launch from the floating panel. At run start, the helper pins the focused window's owning PID, process start time, and character UID, cross-checking chat and player identities. It does not launch a game, bring another task forward, or select a fallback process. Losing the selected window, restarting the game, or changing characters stops the run. The injected input agent checks the character UID again before input.



Version 0.12 removes 0.11's display-resolution override, which restarted Parallel Space and could change accounts. It uses the existing portrait game surface (the OnePlus remains **1080×2160**), maps top/center/bottom UI anchors, and detects truck bodies in actual screenshot coordinates. STOP does not change the display or reopen a game. Each run keeps one interactive input session, using nonce-tagged JSON over injector stdin/stdout, then detaches once during cleanup. This replaces repeated per-action attachment, which caused a detach timeout and game freeze during development.



## Controls



The app and floating panel expose the three truck modes, **Scan / resume bounties**, a power limit, the World-share excluded state, bounty start/end states (default **17–64**), **Preview only**, and STOP. Diagnostic/navigation buttons and the truck refresh-limit setting were removed from the user interface. Tap the floating title to expand/collapse; drag it to move. Settings are disabled while running and STOP remains outside the settings scroll area.



Preview prevents all messages and attacks. It may navigate, refresh, and inspect share destinations. Close startup popups before starting. The group route uses the native Share list; it does not copy or paste a link.



Bounty scanning visits each state's capital region at the approved zoom, checks completed 12/15-box bounty previews, skips exhausted and unavailable targets, and shares to World with no added text. It never plunders. An interrupted range resumes automatically; a completed range starts again.



## Live UI geometry in 0.22



Bounty navigation no longer taps fixed State/X/Y/search coordinates. Named Lua UI controls supply Unity instance IDs. A bounded callback on Unity's render thread resolves the live objects, checks visibility and Selectable interactability, reads RectTransform world corners, and projects them through their Canvas camera. Android input then clicks the measured center after rechecking account, focus, instance identity and freshness. Missing/hidden/disabled/off-screen controls stop instead of falling back to guessed pixels.



This covers map search, State/X/Y fields, coordinate confirmation, base-to-World navigation, bounty Share, share-menu close/copy, World channel selection, share-note inspection and the final Share button. World rows must match both the active country room ID and the rendered World label. The share note must be empty. Bounty selection projects its map location through the live main camera and verifies the selected bounty UUID. Popup dismissal uses a short map drag derived from live popup bounds, avoiding a background tap that could select a neighboring base. Current production truck and battle buttons also use named controls or live label selection. Zoom and map scanning use fresh camera pixel rectangles, Screen.safeArea and visible GraphicRaycaster blockers. The agent selects a clear rectangle and derives native-pixel gestures inside it. Scan routes contain directions, not pixel endpoints; map coordinates must change before another scan. Pinches use viewport-relative travel and camera-height feedback. Missing/occluded/stale geometry stops. Group scrolling also remeasures the actual list viewport immediately before input. Retired fixed-tap text/numeric diagnostics, raw coordinate input APIs, reference-canvas mapping and image-position templates were removed.



The getters do not invoke game Share/Plunder handlers or write gameplay fields. World tile-to-position conversion retains the pinned build's calibrated hex-map representation. This geometry bridge is tested on the connected ARM64 phone; the disconnected emulator has not been retested.



## Duplicate prevention and receipts



Persistent ledgers record attempted sends before the destination is clicked. Group keys include the pinned room ID and truck UUID, separately from World and legacy private keys. Uncertain sends are not retried automatically. The group confirmation must match room ID, post type 604, truck UUID and an empty note. A server receipt must match room, sender, sendState 0, sequence and exact truck UUID from param or the JSON attachmentId; large UUIDs are kept as integers. Group scrolling reads the instantiated row numbers and uses live viewport bounds in either direction; clipped share buttons are rejected.



Attack attempts are tracked separately by truck UUID. Existing five-hero formations are reused; empty formations use the live one-key formation control, while partial formations stop for manual selection. Unknown power, changed identities, unexpected dialogs, lost focus, and unrecognized result/confirmation screens stop the run.



World confirmation now verifies room, post type, target identity and the live input field's empty text before clicking its exported button bounds. Server receipts also match the target identity. Version 0.13 removed all World power announcements: no share-note text and no separate visit to chat. Production delivery uses native tiles; retired private-link draft diagnostics and image confirmation templates have been removed.



State is stored under `/data/user/0/dev.codex.lastzhelper/files/`: `world-shares.json`, `truck-attacks.json`, bounty checkpoints, screenshots, and `last-run.txt` (updated during a run). Updates retain the signing key, options, and ledgers.



## Build



Requires JDK 17, Android SDK platform 35/build-tools 35.0.1, and Python for Windows packaging:



```powershell

python tools/last-z-helper/fetch_arm64.py

powershell -ExecutionPolicy Bypass -File tools/last-z-helper/build.ps1 -Install -Serial f7c5e6fe

```



Output: `bin/last-z-helper.apk`. The two large Frida 17.24.3 injectors are ignored by Git and SHA-256 checked by the build. `fetch_arm64.py` verifies the official release archive digest and ELF machine. The x86_64 asset can be recovered from a previous APK with `bootstrap_assets.py`. Keep `runtime/helper-build/test-key.jks` to preserve update signing identity. Java bridge and Frida license texts are bundled.



The supported ARM64 game library SHA-256 is `310ad5120b508f8063bdc393dc9d605ef6ace7cf83ecf403cdd1dabe7bc2b660` (also used through translation by the tested LDPlayer game). New builds stop for review.



## Validation



Run `powershell -ExecutionPolicy Bypass -File tools/last-z-helper/validate.ps1`. It builds from a fresh classes directory, runs the mandatory input-position audit, 62 policy/identity rule checks, 16 gesture-geometry scenarios, four error-text cases and 15 Python tests (eight pool-analysis, seven audit checks). Twelve obsolete reference-pixel/image fixture assertions were retired. JavaScript syntax is checked too. Each build archives only its newly compiled classes before dexing; deleted classes cannot leak from an older compiler directory.



The audit rejects retired coordinate APIs, literal input endpoints, raw-coordinate actions, reference-canvas mapping and image-position assets. It is a regression guard, not a proof against every future way of introducing coordinates. Remaining numeric values describe gesture proportions, validation/timing bounds, supported display dimensions, data IDs and the pinned hex-map representation—not button locations.



Unavailable-state handling reads active Unity text through getters and recognizes bounded state/server/warzone unavailable messages. It compares against text visible before the search. Unknown messages or unconfirmed destinations stop; no image-location fallback remains. The exact live message “The State you are searching for does not exist.” is recognized; discontinued states are skipped and the scan advances. State40 was verified live. Prior recognized text must clear before another search, preventing stale-message skips.



Live bot checks passed: camera/occlusion discovery, coordinate-confirmed map drag, State17 and State22 search/approved zoom/short preview sweeps, UUID-bound truck selection and virtualized trucks-group reveal after deliberate scrolling. No posts or attacks in these previews. ARM64 phone evidence only; emulator/new display layouts still need live retesting. Qualifying bounty receipt validation is pending.



### Historical validation and performance



0.19 adds an opt-in, bounded JSONL refresh-pool study (`logRefreshes` debug option; enabled by PrivateSendCheck). It records stable loaded UUIDs, exact owner UIDs and rendered IDs once per successful refresh index, without treating a second inspection of the same list as another refresh. `analyze_refresh_pool.py` measures new/returning UUIDs, roster repeats, owner-versus-truck repeats and lag cycles. Eight analyzer tests cover false-cycle cases, large IDs, missing frames and partial writes. Logs stop at4000 observations or8MiB; ordinary app runs leave the debug logger off.



Automation jobs hold a time-bounded screen-dim wake lease while running and release it during cleanup (maximum6h). A separate10-minute diagnostic lease is available through HelperService actions hold-awake/release-awake. Neither uses wake/unlock flags nor changes global power settings. The phone must already be unlocked and the chosen game visible before input; manual locking still stops automation. This addresses automatic screen timeout during injected input, which is not physical Android touch activity.



0.18 refresh optimization: measured refresh-only cycles dropped from a mean8.96s (five baseline samples) to1.30s (ten optimized samples, range1.14–1.55s) on the same phone/build; the baseline account was Gaarix and the optimized account OnionRing92. Field locations are cached with current table/node/key validation, but truck values are always read fresh. Runtime manager/class bindings are reused only while still valid in the same pinned process. Read-only focus observations have a maximum500ms age; every input still forces fresh PID/focus/account validation and the injected agent's own checks. Unchanged refreshes wait on actual list changes at100ms intervals, up to10s, with full window/modal guards. Two stable reward observations remain required. The450ms refresh-only settle delay and repeated state rebuilds were removed; other control settle delays remain.



Validation added16 synthetic Lua mutation checks (fresh values, moved/deleted/reused fields, rehash, exact integers and UTF-8),21 live runtime/focus checks (including invalid binding rediscovery and forced fresh focus), and a successful Trucks close/reopen readiness check. Existing65 rule and10 receipt checks still pass. Timings are saved in runtime/helper-build/refresh-benchmark-2026-10-28.json. Group targets are now rechecked in their map preview before sharing, so a cached3-slot listing that has already lost rewards is skipped without posting.



0.17 adds a common exact-UUID receipt parser for World and group tile posts. Android's getLong(String) can round a quoted 19-digit UUID; the parser now accepts exact integer/string representations and rejects floating-point identities. All 10 Android receipt checks pass, including adjacent large IDs, string IDs, mismatched post types and overflow. It also decoded real World truck and bounty receipts without sending.



The latest live group scan completed 30 refreshes / 244 record observations with no qualifying 3+ truck below 440m, so it sent nothing. A state64 capital sweep completed 19 scan positions / 57 bounty observations with no completed available 12/15-box match and no posts or attacks. These counts include repeated cached records. Neither proves a qualifying end-to-end send; the earlier explicitly authorized random group tile remains the successful live group transaction.



Victory and defeat were live-tested before the gesture migration. Victory returns through btnContinue; defeat returns through continueTipText (Tap to close). These control paths were preserved; no additional attacks are needed for this migration. Bounded diagnostics refuse account switches and use the same controller lock and durable ledgers.



See `docs/PHONE_SETUP.md` for the actual phone evidence, test coverage, and remaining limitations; `docs/BOUNTY_MEMORY.md` retains the earlier investigation.


## Native maintenance migration (0.25)

VIP free rewards is available in both panels. It checks/claims only daily login points and Daily Freebies, returns to base and reports claimed/cooldown/blocked results. Preview uses live state without claims or completion writes. Activate, VIP packs and Shop controls are excluded by an input allowlist. Each claim is saved before input and requires the claimed/cooldown transition; uncertain operations are not retried. Status and attempts live in per-character maintenance-state.json, separate from share/attack/bounty data. Game countdown determines next due. A manual VIP run does not enable a background maintenance profile. Other Python features remain planned in docs/PYTHON_TO_ANDROID_MIGRATION_PLAN.md.

## Alliance maintenance (0.26)

Alliance Help and Alliance Gifts are available in the main and floating panels. Each run uses the current character only. Help runs one free Help All action and verifies the pending count plus points/handled evidence; Activate is excluded. Gifts checks Common and Rare separately, journals selected gift UUIDs before Claim All and requires each UUID to become received with a receipt time. Delete, level chest, settings and purchase controls are excluded. Preview navigates and inspects without claiming or saving completion. These manual buttons do not enable a background scheduler. Uncertain attempts block automatic retries; verified claims remain saved even if later navigation fails.

Live evidence: OnionRing92 helped10requests (280→380points), repeat had no work. Common Gifts155UUIDs verified received. Rare had no unclaimed fixture; live Rare claim remains unverified. Credit-cap Help verification remains unverified; without points or handled evidence the run stops uncertain. See migration plan for exact evidence and remaining work.

## Maintenance preflight (0.27)

Expected-account options are checked before injected foreground inspection. Preview status explicitly discloses game instrumentation. A required build audit guards this ordering; a mismatched-account diagnostic with a nonexistent injector rejected before launch. Mail inspection remains diagnostic-only and cannot claim, mark all read or delete; actual Mail collection and scene-object chest geometry are still pending. Risk assessment: docs/BOT_DETECTION_RISK_ANALYSIS.md.

## Finished troops (0.28)

Collect finished troops is available in both main and floating panels. It collects only completed Car/Foot/Bow training queues linked to their exact building and bubble; it never starts training, heals Hospital units or upgrades troops. Every attempt is journaled before a fresh geometry/collider/queue/inventory-checked tap. Success requires the queue to become Free, free units to increase and in-training units to decrease by the recorded quantity. Live Bow145collection verified free56→201/train145→0; repeat0claims, Car/Foot/Hospital records unchanged. Preview is non-consuming. Unknown outcomes remain quarantined.

Native scene references use verified XLua metadata and live camera/collider/raycast/HUD bounds, with lifecycle and exact64-bit ID tests. Explicit pre-dispatch cancellation retains evidence and a separate retry record; it never clears uncertain dispatched actions. Older helper versions conservatively block the new cancelled state on rollback.

Eight-hour chest collection remains UNRELEASED/entrypoint disabled: a legacy attempt was rejected before gesture by a transient notification but lacks a structured receipt, so it remains uncertain rather than being bypassed. Only chest inspection/open-only diagnostics exist; no chest claim button. See CURRENT_HANDOFF.md for reconciliation and remaining validation.


Release0.31 uses immutable SHA256-addressed native agent assets and adds a memory-only own-base inventory diagnostic. It joins exact own building/item identities; all bubbles remain unclassified and collection-disabled. Existing runtime files are preserved. No passive resource collection button is exposed. Installed/source-only details remain in CURRENT_HANDOFF.md.
