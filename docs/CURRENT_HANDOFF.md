# Current handoff - start here

## Repository separation — 2026-10-31

The user moved ALL Android overlay/helper and migration work to **https://github.com/garyrizzo1992/lastz_android_helper**. Canonical Windows checkout is **C:/Users/Gary/Documents/vscode/lastz_android_helper**. Continue HERE; do not put helper source, migration documents or compatibility edits back into the original Last Z Python checkout.

Android app remains under `tools/last-z-helper`; migration docs are in this `docs` folder. The Python/Go working-tree reference (including ownership adapter, audit fixes and their tests) is preserved under `legacy/python-bot`; use that snapshot when resolving earlier Python-source paths. The helper ownership test now loads that reference directly. The original Python checkout is being restored to its pre-migration code and its committed migration doc removed from the current tree, preserving published Git history.

Private local assets moved too: runtime/helper-build, bounty-investigation, phone-root, phone-backups, signed APK/idsig, existing signing key and copied shared ADB dependencies. `runtime`, `bin`, `scrcpy`, keys, binaries and generated/private assets are ignored and are NOT published to this PUBLIC repository. Raw transfer manifest, Python patch and validation logs are in ignored `runtime/migration-transfer`. No credentials were found in the publication scan. No device action, install, game/account selection or worker start was performed for this move.

Relocated `validate.ps1` passes the full current suite, including35Python checks, recovery/storage/ownership/reconciliation/orchestration and Boomer/carousel checks. `fetch_assets.py` now prepares both checksum-pinned injectors for a fresh clone; existing binaries were verified without downloads. Signed installed artifact is still0.39 SHA256 e0e52e38deb18db0636afe47cb1e5130402cee0208c578fe37bf7a594d5787ce; relocation validation builds DEX only and does not replace that APK. Source/generated agent remain ahead of installed0.39 due to unreleased Boomer diagnostics. Keep the operational state and pending account-choice question in the next checkpoint below.

Mac copies/mirrors mentioned below are historical locations; repoint any future source synchronization to this repository before writing. This move does not deploy the Python shared-lock adapter to the old Mac service, resume either bot or authorize pending Auto Boomer activation.

## Latest checkpoint: Run bot/recovery 0.39 verified; Boomer reader ready, 2026-10-31

Installed signed0.39 SHA256 **e0e52e38deb18db0636afe47cb1e5130402cee0208c578fe37bf7a594d5787ce**. This is the authoritative installed artifact; older039hashes below are historical. Run bot/Preview bot/defaults/opt-outs are installed. Full worker recovery and actual Android foreground-service/helper-app crash recovery passed: app22442 was replaced by27251, SAME active generation resumed WAITING with restartCount1 and no account launch/feature/input replay. Lifecycle fix routes floating Run/Preview through BotRun.service/onStartCommand. STOP after recovery passed. Preview independence, enable-all/disable-all, missing-feature/account validation and restored selections passed. All15 existing XML/JSON files survived final update. Source negative/persistence/orchestration tests passed; game restart/watchdog branches still lack exhaustive live fault coverage, so do not claim every failure self-heals.

**Operational state:** Python remains stopped. Helper is idle, all five accounts unselected, all currently available feature flags restored enabled. No unattended rotation. Controlled live VIP-only run only verified cooldown/NOTHING_TO_DO with zero claims. No new purchases/dispatches/attacks. Old Python Mac deployment has NOT been updated for the new shared-lock adapter; Windows source is updated, Mac old service must stay stopped.

### Auto Boomer progress, not yet a production feature

- Added source-only BoomerPolicy/BoomerReader and bounded EventDiscoveryProbe. Added PhoneCheck boomer-read/event-carousel diagnostics, no new user-facing inspection button and no registry enrollment yet.
- Full validate.ps1 passes existing suites plus19Boomer policy and16native carousel guard checks. Existing phase0 totals include37recovery policy/39storage-default/11cross-process ownership/17reconciliation/15orchestration/5lease-handoff checks and35Python tests.
- Exact live Event Center entry: UIManagerInstance/windows/MainUI_SU/View/rightLayer/activityViewBtnSlg (btnActivity). Danger Lurks activity40005/type21/name exact Danger Lurks/group372337. Card path UIActivityCenterTable/View/groupItems/372337/tabItems/40005/btn. One native geometry-derived carousel swipe reveals it; offscreen clicks correctly rejected. Native eventCarousel guard restricts exact activity/path/viewport/direction, scene1/modal1/windowState2. Initial shell-swipe draft failed source input audit and was REPLACED, no audit bypass.
- Panel UIActivityCenterTable/View/panelComponentList/40005/autoBtnN opens UIAllianceAutoJoinRally. Read-only snapshot verified **ACTIVE**, expiry1793436399939, timer33567seconds at1793402835522, options type1 and2 selected. Dialog title Auto Team-Up, button label Activate, duration text Auto-Join Duration (with optional color markup), numeric View/endTime agrees. Next check is actual expiry, never a fabricated additional12hours. No activation, Off or join-option toggle was pressed. Guard/policy rejects inconsistent title/timer/layout and unknown paid labels.
- Current reader uses exact event/panel identity plus stable expiry and independent native text/control reads. Authoritative manager lookup is still unresolved: full DataCenter has370managers; AllianceAutoInvite/AllianceTeamAssemble are unrelated; global auto/rally-name search empty. Do not invent server proof. Inactive layout and successful activation/expiry transition still require actual observations.
- BoomerPolicy contains an INACTIVE layout model but it is unverified; activationEnabled remains false. Do not enroll as production or treat inspection as completion. Need scoped native entry/card/auto/activation/close guards, durable activation operation, exact expiry/options receipt, uncertainty reconciliation, readiness/backoff and actual eligible live verification before enrollment.

### Pending user input and exact next action

An asynchronous question asks which account to use for a real Auto Boomer activation/renewal test (trucks by garix, yn gaarix, baby gaarix). Existing trucks-by-garix has ~9hours active; do not turn it Off merely to manufacture a test. Wait for the requested account choice before dependent activation testing; continue independent source work in the meantime. Activation/renewal is intended free and does not break shields, but do not choose an account on the user's behalf after asking.

1. Read this latest checkpoint, preserve idle/unselected state and user account choice if received.
2. Implement/validate remaining Auto Boomer production workflow and native final guards; inspect the chosen account's inactive/renewal flow without premium actions or generic click permissions. Renew active protection only if the user chose that test account and explicitly accepts the renewal test; otherwise retain its current timer.
3. On successful live proof, enroll Auto Boomer default-enabled while preserving existing opt-outs, package a new version and data-preserving update; repeat preview/no-work/STOP and record evidence. If eligible sample/proof unavailable, leave this feature pending and progress another independent slice from ANDROID_BOT_REMAINING_PLAN.md.
4. Keep checkpoints after meaningful milestones. Entire Python parity remains pending (training/healing/construction/research/gathering etc.). No agents used or requested.

### Evidence/source locations

Windows docs and source C:/Users/Gary/Documents/vscode/lastz_android_helper. Mac chat work dir /Users/garyrizzo/Documents/Codex/2026-10-30/c-users-gary-documents-vscode-lastz. `work/windows_ps.py` performs SSH PowerShell; `work/phone.py` root ADB; `work/helper_ui.py` reads native UI XML and operates helper controls. Phone f7c5e6fe attached/unlocked on Mac, boot03b4464e-126a-44a1-8549-165aa04c4faa. No private key/config contents in docs/logs.

