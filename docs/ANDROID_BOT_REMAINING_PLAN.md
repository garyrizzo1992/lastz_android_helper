# Android bot: remaining implementation plan

## Progress checkpoint — 2026-10-31

Run bot/Preview bot, enabled defaults with saved opt-outs, bounded recovery and shared controller ownership are installed as0.39. Two-account previews, actual idle-worker/helper-app recovery without replay, STOP, UI/default persistence and update data preservation passed. Broader repeated live consumption/hung-game/watchdog fault coverage remains incomplete. Auto Boomer's read-only active-state/expiry/options reader and exact native carousel navigation are implemented/tested in source but NOT production-enrolled/deployed; real activation/renewal validation awaits a user-chosen account and a proven receipt. Read the newest CURRENT_HANDOFF.md block for exact state and evidence; remaining phases below still apply.


Prepared 2026-10-30, Europe/Malta. Baseline: installed helper 0.38.

## Objective

Complete the useful behavior of the Python maintenance bot inside the Android helper. One press of **Run bot** must open each selected account, verify its identity, perform its selected and due work, release its input session, visit the next account, and repeat until STOP. All available production features are enabled by default; saved user changes override those defaults. Trucks and World-map bounty sharing remain separate manual modes.

This is an implementation plan, not an instruction to start gameplay. Current operational choice remains: Python stopped, Android helper idle, all five accounts unselected. User update: all available production feature toggles default enabled. Preserve explicit user opt-outs. Unimplemented/unverified features remain visibly pending and cannot execute until delivered; do not claim an unfinished feature works merely by checking a box. Features needing exact account mapping, budgets or external setup must show the missing requirement and refrain from that action until configured. No agents or parallel phone controllers are required by this plan.

## Read these first

1. The newest block in `docs/CURRENT_HANDOFF.md`: actual installed version, device state, tests and blockers.
2. `docs/ANDROID_BOT_PARITY_HANDOFF.md`: authoritative feature behavior and acceptance contract.
3. This document: remaining work, dependencies and delivery order.
4. Actual Python/Java source, feature-specific documents and evidence. Older roadmap paragraphs are historical when contradicted by the newest checkpoint.

The previous 0.37/reboot-locked checkpoint has been superseded. Do not rebuild the rotation from scratch. The unexplained earlier reboot remains an unresolved diagnostic finding, although the resumed previews/UI checks did not reboot the phone.

## What exists and what does not

| Capability | Current Android status | Remaining work |
| --- | --- | --- |
| Account discovery, UID verification, serial rotation, due dates, floating controls and STOP | Installed 0.38; two-account preview and installed UI tested | Repeated live visits, more interruption timing, ownership across Python/native tools |
| VIP free rewards | Existing production worker | Close any missing live/repeat coverage during rotation validation |
| Alliance Help and Common/Rare Gifts | Existing production workers | Help credit-cap ambiguity; Rare Gift live receipt coverage |
| Finished troop collection | Existing production worker | Validate all building families and partial results in rotation |
| Own finished Wanted rewards | Existing production worker | Hidden/unloaded state remains deferred; test real available samples |
| Auto Boomer / Danger Lurks Auto Team-Up | Missing | Implement activation, expiry proof and scheduling |
| Passive base resources and finished building acknowledgements | Inspection only | Exact free action and verified reward/completion |
| Mail rewards | Inspection only; coverage/sample gaps | Complete relevant mailbox coverage and verified ordinary attachment claims |
| Eight-hour chest | Quarantined unresolved attempt | Reconcile existing attempt before enabling claims |
| New troop training | Inspection only | Highest eligible tier, capacity/cost checks and verified new queue |
| Healing, research, construction | Missing production workflows | Implement each separately, including alliance-help requests |
| Alliance Tech donations | Missing | Attempt/currency limits and verified donations |
| Wanted hero dispatch and ally assists | Missing | Separate mission, hero, attempt and receipt logic |
| Own trade-truck collection/dispatch | Missing | Tickets, quality, daily count and transit receipts |
| Radar events and resource gathering | Missing | March reader, protection policy, scoped actions and march receipts |
| Alliance Shop | Missing | Per-item catalog, allowances, costs and purchase receipts |
| Scheduled shields, coverage monitoring and reporting | Missing | Explicit account mapping, activation proof, scheduling, durable reports/alerts and outage detection |

