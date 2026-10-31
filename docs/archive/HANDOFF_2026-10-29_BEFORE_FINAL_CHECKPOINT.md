# Current handoff - start here

Updated 2026-10-29, Europe/Malta. This document supersedes historical pending instructions in the archived handoff and migration log.

## Authorization and ownership

User requests autonomous continuation without questions while away, regular checkpoints, and a durable handoff before limits. Latest user permits agents IF NECESSARY; use only for independent source review. Root owns all phone control. Earlier blanket no-agents instruction is superseded only to that extent. Use the active game only. Never switch or relaunch accounts. No background job is intentionally running. Do not restart the old bounty scan or monitor.

Workspace: C:/Users/Gary/Documents/vscode/lastz_android_helper. ADB: scrcpy/adb.exe -s f7c5e6fe. Rooted OnePlus 5T, Android 10. Latest memory-only check: OnionRing92 UID 2059765822000064, PID 4652/start 8058934, base scene 1/level 10001, no normal modal. Recheck after interruption. Before injection, input, asset push or install, verify there is no active controller/injector. One controller/lease only. Preserve signing key, settings, ledgers and checkpoints.

## Installed release: 0.31 (verified)

VersionCode 31/versionName 0.31 installed successfully. Main and floating panels include existing trucks/bounties plus VIP free rewards, Alliance Help, Alliance Gifts Collect finished troops and Collect Wanted rewards. Manual maintenance does not enable scheduling.

- VIP login points/freebies: live claim and repeat/cooldown verified earlier on Garix922. Paid/Activate excluded.
- Alliance Help: Onion pending 10 to 0, points 280 to 380; repeat no work. Credit-cap behavior remains unverified.
- Alliance Gifts: 155 Common gifts verified by UUID/receiveTime, repeat Common/Rare no work. Rare live claim remains unverified. No activation, purchase, deletion or level chest.
- Finished troops: one Bow queue collected 145 units; queue Finish 3 to Free 0, army free 56 to 201 and train 145 to 0. Repeat zero. Exact Car/Foot/Hospital queue records unchanged. Exactly one verified collection journal. No new training, healing, upgrade or dispatch.
- All nine settings XML/app-private JSON hash maps identical before/after0.29 installation AND installed Wanted preview. Evidence runtime/helper-build/deploy-029-{before,after,after-preview}.txt and wanted-installed-preview.txt. Installed service returned correct no-work on nine received personal tasks. No controller remains running.0.28 troop evidence remains deploy-028-* and training-installed-preview.jsonl.
- Maintenance checks expected UID before instrumentation. Memory-only features cannot invoke native input. Unresolved-operation reporting also avoids injection. Preview explicitly discloses instrumentation.

## Wanted finished rewards - deployed0.29

Main/floating Collect Wanted rewards runs a bounded pass (max10). Only completed OWN personal rewards. No GO, assistance, stealing, refresh, hero assignment, dispatch or combat.