Evidence copied to Windows runtime/helper-build/phase039-resume-evidence and boomer-discovery-evidence. Mac originals work/phase039-evidence/system-recovery-live.json, installed-preview.json, lifecycle-fix-before.json, and work/boomer-evidence/boomer-reader-live.jsonl, danger-panel/auto-dialog/tab-items snapshots, native carousel/card bounds, option-one/two, close-auto/event receipts. Full logs boomer-validation{,-stderr}.txt; phase039 logs retain earlier suites.

Installed bin/last-z-helper.apk remains039 e0e52...; **source/assets/latest dex now contain unreleased Boomer reader/carousel diagnostics**. Do not install latest dex as if it were a signed release. Staged discovery dex /data/local/tmp/boomer-discovery.dex, staged agent /data/local/tmp/lastz-boomer-controls/input-agent-new.js. Mac source mirror work/phase0-source. Original038rollback runtime/helper-build/last-z-helper-038-before-phase0.apk. Handoff older blocks below historical; never discard uncommitted user/helper changes.

## Active checkpoint: 0.39 recovery verified; Auto Boomer discovery, 2026-10-31

Installed039 SHA e0e52e38deb18db0636afe47cb1e5130402cee0208c578fe37bf7a594d5787ce. Helper-app restart and worker recovery PASSED without replay. Preview independence/default restoration/no-account Run passed again; all five accounts unselected, all available feature flags enabled, Python stopped, no rotation running. Current diagnostic UI: Auto Team-Up dialog over Danger Lurks, UID2059765822000064. No activation or setting change. Close recognized dialog/event using live controls before leaving or unrelated work.

Auto Boomer: Event Center entry MainUI_SU/View/rightLayer/activityViewBtnSlg. Danger Lurks activity40005/type21/group372337 and exact data.name. Card path UIActivityCenterTable/View/groupItems/372337/tabItems/40005/btn. One native geometry-derived left carousel swipe revealed its offscreen card. eventCarousel native guard requires exact scene1/modal1/windowState2, viewport/path/direction and event identity;16regression checks pass. Input-position audit rejected an initial shell-swipe draft; it was replaced with native geometry, never bypassed.

Danger panel UIActivityCenterTable/View/panelComponentList/40005: autoBtnN opens UIAllianceAutoJoinRally. Active account shows Auto Teaming Up; dialog title Auto Team-Up, autoJoinBtnTxtN Activate, active stopBtn, leftTimeN duration roughly9hremaining and numeric View/endTime1793436399939. Do NOT activate/stop merely for discovery. Need independent authoritative state/expiry and inactive-state sample before activation receipts. AllianceAutoInviteManager/AllianceTeamAssembleManager are unrelated; full DataCenter list370managers. Filtered global auto/rally search returned empty.

Source-only EventDiscoveryProbe and PhoneCheck event-carousel staged at /data/local/tmp/boomer-discovery.dex; carousel agent ONLY /data/local/tmp/lastz-boomer-controls/input-agent-new.js. Installed039 agent unchanged. bin APK remains installed039; source/generated assets/dex contain unreleased discovery/native-carousel changes. Do not claim Auto Boomer implemented/deployed. Mac work/boomer-evidence holds snapshots, control text, card IDs, native swipe and dialog states. Windows boomer-discovery-build logs hold compilation/audit results.

Next: exact enabled/expiry reader/policy, scoped navigation and activation journal/native guard, tests, eligible live sample. Preserve active setting. Keep regular checkpoints; older blocks below historical.

## Latest checkpoint: 0.39 lifecycle recovery fix verified, 2026-10-31

Installed signed0.39 APK SHA256 e0e52e38deb18db0636afe47cb1e5130402cee0208c578fe37bf7a594d5787ce. Lifecycle fix routes floating Run/Preview through BotRun.service/onStartCommand, so Android receives START_STICKY for the active user-requested session. All15 existing XML/JSON files preserved across this update. Actual helper-app crash test PASSED: killed verified idle helper PID22442 with no injector, Android restarted as27251, same run generation resumed WAITING with workerRestarts1, no repeated account launch/maintenance result/input/claim. On-screen STOP cancelled it. Prior isolated worker recovery and all source suites remain passed. Both crashes were controlled idle tests, not evidence that every hung-game/feature recovery path has live coverage.

Current work: finishing Preview/reset verification and moving to Auto Boomer read-only metadata/control discovery. Python remains stopped. No uncontrolled worker is left running; final selected account/feature reset is being verified. Prior user-stop cleanup on Oct31 restored all five unselected and operation histories unchanged; resume temporarily selected first account/VIP-only for this non-consuming lifecycle test. Do not treat historical selected-test notes as production Run permission.

Next implementation: Auto Boomer exact event ID, enabled/expiry fields, control mapping, journal and final-dispatch guard; no generic event activation or shield gating. Keep checkpoints after significant milestones. All older status blocks below are historical.

## Latest active checkpoint: 0.39 installed; phase 0 recovery/UI checks in progress, 2026-10-30

USER REQUEST: implement ANDROID_BOT_REMAINING_PLAN.md; add live Run bot, separate Preview bot, all available feature defaults enabled with opt-outs retained, and bounded self-healing. User additionally requests REGULAR CHECKPOINTS due to usage/context limits. Update this newest checkpoint after every substantial implementation/test milestone. No agents were requested/used.

**Installed release is now 0.39**, signed with the existing key. APK SHA256 `ecd0c67b84cb469ef5e3d51b80f8fd2d6d63db8cff4761f3d002ee50abfeef34`. All twelve pre-existing app XML/JSON files were byte-identical across install. It is NOT full Python parity. A bounded live VIP-only run verified NOTHING_TO_DO/zero claims, then waiting-worker recovery and on-screen STOP passed. The helper is stopped. Temporary first-account/VIP-only selection still needs restoration; all other accounts remain unselected. Python remains stopped by explicit user choice. End tests with helper idle and all accounts unselected.

### Implemented in this slice

- BotRun and main/floating/configuration UI: explicit **Run bot** (dryRun:false), **Preview bot** (dryRun:true); **Accounts and features**; per-account enable-all/disable-all; missing newly introduced feature keys default true, explicit false choices survive. Account selection remains explicit. Only the existing five production maintenance workers exist; Auto Boomer and other parity features are NOT implemented yet.
- Durable RunRequest (`bot-run-request.json`): generation, selected-profile/options snapshot, requested-running consent, boot identity, bounded worker restart history. STOP revokes consent and writes the stop signal; stale generations cannot resume/cancel newer runs. Reopening alone never starts a job. Foreground service can request recovery only on Android's system sticky-service restart of a still-active same-boot run.
- RecoveryPolicy/State/Engine: recognized transient pre-input/navigation failures retry after 2/10/30 seconds, persist counts/deadlines, request one controlled game reopen per failed feature, defer still-failing work 15 minutes, limit game/worker restarts to three per account/session budget over 30 minutes. Healthy independent tasks can continue when state is proven clear. Unknown UID/focus/build/modal/detach remains a guarded stop. Waiting/full/exhausted states are not restart reasons.
- RotationController keeps the global lock across recovery, revalidates exact clone/UID, uses exact owned game PID for controlled restart only after verified input detach/current clear state, and preserves operation barriers. Recognized supported interrupted Wanted/training operations can reconcile read-only using exact task/queue/unit/building identities and strict transitions/deltas. Unsupported/ambiguous operations remain fenced; no generic claim/spend replay. RecoveryEngine explicitly defers uncertainty to avoid busy loops.
- JobRunner supervisor/watchdog: five-minute real-progress timeout requests worker detach; only a confirmed exit can recover. Unconfirmed detach halts recovery. Persistent worker budget, same generation, previous game identity/UI checks, STOP and boot checks gate replacement. Final checkpoints preserve game identity so safe waiting-worker recovery is possible. Idle before any game visit may resume waiting without opening a game.
- Shared ownership: ControllerOwnership/LegacyOwnershipSession/LegacyLease use the same Java FileLock across native tools and the updated Python source. Legacy shell commands execute as Android shell UID 2000 under the held lock, with a pending-input marker before child creation. Lost/failed command receipt fences native takeover. `bot/phone_ownership.py`, `bot/android.py`, and main_scrcpy.py in the WINDOWS SOURCE checkout acquire/use this adapter. The Mac's old installed Python checkout/service was NOT redeployed and must stay stopped; its bootstrap also fetches Git on start. Do not claim the legacy deployment has been upgraded.