Inspection, code compilation and a button appearing in the app do not count as an implemented feature.

## Rules for every implementation slice

Use this sequence for each feature; do not combine several new consuming workflows in one release.

1. Trace the real Python scheduler caller, configuration, storage and tests. Record actual deployed overrides without exposing secrets. Preserve useful behavior; retire fixed coordinates and optimistic success inference.
2. Read the exact live account, feature state, target identities and relevant costs/capacity. Distinguish missing/unloaded information from a real zero or exhausted state.
3. Add a pure decision policy and an inspection preview. Use fresh metadata and exported control/scene geometry. Do not call undocumented game/network methods to perform actions.
4. Before a claim, spend, dispatch or activation, persist an account-scoped operation record containing the exact target and before-state. An unresolved attempt blocks another attempt at that operation.
5. Recheck UID, foreground process/start, expected panel, live target, cost and geometry immediately before input. Permit only that feature's required actions; do not weaken existing truck/bounty combat guards.
6. Verify an independent after-state tied to the same target. A tap, disappearing popup, reduced list length or generic reward overlay is not sufficient alone.
7. Save verified partial results even if a later action fails. Keep completed, nothing-to-do, waiting, blocked, failed and uncertain outcomes distinct. Never automatically replay an uncertain commit.
8. Add the proven worker to the maintenance registry and account settings, enabled by default, with feature-specific configuration and a persisted next-due time. Persist user opt-outs; do not re-enable a feature the user disabled. Preview must not consume or claim completion.
9. Run relevant regression/negative tests and a bounded live validation on the specifically selected account/task. Verify the installed app path, not only a diagnostic entry point.
10. Build a signed update, preserve the existing signer/data, compare settings/history before and after, and update CURRENT_HANDOFF, the feature status and evidence references. Leave no unattended test running.

If a feature lacks an eligible live sample or a required proof, record the exact blocker and continue an independent slice. Leave that feature disabled; do not turn an inspection tool into a production action to make the checklist look complete.

## User-facing controls: Run bot and enabled defaults

Required by the user's 2026-10-30 update. These instructions supersede earlier default-off assumptions for available production features.

1. Put a clearly labelled **Run bot** button in the main/floating controls and the account/feature configuration screen. It starts normal maintenance immediately using the saved account selection, feature checkboxes and per-feature settings; no second Run confirmation or manually opening each game is required.
2. Save and validate the current screen's choices before starting. Require at least one explicitly selected account and one enabled available feature. If something is missing, show the precise configuration issue rather than choosing accounts or inventing defaults for a spend/target.
3. Enable every available production feature by default for a newly enrolled account. Existing explicit enabled/disabled choices must survive reopening, updates, retries and restarts. When a newly delivered production feature is introduced, its initial toggle is enabled; other existing user choices are unchanged. Include **Enable all features** and **Disable all features** convenience controls, scoped clearly to the account being edited.
4. Keep account selection separate from feature defaults. Do not automatically select all five discovered games; Run bot uses only the user's selected accounts.
5. Make **Preview bot** a separate action which runs one non-consuming preview round. The old maintenance preview checkbox must not silently turn **Run bot** into a preview. Truck/bounty preview controls remain specific to their separate tools.
6. **STOP** remains visible during launching, running, waiting and recovery. It cancels the active session, queued retries, restarts and future account switches. Showing controls, reopening the app or recovering a cancelled task must never undo STOP.
7. Show the current account/task, next account, retry attempt/reason, next retry time, last verified result and any feature needing attention. Add recovery status to the existing grouped interface, not a separate diagnostic-only workflow.
8. Pending features are labelled **Not implemented** / **Needs verification**. An enabled preference is not permission to run nonexistent/unverified code. For missing settings (for example shield target UID mapping or reporting provisioning), show **Needs setup** for that feature and continue independent configured work where possible.

