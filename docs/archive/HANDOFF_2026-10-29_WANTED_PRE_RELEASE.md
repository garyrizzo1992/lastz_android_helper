# Current handoff â€” start here

Updated 2026-10-29, Europe/Malta. This document supersedes historical pending instructions in the archived handoff and migration log.

## Authorization and ownership

User requests autonomous continuation without questions while away, regular checkpoints, and a durable handoff before limits. User later explicitly authorized parallel agents until limit. Root owns all phone control; agents are limited to independent source review/tests/docs. Use the active game only. Never switch or relaunch accounts. No background job is intentionally running. Do not restart the old bounty scan or monitor.

Workspace: C:/Users/Gary/Documents/vscode/lastz_android_helper. ADB: scrcpy/adb.exe -s f7c5e6fe. Rooted OnePlus 5T, Android 10. Latest memory-only check: OnionRing92 UID 2059765822000064, PID 4652/start 8058934, base scene 1/level 10001, no normal modal. Recheck after interruption. Before injection, input, asset push or install, verify there is no active controller/injector. One controller/lease only. Preserve signing key, settings, ledgers and checkpoints.

## Installed release: 0.28 (verified)

VersionCode 28/versionName 0.28 installed successfully. Main and floating panels include existing trucks/bounties plus VIP free rewards, Alliance Help, Alliance Gifts and Collect finished troops. Manual maintenance does not enable scheduling.

- VIP login points/freebies: live claim and repeat/cooldown verified earlier on Garix922. Paid/Activate excluded.
- Alliance Help: Onion pending 10 to 0, points 280 to 380; repeat no work. Credit-cap behavior remains unverified.
- Alliance Gifts: 155 Common gifts verified by UUID/receiveTime, repeat Common/Rare no work. Rare live claim remains unverified. No activation, purchase, deletion or level chest.
- Finished troops: one Bow queue collected 145 units; queue Finish 3 to Free 0, army free 56 to 201 and train 145 to 0. Repeat zero. Exact Car/Foot/Hospital queue records unchanged. Exactly one verified collection journal. No new training, healing, upgrade or dispatch.
- Settings XML and every app-private JSON hash identical before/after installation AND installed preview. Evidence runtime/helper-build/deploy-028-{before,after,after-preview}.txt and training-installed-preview.jsonl.
- Maintenance checks expected UID before instrumentation. Memory-only features cannot invoke native input. Unresolved-operation reporting also avoids injection. Preview explicitly discloses instrumentation.

## Active work: Personal Wanted finished rewards

Only finished reward claims are the next slice. Python bot/daily_rewards.py also assists allies and dispatches heroes: those actions are NOT part of this slice. Do not click GO/world objectives, assign heroes, dispatch marches or start combat.

Verified discovery and source-only preview:

- Actual visible Wanted shortcut is MainUI_SU/View/bottomLayer/dispatchBtn. Fresh UI bounds were used once to OPEN the panel only. Despite the object name, it is an entry button; no hero dispatch was pressed.
- Opened UIActivityCenterTable, activity string 400001, goID numeric 400001, panelComponentList/400001 class DispatchTask, personal tab 1. Current phone remains in this panel for inspection.
- Correct data owner is DataCenter/ActDispatchTaskDataManager/singleTask. HeroBountyDataManager is a different, unloaded feature and must not be used for this workflow.
- showDatalist has 10 rows: one completed unreceived personal task UUID1430459261720215782/config600501, eight received tasks, one stealing/GO placeholder (uuid0/isstealtask true). First rendered cell receive_btn active, go_btn inactive. Exact raw table identity joins displayed row to singleTask UUID; do not use rounded JS IDs.
- Added WantedPolicy/Reader/WantedInspectionFeature and diagnostic maintenance-wanted-preview. Memory-only, already-open panel required; no native input/injection, claim, dispatch, navigation, or completion write. Source-only, not in installed APK0.28.
- Live preview passed with deliberately NONEXISTENT injector/agent paths: 1 READY_INSPECTION_ONLY, 8 ALREADY_RECEIVED, 1 EXCLUDED. Evidence wanted-memory-preview.jsonl. Initial preview rejected lastActivityId as numeric; corrected to its observed STRING type and separately validates numeric goID. Full validation now 93 maintenance checks plus prior suites, all pass.
- All bounds/open/preview commands completed; no controller intentionally running. Installed release remains0.28.