- Actual shortcut MainUI_SU/View/bottomLayer/dispatchBtn opens UIActivityCenterTable activity STRING400001/goID NUMBER400001, panelComponentList/400001 class DispatchTask/tab1. Data owner ActDispatchTaskDataManager/singleTask, NOT HeroBountyDataManager.
- Exact native table identity links showDatalist to personal19-digitUUID. Nonempty personal-cache/display coverage required; empty/unloaded/invalid/duplicate records block. Positive config, sane start/end, nonsteal/nonworld/unowned, rewarded0, ended, exact active Claim label/control, current account/focus/active-window allowlist required. Native guard repeats before geometry and before input. Claim fully inside actual ScrollView viewport with exact exported owner ID; offscreen candidate BLOCKS, no auto-scroll.
- One live Claim UUID1430459261720215782/config600501 verified rewarded0->1 and journal. Only that flag changed across all nine personal task scalar records; no task added. Preview and no-duplicate repeat passed. Evidence wanted-claim-{preview,live,repeat}.jsonl and wanted-{personal-tasks,after-personal-tasks}.json.
- Wrong UUID native rejection passed inputDispatched:false. Viewport diagnostic accepted visible first row, rejected wrong viewport owner and offscreen row9. wanted-negative-uuid.jsonl / wanted-viewport-check.jsonl. A bounds preflight initially entered consuming guard; corrected ui-bounds bypass while keeping tap guard. No input on that failure.
- Reward UIDispatchRewardGet is Info-stack overlay (normal modal count remains1). Centre tap hit its sibling scroll/mission area and DID NOT close; earlier one-tap cleanup assumption is superseded. Current cleanup scans WHOLE exact reward hierarchy for child input handlers, derives clear point from live geometry, validates parent Graphic.Raycast, then native route/context/freshness guards before ordinarytap. wanted-reward-clear2.jsonl / wanted-reward-dismiss-guarded.jsonl prove dismissal; subsequent memory query found window removed.
- Wrapper waits boundedly for reward popup before continuing and only closes known reward/panel. Unknown activity notices BLOCK; inspected one UIActivityNoticeTip02 and manually closed exported btnClose (never btnGo) during route test. Do not whitelist unknown overlays.
- After final reward, game hid shortcut. Hidden-shortcut path requires actViewOpened plus nonempty exact valid records all received/waiting; reports NO READY IN LOADED RECORDS, serverCompletenessProven:false. Empty/unloaded/ready/invalid blocks. All nine currently received. Live installed preview passed this path. Do not force hidden shortcut or invoke game handler.
- Diagnostic maintenance-wanted-preview is memory-only, already-open panel required, tested with nonexistent injector/agent paths. Production maintenance-wanted does instrument for compatibility/geometry even if its eventual hidden-cache check is no-work. Do not conflate these modes.

## Current work after installed 0.30 - source only

User requests sustained autonomous work without questions or agents, with durable checkpoints. Work alone. Installed APK is now0.31; see latest release checkpoint below. Do not restart Python/Go or run them alongside the helper. No controller intentionally running; verify before any device action or asset push.

### Completed desktop changes

- Legacy startup selects explicit `LASTZ_DEVICE_SERIAL` (then CONFIG.device_serial), otherwise exactly one matching model. Missing explicit device, ambiguous model matches and unauthorized/mismatching devices fail closed. No arbitrary available-device fallback.
- Recovery probes only the selected serial using get-state. It never discovers/rebinds to another phone. Offline, unauthorized, timeout or session change does not report recovery.
- Trace screenshots default off in main_scrcpy CONFIG and observability fallback; explicit `--trace` still enables them. In-memory vision remains unchanged; old images preserved.
- Axiom/ntfy log delivery allows one in-flight request and no backlog. Burst records are counted in dropped_records, close prevents new delivery, thread-start failure releases the slot. Existing in-flight request may finish within its configured timeout. Discord's synchronous handler is unchanged.
- ADB command logging uses allowlisted operation/tool categories, not full payloads, serials or paths. Raw stderr and exception details are omitted; recovery uses a constant reason code. Original command arguments/results remain unchanged for execution/callers. This does not redact every other legacy log boundary.
- Removed unsupported docstring claim that tap jitter prevents detection. Jitter behavior itself was not expanded or changed.

**Validation:** full Python suite 237 tests passed in24.371s, `runtime/helper-build/legacy-full-tests-final.txt`. New tests: selected_device_recovery(9), log_delivery_bounds(3), adb_log_minimization(5); existing platform/reliability passed. Tests used mocks; no external messages or bot starts. Desktop changes are not deployed/restarted.

### Passive own-base inventory diagnostic

New BaseBubblePolicy/Reader/InspectionFeature and `maintenance-base-bubble-preview` are SOURCE ONLY after installed0.30; no production button or collection action.