Completion: pressing Run bot starts live selected maintenance, Preview bot does one preview, every new available feature initially appears enabled, saved opt-outs remain disabled, and STOP prevents any restart. These are planned changes; installed 0.38 still has its existing Run maintenance rotation/preview-checkbox UI until this slice is built and deployed.

## Automatic recovery: retry, reopen and resume safely

Goal: an ordinary temporary failure should not require the user to babysit or restart the whole bot. Implement this shared recovery layer before expanding the maintenance feature set. It operates only inside a user-started active Run bot session.

### Persist the recovery/session state

- Add a versioned session record: run generation, requested-running/stopped state, selected accounts/features snapshot, current UID/task, last verified progress, retry count/time, restart count, last error and unresolved operation keys.
- Maintain one exclusive ownership lease across normal work and recovery. Drain/release the old input session and prove old worker exit before starting a replacement. A recovery supervisor must not overlap workers or race an external controller.
- Heartbeat on real progress and expose Running, Waiting, Retrying, Restarting game, Reconciling and Needs attention. Scheduled waiting and known loading are not a hung worker. Use feature-specific deadlines rather than one short global timeout.

### Recovery decisions

| Failure | Required automatic behavior |
| --- | --- |
| Temporary network/loading failure, missing control during a known transition, short-lived unavailable data | Refresh live state and retry the bounded step after 2, 10 and 30 seconds. Recheck UID/focus/target before each attempt. Use a known loading deadline (currently up to 120 seconds for game launch), not rapid taps. |
| An operation timed out after input may have been sent | Reconcile the original operation read-only first. If its exact receipt proves success, record success and continue. Retry only if fresh evidence proves no input/commit occurred and the original operation can be cancelled-before-input. If ambiguous, retain UNCERTAIN, disable further consuming work for that feature and report attention; do not repeat the spend/claim/dispatch. |
| Game crashed or is demonstrably unresponsive; no competing/manual account change | Release the old session and verify worker exit. Restart/reopen only the selected game's proven route, then verify the exact UID. Reconcile outstanding operations before resuming at the next unverified step. Never close unrelated apps or guess another clone. |
| Owned controller/helper worker crashed | The recovery supervisor may replace it within the active user-started session after ownership checks, backoff and journal reconciliation. Preserve cooldowns, selected features and verified results. Opening the app alone is not a new Run command. |
| A feature repeatedly fails before committing | After its bounded retries and at most one game reopen for that failure episode, defer that feature for 15 minutes, show its reason and continue independent safe features/accounts. Use a circuit breaker so repeated visits do not hammer the same broken action. |
| Uncertain feature outcome | Quarantine that feature's consuming operations. Continue other independently verified features only when a clear known UI/account state can be established. If UI or identity cannot be proven, halt that account/session instead. Never clear its history to recover. |
| Insufficient resources, busy queue, full marches, exhausted attempts, event inactive or missing provisioning | Record a normal waiting/needs-setup result and its proper next due; do not restart the game to fix a real game limit or missing setup. |
| Login/authentication prompt, changed/unknown character, manual focus/account change, unfamiliar modal, incompatible game build, ownership conflict, unconfirmed detach | Stop input and show actionable Needs attention. Do not fight user navigation, select a fallback account, bypass a login or replace uncertain controls with blind taps. |
| STOP, a cancelled run, update-install, device reboot/lock | Cancel queued recovery. No automatic restart of a stopped run, no automatic unlock or phone reboot. On a later explicit Run, reconcile old operations before proceeding. |

Initial recovery bounds: three transient retry attempts per failing step; one controlled game reopen per failure episode; at most three automatic game/worker restarts per account in 30 minutes. Exceeding the restart bound pauses that account for 15 minutes and reports attention while other accounts may continue if ownership and state are clear. Reset failure counts only after verified progress, not because a new process appeared. Review these defaults using measured evidence; make recovery limits configurable if needed.