Latest bounded live claim test (SOURCE ONLY, installed0.28 unchanged):

- Added WantedClaimCheckFeature / maintenance-wanted-claim-check: one completed personal task, already-open panel. Exact Claim label and permissions exclude GO/refresh/preview consumption. Native pre-input guard repeats account/focus/active-window allowlist, activity/tab/class, exact displayed-row to personal UUID table identity, start/end/config/rewarded/nonsteal/nonworld state and Receive/GO controls. Unity callback verifies ReceiveBtn/Claim label.
- wanted-negative-uuid.jsonl: wrong UUID1 rejected with inputDispatched:false/native_pre_dispatch. No journal/consumption. wanted-claim-preview.jsonl passed.
- wanted-claim-live.jsonl COMPLETED UUID1430459261720215782/config600501 rewarded0->1, precommit journal verified. Comparing wanted-personal-tasks.json and wanted-after-personal-tasks.json: ONLY that rewarded flag changed; all eight other task scalar records unchanged, no task added. No GO/dispatch/assistance/stealing/refresh.
- UIDispatchRewardGet overlay appeared in Info stack (normal modal count still1), nameText Congratulations!, btn UICommonRewardPopUp/Panel. Fresh View/btn tap closed it, wanted-reward-close.jsonl. wanted-claim-repeat.jsonl NOTHING_TO_DO, zero duplicate.
- Validation93maintenance plus prior suites passes. All commands completed. Phone remains Wanted personal tab with reward overlay closed. No controller intentionally running. Diagnostic dex/agent newer than installed0.28.

Next: production base-entry/reward-dismiss/panel-close wrapper with strict active-window guards, main/floating control, route preview/no-work check, signed deployment preserving settings/ledgers. No ready reward remains in this sample. Every subsequent claim must reread sorted/recycled row and exact UUID; never cache row index. Do not expose GO/stealing/refresh/dispatch.

## Chest: quarantined, consuming mode disabled

Chest scene opening was verified once, without Collect. Actual route is UIJeepAdventureMain then UIStoryHangup. Full preview recognized Idle Reward / 08:00:00 (MAX) / Collect and eight reward rows. No successful collection was recorded.

Legacy eight_hour_chest operation since_1793234949105 / collect_full is UNCERTAIN after a transient UINoticeTips guard rejection. Its old receipt lacks structured dispatch proof. Do not delete/reset it, fabricate receipt flags, switch ledgers or blindly retry. Reconcile read-only or observe a real later reset. Consuming maintenance-chest is removed from accepted modes in 0.28; ChestFeature source remains unreleased. Diagnostic chest preview/open-only modes remain available.

Future structured pre-dispatch cancellation requires explicit inputDispatched:false/native_pre_dispatch receipt plus fresh unchanged game version. Store retains cancelled attempt and separate retry key; dispatched/unknown outcomes remain quarantined. No automatic retry loop.

Global modalWindowCount counts normal stack only. Chest/training actual-input guards also check exact active-window allowlists. Do not globally change stack semantics or whitelist transient notices without evidence. Read-only geometry can observe behind notices while checking UI blockers; actual input remains strict.

## Other pending migration work

Mail inspection only: six tabs loaded Report16/Jungle25/Alliance20/System20/Recharge0/Favorite0. Ordinary candidates zero; special deal100 code announcement excluded. Paging/completeness and normal attachment claim receipts unverified. No production Mail button or claim/read-all/delete permission.

See PYTHON_TO_ANDROID_MIGRATION_PLAN.md for full inventory/order, SCENE_OBJECT_GEOMETRY_PLAN.md for geometry acceptance, BOT_DETECTION_RISK_ANALYSIS.md for evidence and risk improvements. Detection probability is unknown; memory reads and instrumentation are not proven invisible. No concealment/bypass work.

## Do not regress gameplay rules