### Verification already complete

- Full validation passes all previous suites plus 37 recovery-policy checks, 39 persistence/default/ownership-state checks, 11 real cross-process ownership-protocol checks, 17 reconciliation checks, 15 orchestration checks, and 35 helper Python tests. RecoveryStorageFixture (39) and RecoveryEngineFixture (15) also passed on Android in isolated /data/local/tmp directories, no game memory/input.
- Actual staged Android/Python ownership protocol passed: token ping, shell UID 2000, competing native controller blocked before memory/input, deliberately failing harmless `false` command fenced Python and subsequent native takeover. Fixture-only marker restored to its pre-test state; no gameplay action occurred. A first run found /system/bin/su absent; fixed to the established PATH-resolved `su` (/sbin/su on this phone).
- First two-account preview passed account 0 but stopped at account 1's pre-input Java guard `UI window context changed`. Fresh read-only inspection proved a clear base afterwards. Recovery now classifies that exact pre-input navigation guard as transient ONLY when fresh recovery state is clear; unknown/modal cases still halt. Final two-account preview passed all ten outcomes as PREVIEW, no deferred failures/claims/reboot. Hidden Wanted remains uninspected/deferred; do not call it a completed mission inspection.
- Signed APK contains the tested dex/unchanged agent, signer matches 0.38, update-install succeeds with all twelve old XML/JSON hashes preserved.
- New UI entry labels Run bot / Preview bot / Accounts and features were found; account/feature screen is open. Remaining installed-app checks below are not yet completed.

### Latest follow-up: final ownership refinement installed; Android app-crash test found a lifecycle gap

Phase039 lease/final-checkpoint race was tightened: recoveries wait up to20seconds for old ownership (STOP-aware), and the final checkpoint is now written before releasing the lock. Full suites plus5new lease handoff cases passed; interim installed039SHA was d453ff97bcf38b26a96ef52898bbe8da6c748ab04eb39362855ac626404c4a9f with all15 persistent JSON/XML files preserved. Installed Preview bot independence, restore defaults/selections and no-account Run rejection all passed. A new non-consuming VIP-only run then tested killing ONLY the helper app while WAITING/no injector. Android did not restore that run within50seconds; the test explicitly requested STOP. Cause found: floating launchBot called JobRunner directly, bypassing onStartCommand and its START_STICKY result. Source now routes floating Run/Preview through BotRun.service, matching main/config entry points. Rebuild/update and repeat the actual app-crash test before claiming app-process recovery. User selections currently temporarily first-account/VIP-only for this test; run stopped. Restore all five unselected/original feature flags before leaving.

### New verified milestone: installed Run bot and worker recovery

Installed UI enable-all/disable-all works, no-feature Run is rejected before worker start, saved opt-outs persist, and live Run bot uses dryRun:false with the exact one-account/VIP-only snapshot. Both VIP categories were proven on cooldown beyond the test duration; the real result was NOTHING_TO_DO with claimed:0. While waiting with no injector, verified owned RotationController PID18946 was killed and replaced by22875 in the SAME run generation. workerRestarts became1, resumed waiting was verified after a fresh reconciling event, and no account reopen or feature result/input was replayed. On-screen STOP then revoked requestedRunning and ended the recovered worker. The initial test observer briefly read the old waiting checkpoint before the replacement had emitted progress; the observer was corrected to require the new reconciling event, and the installed code recovered successfully. Evidence is work/phase039-evidence/worker-recovery-live.json, live-run-log.jsonl and stop-after-recovery.json on the Mac. Next: Preview bot independence, restore all selections/feature flags, final persistence comparison, and final phase039 checkpoint.

### Exact continuation: finish phase 0 validation before Auto Boomer

1. Finish installed configuration checks: all available features initially enabled; account selection still false; enable-all/disable-all work; saved opt-outs persist. Test no selected feature/account reports setup issue without starting a job. Keep tests scoped and restore original selections afterwards.
2. Test live Run bot routing on a single selected account with ONLY VIP enabled and its TWO categories freshly proven on cooldown well beyond the test duration. This is a non-consuming scheduler/wait test, not permission to claim other rewards. Confirm saved request has dryRun:false and exact feature snapshot; if not due, waiting without reopening a game is correct. Preserve and compare production operation records; no claims/purchases/dispatches. Capture current JSON before modifying configuration.
3. While that run is WAITING and no injector exists, test owned-worker recovery by killing ONLY its verified RotationController PID/start (never game/helper/other process). Check same run generation, worker restart counter, replacement controller and resumed waiting; no replay or account opening if nothing is due. STOP must then cancel retries/restarts and terminate the worker. This actual app-worker crash test is PENDING; do not claim it passed from policy fixtures.
4. Verify Preview bot is independent of old preview preferences; verify STOP from the new UI; restore all five accounts unselected and original feature flags, leave helper idle. No unattended live run. Compare old settings/operation histories and document only intended validation metadata changes.
5. Update this checkpoint, the plan status, parity doc and phase039 release metadata with final evidence/limits. Only then begin Auto Boomer's exact metadata/control discovery and production slice. Entire Python parity is still pending.

### Environment and evidence

Phone f7c5e6fe is connected/unlocked on the MAC, same boot ID `03b4464e-126a-44a1-8549-165aa04c4faa`. Windows project is `C:/Users/Gary/Documents/vscode/lastz_android_helper`, reached by SSH gary@192.168.1.12. Source/builds are on Windows, ADB is /opt/homebrew/bin/adb on Mac. Mac chat working directory is `/Users/garyrizzo/Documents/Codex/2026-10-30/c-users-gary-documents-vscode-lastz`; `work/windows_ps.py` sends encoded PowerShell and checks errors; `work/phone.py`, `work/helper_ui.py`, `work/run_preview.py` are existing task helpers. UI XML dumps and screenshots are in work/device-evidence and work/phase039-evidence. Never print private SSH key/configuration values.

Current signed candidate is bin/last-z-helper.apk; 0.38 rollback backup is runtime/helper-build/last-z-helper-038-before-phase0.apk. Windows logs: runtime/helper-build/phase039-{validation,validation-stderr,build,build-stderr}.txt. Local Mac: work/phase039-evidence/before.json (twelve hash baseline), maintenance-before.json, ownership-live.json, Android fixture outputs, install.txt, two-account-preview-final.jsonl; work/device-evidence/phase039-final-preview.jsonl. Failed preview remains phase039-two-account.jsonl and preview-blocked-windows.json for diagnosis; do not use it as success evidence. Test session points to /data/local/tmp/lastz-phase039-checks with isolated profile/history directories. Staged dex work/phase039-classes.dex; installed signed APK work/candidate039.apk.