Use a recoverable UI step and fresh semantic geometry after reopening. Do not replay an entire feature from its first click if earlier steps already consumed items or dispatched troops. Explicitly list the safe resume boundaries for each worker.

Critical shield obligations require immediate visible/reportable attention when recovery cannot establish protection; do not hide a failure behind a 15-minute generic retry or claim coverage from an alarm. Recovery must respect the shield service's catch-up windows, outbox rules and no-repeat Use fences.

### Recovery acceptance tests

- Simulate a short network/UI-loading failure: retry succeeds, no duplicate input, rotation continues.
- Crash/restart the owned game/worker before input and after a committed operation: exact UID is reverified, completed work is not repeated, uncertain work remains fenced.
- Interrupt a claim/start/dispatch acknowledgment: read-only reconciliation detects success, proven no-dispatch or unresolved outcome correctly.
- Verify restart circuit breaker/backoff across process restarts; it cannot reset itself into an infinite loop.
- Fail one feature/account repeatedly: independent work proceeds while the failing feature's reason and next retry remain visible.
- Press STOP during each retry delay, launch, reconciliation and restart; no later action/restart occurs, including after reopening the app.
- Exercise full/busy/exhausted/missing-setup conditions: no pointless restarts or rapid polling.
- Verify manual account/focus change and another controller cause a guarded stop, not automatic switching back.

## Delivery order and exact instructions

### 0. Deliver Run bot, enabled defaults, recovery and remaining rotation tests

Reuse RotationController, MaintenanceRunner, MaintenanceStore and the installed profile/UI foundation. Implement the Run bot/defaults and recovery contracts above first; refactor RotationController's current halt-on-every-blocked/failed result into the explicit recovery classifications without weakening commit or identity checks.

- Establish one ownership mechanism across native automation and any Python/diagnostic tool that can operate the same phone. A Java control.lock alone does not prove Python is idle. Do not start Python to compare outputs live.
- Complete bounded live validation of the existing five workers on explicit selected accounts when eligible samples are available. Preserve independent per-UID receipts and due dates.
- Exercise repeated visits: account A -> B -> A; not-due work must skip, idle accounts must wait, and one account's cooldown must not affect another's.
- Test STOP during launch/loading, inside a feature, between accounts and while waiting. After STOP, no later input, account launch or automatic restart is allowed.
- Test manual focus/account change, wrong UID, changed process, unavailable shortcut, input detach failure and interrupted commits. Require visible actionable status and preserved state.

Completion: repeated rotation and recovery are verified, not merely a successful preview. Unknown/unconfirmed work remains visible and does not get marked complete. Implement the recovery behavior below instead of stopping the entire rotation for every transient failure.

### 1. Implement Auto Boomer early

References: parity contract 5.13; `bot/events.py`; `boomer_auto_join`; `tests/test_reliability.py`.

- From the verified base, open Event Center and locate Danger Lurks by identity in its scrollable carousel.
- Resolve the actual Auto Team-Up control, including the green/yellow variants, and wait for readiness within a bounded timeout.
- Read current enabled state and expiry. If already sufficiently enabled, retain that proof instead of toggling it off/on.
- Journal the activation, operate the recognized Activate flow, then verify enabled state and expiry for the same account/event.
- Set the next successful check to 12 hours only after proof. A failed activation retries in 15 minutes; do not postpone a failed operation for 12 hours.
- Return to a known base state. Shield protection must not block Auto Team-Up: this operation is separate from a manual attack or troop march.
- Add an Enable Auto Boomer checkbox per account, enabled by default when the production feature is delivered; preserve a saved user opt-out.

Completion: one verified activation, already-enabled repeat, unavailable/not-ready event, failed activation, STOP and account-change tests. An event icon being found is not activation proof.

### 2. Complete free collection features

