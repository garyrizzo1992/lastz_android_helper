# Next migration slice after Wanted

Updated 2026-10-29, Europe/Malta. Source audit only: no phone commands, input, injection, installation or account changes were performed for this document. The latest user authorization permits parallel agents; the primary agent alone owns the phone. Read `CURRENT_HANDOFF.md` for deployed status and current device state before any live work.

## Recommendation: Mail coverage and ordinary-attachment inspection

Finish and deploy Wanted first. Then implement a bounded, memory-only Mail coverage reader before enabling attachment claims. This extends an existing discovery foundation and resolves a concrete correctness gap: the current reader always returns `completeMailboxProven:false`. An empty loaded cache cannot establish that every message or attachment has been inspected.

Keep this slice non-consuming. No Claim All, Read All, batch selection, deletion, special code processing, attachment claim or direct invocation of game/network methods. Existing tab navigation can be used later as a separate diagnostic step with one controller, but it is not memory-only and may trigger ordinary game-side read/selection effects. Do not describe it as having no side effects without comparing message read state before and after.

Source anchors:

- `bot/alliance.py:34`: Python `claim_all_mail_rewards`; line 91 taps configured Claim All; lines 117-145 treat visiting configured tabs as completion. Preserve useful tab coverage, not its tap-based success inference.
- `bot/scheduler.py:249`: daily Mail gate; line 260 invokes collection and lines 264-266 record all tabs. Android must not set this daily completion based only on loaded headers.
- `tools/last-z-helper/src/dev/codex/lastzhelper/MailReader.java:6`: current reader joins UI tab and repository headers; line 21 explicitly leaves completeness unproven.
- `MailPolicy.java:8`: inspection allows only entry, six toggles and close. Line 10 defines the current ordinary candidate (`hasReward`, `rewardStatus==0`, `deal==0`, unexpired).
- `MailInspectionFeature.java:12`: six-tab navigation, then current reader. This diagnostic currently requires injected bounds/labels; it is not the proposed memory-only reader.
- `MaintenanceContext.java:8`: memory-only features are denied native actions. Reuse this guarantee and test with nonexistent injector/agent paths.

## Established evidence to reuse

Historical evidence under `runtime/helper-build` is not fresh phone state. Read JSON using BOM detection: some PowerShell redirects are UTF-16.

| Observed owner | Existing fields/evidence | What remains unproven |
| --- | --- | --- |
| `DataCenter/MailFacade/_repository` | `_mailDict`, `_count`, `_lastUid`, `_lastTime`, `_detailAccessOrder`; saved `mail-repository.json` | `_count` scope, whether `_mailDict` is a full mailbox or loaded/cache subset, how details expire/evict |
| `DataCenter/MailFacade/_pagingManager` | `_tabReachedEnd`, `_tabLocalExhausted`, `_tabOldestCursor`, `_tabBeforeTime`, `_loadContexts`, `_groupCountDict`, `_reqMoreTimeoutTimers`, `_reqMoreCallbacks`, `_headWindowDays`, `_headTime`; saved `mail-paging.json` | Actual key types and per-tab values; local exhaustion versus server exhaustion; in-flight/timeout semantics; time-window scope |
| Same paging owner | `_isUsingNewLoadLogic` observed true | Version/branch guard and whether the same semantics hold after process/account changes |
| `DataCenter/MailFacade/_rewardManager` | `_rewardReqList`, `_claimingGroups`, `_rewardCount`, `_accumulatedReward`, `_isAll`, `_isAllReward`, `_expiredPendingDelete`; saved `mail-rewards.json` | Which fields represent a committed request, acknowledgment, accumulated overlay or cleanup; no verified claim transition yet |
| `UIManagerInstance/windows/UIMailNew4/View/ctrl` | `currentTab`, `currentMailId`, `_nextShowMailId`, `mailList`, `_dirtyGroups`; saved `mail-ctrl.json` | Exact repository-to-rendered-cell identity, selection/auto-read behavior and paging list completeness |
| Mail header | UID, recipient, group, `hasReward`, `rewardStatus`, `deal`, expiry are read by current MailReader | Attachment detail schema, currency/item quantities, claimability and stable reset/claim token |
| `UIMailNew4/View/_btnAllRead` | Native object is `btnAllRead`; saved `mail-claim-control.jsonl` | Exact action semantics and current label. Do not assume this is a harmless claim-only control or click it to discover behavior |

Current Mail tab mapping is UI index 1-6 to transport group types `10,2,4,1,17,5`, labels Report/Jungle/Alliance/System/Recharge/Favorite. Prior six-tab sample loaded 16/25/20/20/0/0 ordinary headers; no ordinary pending reward was found. One special System announcement had `deal=100` and must remain excluded. Synthetic no-reward headers have narrow exceptions in `MailPolicy.placeholder`; do not broaden those exceptions to conceal unknown identities or rewards.

## Bounded implementation sequence

