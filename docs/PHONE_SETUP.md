## 2026-10-29: live geometry migration, version0.22



Fixed pixel paths have been removed from the helper's automatic input sources. Map gestures use freshly measured Camera.pixelRect, Screen.safeArea and active GraphicRaycaster blocker rectangles; directions and zoom travel are computed within a clear region. Group scrolling remeasures its actual list viewport. Camera projection now performs bounty taps in one guarded action. Retired raw-coordinate/text/numeric helpers, reference layout mapping, frame/template classes, image-position assets and their extraction scripts are removed. The build runs audit_input_positions.py and uses a fresh class directory/archive.



Passed62 retained policy/identity tests,16 gesture geometry scenarios,4 unavailable-text cases,15 Python tests, agent syntax and APK agent/asset/class checks. Twelve obsolete pixel/image fixture assertions were removed. Getter class/method lookup caches contain metadata pointers, never gameplay values or geometry.



On OnionRing92 UID2059765822000064/PID11076: live clear region with32 blockers, tile-confirmed move, State17 and22 short dry sweeps with approved zoom, truck UUID1430458885835077914 selection, group scroll/reveal preview, and camera-projected bounty selection at State17 X212/Y809 with matching UUID and popup dismissal passed. No posts/attacks in previews. Bounded live eligible-bounty search from historical X230/Y794 covered19 positions/142 observations, no qualifying12/15 match,shared0,attacked0. End-to-end qualifying bounty receipt is still pending. Real unavailable-state message and disconnected emulator/new layouts are also unverified; unknown errors stop rather than guess.



Signed0.22 update-installed; versionCode22/versionName0.22 verified. All settings XML and app JSON hashes matched before/after installation; evidence deploy-022-before/after.txt. Installed-app short dry bounty verification passed:oktrue,scanned3,planned0,shared0,attacked0. Core settings/history/real checkpoint hashes unchanged after preview; no injector remains; awake released and floating controls reopened. No agents.



## 2026-10-28: repeat-pool logging and screen timeout



User requested measuring whether refreshes reuse a finite pool. The unlogged0.18 bot run completed100 refreshes /817 truck observations without a qualifying share. A UUID-logging study was then started, but stopped after its initial9-truck list when Trucks disappeared and the phone showed its PIN lock screen. That sample cannot answer the pool question. A request to unlock and leave the bot active is pending; no PIN was requested or bypass attempted.



Added opt-in bounded TruckRefreshLog with all loaded UUIDs, exact owner UID and UI-gate IDs, one sample per actual successful refresh index. Added analyze_refresh_pool.py with8 passing tests for same-owner/new-truck distinction, periodic rosters, noncyclic overlap, changing rewards, precise UUIDs, duplicate/gapped refresh indices and incomplete terminal writes. Data remains local. Partial sample: runtime/helper-build/truck-refresh-pool-live.jsonl.



0.19 adds a scoped SCREEN_DIM_WAKE_LOCK with normal WAKE_LOCK permission. Normal jobs release it in cleanup and have a6h safety timeout; explicit diagnostic service leases last10m. No ACQUIRE_CAUSES_WAKEUP flag, keyguard bypass, global power-setting write, task/account switch or resolution change. After user unlocks, verify that the diagnostic lease is held before resuming the300-refresh study. Search remains bot-only with at most one qualifying group share and no attacks.



## 2026-10-28: 0.18 refresh performance



On the same OnePlus5T and pinned game build, no-action refresh cycles improved from mean8.96s across5 baseline samples (Gaarix) to1.30s across10 optimized samples (OnionRing92;1.14–1.55s), about6.87x faster. Different random lists/accounts; startup and match actions excluded. Saved timings: runtime/helper-build/refresh-benchmark-2026-10-28.json.



Removed repeated Lua field scans and process-map rebuilding using validated locations/runtime bindings, without caching values. Read-only focus observations expire after500ms; each actual input still forces fresh focus/PID/account verification plus agent checks. Refresh has no fixed450ms settle delay; a guarded100ms poll waits for a changed nonempty list with a10s bound. Two stable list observations and unexpected-dialog stops remain. Explicit window/tab and empty-list readiness waits replace reliance on accidental slow reads during cold entry.



Passed65 rules,16 memory-layout mutation checks,21 live binding/focus checks,10 receipt checks, JS syntax and close/reopen readiness. User requested searching on a bot and sharing a fresh qualifying truck to trucks before asking him to open Gaarix. Active bot verified as OnionRing92 UID2059765822000064/PID29274. No attacks on the bot. Group mode now checks the actual map rewards before its Share step.



## 2026-10-28: 0.17 validation follow-up



