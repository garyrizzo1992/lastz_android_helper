# Next passive slice: own-base bubble inventory

Status: **memory-only inventory implemented locally and live-preview verified; not in installed0.30.** BaseBubblePolicy/Reader/InspectionFeature + maintenance-base-bubble-preview added.26purepolicychecks and fullhelpervalidation pass. Live with nonexistentinjector/agent returned46exactown-building joins, allBuildBubbleTip/allisShowtrue, five sensitivebuildings excludedfromeligibility. Nonpreviewmode rejected. AllninehelperXML/JSONhashesunchanged vs0.30installedpreviewbaseline. No input/claims orUIbutton. Evidence runtime/helper-build/base-bubble-{preview,reject-live}.jsonl andbase-bubble-after-hashes.txt. Currenthandoff remainsauthority.

Important: isShowtrue for ALL46cachedbubbles, so it doesnot prove renderedvisibility orclaimeligibility. One resource-like samplebuilding731000has isResourceFulltrue and abbreviatedrewardCountText15.8K, but no exactamount/inventoryreceipt/controlsemantics established. Neverclaimfromthattextorflag. AllrowsremainUNCLASSIFIED/claimEnabledfalse. Next join exactproduction/resourcecounters, determine actualbubblestate/version and freshgeometry, then separatelytestjournaledcollection onlyafterfreeaction/receiptproof.

Proposed new files:

- `tools/last-z-helper/src/dev/codex/lastzhelper/BaseBubbleReader.java`
- `tools/last-z-helper/src/dev/codex/lastzhelper/BaseBubbleInspectionFeature.java`
- Optional pure whitelist/shape policy and separate tests, only if meaningful.

Proposed reader API: `static JSONObject read(String cache, String expectedUid)`.
Feature ID: `base_bubble_inspection`; `requiresInstrumentation()` returns false.
The feature must reject `!context.preview` before reading or returning a result so the runner cannot write a feature outcome. Root must also ensure the controller rejects non-preview diagnostic requests before invoking the runner.

The reader must validate the expected active UID and clear own base before touching the inventory. Require scene1, currently verified level10001, no normal modal, and an exact active-window allowlist (`MainUI_SU`, `UIAlarm`, `TouchScreenEffect`, `UIMultiLanguageFloatingBall`). Repeat pinned process/account/focus checks at the end. No input, injection, navigation, claim, journal, settings/history or outcome writes. Existing `GameMemory(cache)` discovery-cache refresh may occur and must be disclosed as `infrastructureCacheMayRefresh:true`.

Read only `DataCenter/BuildBubbleManager/allBuildBubble`, bounded to at most128 typed table rows. Each bubble's numeric dictionary key must be a positive exact integer string. Join it to `DataCenter/BuildManager/allBuilding/#<buildingUuid>` and require that building's exact integer `uuid` equals the dictionary key. Require a positive exact integer building `itemId`. Reject invalid/missing joins; do not treat an unjoined bubble as owned. Exclude `isWorldBuild:true` records from this own-base inventory and report only an excluded count. Bound table log/array sizes before calling `GameMemory.rows`, then enforce the final128-row cap.

Allowlisted output per row:

- Exact building UID as a string and building itemId.
- Typed `isShow` boolean; missing/unsupported shape must remain explicit rather than false.
- Optional bounded class/name from `_class_type/__cname`, `__name` or `name`; do not read Unity object pointers or call getters to obtain names.
- `param` scalar keys **only**: `uuid`, `funcUuid`, `itemId`, `count`, `type`, `buildUuid`, `queueUuid`. Report present supported scalar types honestly; integer identities stay strings. Missing and unsupported shapes are explicit. Never traverse arbitrary nested param tables.
- `classification:"UNCLASSIFIED"`, `claimEnabled:false`, `eligibility:"NONE_PASSIVE_INSPECTION"` for every row. No resource/EXP/free-claim inference from icons or artwork. Hospital/healing, new training and upgrades are excluded from eligibility; no actions exist in this slice.

Never emit raw addresses/pointers, complete bubble or building dumps, callbacks, models, sprites, icon paths, positions, arbitrary text or other param keys. Snapshot metadata should disclose `readOnly:true`, `memoryOnly:true`, `claimEnabled:false`, the expected UID and sample time. This inventory does not establish resource/EXP collection semantics or permission to tap any bubble.

Saved schema evidence already inspected:

- `runtime/helper-build/training-ready-bubble.json`: known Bow bubble has `isShow:true`, numeric `buildId425000`, param exact queue `uuid1256861624250155192`, building `funcUuid1256861624241766514`, item string `107207;145;0`. It also contains non-allowlisted callback/model/positions/icon/EXP fields: do not export those.
- `runtime/helper-build/training-completed-building.json`: matching own building UUID, itemId425000, `isWorldBuild:false`, state0/unlock1. Do not assume all bubble types share its shape.
- Existing `TrainingReader.java` demonstrates exact integer UUID joins. `TrainingInspectionFeature.java` demonstrates the memory-only feature pattern, but this new feature additionally requires preview-only execution.

Acceptance before wiring a diagnostic mode: meaningful pure whitelist/identity/type/bounds tests, build/source audit, then root-owned preview on the already-active account with deliberately nonexistent injector/agent paths. Confirm no action or feature outcome write. No helper UI button or production collection mode is justified by this inventory alone.


## Additional own-inventory counter discovery

ResourceItemDataManager.itemList isempty; it isnot theloadedcounter. ItemData.ItemIdAndUuid/200394 -> exactstringUUID1254334526042161344, thenItemData.ItemInfos/<UUID> provides matchingstringitemId/uuid andexactintegercount11941929 atsampletime. This canbe futurecounterbefore/afterevidence, NOTclaimeligibilityoramountproof. No amount/receipt/safeclaimtapimplemented; resourcebubble15.8Kdisplayisabbreviatedandproductioncanchangebetweensamples. Evidencebase-item394-index.json/base-resource-item394.json. No claims.


## Exact own-counter inventory integrated locally

BaseBubbleReader nowjoins SINGLEnumericparam.itemId references to exact ItemData.ItemIdAndUuid/ItemInfos. UID/itemidentity/count>=0 required, countTextintegerstring; encodedtrainingpayloads excluded. Livepreviewwithoutinjectorpassed46bubbles/8counterobservations/38not-single-itemreferences. Basepolicy31fixtures/fullvalidatepassed. This is observationonly; noaction/claimability/amountsemantics. Installed0.30unchanged.


## Live geometry proof completed (source after0.31)

Readonlyknownproductiongeometrymode foundvisiblebuilding1254334576017293505 andmatchedfirstnativecollider-65198. ExactcurrentUID/ownbuilding731000/item200394/lastCollectTime1793259632009/paramUUID/class/state/unlock/nonworldguards; freshcamera/viewport/HUDblockers andraycast. ReceiptinputDispatchedfalse. Sourcefeatureallowsnogameplayinput; ephemeralcandidatecannotbereused. Evidence base-resource-geometry-preview3.jsonl. Clippedfirstcandidateandtransientoverlayfailuresrecorded; do not relaxguards. Next FREEACTION/amount/receiptproof remains, notcollectionready.