1. **Extract memory-only snapshot.** Separate UI text/bounds from repository/paging enumeration. Require the active expected UID and stable PID/start before and after. Permit inspection of an already-open Mail panel without injection; if Mail is not loaded, report `UNINSPECTED`, not empty or completed.
2. **Capture per-tab coverage fields.** Read only the known paging/manager paths first, bounded by count and depth. Preserve exact integer/string identities and observed key tags. Record explicit presence/missing/unknown rather than converting absent flags into false. Do not infer field semantics from names alone.
3. **Model coverage conservatively.** Use states such as `UNINSPECTED`, `LOADING`, `PARTIAL`, `COMPLETE_PROVEN`, `BLOCKED`. Keep `loadedCount` separate from a verified server total and keep special/unhandled pending rewards separate from ordinary candidates. No daily completion or outcome persistence during preview.
4. **Establish semantics through observations.** On one bot, the primary agent can perform a bounded tab/paging diagnostic using live controls after recording the baseline. Compare flags/cursors/counts before load, during a request, after settle, at a genuinely terminal page, and on an empty tab. Record whether tab/row navigation changes read status. Use ordinary UI requests; do not directly call game internals or protocol senders.
5. **Do not equate local exhaustion with full history.** The observed seven-day head window and oldest cursor may describe only a loading scope. Claim that a tab is complete only after the scope and terminal marker are independently established and no request is pending. If that proof is unavailable, retain `PARTIAL` and continue another independent task.
6. **Add pure policy regressions.** Empty-unloaded, cached-but-partial, missing/mixed-key flags, in-flight/timeout, new mail arriving during enumeration, cursor moving, account/process change, special deal100, synthetic headers, expired attachments, and recipient mismatch. A no-work outcome requires the entire intended scope to be proven, not only zero candidates.
7. **Run memory-only acceptance.** Supply nonexistent injector/agent paths and verify the reader returns an accurate preview without native actions, persistent completion writes or changed XML/JSON. Keep tab navigation and inspection evidence distinct.

The first deliverable is a truthful coverage report and actionable blocker list, not a production Mail button. A permanent app control should wait until the underlying action is useful and verified, avoiding another confusing diagnostic button in the user's helper.

## Later claim slice: evidence required before implementation

After the reader is sound, ordinary-attachment collection can become a separate task. It still needs all of the following:

- An actual ordinary unclaimed attachment sample. No such sample exists in the recorded six-tab run; a special deal100 announcement is not a substitute.
- Exact attachment details, recipient, message UID/group and a verified rendered-row/control join. Refresh immediately before input and reject recycled/reordered rows or a changed selected message.
- Observed free claim control text and handler context; no Read All, delete, special code, premium action or bulk side-effect substitution.
- Precommit operation keyed by account and immutable message UID/attachment revision. Persist before the gesture; existing unresolved attempts must block retries.
- Native pre-dispatch guard for active account/window, same message/details/reward state and fresh live geometry. No stored coordinates.
- Receipt tied to the exact mail: observed `rewardStatus` transition plus a matching reward acknowledgment or inventory delta where available. Count decrease or a Congratulations overlay alone is insufficient for identity.
- Verified reward overlay cleanup, repeat no-work, partial failure, stale row, interrupted request and uncertain-result handling. Preserve all histories/settings during deployment and test the installed APK.

Do not enable daily-complete status until every relevant tab's coverage and any eligible rewards are proven. An individual verified claim can be recorded even if a different tab remains partial; that must not be flattened into whole-mailbox success.

## Independent fallback if Mail discovery stalls

Perform a **memory-only passive base inventory**, reusing the scene-object foundation, not new training/healing starts. `bot/scheduler.py:135` handles construction completion markers and line 222 enumerates resource/EXP bubbles. `TrainingReader.java:10` already joins queue/building identity and line 12 uses exact `BuildBubbleManager` parameters.

Inventory visible bubble owner class, building/queue UUID, declared action type, completion version and available reward metadata. Classify only; exclude Hospital, new training, upgrade starts, social gifts and unknown bubbles. A later resource-only claim slice requires an exact resource/EXP delta and bubble version change. A later construction-completion acknowledgment requires its own queue/building transition and known confirmation overlay. Do not port Python camera swipes or assume every yellow/green bubble is a passive free claim.

Chest is not a fallback live test: its legacy uncertain operation remains quarantined. Read-only reconciliation is independent, but do not clear the operation or use a different ledger to resume collection. New training, healing, research, construction, hero dispatch and purchases are broader consuming workflows with missing cost/capacity/prerequisite receipts; they follow the migration plan after these bounded inspection gaps.

## Continuation checkpoint

This audit did not modify deployed code or existing shared handoff/plan files. Primary agent is completing Wanted integration and owns device state. Before starting this slice, check current `CURRENT_HANDOFF.md`, source and installed version, verify idle controller/expected UID, and update that handoff after every meaningful discovery. Technical detection probabilities remain unknown; reducing unnecessary instrumentation is not an invisibility claim.