- Truck sharing uses the initial BIG BLUE Share button, never Plunder/goBtn or location sharing.
- Group trucks: 3+ orange-frag slots, strictly below configured power (default 440m), Gaarix-owned trucks room custom_vip_2028198887000064_1793214114.
- World trucks: 2+ slots at any known power; tile only, empty note, no extra power text.
- Attack only explicit truck-attack on Gaarix UID2028198887000064, 3+ below limit. Preserve combat guard and victory/defeat recovery.
- World bounties: completed available 12/15 boxes; empty note, World/group target as selected. Never plunder.
- Old bounty job ended state54 (2065 observations, zero shares/attacks); monitor deleted. No implicit restart.
- All input derives from current metadata/live geometry. No fixed pixel, screen scaling, OCR/template coordinate fallback.

## Validation and build

Latest full validate.ps1 passed: 72 old rule checks, 93 maintenance checks, 16 prior geometry, 7 unavailable-text, 17 Python, 18 scene geometry, 14 reference lifecycle and 8 exact Lua integer-key checks. Android MaintenanceStoreTests: 20 checks. No changes warranting retest since the last diagnostic hierarchy addition; that source validation passed too.

Commands:

    powershell -ExecutionPolicy Bypass -File tools/last-z-helper/validate.ps1
    powershell -ExecutionPolicy Bypass -File tools/last-z-helper/build.ps1 -DexOnly
    powershell -ExecutionPolicy Bypass -File tools/last-z-helper/build.ps1

Signed APK bin/last-z-helper.apk; preserve runtime/helper-build/test-key.jks. Diagnostic device folder /data/local/tmp/lastz-phone-check contains helper.dex, input-agent.js, injector, stop-request, probe-cache.txt. Push only when idle. Avoid prepare unless required: it repushes the large injector. Query mode is memory-only:

    python tools/last-z-helper/phone_check.py query --path PATH --depth 0 --pattern REGEX

Other inspect/bounds modes may inject even without input. PowerShell redirects may be UTF16; detect BOM. Local text explicit UTF8. Keep tool output bounded.

## Implementation facts needed for continuation

Exact 19-digit Lua numeric keys are compared as signed integer strings, never JS doubles. Training joins QueueDataManager queue UUID -> BuildManager building -> BuildBubbleManager bubble param UUID/funcUuid -> ArmyManager unit. Allowed completed training types Car1/423000, Foot8/424000, Bow9/425000; exclude Hospital3 and ArmyUpgrade34. Payload family must match, queue ended, building valid/unlocked, bubble visible and exact IDs, train count sufficient.

Native scene references resolve through metadata-verified XLua translator/object pool with allocated slot/type/lifecycle checks. Fresh actual collider bounds, camera, safe viewport, HUD blockers and first-hit Physics.Raycast are required. Never treat userdata integers as Unity instance IDs or reuse old candidate coordinates.

Training receipt requires queue Free AND free count gain AND train count drop by quantity. Journal key includes queue UUID and end time. Feature has no capability for train/heal/upgrade/dispatch/UI-tap.

Detailed historical evidence and intermediate failures: archive/HANDOFF_2026-10-29_PRE_CONSOLIDATION.md. That archive contains superseded source-only and pending deployment notes; use this document for current status.


## In-progress production Wanted review checkpoint

Production WantedFeature wrapper and guarded entry/reward/panel-close routes are local source only. Agent review identified viewport clipping, empty-cache coverage, delayed reward-popup handling; fixes added plus64 independent Wanted workflow tests (full validate passes). A newly added bounds preflight mistakenly entered consuming guard; corrected to skip claim guard for read-only ui-bounds. Native tap guard remains mandatory. Do not call new viewport guard live-verified until wanted-viewport-check passes.

IMPORTANT correction: one earlier reward close tap did NOT prove overlay State changed. Latest strict route test blocked because UIDispatchRewardGet was still active. Earlier no-work repeat used older Reader without active-window check, so it only proved no duplicate claim. A second fresh exported reward-close tap is running/finished (wanted-reward-close2.jsonl); read tool result/window State before proceeding. Do not assume clean base. No deployment after0.28 yet.