References: parity 5.2-5.5; `BASE_BUBBLE_NEXT.md`; `MAIL_COVERAGE_FINDINGS.md`; actual maintenance operation history.

A. Existing Help/Gifts: obtain missing Rare Gift live receipts and resolve credit-cap reporting without inventing gained credit. Help and Gifts must be revisited as requests/gifts regenerate.

B. Passive resources: enumerate owned buildings and production instances for EXP, food, electricity, Zent, wood and fuel variants. Prove exact collectible output/amount/version and the free action. Collect through the live target and verify the exact production transition plus reward receipt. Reject ambiguous/infinite sentinels rather than guessing a quantity.

C. Finished buildings: acknowledge the exact completed building/queue and recognized completion confirmation; verify level/state. Treat this separately from starting an upgrade.

D. Mail: prove coverage of Report/Jungle/Alliance/System/Recharge/Favorite and their relevant pages. Obtain an ordinary unclaimed attachment sample; verify recipient, message UID, attachment identity and free claim control. Claim and verify each operation, retaining partial tab progress. Do not substitute Read All/delete or special deal100 handling. An empty loaded cache is not whole-mailbox completion.

E. Chest: inspect and reconcile the existing uncertain operation read-only. Do not clear it, switch ledgers or blindly press Claim again. Resume production collection only when eligibility and the original attempt are resolved; require reward plus cooldown/version evidence.

Completion: each enrolled collection feature has a verified live result and repeat/no-work behavior. Blocked Mail/chest work does not delay independent Auto Boomer, training or other features.

### 3. Start new troop training

References: parity 5.6; `bot/training.py`; `tests/test_troop_training.py`; TrainingStartReader/Policy.

- Inspect all three training-building families and collect completed queues before evaluating new starts.
- Resolve the highest actually unlocked troop tier from building/science/item prerequisites; a template list alone is not eligibility.
- Read runtime troop capacity, healthy/free/queued counts, allowed quantity and effective resource costs.
- Journal the intended unit/quantity and costs, operate the exact training UI, then verify the new matching queue and resource debit.
- Respect bounded work: up to three collections/three training iterations as in the contract. Busy queues are normal. Full capacity delays starts about one hour but must never disable completed collection.
- Reject unknown costs, insufficient resources, premium/speedup prompts and unexpected lower-tier substitutions.
- Add separate Collect finished troops / Start troop training choices, plus only configuration that the implementation can enforce.

Completion: all three building families; highest-tier selection; full/busy/shortage cases; multiple completions; exact queue/debit proof; restart does not duplicate a start.

### 4. Implement healing, research and construction separately

References: parity 5.7-5.9; `bot/healing.py`, `bot/research.py`, `bot/construction.py` and their tests.

Shared prerequisite: implement a verified request-alliance-help component. A successful start remains successful if the later Help request fails; report the two outcomes independently.

Healing: collect finished healing first. If a queue is free, read wounded troops, selected batch and actual displayed duration/cost. Target 7,200 seconds, tolerance 300 seconds, maximum 8,100 seconds and six bounded adjustment attempts. Heal all available troops if that is a shorter batch. Verify the exact healing queue/units/timer, then request help. No premium spending or speedups.

Research: read the current queue, eligible recommended technology, prerequisites and effective cost. Start only with a free queue and permitted resources. Verify the technology, timer/queue and debit; request help separately.

Construction: inspect every builder row, distinguishing occupied builders, free builders and rentals. Resolve the eligible recommended owned upgrade, prerequisites and exact cost. Support owned resource-pack replenishment as a separately bounded per-account policy: prove deficit, pack/quantity/conversion, then verify the eventual upgrade queue. No rental, diamond or premium fallback. Completion acknowledgement remains a separate action.

Completion: each feature independently passes busy/free, shortage, multiple target, unknown-cost and interrupted-commit cases. Each becomes its own rotation checkbox only after its action is verified.

### 5. Add donations and finish personal Wanted