User authorized continuing the remaining validation. A live group run on OnionRing92 completed all30 refreshes:244 truck-record observations, zero eligible matches, sends or attacks. Then BountySendCheck completed state64 capital plus18 moves at approved zoom:57 bounty-record observations, zero eligible completed12/15 matches, sends or attacks. Counts include repeated cached records. The bounty diagnostic uses the real send ledger but never writes the user's bounty checkpoint.



Found/fixed WorldReceipt's decoded-param-only assumption by sharing the exact tile identity reader with group receipts. Ten Android-runtime JSON checks pass. Crucially, getLong on quoted19-digit UUIDs rounds on this Android version; the new reader inspects the raw value, preserves integer/string precision and rejects floating-point/overflow identities. Read-only verification decoded real World truck sequence717593 UUID1430459057344357657 and bounty sequence717539 UUID1430458922132586415. No message was sent by these checks.



Current production truck/battle button paths use live named controls/labels. Fixed taps found in legacy TruckFlowCheck were replaced with refreshTrucks/truckShare; its mode classifier now follows the selected diagnostic mode. Added bounded AttackCheck (one attack, active Gaarix required), a one-share bounty limit, and recognized-result-only startup for explicit battle-return recovery. Full live attack/result return remains pending the user opening Gaarix; an asynchronous request is pending. No account switch performed.



## 2026-10-28: 0.16 trucks group route



Signed 0.16 update-installed on f7c5e6fe and verified by package manager. Existing settings and share ledger hashes matched before/after installation. Installed-app bounded dry group-mode run completed ok:true, scanned7/planned0/shared0/attacked0. No qualifying truck was present in that sample; the separate explicitly authorized random-truck group transaction and scrolling diagnostic provide the group-route evidence. Floating controls reopened with no automation running.



Latest user direction replaces copied private links with native truck tiles to the group **trucks**, visible in the blue Share list. Pinned room: custom_vip_2028198887000064_1793214114, owner Gaarix UID2028198887000064. Existing 3+ orange-fragment, purple/yellow and strict configured power rules remain. Empty note; no World side-post and no attacks in this mode. Main and floating buttons now say Share 3+ to trucks group; stored mode truck-dm is retained for settings compatibility.



User explicitly authorized a random-truck test and confirmed it worked. Exactly one test tile, truck1430458630091584086 / PRM380 Farm, was sent from OnionRing92. Server group sequence7, post604, sendState0, sender UID2059765822000064 and exact attachment UUID were verified. Its existing pending attempt was reconciled using --verify-only; no second send occurred. Receipt identity lives in JSON attachmentId in this runtime, rather than param. The attachment reader is bounded to16KiB; UUID parsing preserves integer precision.



Dry group-scroll-preview passed from a list scrolled to its bottom: it found the group, deliberately scrolled it out of view, then found it again with shared0/attacked0. Share rows are virtualized. Missing rows are located by comparing the requested index with instantiated child names; gestures derive from live ScrollView bounds. Share buttons must fit inside the actual viewport before tapping. Room identity and exact label are checked separately.



65 rule checks and JavaScript syntax passed. Old private-link production delivery is retired; copy-only diagnostic support remains. Existing settings, signing key and ledgers must remain intact. The group test is in the real app ledger under group-truck:<room>:<uuid>; existing private and World entries remain separate. No agents used.



# OnePlus 5T setup — 2026-10-28



OnePlus 5T A5010, Android 10, stock build `ONEPLUS A5010_43_201029`, was bootloader-unlocked at the user's request, factory-reset, and rooted with official Magisk 31.1. Root was verified with `su -c id` returning UID 0 in the Magisk SELinux context. TWRP was booted temporarily to save the exact stock boot image; the installed recovery/system partitions were not flashed.



Original and patched boot images, hashes, installation details and progress are in `runtime/phone-root/OnePlus5T-f7c5e6fe/STATUS.md`. Preserve the original boot image for rollback. Do not relock the bootloader while the patched boot image is installed.



Installed Parallel Space 4.0.9500, Last Z 1.250.731 and Helper 0.10. Recovered external game assets were restored. The pre-wipe archive did not contain readable protected Last Z profile files, so cloned account login sessions were not recovered. The player must recreate clones and use each character's bound login.



## Helper 0.15: live UI geometry



Version 0.14 deployed the temporary tall-phone coordinate scaling fix and passed 65 host tests. Version 0.15 replaces that approach for bounty controls with named exported Unity objects and measured screen bounds. The bridge uses `il2cpp_class_from_name`, runtime metadata and getter calls; it does not depend on hardcoded native method addresses or game action handlers. A one-shot `Canvas.SendWillRenderCanvases` callback runs getters on Unity's render/main thread. Controls are resolved from Lua wrapper `instanceId`, checked active/interactable, and projected from RectTransform corners through their actual Canvas camera. The Android tap is queued immediately with account/focus/instance/freshness checks. Slight screen-edge clipping is tolerated only when at least80% of the rectangle remains visible; hidden or invalid controls fail closed.