- Preview-only, memory-only; rejects non-preview before any outcome write. Requires expected UID, clear own base, known active windows and fresh raw scene/stack checks.
- Bounded128 typed rows joined by exact building UUID. Allowlisted params only; no Unity getters, positions, callbacks, raw addresses, arbitrary text or claim inference.
- All rows remain UNCLASSIFIED, claimEnabled:false. Hospital/training buildings explicitly excluded from eligibility.
- Optional single numeric item reference joins ItemData.ItemIdAndUuid -> ItemInfos with exact string item/UUID and nonnegative integer count. Encoded training payloads are not treated as item references. Counter observations do not prove a collectible amount or action receipt.
- Live with NONEXISTENT injector/agent passed46 bubbles: all BuildBubbleTip, all isShow:true; five sensitive buildings; eight exact own counters and38 non-single-item references. **isShow is not rendered visibility or eligibility proof.** No bubble tapped/collected.
- All nine helper XML/JSON hashes remained identical to the0.30 installed-preview baseline during the first inventory/reject-live checks. Evidence base-bubble-{preview,reject-live,inventory-preview}.jsonl, base-bubble-after-hashes.txt.
- Latest full helper validation passed, including31 base policy checks plus previous suites: `base-inventory-validation.txt`. Diagnostic dex on phone is newer than installed APK.

Resource discovery: ResourceItemDataManager.itemList is empty, not proof of no work. ItemData.ItemIdAndUuid/200394 maps UUID1254334526042161344; matching ItemInfos has exact count11941929 at sample time. Building731000 bubble reports isResourceFull:true and abbreviated15.8K text, but exact production/claim amount/version semantics remain unproven. Never collect from those flags/text alone. See BASE_BUBBLE_NEXT.md.

### Audit coverage

Saved manifest currently records56 focused reviews,124 pattern-only entries and1 excluded vendor bridge (181 entries total). These are reviewed surfaces/functions, not proof every line/dependency was audited. See BOT_DETECTION_CODEBASE_AUDIT.md for scope/findings. Detection probabilities and actual anti-cheat mechanisms remain unknown; no detector probing, concealment or bypass.

Important outstanding findings: Python/Go/helper leases are not shared, legacy raw input lacks helper-level account guards, Go visual receipt is weaker than helper exact sender/post/server proof, screenshot/event retention and remaining log boundaries need review. Never run controllers concurrently. Do not replace helper truck rules or receipts with legacy rules.

### Exact next steps

1. Keep working alone and checkpoint after milestones. Verify active UID/process/window and idle controller before device actions.
2. For passive collection, establish exact production amount/version, free action identity, fresh metadata geometry and independent receipt before adding input. Counter identity alone is insufficient. Base inventory remains inspection-only.
3. Review shared controller ownership design across Python/Go/helper before implementing it; a check-only lock query has a race. Do not weaken account/focus/STOP/uncertain-operation barriers.
4. Mail claims remain blocked on absent ordinary attachment sample and unproven paging coverage. Chest remains quarantined (timestamp unchanged1793234949105).
5. Broaden the remaining124 pattern-only source reviews incrementally. Track concrete access/retention improvements and exclusions honestly.
6. Any next APK release must preserve signing key, XML/JSON hash maps, installed preview and source/deployed distinction. Do not repeatedly install diagnostic-only work without a useful complete release.

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

Latest release0.30 validation:72rules,93maintenance,76Wanted,29cache,46Mailcoverage,36Mailheader,16geometry,7unavailabletext,27Python,18scene,14reference,8integerkeys. AndroidMaintenanceStore20checks previouslypassed. See release030-validation.txt; no source changes after that build except documentation.

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





## Latest runtime asset source improvement (not yet deployed)

JobRunner now derives agentfilenamefromfullSHA256content via RuntimeAssetIdentity andextractswithreplacefalse. Existingcontentisrehashedandmismatchfailsclosed; nooldagentdeleted/rewritten. Commandsuseexactreturnedassetpath, notsharedinput-agent-v06.js. Thispreventsagentpreparationoverwritinganolderactivefilebeforecontrollerlock. ItdoesNOTsolveallpreparationownership: ledgerinitialization/STOPfiles/globalPythonGoleasesstillneeddesign. CONTROLLER_OWNERSHIP_PLAN.md recordsraces/requiredtests andisdesignonly.