References: parity 5.2 and 5.10; `bot/alliance.py`; `bot/daily_rewards.py`.

Alliance Tech: select the recommended eligible technology, read remaining donation attempts and permitted currency/cost, donate within configured attempts/budget, and verify attempt/currency/technology changes. Exhaustion is normal; no premium fallback.

Wanted ally assistance: inspect the Ally tab and actual remaining allowance. Assist the exact eligible mission and verify its task receipt and counter increment.

Wanted dispatch: inspect a dispatchable personal mission, remaining count and hero requirements. Select suitable available heroes through the proven Quick Deploy/selection flow. Journal and dispatch, then verify mission status and remaining count. A GO action that opens a World objective is not permission to attack it.

Keep finished Wanted reward collection independent. Preserve hidden/unloaded = deferred inspection. No stealing, premium refresh or World plunder.

Completion: each operation has its own permission, identity, counter receipt and restart barrier; already received/running/exhausted missions are not dispatched again.

### 6. Add own trucks, radar and gathering

References: parity 5.11-5.12; `bot/trucks.py`, `bot/radar.py`, `bot/gathering.py` and related tests.

First implement shared account-scoped march/army and protection readers. They must prove used/free march slots, healthy available troops, selected positive troop capacity and the applicable protection rule. Missing fields are unknown, not free capacity. Manual march features remain disabled while their protection policy is unresolved.

Own trade trucks: collect eligible returned trucks; read real truck IDs and daily trades remaining. Preserve high-grade trucks; use only known available refresh tickets toward purple/orange, with the legacy bound of 50 refreshes. Verify grade and ticket changes before dispatching. Verify exact truck in-transit state and daily-count change. Zero remaining trades schedules the next actual game-day reset; unknown count does not get a guessed fallback.

Radar: inspect exact event IDs and kinds, including NPC/HQ and resource-contest events. Create feature-scoped permissions for each permitted kind; do not enable generic attacks in maintenance. Use healthy nonzero troops and verify exact march/destination plus event-state transition. At most four events per check. Resolve radar work before spending remaining march slots on gathering.

Gathering: use remaining proven slots, search configured resource types/levels, select a verified available node and positive troop capacity, journal dispatch and verify the exact node/march plus slot change. Preserve configurable preferences; the Python source default Food/Wood/Zent weights are 50/50/0, subject to actual deployed overrides. Stop at proven full capacity and recheck later, roughly every two minutes.

Completion: returned/active/exhausted trucks; ticket exhaustion; occupied/changed nodes; all marches busy; no healthy troops; account/focus changes; protection blocks; receipt uncertainty; no duplicate dispatch after restart. Gathering must actually send troops and verify their march, not just open a resource search.

### 7. Implement the shop and scheduled shield service

References: parity 5.14 and section 6; `bot/shop.py`, `bot/shields.py`, `shield_ui.py`, `shield_health.py`, `SHIELDS.md` and tests.

Shop first: maintain one item catalog and exact item IDs/durations. Read live weekly allowance, stock, currency, quantity and total cost. Default enabled catalog from the contract: ten Badge bundles/week, one 24-hour shield/week, three 8-hour shields/week, capped by actual availability and balance. Other catalog choices remain disabled until configured; unnamed items remain disabled until identified. Verify exact item/quantity and currency/inventory changes. Buying a shield does not activate it.

Map the actual legacy four farm accounts to verified UIDs explicitly; do not assume all five discovered profiles are shield targets.

Shield activation: inspect existing protection and the exact owned duration/count. Skip consumption if verified coverage already suffices. Save before-inventory evidence and a durable operation fence before Use; reject Purchase & Use. Handle only the exact recognized replacement confirmation and do not shorten sufficient protection. Verify exactly one item consumed plus a consistent shield expiry. Save ordered before/after/timer screenshots.