Verified on OnionRing92 UID2059765822000064, game PID18262/start1412169, native1080x2160:



- Map Search opened using its live bounds. The same object was correctly rejected while hidden at the far-out map level.

- State17/X500/Y500 were entered through live input bounds and the focused Unity numeric dialog. Each editor was read back, then each committed value checked in exported game state.

- Two bounded State17 dry runs completed capital navigation, approved zoom, scanning and one map move; the latest scanned26 records with zero shares/attacks. These samples had no eligible12/15-box target.

- A loaded2-box bounty was used only as a non-sending fixture: map coordinates projected through Main Camera, selected UUID verified, exported Share button opened the menu. World room/list row and rendered World label matched; clicking its live bounds opened confirmation, whose exported input field read back empty. The final Share button was not pressed and no plunder was attempted.

- A terrain tap intended to dismiss the popup selected a nearby base; Back was ignored. The final implementation instead uses a short world drag in the space measured beside the popup. This closed it without selecting another map object.

- 65 host rule tests passed; generated input-agent JavaScript passed syntax checking. Runtime sessions detached successfully after checks.

- Final0.15 signed APK installed and package manager verified. A bounded dry run through installed HelperService/JobRunner and private assets completed State17 capital plus one move: `ok:true`, scanned28, planned0, shared0, attacked0. No controller/injector remained, game PID18262 and native1080x2160 unchanged. Floating controls reopened with automation idle; saved options and ledgers retained.



Migration scope includes coordinate inputs/buttons, base-to-World, bounty Share, common Share close/copy, World row, empty note and confirmation button. Bounty selection now uses camera projection. Remaining truck/battle/private-chat navigation and scanning/zoom gestures have not all been migrated. The old screenshot confirmation templates are historical diagnostic fixtures; production World confirmation uses room/target/post identity plus the actual input field text and live button bounds. No eligible bounty was posted during these tests, so live bounty server acknowledgement after this change remains unverified. Private live delivery and phone battles also remain unverified. No game/task launch, account switch or resolution change was introduced.



## Earlier 0.13 active-window controls



The 0.11 resolution override could restart Parallel Space and open another account. Version 0.12 removes it completely. Runs use the existing 1080x2160 surface and pin the focused window's PID, process start time, and character UID. Chat/player UID sources must agree; both are checked again before input. No game launch, task switch, or fallback process selection is performed. Window/character changes stop the run. The user may deliberately run from main; no permanent account block is installed.



Both interfaces now offer **Send 3+ to Gaarix**, **Attack 3+ on Gaarix**, **Share 2+ to World**, bounty scanning and STOP. Send/Attack require 3+ separate orange-fragment slots and power strictly below the configurable limit (default 440m). World shares only the truck tile for 2+ at any known power. Version 0.13 removes power announcements entirely at the user's request: neither the share-note box nor a separate chat message is used. Attack requires Gaarix's verified UID `2028198887000064`; private Send rejects sending to itself. Skip state affects World only. Confusing inspection/navigation buttons were removed.