RuntimeassetknownSHA256/stability/path/empty/oversizefixturesadded andwiredvalidate. Currentvalidationlogimmutable-assets-validation.txt; checkcompletionbeforenextbuild. NewbasebubbleandPythonchangesstillsourceonlyafterinstalled0.30. Noagents/nobotrestart/noinput.


##0.31 installation completed / continuing production metadata

SignedAPK31/0.31installed. Installedbaseinventorypreviewpassed46unclassified/noinput. NineXML/JSONhashmapsunchanged before/afterinstall+preview. Oldinput-agent-v06.js hashunchanged; exactlyoneNEWagentfilecreated andfilenameequalsitsSHA256. Evidence deploy-031-{before,after,after-preview}-persistent.txt, deploy-031-{before,after-preview}-agents.txt, base-bubble-installed-031-preview.txt/build-031.txt. Currentinstalled0.31supersedesearlier0.30references. Passiveinventoryisdiagnosticonly, noUIbutton/claimpermission.

Productiondiscovery ownbuilding731000/level5: lastCollectTime1793259631961, produceEndTimeLong.MAX_VALUE(9223372036854775807),state0/unlock1/lockInputfalse. Neverinterpretinfinitysentinelasnormalendtimestamp. BuildTemplateManager.buildLevelTemplateDic/#731005 isBuildingLevelTemplate withindexData columnmapping+lineData: para1 col28 STRING2.2,para2 col29 STRING15840,para3 col30 STRING396,para4 col45 STRING200394. capcandidate15840matchesabbreviated15.8Kdisplaybutunits/rate/bonuses/receiptsemanticsunverified. No resourceclicked. Evidence resource-{building-fields,building-version,template-owner,production-template-keys,production-description,level5-fields,level5-nested,template-column-map,template-production-values}.json.

SOURCEONLYafter0.31: BaseBubbleReader addsbuildingVersionObservation(level/state/unlock/lockInput/lastCollectTimeText/produceEndTimeText), semanticsfalse. Needvalidate/previewbeforecallingverified. RetainsLong.MAX_VALUEasexactstring. Continueestablishingrate/capacity/actionreceipt; noinputauthorizationfrommetadataalone.


## Latest production geometry milestone - source only after0.31

BaseResourceGeometryFeature + mode maintenance-base-resource-geometry and nativebase-resource-geometry-preview added. Previewonly; nonpreviewrejectedbeforeinjection. ItallowsONLYreadonlygeometryaction, no ui-tap/maptap/trainingcollect/resourcecollect capability. Selectsatmost4knownownbuilding731000/item200394candidates; exactUUID/class/base/state/unlock/nonworld/lockInput/lastCollectTime/paramIDs/isShow revalidated beforeandaftermeasurement. ExistingXLuapool/type/lifecycle/nativecamera/collider/raycast/HUDblockerprojectionused. AllclaimEnabledfalse.

Firstsampleblockedclippedcamera(noinput). Secondrunblockedtransientunknownoverlay beforeinventory; laterfreshreadonlywindowcheckconfirmedclearbase, thenboundedretryPASSED. Thirdlog base-resource-geometry-preview3.jsonl: buildingUID1254334576017293505, lastCollectTime1793259632009, intendedcollider-65198==firsthit-65198, freshcandidatefromactualcamera, inputDispatched:false. Diagnostic coordinates areephemeral; NEVERtapstoredcandidate. Triggerpath Scene_main_chapter_10/Dynamic/BuildStateIcon(Clone)/Go/Trigger. Visibilitymissesfromotherknowncandidatesrecorded, onlyspecificclipped/UIcovered/raycastmismatch maycontinue; unknownidentity/focus/runtimeerrors stop.

Basepolicy36checks+fullhelpervalidationpassed(base-resource-geometry-validation2.txt). Source/dex/diagnosticagentnewerthaninstalled0.31; NOconsumingresourcefeatureorUIbutton. Nextestablishpassivefreeactionidentity andexactamount/version/counterreceiptbeforeaddingjournaledinput. No resourcewascollected; Car/Footqueuesalsoleftuntouched. Noagents/controllerrunningintentionally. Preservealreadyinstalledsettings/history.