Scheduler: Friday 23:00 Europe/Malta -> 24-hour shield; Saturday 21:00 -> 8-hour shield. Prioritize due shield sweeps across target accounts at safe action boundaries rather than waiting four 20-minute visits. Preserve Friday catch-up to Saturday 03:30 and Saturday one-hour catch-up. Saturday renewal must not depend on Friday having succeeded. Test DST/reset boundaries and clock changes; one-off overrides must not become weekly rules.

Monitor/reporting: independently audit coverage every 15 minutes; warn at 60/30/10 minutes, expiry and unknown protection. After Saturday 21:10 flag unverified coverage through Sunday 04:00. Continue monitoring through Sunday 06:00. Only say all four verified when all four are verified. Use the configured last-z-treasure reporting destination privately. Persist report/alert outboxes; retry delivery, never another uncertain Use. Include account, operation, Malta timestamp/expiry and the three ordered evidence images. An independent heartbeat is required to detect a powered-off/networkless phone.

Completion: purchase and activation remain distinct; enough coverage avoids consumption; correct replacement and inventory/expiry proof; missed-window/restart/clock fixtures; delivery loss; partial account failure; independently functioning coverage monitor. Its production feature preference follows the enabled-by-default requirement, but execution remains Needs setup until exact targets, provisioning and controlled validation are complete. Never turn a checked preference into an invented shield target or duplicate activation.

### 8. Finish the complete rotation and cutover

- Run the enabled proven features across the explicitly selected accounts over repeated visits and an actual game reset.
- Preserve the contract's task priorities: overdue shield duties at safe boundaries; VIP/healing/passive work/mail/training/Wanted; periodic development/alliance/shop/Auto Boomer/own trucks; radar before gathering. Implementation order above is not execution order.
- Refresh time after long tasks. Keep elapsed visit budgets monotonic; use timezone-aware calendar keys for daily/weekly work. Daily baseline is 04:00 Europe/Malta; shop limits follow the actual game's reset.
- Verify new feature configuration, per-UID next due, last result/reason, unresolved operation, current/next account and stopped/needs-attention status in the installed app.
- Demonstrate no repeated consumption after interruption/update/restart and no automatic job restart on launch or reboot.
- Keep separate truck/bounty destination/history/rules intact; maintenance must not gain those modes' combat capabilities.
- Preserve the Python deployment/configuration and rollback state until every desired parity row is delivered or explicitly deferred. User-started native production use requires Python to remain stopped on that phone.

Completion: every desired feature has proven useful behavior in rotation, not simply a checked list of source files. Record remaining exclusions explicitly before describing the migration as complete.

## Required evidence for each feature

Record in the feature document/status matrix:

- Python source/configuration reference; Java policy/reader/worker and native guard entry points.
- Account UID, target identity, permitted costs/capacity and actual default/enabled policy.
- Before/after receipt, durable operation key and next-due/reset rule.
- Positive live action, repeat/no-work, busy/exhausted/shortage, wrong account/process/focus, stale target and unexpected modal results.
- STOP before input, during waits and after a commit; interrupted/uncertain operation survives restart without replay.
- Installed version and signed artifact identity, preserved data and installed UI behavior.
- Evidence paths and exact unresolved blockers. Label source-only, preview-only and live-verified accurately.

Run `tools/last-z-helper/validate.ps1` for relevant source changes and `build.ps1` for signed releases. Add tests for meaningful decision/receipt boundaries, not a test that merely repeats the implementation. Do not repeat broad suites after success unless new changes or failures justify it.

## Immediate next work

1. Implement Run bot / Preview bot controls, enabled feature defaults, persistent user opt-outs and shared recovery/session ownership; complete the remaining rotation/recovery tests.
2. Implement Auto Boomer's reader/policy/preview and activation receipt as the first independent missing feature.
3. In parallel in the delivery schedule (not concurrent phone controllers), complete the bounded passive-resource claim slice; record Mail/chest blockers and move on if their proof/sample is unavailable.
4. Add training starts, then follow the dependency order above.

After each completed slice, update CURRENT_HANDOFF with: what changed, what was tested, what is installed, what remains blocked, current phone/job state and the exact next task.