Do not reset/clean/revert the checkout: older user changes and helper files are uncommitted. Do not restart the old Python service. All older release/planning blocks below are historical.

## Latest planning update: full parity, Run bot, enabled defaults and recovery, 2026-10-30

The user requested a clear plan for all remaining features, then explicitly added: a **Run bot** button that starts the selected features, **all available features enabled by default**, and **automatic retry/restart recovery**. Read [ANDROID_BOT_REMAINING_PLAN.md](ANDROID_BOT_REMAINING_PLAN.md) before implementation. These user requirements supersede older default-off assumptions and halt-on-every-transient-error behavior. Preserve explicit user opt-outs; account selection remains explicit. Preview bot is separate from live Run bot. Recovery must preserve receipts/uncertainty and respect STOP, exact UID and ownership.

This turn changed planning documents only. Installed release remains **0.38**; the new Run bot UI/default/recovery behavior is NOT implemented or installed yet. Python remains stopped, helper idle, all five accounts unselected by explicit user choice. No phone input, test, claim, controller or installation was performed for this planning update.

Next: implement plan phase 0 (Run bot / Preview bot, feature defaults, shared ownership/recovery and remaining rotation tests), then Auto Boomer and the remaining feature sequence. The plan includes passive/mail/chest claims, new training, healing/research/construction, donations/Wanted dispatch/assists, own trucks, radar/gathering, shop/shields/monitoring, and complete cutover criteria. Do not call the migration complete based only on rotation release. The detailed 0.38 release/evidence checkpoint follows below.

## Latest: rotation 0.38 installed and preview/UI verified, 2026-10-30

Continuation used the Windows checkout over SSH; the phone f7c5e6fe is attached to the Mac by USB. **Installed release is now 0.38**, same signing certificate as 0.37. APK SHA256 `91b29b03497e556f27a761eb99aa0943ef8cba59414be10c20fb0501981674c0`. NO native controller/injector or Python bot is running. The user explicitly chose **keep Python stopped; leave helper idle**. Mac LaunchAgent `com.garyrizzo.lastz` was booted out after a clean Python SIGINT shutdown; no service/configuration file was deleted. Bootout is not a permanent disable across a future login.

### Completed from the preceding checkpoint