An input-detach timeout during development froze the game. The user manually reopened the intended account. The revised input path keeps one interactive injector session for a whole run, exchanges nonce-tagged JSON commands over stdin/stdout, and detaches once during cleanup. This avoids hundreds of attach/detach cycles. The pinned Frida protocol is documented in its [17.24.3 injector source](https://github.com/frida/frida-core/blob/17.24.3/inject/inject.vala). This reduces the observed trigger; long-running stability still needs practical use.



Historical 0.12 validation on OnionRing92 (`2059765822000064`), selected game PID 15684:



- 62 host tests passed: mode separation, strict power boundaries, account restrictions, focused-window ownership, native layout, copied-link identity and bounded image-tint normalization.

- Persistent input inspection confirmed native 1080x2160 and the intended clone. Several UI actions completed within a single session; cleanup exited successfully.

- Copy-link control was recognized visually. The clipboard contains a formatted owner/state/coordinate link, not necessarily the truck UUID. Validation binds the selected share-menu UUID to the exact copied owner, alliance, state and coordinates.

- The helper followed Private Chat / Friends / Gaarix, verified the exact one-to-one room and recipient UID, pasted the copied link, read it back and cleared it. No Send button was pressed in that diagnostic. The game remained responsive afterward.

- World preview scanned 15 records, recovered from an unselectable truck by refreshing, and verified one qualifying truck's live identity/rewards and World-row label without posting.

- Updated app installed successfully. All three floating buttons and settings were verified from Android UI hierarchy. A World preview launched by tapping the floating button scanned 28 records over three lists; tapping its STOP button returned `stopped:true`, with no controller/injector left. Native resolution and selected game PID stayed unchanged. Preview was restored off afterward; power440, skip0 and states17-64 were retained.

- Live World card delivery was verified on truck `1430458739369970731`, server sequence717285. During the earlier 0.12 test its initial `315m` follow-up was blocked by the keyboard. After verifying the own-account card and absence of that text in server history, a controlled follow-up was sent and acknowledged; the card was not reposted. Version 0.13 subsequently removes the entire follow-up path, including its recovery diagnostic. Existing ledger history remains intact.

- Native confirmation templates now support 1080x2160. Two captured dialogs with differing tint pass; a modified fixture containing an existing draft is rejected. Confirmation still requires exact World glyphs, empty-note structure and a gold Share button.



Private server acknowledgement and phone battle formation/result return are not yet live-verified. Earlier bounded scans of more than 300 truck records found no qualifying 3+ private-send candidate below 440m; they sent nothing. Do not treat the successful unsent-draft test as proof of server delivery.



## Earlier 0.11 validation (superseded display behavior)



The initial phone port selected ARM64 correctly and used a temporary 1080x1920 display, restoring the preceding override afterward. That approach was superseded by 0.12 because resolution changes restarted clones. The checks below describe the earlier port, not the current account-selection behavior.



The phone's ARM64 `libil2cpp.so` SHA-256 is `310ad5120b508f8063bdc393dc9d605ef6ace7cf83ecf403cdd1dabe7bc2b660`, exactly the previously supported library. Earlier claims that the phone hash was different were incorrect. Live read-only discovery succeeded inside Parallel Space, UID 10221, clone cache `/data/data/com.lbe.parallel.intl/parallel_intl/0/com.readygo.barrel.gp/cache`. ARM64 injector 17.24.3 came from the official Frida GitHub release, archive digest `0ef2d078a5519e79736fdff7f5c0a35074cb2a8245af5101d84d373a72255ded`, decompressed digest `3133d798ef48aa10fec06594ad9b69d80220038ebdaa4775c836741bfc3bf5a4`.



Magisk 31.1 requires explicit Superuser grants. Shell was granted through the app's Grant Superuser selector. The user subsequently granted Helper. Game/Parallel Space apps do not need blanket root access.



Historical 0.11 checks on the connected phone, 2026-10-28:



- Helper's own `su` runner read live state successfully after installation (not just the separately authorized ADB shell).

- Final installed-app dry run also passed through `HelperService`/`JobRunner`, its private ARM64 injector and helper-process owner guard: five trucks scanned, result `ok:true`, zero posts/attacks. The app retained its previous settings; the saved Dry run checkbox was false and was not overwritten by the diagnostic's explicit dry options.

- ARM64 inspector attached to the Parallel Space clone and confirmed fullscreen 1080x1920. Its resolution-driven account-selection defect was subsequently reported and removed in 0.12.

- Base-to-World navigation passed. Coordinate editors entered state 64, x500/y500; capital metadata and approved height/LOD were verified. One map move completed and nine bounty records were scanned. This bounded sample contained no qualifying bounty share preview.

- Truck recovery refreshed once, read 13 records across two lists, selected a qualifying truck and passed both the memory-identity/reward check and the scaled World-share-row screenshot guard. Dry-run result: planned 1, shared 0, attacked 0. An earlier unselectable truck was handled by the existing refresh recovery.

- World chat draft `154m` was entered through Android input, read back from the focused editor, then cleared and verified empty. The Send button was not pressed.

- Display restored to physical 1080x2160 after each completed/failed check. No injector remained after the check.

- 35 host rule/focus tests passed; signed APK build and update install passed. Earlier emulator rule behavior was retained in source but the disconnected emulator was not retested in this phone session.

- Floating controls verified with Android UI hierarchy: Run/Resume bounties and Run trucks enabled; STOP bounds `[16,1634][893,1760]` fit inside the physical 1080x2160 display. Panel left open with the final successful dry-run summary.



No live World share or battle was performed during the phone port. Phone battle formation/result return and server acknowledgement of a live phone share remain unverified. The existing attack/share rules were retained; minimum attack fragment count is still fixed at three, with the power limit configurable. Saved user options, ledgers and signing identity are preserved by update installation.



Bounded diagnostics: build with `-DexOnly`, then run `python tools/last-z-helper/phone_check.py prepare` and a mode (`inspect`, `world`, `roundtrip`, `trucks`, `bounty --state 64`, `chat`). All automation in this diagnostic entry point is hardcoded dry-run. It uses a separate diagnostic folder and lock, not the app's live ledger. The `app-trucks` mode instead starts the installed helper with explicit dry-run options and a zero refresh limit, leaving its saved options untouched. Do not run diagnostics alongside another controller.