## CRITICAL most recent finished-training live test

Installed0.31preview verifiedCar+Footgeometry. BoundedlivecollectionthenverifiedCar145(type1/queue1256861592788680957/unit107007), butFootblockedbytransientUIScreenCenterTips BEFOREdispatch. Footoperationpreservedcancelled_before_input with explicitinputDispatched:false/native_pre_dispatch andunchangedqueueversion. NOautomaticretry. UIlaterreadonlyconfirmedclearbase; FootstillFinish, CarFree, Hospital+allotherqueuerecordsunchanged. Evidence training-car-foot-{before-queues,after-queues,maintenance,blocked-windows}.json / training-car-foot-live.txt / training-installed-031-preview.txt.

Maintenance-state.jsonINTENTIONALLYchanged(newverifiedCar/cancelledFoot); previouswholehashbaselinesapplybeforethisauthorizedtest. OtherXML/JSONmustremainunchanged. ReadexactverifiedCarreceiptfromsavedmaintenancebeforeclaimingcountdeltas. No newtraining/healing/upgrades/dispatch.

SOURCEfixinTrainingCollectionFeature nowpreservesclaimedcount+verifiedreceipts inBLOCKED/FAILED/UNCERTAINresults (installed0.31omittedpartialcount). Notyetvalidated/build/deployed. CurrentphoneclearbaseOnion; noactivecontroller. Footretryonlyafterstructuredfalse-dispatchproof+freshidentity/geometry/windowcheck; doNOTdeletecancelledrecordoruseanotherledger. Userauthorizedmigrationtests; noquestions/noagents.


## Latest Car/Foot completion and no-work proof

SecondboundedFootattemptafterfreshqueue/window/false-dispatchproof PASSED: unit107107/145, free939->1084, train145->0, queueFree. EarlierCarreceipt exactunit107007/145,free1404->1549,train145->0. Comparingallqueuebefore/after: ONLYCar+Footchanged, Hospitalandallotherqueuerecordsunchanged. No newtraining/healing/upgrade/dispatch. Footcancelled_before_inputrecordretainedbesideseparateverifiedretry; nobypassedledger.

LiveNONEXISTENTinjector/agentrepeat returnedNOTHING_TO_DO0queues(training-completed-repeat-no-work.jsonl); previewalso0geometrychecks(training-zero-ready-no-inject.jsonl). Thisnowestablishesthezero-readydeferredinstrumentationruntimecase. Onlymaintenance-state.jsonchanged acrossauthorizedcollectiontests; allotherXML/JSONsettings/sharehistoriesunchanged(training-car-foot-{before,after}-hashes.txt). Evidence training-foot-bounded-retry.jsonl/training-all-after-foot.json/training-all-final-maintenance.json.

Trainingpartialreportfixvalidatedfullhelpersuiteand6AndroidJSONfixturechecks(TrainingPartialResultTests), butSOURCEONLYafter0.31. Itretainsverifiedcount/receiptsinblocked/failed/uncertainresults. Source-nativeproductiongeometryalsoafter0.31, noresourcecollectionactionexists.

Latestuserpermitsagentsifnecessary. Oneindependentread-onlyreviewagent migration_review_current active/reviewingBaseBubbleReader+BaseResourceGeometryFeature/nativepreview+partialreporting. Itmustnotusephone/edit/build/spawn. Rootownsdevice. Waitreviewfindingsbeforenextrelease; nootheragentsauthorizedforphone. Noagentblanketparallelburn.

CurrentphoneOnionclearbase, all3trainingqueuesFree; noactivecontrollerintentionally. InstalledAPK0.31. Maintenancehistoryhas3verifiedtrainingcollections(Bowearlier,Car/Footnow)+preservedFootcancelledattempt. Chestquarantineremainsunresolved andresourceclaimingdisabled.