- Phone is RUNNING_UNLOCKED. All ten original persistent XML/JSON hashes matched the pre-reboot baseline before testing. Existing five enrollments survived, unselected. Reboot cause remains UNKNOWN: prior init SIGABRT is still the only crash record, pstore is empty and no system_server_watchdog entry was found. No reboot recurred during this continuation (boot ID remained 03b4464e-126a-44a1-8549-165aa04c4faa). Memory pressure/lowmemorykiller events were observed; this does not establish the cause of the earlier reboot.
- Minimal one-account VIP preview passed; then a complete two-account round passed all ten feature outcomes as PREVIEW, exact UIDs 2059765822000064 and 2059770776000064. VIP, Help, Gifts and training geometry were inspected without claims. Hidden/unloaded Wanted was correctly **deferred for 15 minutes**, not reported as inspected/completed. Full live claiming/repeated live rounds are NOT newly verified.
- Integration exposed `UICommonMessageBar` (the game's nonmodal message banner) blocking Wanted on an otherwise clear base. WantedReader now recognizes only that exact window AND its observed prefab path, provided it is absent from the bounded modal stack. Unknown/replaced/modal windows still block; no dismiss-anything path or broader input permission was added. New WantedWindowPolicy and ten negative/positive checks; full validate.ps1 passed, including existing suites and 27 Python tests.
- Signed APK contains the tested dex, matches the installed signing certificate, and update-installed successfully without uninstall/clear-data. All **12** existing settings/history/enrollment/progress XML/JSON files matched before/after installation. Old pre-fix root-owned rotation-profiles/progress were adopted to the app parent UID/GID, chmod 0600, restorecon, with identical bytes. The existing RotationFiles writer already applies this for future root writes.
- Actual installed UI verified: launcher/reopen immediately opens expanded floating controls and starts NO job; grouped rotation screen reads all five profiles; account/feature choices save and survive reopening under the actual app UID; preview Run restores collapsed floating STOP bar; on-screen STOP produced stopped:true/running:false and detached. A separate initial STOP-file cancellation also passed. Prior isolated wrong-UID/unresolved-history/waiting-STOP evidence remains applicable; STOP at every possible launch timing has not been exhaustively rerun.
- Overlay permission denial opens the system permission screen; returning denied leaves the helper usable. Permission restored to original allow state; reopening shows floating controls and starts NO worker.
- Temporary two-account UI test selections were restored: **all five profiles unselected, original feature flags restored**. The only intended old-preference change after UI tests is adding rotationMinutes=20 and rotationPreview=true; other nine baseline XML/JSON files remain byte-identical, including production maintenance/share/attack/dead-state histories. Rotation progress/last-run record the stopped preview normally.

### Evidence and next work

Evidence is in `runtime/helper-build/rotation038-mac-evidence/`, notably release038.json, post-reboot-preservation.json, minimal-vip.jsonl, two-account-final.jsonl, install038.txt, ui-stop038.txt and UI XML snapshots. Validation/build logs are rotation038-mac-validation{,-stderr}.txt and rotation038-mac-build{,-stderr}.txt. The first failed previews are preserved and are not success evidence. Local rollback APK/private-state backup also remains in this Mac chat's work directory.

**No unattended rotation was started.** User must explicitly select accounts/tasks and Run. This completes the preceding checkpoint's rotation stabilization/release slice; complete Python parity remains pending. Continue the next bounded production slice from ANDROID_BOT_PARITY_HANDOFF.md section 9 (safe claims, then training starts, etc.), using existing receipt/uncertainty barriers. Do not arm shields, consume/spend or reopen quarantined chest attempts merely because rotation now installs. Do not restart Python without a new user instruction. Prior blocks below are historical.

## Latest: rotation source implemented; phone reboot blocked final testing/deployment, 2026-10-30

USER REQUEST: mimic Python: automatically open game A, run its enabled maintenance tasks, switch to B, repeat selected games until STOP. Trucks and World-map bounty finder stay separate. Work was started and implemented WITHOUT agents. Read [MAINTENANCE_ROTATION_PLAN.md](MAINTENANCE_ROTATION_PLAN.md) for design, test status and exact continuation priorities.

**Installed release remains0.37. New signed0.38 candidate is local ONLY: bin/last-z-helper.apk. No unattended worker/controller/injector is running.** Do NOT say this was deployed or fully phone-verified. Phone f7c5e6fe unexpectedly rebooted during the final two-account preview (shell exit255 during first bot's VIP inspection). Android reports user0 RUNNING_LOCKED; encrypted helper files are currently inaccessible. This is not evidence of data deletion. No reboot command was issued. Boot reason `reboot`, pstore empty and no system_server_watchdog entry: cause UNKNOWN. Do not blindly repeat instrumentation, initialize replacement state or install while old settings/history cannot be verified. No automatic job restart after reboot.

### Implemented in source

- MainActivity opens expanded floating controls immediately on resume/reopening. No automation starts merely by opening the helper. Permission return survives activity recreation. Run from rotation configuration restores the collapsed floating STOP bar.
- Main/floating UI replaces five maintenance action buttons with Maintenance rotation. RotationActivity shows accounts and per-account five-feature checklists, visit duration (20min default), preview, setup and STOP. Profile forgetting removes only enrollment, never game/history. No accounts auto-selected.
- RotationController keeps one global control.lock across opening games, visits and waits; opens Android-registered shortcut intents, proves clone via process maps and exact UID from game metadata BEFORE input. Per-account input scope must detach successfully before another launch. Manual focus/identity change stops. Unknown/BLOCKED/FAILED/UNCERTAIN outcomes stop. Normal mode repeats; preview visits selected accounts once. No fallback account/device or restart on process death.
- Reuses existing VIP, Help/Gifts, completed troop collection and finished Wanted workers/receipts, per-UID due dates and unresolved-operation barriers. No truck/bounty scanner/combat/chest or unfinished Python feature in rotation. Wanted zero due gets15min floor; other zero due cannot spin. Root-owned rotation files are chowned to helper parent UID, private0600 and restorecon applied so setup UI can read them (real app-UID access remains a live UI check after unlock).
- Help/Gifts now wait for menu readiness and locate a unique row by type/name, rather than fixed #3/#4 positions. Feature request and native final-dispatch guards recheck allowed operation/type/name/guild. First transient menu failure reproduced, fixed and live-preview verified.
- Hidden Wanted + unloaded/empty personal cache returns inspection-deferred WAITING (preview PREVIEW), retries15min and never claims completion/no rewards from absent evidence. Other unknown/pending conditions retain their guards.
- Long-running rotation log keeps bounded RECENT UTF-8 evidence/final errors, display lease renews on progress, interrupted root worker reports useful error, cold helper startup reports unfinished rotation rather than silently restarting.

### Verified and evidence

Full validation passed:19rotation policy,13native alliance-menu guard, bounded UTF-8/final-error log retention, all prior suites including86truck rules/52cargo/19truck filter/12dead-state/93maintenance core/157native field-cache and27Python tests. Final Android profile/shortcut/deferred-Wanted fixture22checks passed with ZERO game inputs/memory reads. Signed build verified by build.ps1. Logs: runtime/helper-build/rotation038-{validation,build}.txt and rotation038-final-fixture.jsonl.

Read-only setup opened ALL FIVE registered clones and verified unique UID/name mappings; actual rotation-profiles.json was created unselected. Observed: clone0 trucks by garix2059765822000064; clone1 yn gaarix2059770776000064; clone2 baby gaarix2059744163000064; clone3 Dassy1850977487000064; clone4 Garix9221430578113000153. No main-character UID was inferred/selected. Evidence rotation038-setup.jsonl and rotation038-enrolled-profiles.json. Original existing settings/history baseline saved rotation038-before-setup-persistent.txt; setup adds profiles/progress only. Post-reboot preservation comparison is PENDING unlock.

Isolated live guards passed: unresolved vip history stops BEFORE launching; STOP wakes idle wait and exits stopped:true; intentionally wrong expected UID stops BEFORE instrumentation with nonexistent injector/agent. Logs rotation038-{pending-gate,stop-wait,wrong-uid}.jsonl; these fixtures are under /data/local/tmp, NOT actual maintenance history.

First bot preview passed VIP cooldown, Help14pending, Gifts119Common/5Rare, and geometry of one completed troop queue with collection disabled. NO CLAIMS/SHARES/ATTACKS. That round blocked on hidden/unloaded Wanted; deferred scheduling fix was then implemented. Final round died on reboot before completing, so neither the complete two-account cycle nor new startup UI/deployment is verified. Logs rotation038-preview-first-failure.jsonl, rotation038-preview-wanted-deferred-before.jsonl, rotation038-preview.jsonl, rotation038-reboot-evidence.json. Do not use stale exit/error files as success evidence.

### Next agent: continue in this order

1. Confirm phone unlocked/user0 RUNNING_UNLOCKED; inspect health/reboot evidence FIRST. No blind full-preview rerun. Compare private settings/history to saved baseline (allow only known new rotation files); do not replace missing CE data.
2. Read the source/plan and verify a minimal one-bot/one-feature preview remains stable. Then full two-account preview with current assets, dynamic-menu final guards and Wanted deferral. Tests must use isolated storage and no claims unless explicitly running a selected production account/task.
3. At idle, install signed0.38 with same key and before/after hashes. Check helper app UID can read/write enrolled profiles, launcher/reopen immediately shows floating controls, grouped UI/task selections persist, denied/granted overlay permission, restored STOP bar and STOP during switching/waiting. Verify no worker starts just by opening helper.
4. Leave no unattended rotation running unless user explicitly chooses accounts and Run. Root setup discovered games but did NOT select them. Exact game-to-game loop is implemented; entire Python feature parity is NOT.

Checkpoint is current. All older active-job/STOP/status blocks below are historical and do not override this section.

## In progress: automatic maintenance rotation implementation, 2026-10-30

User said START. Implemented source: RotationActivity account/task checklist, RotationController automatic registered-shortcut launches and exact clone/UID verification, RotationProfiles private enrollment, MaintenanceRegistry for five available tasks, RotationPolicy due floors/stop rules. Main/floating UI now group maintenance under one entry. Fresh helper startup opens the expanded overlay. Rotation keeps the existing global control.lock across all visits/waits; context detach must succeed before switching; unknown/blocked/failed/uncertain outcomes halt, manual account/focus changes stop. New accounts are NOT selected automatically. Setup is memory-only; preview visits selected games once, normal rotation repeats until STOP. Pending/uncertain ledgers preserved; chest/scanners/combat excluded. Installed release STILL0.37; source not installed yet.

Read-only Android discovery found five registered com.lbe.parallel.intl Last Z shortcuts with exported EXTRA_LAUNCH_UID0..4, exact launch action/component and package. Current game's mapped files prove clone0 via /parallel_intl/0/com.readygo.barrel.gp/. No guess based on screen position or label. Full source validation passes17new rotation-policy checks plus all existing checks. Next: Android JSON/profile/shortcut fixture, lifecycle/source review, then targeted idle-phone setup/preview and signed release. No game switched or worker started as of this checkpoint. See MAINTENANCE_ROTATION_PLAN.md; update this block when testing/deploying.

## Latest: maintenance rotation plan and floating-startup source, 2026-10-30

User clarified the final behavior MUST mimic Python's automatic game loop: open each selected game/clone, verify UID, run its enabled maintenance bot, switch to the next game, repeat until STOP. No manual account opening or repeated Run presses between visits. Single-account work is only an internal development milestone. Trucks/bounty finder remain outside this rotation. See the plan's Requested behavior for the concrete sequence; rotation has not yet been implemented.

User requests immediate floating controls on helper opening, and all non-truck/non-world-bounty production features grouped into rotating game-account maintenance, like Python. Plan: [MAINTENANCE_ROTATION_PLAN.md](MAINTENANCE_ROTATION_PLAN.md). It supersedes prior design deferral of rotation, but no account switching/worker was performed. Five currently available maintenance tasks first form a due-aware single-account pass, then explicit verified UID/clone profiles and a serial coordinator; unimplemented/inspection-only/quarantined features remain excluded. Main/clone launch selection must never be guessed; current manual modes keep current-window guards.

MainActivity source now automatically opens the expanded floating service panel and backgrounds itself on fresh activity creation; opening controls starts NO job and does not save/validate configuration. Existing manual Show still saves. Overlay permission return survives activity recreation. `build.ps1 -DexOnly` passed, including input-position audit. NOT packaged/installed/live-tested yet; installed release remains0.37. No device commands, jobs or account switches in this planning task. Next: finish startup release verification at idle boundary, then implement single-account maintenance registry/pass before any multi-account switching. Migration implementation otherwise remains stopped.

## Latest: checkbox readiness fix installed0.37,2026-10-30

User's truck-world-cargo run errored before scanning/sharing: Hide trucks checkbox unavailable. Fresh inspection on mini gaarix UID2059765822000064, PID2906/start18037170 found managertrue/nativecheckedtrue/active/interactabletrue; original error did not preserve which flag was unavailable earlier. Fixed premature rejection: wait up to5s for UI readiness/state agreement; accept an already-ON checkbox even when not clickable; require active/interactable only to enable an OFF box. At most ONE enable request, no blind retoggling; native/focus/identity guards remain. Timeout reports individual readiness flags. See [TRUCK_HIDE_STATE.md](TRUCK_HIDE_STATE.md).

Signed0.37 installed;10XML/JSON settings/history/state hashes unchanged across upgrade. Full validation19filter+86rule+52cargo+12deadstate+all prior suites passes. Live setting-only check0clicks, checkboxstillon, gamepreferencesunchanged. CURRENTLY NO CONTROLLER/INJECTOR RUNNING. Floating panel opened; scan NOT restarted. Same user-selected account left open; no account switch/relaunch. Older active-job notes below are historical; migration STOP remains.

## Latest: persistent dead-state cache installed0.36, 2026-10-30

User says dead states never return. Implemented [DEAD_STATES.md](DEAD_STATES.md): /data/user/0/dev.codex.lastzhelper/files/dead-states.json learns ONLY a fresh definitive “The State you are searching for does not exist.” message after a submitted request. Immediate atomic persistence, no expiry, shared across accounts and World/group bounty modes. Cached states skip before any search/navigation and still advance checkpoints. Temporary unavailable/not-yet-open/timeouts are not permanently cached. No guesses/backfill from generic past errors.

Signed0.36 installed;9existing XML/JSON settings/history/checkpoint hashes unchanged.12new policy+18Android fixture checks and full existing suite passed. Fixture synthetic state40 lives ONLY in isolated test directories; it is NOT real evidence and does NOT preseed the app cache. Real states learned during test0; first future confirmed permanent error creates the real file. No game input/navigation/injection/shares/attacks used by this feature's test.

CURRENTLY NO CONTROLLER/INJECTOR RUNNING. User had stopped newer truck-world-cargo run after4verified shares/0attacks; it was not restarted. Latest observed USER-selected character baby gaarix UID2059744163000064, PID32112. No account switched/relaunched by agent. Floating controls opened after install. Older0.35active-cargo notes below are historical. Migration STOP remains; no agents used.

## Latest: mandatory Hide trucks checkbox installed0.35, 2026-10-30

PERMANENT USER RULE: ALWAYS enable “Hide trucks of this state” for ALL truck modes. See [TRUCK_HIDE_STATE.md](TRUCK_HIDE_STATE.md). Game filterLocalServer wasfalse. One ordinary click on the exported outSeverToggle enabled it; native Toggle.isOn and managertrue verified. Repeat0extra clicks. Game saved TrainFilterLocalServer2059765822000064=1 itself. A fresh controller after helper restart/install foundtrue and sent0clicks. No full phone/game reboot was done. Helper verifies each new truck controller/screen entry and checks manager flag before snapshots/final share payload; repairs only false/false, never blindly toggles. Mandatory even in truck preview; no new user setting.

Signed0.35 installed, all9helper XML/JSON settings/history/checkpoint hashes preserved; full validation86rule+52cargo+9filter+all previous suites passed. Current SAME bot OnionRing92 UID2059765822000064, PID4389/start16784835. Original cargo-to-trucks-group run (which had verified2shares before this change) was stopped normally, then resumed with identical options: Group,440m,Skip0,live,maxRefreshes-1. LEAVE THIS ACTIVE JOB RUNNING; no concurrent controller, injection, hot-install or asset replacement. Shared selector remains Group. Older no-controller notes below are historical. Migration STOP remains; no agents used.

## Latest: unified destination and cargo button installed0.34, 2026-10-30

See [TRUCK_CARGO_FILTERS.md](TRUCK_CARGO_FILTERS.md). User clarified ONE cargo button with OR rules (4+module icons /1+orange+3boxes /2+orange+2boxes /3+orange), removing the duplicate1frag/3box rule. Module item253102/car_compon_giftbox_blue counts one icon as one box despite raw quantity2. Base+extra CURRENT cargo counts, snapshot stability and actual final tile-payload checks now include module icons.

ONE saved Trucks group / World Chat selector applies to BOTH trucks AND bounties in main and floating UI. Channel-specific buttons removed; Share bounties resolves using that selector. Truck buttons are Share2+orange, Share3+orange, Share cargo combos, plus separate Gaarix attack. Group truck shares keep the configured strict power limit; World truck shares any known power. Group posting is allowed on main as well. Combat remains explicit Gaarix-only.

Signed0.34 installed and verified; all9settings/history/checkpoint XML/JSON hashes preserved across install. Full validation passes86rule+52new cargo/destination checks and all existing suites. Live memory-only sample12trucks/3module icons (quantity2each); no cargo-combo match in current sample and no new chat post claimed. Live helper UI checked: selector persists Group/World immediately, all sharing controls present, old channel buttons absent. Original/default World restored; other preferences unchanged. Floating panel left open. NO CONTROLLER/INJECTOR RUNNING. Current bot OnionRing92 UID2059765822000064, PID4389/start16784835. No game inputs or job starts for this feature; only helper selector/scroll controls were tested. Migration STOP remains.

## Latest: truck World recovery and3+option installed0.33

See [TRUCK_WORLD_RECOVERY.md](TRUCK_WORLD_RECOVERY.md). Signed0.33 installed; all9XML/JSON settings/history hashes preserved. Main and floating controls include Share3+toWorld, alongside2+. Same yellow/purple eligibility, any known power, Skip state, empty-note tile share and shared World dedup ledger; no combat permission. Hidden/disabled/offscreen truck-cell failures now return to refresh ONLY with structured no-input/pre-dispatch proof. Errors include the actual control path. Full validation passes86rule tests plus all existing suites.

IMPORTANT: CURRENTLY NO CONTROLLER/INJECTOR RUNNING. Older active-bounty notes below are historical. User's newertruck-world attempt failed before selection on a hidden control. Further diagnostics identify trainCells/#12/btn but are blocked because the game stopped producing NEW frames (unchanged SurfaceFlinger history). Cached frame history can falsely show30FPS. Current bot still OnionRing92 UID2059765822000064, PID20644/start12373636. Do not automatically restart/reopen/switch a clone. The intended game needs manual reopening before another live share verification; no successful share is claimed for0.33. Callback/visibility guards retained; no blind clicks. Helper floating choices opened, no job started. Earlier migration STOP remains in effect.

## Latest: bounty FPS fix deployed as0.32, 2026-10-29

Actual live scan reproduced15.07FPS/p95183ms. Root cause: native input guards repeatedly scanned Lua hash tables synchronously on Android UI thread at every movement step. Added per-request, bounded, validated FIELD-LOCATION cache; every check still reads current values, rechecks layout/key/type and fails closed. No cached account/state values or screen coordinates. Same46account/23map checks per drag: agent time4.5s ->1.1s. Full validation including157new cache checks passed. See [BOUNTY_PERFORMANCE.md](BOUNTY_PERFORMANCE.md).

Signed0.32 installed; all9XML/JSON settings/history/checkpoint hashes unchanged. Stopped the manually started10-64group scan normally, then resumed its saved state16 with the same options on OnionRing92 UID2059765822000064, gamePID4652/start8058934. Active helperPID14812/controllerPID20567/injectorPID20624 at resumption. New immutable agent c217441d91c3a342b30bd0712d9af1bfc92227bf0660225f66299974447e38d6. No agents used. Leave this scan running; do not inject, hot-install, overwrite assets or start another controller. Ordinary new12/15group shares remain authorized; no plunder/attacks. Post-install active map-scanning sample27.50FPS/p9550.43ms versus15.07FPS/p95183.05ms before. State16advanced to182observations with0shares/attacks at that sample; left running.

The older40-64job completed4717observations/0shares/0attacks; the active10-64job is a separate user-started run. Earlier migration STOP remains in effect: no maintenance migration work resumed. Source-only Java/native inspector and partial-training-report changes described below are now packaged in0.32; desktop Python changes remain source-only. No new consuming maintenance feature was enabled.

## STOPPED at the user's request

Checkpoint saved2026-10-29, Europe/Malta. User requested checkpoint/wrap-up with7%usage remaining. **Do not resume migration, phone tests, controllers or agents until the user asks.** Earlier keep-working instructions are superseded. All parallel migration tasks have finished. This is the historical migration checkpoint; the separately resumed active bounty job is documented above.

Workspace: C:/Users/Gary/Documents/vscode/lastz_android_helper. Phone ADB scrcpy/adb.exe serial f7c5e6fe. Last verified account OnionRing92 UID2059765822000064, game PID4652/start8058934, World scene2/level10001 at the latest bounty check. Recheck identity/focus/windows and active processes after resumption. Never switch/relaunch accounts or select a fallback phone. Root owns phone; agents may review source only if newly authorized.

## Installed release:0.37, verified

Signed versionCode37/versionName0.37 installed. Main/floating maintenance buttons: VIP free rewards, Alliance Help, Alliance Gifts, Collect finished troops, Collect Wanted rewards, plus existing truck/bounty modes. Mail and passive base inventory are diagnostics only; no resource-collection button. Chest collection disabled/quarantined. No background maintenance scheduler enabled.

0.31 includes immutable content-addressed native agents and memory-only passive inventory. New agent filename equals its fullSHA256; existing assets are not overwritten, corrupted cached content fails closed, old files retained. Installed inventory preview passed46unclassified bubbles. All9XML/JSON hash maps unchanged across install+preview; old input-agent-v06.js unchanged and one new hash-named agent created. Evidence runtime/helper-build/deploy-031-{before,after,after-preview}-persistent.txt, deploy-031-{before,after-preview}-agents.txt, base-bubble-installed-031-preview.txt, build-031.txt. Those preservation baselines precede the later authorized troop collections below.

## Latest verified gameplay results

- VIP login points/freebies live claims and cooldown/repeat verified earlier; no paid/Activate.
- Alliance Help pending10->0,points280->380; repeat no-work. Credit-cap behavior still unverified.
- Alliance Gifts155Common UUID receipts verified, repeat Common/Rare no-work. Rare live claim unverified; no purchase/delete/activation/level chest.
- Wanted own finished reward UUID1430459261720215782/config600501 rewarded0->1. Only intended flag changed, repeat no duplicate. Exact big panel activity400001/stringID/goIDnumeric, DispatchTask/tab1 and own task UUID joins. No GO/stealing/assistance/refresh/hero dispatch. Clipped pooled rows and unknown windows block. Guarded reward dismissal uses live geometry avoiding interactive sibling scroll areas.
- Finished troops now live-verified across all3types: Bow145 free56->201/train145->0; Car145(unit107007) free1404->1549/train145->0; Foot145(unit107107) free939->1084/train145->0. All corresponding queues Free0. No new training/healing/upgrade/dispatch.
- Foot first attempt was rejected on transient UIScreenCenterTips BEFORE input. Stored cancelled_before_input with structured inputDispatched:false/native_pre_dispatch and unchanged queue version. Cancelled record preserved; a separate bounded retry after fresh queue/window proof succeeded. Never delete/bypass cancellation/uncertain history.
- Comparing all queues before/after Car+Foot: ONLY those two changed; Hospital and every other queue unchanged. Only maintenance-state.json changed across the collection tests; all other settings/share histories preserved.
- Live no-work repeat using NONEXISTENT injector/agent returned NOTHING_TO_DO0queues; preview also0geometry. This proves the actual zero-ready deferred-instrumentation case. Wanted hidden-cache no-work likewise passed without injector.

Training evidence: training-car-foot-{before-queues,after-queues,maintenance,blocked-windows}.json; training-installed-031-preview.txt; training-car-foot-live.txt; training-foot-bounded-retry.jsonl; training-all-after-foot.json; training-all-final-maintenance.json; training-zero-ready-no-inject.jsonl; training-completed-repeat-no-work.jsonl; training-car-foot-{before,after}-hashes.txt.

## Changes developed after0.31, now packaged in0.32

These Java/native changes are now packaged in0.32. Their inspection-only restrictions remain. The older /data/local/tmp/lastz-phone-check diagnostic agent does not include the0.32field-cache fix; do not overwrite it or use it during the active bounty job.

### Passive production discovery and geometry

BaseBubbleReader now exports typed buildingVersionObservation(level/state/unlock/lockInput/lastCollectTimeText/produceEndTimeText), with productionSemanticsVerified:false. Exact own-counter observation joins single numeric param.itemId -> ItemData.ItemIdAndUuid -> ItemInfos with matching string itemId/UUID and nonnegative integer count. No arbitrary text, positions, callbacks, raw pointers, icon inference or gameplay input. All bubbles remain UNCLASSIFIED/claimEnabled:false.

Live memory-only inventory with nonexistent injector:46own-building joins, all BuildBubbleTip/all isShow:true,5sensitive buildings excluded from eligibility,8exact own counters/38non-single-item references. **isShow:true is not rendered visibility or collectible proof.** Non-preview diagnostic invocation rejected. Hashes unchanged during inspection. Relevant logs base-bubble-{preview,reject-live,inventory-preview}.jsonl, base-production-version-preview.jsonl, base-bubble-after-hashes.txt.

BaseResourceGeometryFeature / maintenance-base-resource-geometry is preview-only, native getter inspection, no input capability. Known own building731000/item200394, exact UUID/class/version/state/unlock/nonworld and param identities; at most4candidates. It rechecks object-pool binding and trigger/gameObject/camera userdata tokens after callbacks, age<=500ms, actual viewport/HUD blockers and first-hit raycast. Only known clipped/UI-covered/raycast misses may move to another candidate; identity/focus/runtime failures stop. Non-preview rejected before injection.

Live geometry passed for building1254334576017293505, lastCollectTime1793259632009, intended collider-65198 equals first hit. Receipt inputDispatched:false. A clipped first candidate and transient unknown-window failure were preserved; no guard bypass. The refreshed-token version passed again. Logs base-resource-geometry-preview{,2,3}.jsonl and base-resource-refreshed-preview.jsonl. **Never tap stored candidate coordinates. No resource collection action exists.**

Production template discovery: building731000/level5 has lastCollectTime1793259631961 in the first sample, produceEndTime=Long.MAX_VALUE9223372036854775807. Do not treat that sentinel as an ordinary timestamp. Template BuildTemplateManager.buildLevelTemplateDic/#731005 uses indexData/lineData: para1 column28="2.2", para2 column29="15840", para3 column30="396", para4 column45="200394".15840 matches abbreviated15.8K display but rate units/bonuses/exact amount/free-action/receipt semantics remain unproven. Own item200394 counter joined UUID1254334526042161344/count11941929 at sample time. See BASE_BUBBLE_NEXT.md; all reads are evidence, not claim authorization.

### Partial training reporting

TrainingCollectionFeature now retains verified count and receipts in BLOCKED/FAILED/UNCERTAIN results. Installed0.31 omitted the already-verified Car count when Foot blocked. Source fix passed full validation and TrainingPartialResultTests6Android JSON fixture checks; no gameplay access in fixture. Packaged in0.32.

### New-training inspection foundation

TrainingStartPolicy/Reader/InspectionFeature + maintenance-training-start-preview: memory-only, dryRun required, inherited no-input capability.30loaded supported unit templates joined to own training buildings/queue samples.24meet observed building requirements;3science-requirement rows. All starts/unlocked/capacity/cost-units/highest-tier proof flags remain false. Live preview passed with NONEXISTENT injector/agent; non-preview rejected before outcome write. Evidence training-start-{preview,reject-live}.jsonl.

Sample unit107007: templatelevel8, building423000 requires level24; own building level25. needResource raw counts2950each for types1/2; rawtime1035; max_train0. **Do not interpret rawtime units or max_train0 as capacity/free training.** Own queue state is from an earlier sample, atomicSnapshot:false; refresh it at any future commit. Science/item requirements, runtime batch capacity, balances, cost/time units/bonuses and exact start receipt must be proven before queue-start input.

Independent review found no blocker for current inspection-only scope and confirmed no consuming path. Resource reference-token finding was fixed and live rechecked. No agents currently working.

### Hospital discovery only

HospitalManager.allHospital has own records keyed by unit IDs, raw fields armyId/dead/heal/armsType. Example107007: dead23/heal41; do not infer their exact semantics from names. Hospital type3 queue1256861600841744452, building1254334526042161359, stateFinish3/end1793260772129/itemId"1;0". Hospital was NOT collected/healed/changed. No healing source feature created. Evidence healing-{data-owners,manager-fields,hospital-records,queue-snapshot}.json. Preserve separation from completed troop collection.

## Desktop Python source changes (not restarted/deployed)

- Explicit LASTZ_DEVICE_SERIAL (then CONFIG.device_serial), otherwise one unique model match. Missing/ambiguous/unauthorized/mismatched devices fail closed. Recovery probes selected serial only; no discovery/rebind.
- Trace screenshot defaults off; explicit --trace opts in. In-memory vision unchanged, old images preserved.
- Axiom/ntfy delivery single-flight/no backlog, dropped_records count, bounded timeout/failure cutoff; close rejects later delivery, thread-start failure releases slot. Existing request may finish after close. Discord synchronous delivery unchanged.
- ADB logs allowlisted operation/tool categories only, omit serial/path/payload/rawstderr/exceptiondetails; execution arguments/results unchanged. This is not global redaction of every legacy caller.
- Removed unsupported claim that random tap offsets prevent detection; jitter behavior unchanged.

Full Python suite passed237tests before latest agent-added fixtures (legacy-full-tests-final.txt). Latest19target startup/log tests passed with network/subprocess mocked, including timeouts/precedence/close/startfailure/failedsend. One minor remaining edge: whitespace-only LASTZ_DEVICE_SERIAL trims empty after overriding CONFIG serial, resulting in model selection; record for later, not fixed at wrap-up. No external messages or bot startup occurred in these tests.

## Validation

Latest full helper validation bounty-fps-validation.txt passed157new native field-cache checks plus:72rules,93maintenance,76Wanted,29cache,46Mailcoverage,36Mailheader,36basebubble,18training-startpolicy, runtimeassetidentity checks,16geometry,7unavailabletext,27Python,18scene,14reference,8exactintegerkeys. TrainingPartialResultTests6checks also passed on Android. Source/native syntax and input-position audit passed. No pending build/test process intentionally running.

## Mail and chest remain blocked

Mail six tabs: Report16/Jungle40/Alliance22/System21/Recharge0/Favorite0, allPARTIAL; ordinary candidates0, Systemspecialexcluded1.189common allowlisted headers unchanged across tab navigation. This does not prove server completeness or universal absence of read side effects. No Mail claim/read-all/delete input or production button. See MAIL_COVERAGE_FINDINGS.md and MIGRATION_NEXT_SLICE.md.

Chest legacy eight_hour_chest since_1793234949105/collect_full remains UNCERTAIN. Old receipt lacks structured dispatch proof. Latest read-only timestamp still1793234949105; no new reset proof. Never delete/reset/bypass attempt or use another ledger. Consuming mode remains disabled. No chest collection succeeded.

## Exact next delivery after user resumes

1. Read this file, then MIGRATION_STATUS_MATRIX.md. Verify source versus installed0.37, phone UID/focus/windows and idle controller. Do not resume old bounty jobs/monitors or agents implicitly.
2. Finish one guarded consuming vertical slice rather than adding endless inspectors: passive resource collection needs free-action identity, exact amount/version and independent counter/receipt; new training alternative needs actual unlock/capacity/cost/time/balance proof and start receipt. No input until the relevant proof is established.
3. Partial-training reporting and reviewed source changes were shipped in0.32. Future releases must preserve signing key and9XML/JSON hash maps, including current verified/cancelled training history.
4. Keep Mail claims blocked until an ordinary attachment/control/receipt and coverage evidence exists. Keep chest quarantined.
5. Shared Python/Go/helper device ownership remains design-only; see CONTROLLER_OWNERSHIP_PLAN.md. A check-and-release lock query has a race. Never run legacy input concurrently with helper.
6. Audit manifest56focused/124pattern-only/1excluded vendor; not a completed line-by-line codebase audit. Concrete tasks in BOT_DETECTION_IMPROVEMENTS.md; actual detection probabilities unknown. No detector probing, concealment or bypass.

## Gameplay rules - never regress

Truck sharing uses initial BIG BLUE Share, never Plunder/goBtn or location detour. Group3+orange-frag slots strictly below configured power(default440m), Gaarix-owned trucks room custom_vip_2028198887000064_1793214114. World2+slots any known power, tile only/empty note/no separate power text. Attack only explicit Gaarix UID2028198887000064 mode,3+below limit; preserve combat guard and tested result recovery. World bounties completed available12/15boxes, empty note, no plunder. Old bounty scan ended state54; no restart.

One controller/lease, expected UID/process/start/focus, STOP and uncertain-operation barriers always apply. No fixed pixel, scaled-reference, OCR/template fallback for helper actions. Asset pushes/install/restarts only while idle. Preserve test-key.jks, settings and every duplicate ledger/checkpoint. Diagnostic coordinates expire and never authorize a later tap.

## Commands and evidence

    powershell -ExecutionPolicy Bypass -File tools/last-z-helper/validate.ps1
    powershell -ExecutionPolicy Bypass -File tools/last-z-helper/build.ps1 -DexOnly
    powershell -ExecutionPolicy Bypass -File tools/last-z-helper/build.ps1
    python tools/last-z-helper/phone_check.py query --path PATH --depth 0 --pattern REGEX

APK bin/last-z-helper.apk currently0.37. Diagnostic assets /data/local/tmp/lastz-phone-check/{helper.dex,input-agent.js,injector,probe-cache.txt,stop-request}. Avoid prepare unless needed (large injector repush). Local evidence runtime/helper-build; detect UTF16 BOM on older PowerShell redirects, explicit UTF8 for local edits. Archived historical narrative is under docs/archive; it contains superseded STOP/source-only/deployment notes.
