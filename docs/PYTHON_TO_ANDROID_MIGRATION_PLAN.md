> **Current 2026-10-30:** Account rotation is now explicitly requested and implemented in source; the previous P4 deferral below is superseded by [MAINTENANCE_ROTATION_PLAN.md](MAINTENANCE_ROTATION_PLAN.md). Installed helper remains0.37; 0.38 candidate is not installed. Live verification was interrupted by an unexplained phone reboot. Read [CURRENT_HANDOFF.md](CURRENT_HANDOFF.md) before continuing; older ACTIVE instructions do not authorize restarting a job.


# Python bot to Android helper: functionality and migration plan

Created2026-10-29. Current: Phase0 foundation plus VIP/AllianceHelp/CommonGifts/finishedtroops/Wantedclaims implemented; installed0.31. Mailcoverage andpassivebaseinventory arediagnostic-only; chestquarantined. Source-onlyproductiongeometrydiscoveryongoing. KeepCURRENTHANDOFFcurrent; do not infer completion from historical milestones.

## Objective

Move the useful maintenance workflows from the desktop Python bot into the on-device Last Z helper. Preserve each feature's decision rules and verify its game outcome, while replacing OCR, template positions and fixed taps with read-only game metadata plus ordinary input at live UI bounds.

Do this incrementally. Keep existing truck/bounty modes working, add individually selectable maintenance tasks, then combine proven tasks into a single-account maintenance cycle. Work alone unless the user changes the no-agents instruction.

## Evidence and boundaries

Inventory comes from current `main_scrcpy.py` configuration, `bot/scheduler.py`, the feature modules, `status_store.py`, `workflow_result.py`, and current feature documentation. Enabled below means the checked-in default, not proof of deployment settings or successful execution on every account.

Older notes are not the authority when current code differs: personal/ally bounty missions were removed earlier but restored in October23's `bot/daily_rewards.py`. Older radar/training/shop audit findings also have subsequent fixes; preserve current behavior rather than copying the historical bug list.

The Python README describes four accounts, but current `game_settings` contains five configured slots. Neither those slot labels nor clone indices establish game identity. Android profiles must use verified character UIDs.

New gameplay managers, fields, UI paths and reset timestamps are discovery requirements, not assumed existing exports. Inspect them before estimating a feature's final implementation effort. This planning task does not start phone actions, enable features or stop an existing job.

## Already in the helper: retain, do not rebuild

| Capability | Current scope and caveats |
| --- | --- |
| Other players' truck sharing | Purple/yellow;3+ fragment slots below the configured power to Gaarix's trucks group, or2+ to World at any known power. Initial big blue Share button directly; NEVER Plunder or map-location navigation in share mode. |
| Gaarix truck attacks | Explicit attack mode,3+ slots strictly below configured power, active Gaarix UID only. Victory and defeat returns tested. Keep combat input guards. |
| World-map bounty sharing | Completed, available12/15-box bounty tiles to World or trucks group; no plunder, empty note; independent destination history/checkpoints. Qualifying group send/receipt coverage remains pending. |
| Runtime and live input | Pinned process/start/UID, read-only memory, live Unity geometry, viewport-derived gestures, single controller, foreground checks, STOP, wake lease, signed update and preserved ledgers. |
| Discontinued-state handling | Exact nonexistent-state message skips to the next state; unknown navigation errors stop. |

**Own-truck dispatch is not migrated. Personal Wanted missions are not the same feature as World-map bounty sharing.**

## Functionality inventory

Priority bands: P0 shared foundations, P1 quick maintenance, P2 queue/dispatch workflows, P3 spending/protection workflows, P4 optional infrastructure. Effort S/M/L is relative implementation and validation complexity, not a time promise; metadata discovery can change it.

| Python feature and source | Current behavior/default | Android migration and proof of success | Priority / effort |
| --- | --- | --- | --- |
| VIP login points and Daily Freebies â€” `bot/daily_rewards.py` | Enabled; daily completion with15-minute retry/check gate. | Read claim availability/cooldowns; collect both categories and verify reward/claimed state. Do not infer success from tapping Claim. | P1 / Sâ€“M |
| Mail rewards â€” `bot/alliance.py`, scheduler | Daily tab scan; retry incomplete scans after15minutes. | Enumerate real tabs/messages and claimable attachments. Mark a tab complete only after its rewards are claimed or confirmed absent. | P1 / M |
| Eight-hour chest â€” scheduler | Check every10minutes. | Read availability and next-ready time; claim once and verify cooldown/reward transition. | P1 / Sâ€“M |
| Alliance Help â€” `bot/alliance.py` | Enabled opportunistic help, including after build/research/healing. | Resolve live Help control/requests, act only on available help, confirm request count/state changes. | P1 / Sâ€“M |
| Alliance Gifts â€” `do_hourly_action` | Revisited hourly because gifts regenerate. | Read claimable gifts; collect and verify depletion without suppressing later regeneration for the whole day. | P1 / M |
| Alliance Tech donation â€” `do_hourly_action` | Hourly check of available attempts. | Verify selected tech/attempts and configured donation currency; donate within a bound and confirm attempt/currency change. No premium donation fallback. | P2 / M |
| Passive base collection â€” scheduler | Completion markers, post-construction acknowledgement and passive collection; wider completion sweep less often. | Inventory each actual passive action separately; resolve building/queue objects and claim controls by identity. Enumerate completion metadata rather than copying the Python camera sweep. | P1 / M |
| Personal Wanted mission rewards â€” `bot/daily_rewards.py` | Enabled; collect finished personal missions. | Read mission IDs/state and claim rewards; confirm claimed state before recording completion. Skip World-objective GO missions as Python does. | P1 / M |
| Personal Wanted hero dispatch â€” same module | Dispatch available personal missions after selecting heroes; check15minutes. | Verify mission/hero availability, dispatch, then confirm remaining-count or mission-state transition. Do not confuse this with troop marches. | P2 / M |
| Ally Wanted assistance â€” same module | Help allies with a daily assist counter. | Verify exact ally mission and remaining allowance; confirm assistance counter increments. | P2 / M |
| Completed troop collection â€” `bot/training.py` | Collect completion markers before starting new queues. | Read queues across training buildings and collect completed units; verify queue/capacity changes. Can ship before new-training logic. | P1 / M |
| Highest-unlocked-tier training â€” `bot/training.py` | Per-account enabled; up to3queues/cycle; capacity-full retry after1hour. | Identify unit building, unlocked tiers, selected tier, queue and capacity. Confirm highest eligible tier and active queue. Reject lower-tier warning rather than accepting it. | P2 / Mâ€“L |
| Hospital healing â€” `bot/healing.py` | Per-account enabled;60-second check; batch duration capped at8100seconds. | Read wounded/selected units, duration and queue. Adjust through actual UI within the configured cap; confirm active healing and request help. No automatic speedup/premium fallback. | P2 / Mâ€“L |
| Construction â€” `bot/construction.py` | Check5minutes; start recommended upgrade only with a free builder; resource replenishment exists. | Resolve builder/building IDs, free queue, prerequisites, cost and recommendation. Start only allowed upgrade, confirm queue occupancy/timer and request help. Replenishment gets a separate bounded policy. | P2 / L |
| Research â€” `bot/research.py` | Check5minutes; start eligible research and request help. | Resolve tech/queue/prerequisites/cost; use configured selection rule, verify actual queue start and help request. | P2 / Mâ€“L |
| Own-truck collection, refresh and dispatch â€” `bot/trucks.py:do_trucks` | Daily trades; collect returns, refresh one truck toward target grade, dispatch; counter/reset persistence. | Separate from other-player scanners. Read owned truck IDs, remaining trades, grade, free refreshes and dispatch state. Confirm collection/dispatch and enforce refresh-cost limits. Never guess remaining trades when metadata is absent. | P2 / L |
| Resource gathering â€” `bot/gathering.py` | Uses available marches; resource-level search; roughly2-minute busy-state recheck. | Read live free marches, resource preference/level, target node ID/availability and selected troops. Confirm new march identity/destination and capacity change. Respect shield-protection policy. | P2 / L |
| Manual radar tasks/events â€” `bot/radar.py` | Enabled;15-minute check; up to4events; priority over ordinary gathering. | Read task kind/ID/rewards/expiry, free march and positive capacity. Resolve each permitted Attack/March control and confirm dispatch/task transition. Keep legacy `do_radar` distinct until its actual callers are traced. | P2 / L |
| Danger Lurks/Boomer Auto Team-Up â€” `bot/events.py` | Enabled;12-hour confirmation window,15-minute retry on failure. | Read event identity and activation/expiry; activate only when due and verify real12-hour enable state. Do not copy the historical hourly-repeat bug. | P2 / M |
| Alliance Shop â€” `bot/shop.py` | Catalog enabled; default items Badge,24h and8h shields;6-hour recheck fallback and15-minute failure retry. | Match item IDs/durations and actual currency/price, stock, remaining weekly allowance and reset. Verify purchase quantity plus inventory/currency/reward delta. Keep purchasing separate from using a shield. | P3 / L |
| Peace shield activation/replacement â€” `bot/shields.py`, `shield_ui.py` | Activation/schedule disarmed by default; weekly/dated operation records and replacement rules exist. | Read active expiry and owned inventory; exact item duration, plain Use vs Purchase & Use, replacement policy and consumption receipt. Preserve uncertain-attempt protection and require a controlled live activation before enabling unattended use. | P3 / L |
| Shield health/protection evidence â€” `bot/shield_health.py`, `shields.py` | Coverage audits/alerts and suppression of new manual marches when protection policy is active. | Read expiry in-game, record warning/coverage state per UID, and gate relevant dispatches. Existing external evidence/outbox behavior is optional integration work, not an automatic message-sending migration. | P0 guard + P3 full feature / Mâ€“L |
| Scheduling/status â€” `bot/scheduler.py`, `status_store.py`, `workflow_result.py` | Per-account priorities, durable due times, daily/weekly reset gates, retry/backoff and explicit outcomes. | Reimplement platform-neutrally in Java with per-UID jobs, typed results, reset-aware periods and durable attempts. See foundation phase. | P0 / L |
| Account rotation/recovery â€” Python navigation/scheduler | Launches configured clones/accounts and can recover/relaunch them. | Deliberately NOT copied now. Helper remains current-window/current-account only; future rotation requires a separate design and explicit user direction. | P4 / separate scope |
| Host deployment, remote control and external alerts â€” Ansible, launchers, `observability.py`, remote-phone tools | Desktop lifecycle, SSH pause/resume, logs and optional Discord/ntfy/Axiom integrations. | Signed APK deployment, on-phone status/local notifications and exportable diagnostics replace the required host runtime. Retain external tools only where needed; do not port SSH/host launchers into gameplay. | P4 / optional |

Legacy Python truck plunder and World-bounty hunting are disabled by default. Do not create competing legacy attack modes or port World-bounty plundering: the user's current rule is bounty sharing only, never plunder.

## Proposed phases and delivery order

### Phase0 â€” Shared maintenance foundation

Deliver this before a combined unattended maintenance cycle; basic read-only discovery for the first feature can run alongside it.

1. Define small feature workers rather than expanding `AutomationController` into another monolith: common lifecycle plus separate reader, policy, UI workflow and outcome components per feature.
2. Introduce typed results: completed, nothing-to-do, waiting/cooldown, blocked, failed and uncertain. Preserve reason, evidence, next due time and feature/UID identity.
3. Persist per-UID preferences, daily/weekly period keys, attempts and next due times. Preserve all existing truck/bounty keys and checkpoint files. Use the legacy reset/timezone policy as a baseline, but prefer verified game timestamps; test DST and avoid guessing a weekly reset weekday.
4. Extend existing combat controls with **explicit per-feature capabilities**, not a global bypass. Truck Plunder/Fight remains Gaarix attack-mode only. Radar may eventually need a separately authorized radar-dispatch capability; personal hero dispatch is another operation. Bounty-sharing mode gains no combat permission.
5. Provide a shared march reader and protection gate before any new manual-march feature. A protected account must follow the Python suppression policy, without weakening existing truck restrictions.
6. Define bounded checkpoints/yield points and one-controller ownership. Never preempt a confirmation, input editor, purchase, march commit or battle; never run the Python bot and helper together on one phone.
7. Add structured events with wall time/duration, feature/UID/operation ID, observed state, before/after values, distinct vs repeated observations and next retry. Maintain bounded log retention and screenshot evidence on failures; screenshots are not coordinate selectors.

Exit: scheduler/persistence/policy tests pass, STOP survives/restarts safely, account switches terminate the selected run, and a dry worker round-trip creates correct per-UID outcomes without consuming anything.

### Phase1 â€” Claims and basic alliance maintenance

Order: VIP claims â†’ Alliance Help/Gifts â†’ Mail â†’ eight-hour chest â†’ passive completion and completed troop collection â†’ finished Wanted rewards.

Start with **VIP rewards** as the first vertical slice: two known reward types, daily state and a visible claimed/cooldown outcome. It establishes the claim/reward-overlay pattern used by later tasks. Alliance Help is the next independent slice.

Deliver individual run/preview controls plus per-UID feature toggles. Include already-claimed, no-work, partial completion, unexpected dialog and interrupted-run cases. Daily completion requires all relevant categories/tabs confirmed, not one successful claim.

Exit: each enabled feature has a bot-account live success and a no-work/cooldown result. No premium purchase or fixed-position fallback appears.

### Phase2 â€” Queue maintenance and development

Order: training â†’ bounded healing â†’ research â†’ construction/resource policy â†’ own-truck dispatch. Split claim/inspect stages from resource-consuming starts.

Read resource costs and item balances before enabling starts; carry over the user's configured limits rather than broad Python defaults. Keep queue occupancy, caps and prerequisite blockers distinct from failures. Reuse alliance help, not duplicate fixed handshake taps. Own-truck grade refresh must have an explicit free/paid refresh budget.

Exit: one bounded start, resulting queue/truck identity and resource/counter deltas confirmed per feature; full capacity, unavailable builder, resource shortage and interrupted/uncertain start cases handled without double consumption.

### Phase3 â€” Personal dispatch, events and world marches

Order: personal Wanted hero dispatch/ally assistance â†’ Danger Lurks Auto Team-Up â†’ gathering â†’ manual radar event types individually.

Personal missions, event Auto Team-Up and World troop marches are separate state machines. Require correct mission/event/node IDs. Gathering/radar share real march capacity and priority arbitration; radar gets first use where the Python policy does. Do not use guessed available march/troop values.

Exit: exact dispatch/event identity and post-action status verified, unavailable capacity blocks correctly, protection mode blocks the right actions, and no duplicate dispatch follows a timeout.

### Phase4 â€” Purchases, shields and advanced timing

Order: read-only shop/inventory/expiry views â†’ selected catalog purchases â†’ shield health â†’ exact owned-shield activation/replacement â†’ timezone-aware scheduled protection.

Preserve catalog allowlists and quantities, event/reset data and existing shield operation IDs. Shield scheduling currently describes Friday23:00 and Saturday21:00 Europe/Malta plus bounded dated overrides; verify the desired event timing/reset assumptions before enabling a new native schedule. Unknown availability or consumption must stop, not purchase a replacement or retry Use.

Single-account limitation is material: the helper cannot promise protection for all Python account slots while only one game window is active. Notify that another UID needs attention; do not silently open/switch clones. Keep shield activation disarmed until its own live evidence is complete.

Exit: item/currency/quantity and protection-expiry evidence match intended operations; reset/DST/catch-up tests pass; stopped/offline/uncertain operations do not lead to duplicate purchases or shield use.

### Phase5 â€” Combined maintenance profile and Python retirement

Add **Run selected maintenance** to the app and floating panel, with feature toggles and per-UID settings rather than a long list of unrelated buttons. Show the active account, current action, next due tasks and last failures. Keep existing explicit truck and bounty buttons.

One serial scheduler runs only proven features. Maintenance features use bounded units of work. Existing continuous truck scanning and bounty ranges remain exclusive unless the user explicitly chooses a combined profile; do not secretly interleave maintenance into an ongoing share/attack confirmation. STOP stops the selected session and must not trigger an automatic restart.

Observe short supervised cycles, then a longer unattended run with restart/foreground-loss recovery checks. Disable each migrated feature in the Python scheduler before enabling its Android equivalent. Keep rollback instructions and the old Python implementation until acceptance. Runtime Python/OpenCV/Tesseract/ADB on a PC are no longer required for migrated phone workflows; development/deployment tools can remain.

### Phase6 â€” Optional later projects

Account rotation, multi-account shield coverage, external alerts/outboxes and remote orchestration are separate choices. They are not implied by porting maintenance features. Preserve active-window-only behavior until a new account-selection design is explicitly requested and tested.

## Repeatable recipe for every feature

1. Trace the Python entry point, scheduler gate, current configuration, side effects and existing tests. Write an action contract: permitted action, forbidden substitutions, inputs/limits and actual success evidence.
2. On the selected bot, inspect read-only metadata for the panel/data. Record actual paths/types and freshness; sample ready, busy, exhausted and unavailable states. Do not assume a feature's readable fields exist because truck metadata does.
3. Implement a reader and pure policy with tests. Port decision rules/counter parsing semantics where useful, not image ROIs, coordinates, keyboard heuristics or automatic account launch.
4. Add named live-control navigation, clipped/virtualized-list handling and explicit preconditions. Keep state/focus/UID checks. Stop safely when exports change; no guessed-coordinate fallback.
5. Preview the exact target, cost and intended action without the consuming/dispatching commit. Persist an attempt before a commit that could be repeated after a crash.
6. Perform one controlled live action within the selected feature's limits. Verify a game-state transition or receipt; a button click or finished script is not evidence of success.
7. Test no-work/cooldown, resource/capacity limits, stale data, confirmation mismatch, cancellation and uncertain receipt. Verify STOP/lease/input cleanup.
8. Add app and floating controls, local status, docs and durable schema compatibility. Build with `tools/last-z-helper/validate.ps1`, preserve signing/settings/history during update, and compare persistent hashes. Run an installed-app preview as well as diagnostic dex checks.
9. Promote that feature into the maintenance profile only after passing its acceptance checklist. Turn off its Python equivalent on that device.

## Live implementation log -2026-10-29

### Completed in source

- Phase0 native classes: MaintenanceResult,MaintenanceSchedule,MaintenanceStore,MaintenanceContext,MaintenanceFeature,MaintenanceRunner,MaintenanceController. Independent per-UID state, opt-ins defaultoff, one serial pass/controller lock, typed results, game-day/DST helpers, bounded retry helpers, durable pre-commit attempts and unresolved-attempt blocking. Feature-scoped input allowlists defaultdeny; truck combat guard remains unchanged.
- Dedicated VIP slice: VipPolicy,VipReader,VipFeature. Entry MainUI_SU/View/topLayer/vip_btn; panel UIVip. Daily points box_btn + boxOpened/boxUnOpened + box_btn_text; Daily Freebies free_btn + freeOpened/freeUnOpened + free_btn_text + free_des_text. Daily Freebies heading verified. **get_btn is Activate, not a free claim; gift_btn/shop excluded.** Claim-level guard runs again in the injected input callback.
- Observed login reward overlay UIVIPRewardPopUp/View/return_btn; closes only in the verified VIP+reward context. Unrecognized overlays stop. Native stateOnly getter reads active/text/interactable values without clicking hidden UI.
- MaintenanceController separated from truck/bounty controller; JobRunner routing/status and main/floating VIP free rewards buttons added. Version0.25 signed/update-installed, package verified; all settings/share/attack/bounty/maintenance hashes preserved.
- Fixed a pre-existing receipt metadata bug: group-bounty verified records now use groupSequence rather than worldSequence. Separate Android destination regression tests cover it.

### Verified evidence

- Existing72 rule checks,40 maintenance core checks,16 geometry scenarios,7 error-text cases,16 Python tests and agent syntax/audit pass. Android temporary-fixture checks:15 maintenance persistence checks and5 share-ledger destination checks. No real settings/ledgers used by fixture tests.
- OnionRing92 UID2059765822000064/PID4652/start8058934: native VIP cooldown inspection. Both rewards already claimed; no claim input. Previous bounty job stopped at54 after window/process change,2065 observations,0shares/attacks; monitor was deleted, not restarted.
- User manually opened unclaimed bot Garix922 UID1430578113000153/PID7132/start8197571. Preview confirmed both categories CLAIMABLE and wrote no completion. First live daily-points claim increased score32040â†’32080 and opened UIVIPRewardPopUp; verified operation persisted, then stopped at unknown overlay as designed.
- After observing and adding the popup close control, a continuation dismissed the verified popup and claimed Daily Freebies. Both categories became COOLDOWN and returned to base. Each claim has its own verified operation. Evidence runtime/helper-build/vip-garix922-{preview,live,freebies-live}.jsonl and vip-points-reward.png.
- Repeat live check passed: NOTHING_TO_DO,claimed0; exactly2 verified claim operations remain. Installed-app VIP preview passed both cooldowns and did not change any persistent hashes. No controller remains.

### Important design decisions

- Game countdown implies02:00UTC reset in observed VIP sessions (03:00Malta in winter), unlike Python's04:00Malta baseline. Use game countdown for next due; do not guess local reset hours.
- VIP cache lastUpdateTime stayed unchanged after claiming, so it is NOT a daily reset token. First operation uses an initial observation revision; later operation eligibility IDs follow the last verified category cooldown. Ready-before-that-cooldown is blocked; unresolved attempts block across all revisions/targets. No automatic re-claim to resolve uncertainty.
- Preview writes no live maintenance outcome or completion/cooldown. Manual VIP runs do not opt the account into future background maintenance. Scheduled combined profile remains phase5 work.

### Immediate next steps

1. Complete: repeat no-work check and signed0.25 deployment/installed-app preview.
2. Current: Alliance Help/Gifts discovery on Garix922; see snapshots runtime/helper-build/alliance-*.json. GiftNum15 but giftInfoList is lazy/empty before its panel. AllianceHelpState No0/UpgradeHelped1/RuinsHelped2/UpgradeAndRuinsHelped3; current rows stats1 need helpType-specific interpretation before acting.
3. Implement/preview/verify Alliance Help/Gifts as the next phase1 slice. Do not auto-switch accounts, restart bounty scanning, or deploy while any controller is active.

## Continuation checkpoint â€” Alliance discovery (2026-10-29)

User explicitly requested regular durable updates so another account can continue. Update this plan and NEXT_SESSION.md after each meaningful implementation/test/deployment milestone, and before stopping. Separate observed facts from untested behavior.

- Installed version remains 0.25; VIP migration is complete and verified as recorded above. No Alliance feature has been implemented or deployed yet.
- Last observed account: Garix922, UID1430578113000153, PID7132/start8197571. Re-read current account/windows and controller ownership before further phone input; this checkpoint is not live state.
- Last observed screen: UIAllianceHelp over UIAllianceMainTable. No Help All or Alliance gift claim has been clicked. No automation job was left running by these diagnostic checks.
- Alliance entry: MainUI_SU/View/bottomLayer/alliance_btn. Alliance main button map is UIAllianceMainTable/View/_allianceMain/_buttonListInType. Observed #3 has _itemData.type3/name Help, #4 has type4/name Alliance Gifts; click the validated row's _btn using live bounds.
- Help controls: UIAllianceHelp/View/help_btn; help_txt reads Help All; close_btn returns. Exclude notActivatedBtn and other activation controls: these offer the automatic-help service. Observed AllianceHelpDataManager helpNum91, todayHelpPoint0, refreshTime1793325600000, otherHelpInfoList populated, _handledCallHelpIds empty. Row stats1 semantics remain unresolved; do not infer eligibility from that enum alone.
- AllianceGiftDataManager reported giftNum15 but giftInfoList was lazy/empty before opening Gifts. Gift categories, free eligibility and actual claim controls still need discovery.
- Evidence is under runtime/helper-build/alliance-*.json and alliance-{main,help}-discovery.png (local ignored runtime artifacts). The last help-list query was saved to alliance-help-list.json; inspect bounded fields rather than dumping the entire object.
- Exact next step: inspect saved help-list/base-data fields and current UID/windows; establish authoritative guild identity. Then verify the free Help All transition in a bounded run, implement its reader/policy/journal/feature allowlist and tests, expose main/floating controls, and only then discover Gifts. Preserve the single controller lease and existing combat/share guards. Update this checkpoint with any live action/result immediately.

## Added work task: bot-detection risk analysis (requested 2026-10-29)

Status: planned; apply per migrated function. User specifically wants the risk of game-memory inspection assessed and concrete improvements identified.

Deliverable: docs/BOT_DETECTION_RISK_ANALYSIS.md with a per-function matrix covering read-only process memory access, injected Unity getters, root privileges, overlays/accessibility, automated input, action frequency and server-visible behavior. Distinguish what this project demonstrably does from hypothetical detection signals and unknown anti-bot capabilities. Do not claim a numeric probability or that a function is undetectable without evidence. Local success and absence of a ban are not evidence of non-detection.

Review steps:
1. Trace each function's actual runtime access and permissions from source and existing logs. Explain separately that memory reads may be read-only while the mechanism used to obtain them can still be observable. Record any native injection even if it only calls getters.
2. Consult the game's current official terms/support material when conducting the review; identify permitted interfaces and relevant restrictions. Do not probe the production anti-bot system or run additional live automation solely to test detection.
3. Rate evidence and uncertainty per function, account-impact severity, and exposure; record the basis and limitations of each qualitative conclusion.
4. Produce prioritized account-risk improvements: supported interfaces where available, remove unnecessary injection/access, explicit opt-ins, bounded operation and stop controls, least privilege, clear status, and an option to disable unsupported automation. Preserve existing settings/history and gameplay safeguards.
5. Add regression checks for approved architectural changes and update this plan with findings and remaining unknowns. Detection bypass, concealment of instrumentation, anti-cheat patching and ban-evasion techniques are outside this review.

Acceptance: every migrated function has an evidence-backed assessment and actionable improvements, with implementation status and residual uncertainty. No live protection-bypass experiment is authorized by this task.

## First implementation batch

Recommended next task: **foundation interfaces and per-UID status, then one complete VIP reward slice**. Follow with Alliance Help/Gifts and Mail. This gives useful daily maintenance without starting new combat, consuming shields or changing account-selection behavior.

Before that task's phone tests, check the existing bounty worker/monitor state and coordinate controller ownership. Do not interrupt healthy bounty sharing or overwrite its assets. Current run completion/receipt verification is a separate outstanding validation item, not a reason to rebuild bounty logic during this migration.

## Acceptance checklist

- [x] Full feature inventory and defaults reviewed; distinguish own trucks, other-player trucks, personal missions and World bounty tiles.
- [x] Foundation/persistence/capability design implemented and tested for first VIP worker; remaining feature scopes are explicit later additions.
- [ ] New feature's actual metadata paths documented from live observation.
- [ ] Preview and one verified bounded live action pass, plus no-work/error/uncertain cases.
- [ ] No fixed UI positions or image-coordinate selectors added; source audit extended where needed.
- [ ] Single input owner, active UID, STOP, resource/protection policy and retry behavior preserved.
- [ ] Main/floating controls and per-UID settings agree.
- [ ] Signed update preserves existing settings/ledgers/checkpoints; installed-app check passes.
- [ ] Python equivalent disabled on the tested device; rollback documented.

## Source map for the next session

- Python orchestration/defaults: `main_scrcpy.py`, `bot/scheduler.py`.
- Python features: `bot/daily_rewards.py`, `alliance.py`, `training.py`, `healing.py`, `construction.py`, `research.py`, `trucks.py`, `gathering.py`, `radar.py`, `events.py`, `shop.py`, `shields.py`, `shield_ui.py`, `shield_health.py`.
- Outcome/reset semantics: `workflow_result.py`, `status_store.py`.
- Existing semantics/evidence: `docs/DAILY_REWARDS.md`, `ALLIANCE_SHOP.md`, `SHIELDS.md`, `ARCHITECTURE.md`; relevant `tests/test_*.py`.
- Native foundation: `tools/last-z-helper/src/dev/codex/lastzhelper/` (StateProbe,GameMemory,DeviceInput,CombatPolicy,JobRunner,HelperService,MainActivity,ShareLedger).
- Geometry/audit: `tools/last-z-helper/unity-ui.js`, `gesture-geometry.js`, `input-agent-tail.js`, `audit_input_positions.py`.
- Run handoff: `docs/NEXT_SESSION.md`, `docs/BOUNTY_MONITOR.md`, `docs/REMOVE_HARDCODED_POSITIONS_PLAN.md`.

### Alliance Help live milestone â€” 2026-10-29

AllianceHelpPolicy/Reader/Feature implemented locally, main/floating controls added, dedicated maintenance-alliance-help routing. Validation72rules/47maintenance/16geometry/7error/16Python passed. First preview safely stopped on parent window assumption; actual parent UIAllianceMainTable State3 (suspended) while UIAllianceHelp State2, modalCount2. Reader now accepts observed parent State2/3 while requiring exact child context. Second preview passed with9 pending, no write.

User switched to OnionRing92 UID2059765822000064, guild b4c42d6392e7403d834fe14f67ac5081 (MOB-BORN Farms). Bounded live Help All verified10â†’0 pending and280â†’380points, durable operation verified, returned base. Evidence alliance-help-{preview2,live}.jsonl. No activation/purchase input. _handledCallHelpIds remained empty even after success, so credit-cap behavior still unverified; count decrease alone deliberately does not count as success. Current APK remains0.25; local Alliance code not APK-deployed. Next repeat/no-work, Gifts discovery, build/deploy milestone.

### Alliance Gifts source/preview milestone â€” 2026-10-29

AllianceGiftPolicy/Reader/Feature added locally; controller mode maintenance-alliance-gifts and main/floating button wired. Observed UIAllianceGift/View: tabIndex/toogleIndex1 Common (rewardType2),2 Rare (rewardType1), toogles/#1/#2 with selectName labels, get_all_btn/get_all_btn_txt Claim All, close_btn. Excluded del_all_btn, level chest/libao_info, settings toggle and offers. Native callback rechecks guild/tab/window/account immediately before Claim All; Help callback also now rechecks guild/count/reset/window.

Preview passed OnionRing92:148 unclaimed Common,0 Rare, no claim. giftInfoList rows carry UUID,receiveState(0unclaimed/1received),receiveTime,expirationTime. Receipt requires each selected UUID retained with receiveState1 and positive receiveTime; disappearing rows alone do not prove collection. No-work Help repeat passed0pending/380points. Host72rules/54maintenance/16geometry/7error/16Python passed. Bounded live Gift diagnostic in progress: wait for its completion before pushing assets/installing; log runtime/helper-build/alliance-gifts-live.jsonl. APK still0.25, no new background scheduler.

### Deployment0.26 checkpoint â€” 2026-10-29

Signed0.26 update-installed; package versionCode26/versionName0.26 verified. Persistent XML/JSON hashes identical before/after (deploy-026-before/after.txt). Main/floating controls now include VIP free rewards, Alliance Help, Alliance Gifts. No combined unattended maintenance profile enabled.

Common live claim verified all155selected gift UUIDs state1 with positive receiveTime; durable operation verified before later navigation failed. Rare tab/close inputs immediately after bulk claim were not applied. Bounded state-checked navigation/close retries added; no consuming retry. Repeat both tabs passed NOTHING_TO_DO/collected0 and returned base, without new claims. Evidence alliance-gifts-{live,repeat}.jsonl, maintenance-after-gifts.json, alliance-gifts-after.png. Rare live claim and Help at credit cap remain unverified. Current54maintenance+72rule+16geometry+7error+16Python checks pass.

Installed-service Alliance Help preview currently running; wait for its result before another controller. Then installed Gifts preview, persistent hash comparison, current-window checks; next feature Mail. No memory assets should be pushed during a controller.

### Installed verification complete; Mail next â€” 2026-10-29

Installed0.26 Help preview passed1pending/noinput; Gifts preview passed2newCommon/0Rare/noinput. All persistent XML/JSON hashes still identical to pre-install (deploy-026-after-preview.txt); previews do not write completion or consume. No controller remains after these runs. Evidence alliance-{help,gifts}-installed-preview.jsonl. Mail next: observed MainUI_SU/View/bottomLayer/mail_btn_slg entry and DataCenter/MailFacade,MailShim,MailShowTemplateManager,MailGroupTemplateManager. No mail claim yet.

### Mail discovery checkpoint â€” 2026-10-29

No Mail claim input. UIMailNew4/View: _toggles/#1..#6, _mailChannelType with id/order and type, _txtTitle/check_text; ctrl/currentTab is the selected template type, not displayed position. Observed displayed mapping Report1/type10, Jungle2/type2, Alliance3/type4, System4/type1, Recharge5/type17, Favorite6/type5. Do NOT conflate this with MailChannelType enum (System0/Fight1/Chat2/Self3), which describes header.tabType. Mail headers use groupId matching selected UI template type.

MailFacade/_repository/_mailDict holds objects/_header: uid exact decimal string, toUser, groupId,hasReward,rewardStatus,deal,expireTime,tabType. Current cached172headers; one hasReward/rewardStatus0 is Tuesday Code Released!, deal100 (special). Normal attachment eligibility and special deal handling remain unproven; do not claim this as a standard item reward. Claim All is _btnAllRead, actual child text caption text; Batch Process/delete excluded. _pagingManager has _tabReachedEnd (currentlyempty), _loadContexts, _groupCountDict; cache does not prove entire mailbox scanned. Read-only evidence mail-{view,ctrl,show-groups,header-inventory,channel1,claim-control,load-contexts}.json/.jsonl plus mail.png. Next implement bounded Mail inspection without claims, then resolve eligibility/completeness before live claims; other phase1 claims can proceed independently. Current phone remains Mail; known close _btnClose.

### Mail inspection implemented/verified; chest investigation â€” 2026-10-29

Local MailPolicy/MailReader/MailInspectionFeature and diagnostic maintenance-mail-preview added. No Claim All/mark-read/delete permissions; returns PREVIEW even when invoked without dryRun, never records mailbox completion. After identifying three exact synthetic empty-recipient/no-reward placeholder headers (types73/997/1000), bounded inspection passed all six tabs: Report16,Jungle25,Alliance20,System20,Recharge0,Favorite0 loaded headers; ordinary candidates0, System special deal100pending1. No claims. Recipient/ID checks retained for real mail. Evidence mail-inspection-preview2.jsonl. Host72rules/62maintenance/16geometry/7error/16Python checks pass. Mail code is LOCAL ONLY, APK remains0.26.

Eight-hour chest visible in base-discovery.png; not found in standard HUD exports or42BuildBubble entries. Inspecting read-only Unity text hierarchy for its08:00:00 label (PhoneCheck ui-texts/inspectText visibleNodes diagnostic) to locate owner. No chest input or collection. Query snapshots chest-*.json; avoid repeating broad searches. MapRewardBoxManager/allRewardBox empty, EventBubbleManager/allBubble subgroupsempty, DroppedTreasureDataManager/dataDictempty; none established as chest owner. Current account OnionRing92, base/no modal, no background controller.

### Eight-hour chest owner found; shared geometry gap â€” 2026-10-29

SceneManager/World/ObjMgr/mapObjectLLHangUp is MapObjectLLHangUp. Observed hangUpBubbleState=true,hangUpBuildState3,showMax=true; exports timeDes,bubble,bubble_trigger_obj,car_trigger_obj,box/gameObject as Lua userdata (tag71), not wrapper tables with instanceId. Current input-agent exported() intentionally only permits UIManagerInstance/windows paths and resolves wrapper.instanceId; ui-state on this scene reference safely rejected Invalid exported control path. No chest click/claim. Runtime evidence chest-hangup-{object,car}.json and chest-city-world/obj-mgr.json.

Next technical task: add verified read-only scene-object identity/geometry support for exported Unity references, plus base-scene/input guards and tests, before chest collection or passive/troop-bubble collection. Do not broaden arbitrary scene paths, guess coordinates, invoke handlers, or relax UI input guards to get a quick click. Need accumulation/last-claim metadata and confirmed popup before enabling claims. Existing read-only visibleText diagnostic could not find08:00:00 in TMP/UI.Text; no claim that this hierarchy resolved it. Remaining detailed chest queries saved; avoid repeating them.

Work continues independently with the queued per-function detection-risk review while this shared geometry gap is designed. APK0.26 stable; local Mail inspection/readonlydiagnostics not APK-deployed. No job remains; phone OnionRing92/base.

## Resumed checkpoint â€” pre-injection account gate fixed

User resumed work here and requested no questions while away; keep regular handoffs. Memory-only read confirmed OnionRing92 UID2059765822000064/base; no controller/injector active. MaintenanceController now constructs context/checks expectedAccountUid BEFORE input.foreground(). Full validation72rules/62maintenance/16geometry/7error/16Python passed. Bounded mismatched-UID diagnostic supplied deliberately nonexistent injector/agent paths and returned expected-character rejection, proving no injector startup was needed; no gameplay input. Source/dex only, APK remains0.26. Evidence maintenance-uid-preflight-rejection.jsonl.

## Deployment0.27 complete â€” account preflight and risk checkpoint

Signed27/0.27 installed, expected UID validated before injection. Mandatory buildaudit+positive/negative regression catches reordered gate. Diagnostic and installed-class test used mismatched UID/nonexistent injector and returned expected-character rejection before launch. Persistent XML/JSON hashes unchanged before/after install and installed check; evidence deploy-027-{before,after,after-check}.txt and maintenance-uid-{preflight,installed}-rejection.jsonl. Validation72rules/62maintenance/16geometry/7error/17Python passes. Preview status states game instrumentation. No gameplay input or background job.

Detection-risk per-function matrix and prioritized improvements saved BOT_DETECTION_RISK_ANALYSIS.md; actual probabilities unknown. The account preflight improvement is now deployed. SCENE_OBJECT_GEOMETRY_PLAN.md records staged scene-reference geometry implementation/acceptance. Next chest blocker is verified XLua userdataâ†’Unity mapping; no raw pointer guessing, sceneinput not enabled.0.27 contains diagnostic-only Mail inspection and readonly textdiscovery, still no Mailclaims.

## Scene-reference foundation milestone (source/diagnostics only)

Observed XLua metadata and Lua5.4 userdata layout resolve four chestrefs plus basecameras on Unity thread, read-only. Trigger has BoxCollider/TouchObjectEventTrigger; timeDes is SuperTextMesh._text and reads08:00:00. Main camera's mask includeslayer0; HUD excludes it. Eightcollidercorner projection saved chest-collider-projection.jsonl. No input/claim.

Local scene-geometry.js computes conservative candidates only, always requiresRaycast;18cases cover wronglayer/depth/clipping/invalid/degenerate/blockers. Added to audit and validate; full72rules/62maintenance/16existinggeometry/7error/17Python+18scenegeometry pass. Not packaged or wired to sceneinput. Diagnostic source newer than installed0.27. Next fresh native raycast exactcollider/occlusion and broaderlifecycle tests, then chesteligibility/receipt metadata. SCENE_OBJECT_GEOMETRY_PLAN.md details evidence/acceptance.

## Chest geometry preview verified (no input)

Exact native raycasthit matches intendedcollider; combined livebounds+raycast+HUDblockers preview passed with08:00:00 andclaimEnabled:false. Evidence chest-{collider-raycast,geometry-preview}.jsonl. No scene-tap/claim action enabled; pending sceneidentity/freshness/lifecycle testrefactor and chesteligibility/reset/freepopup. Local agent bundles scene-geometry.js;0.27 APK unchanged.18scenegeometrycases and existingvalidation pass. Handofftopupdated; no controller remains.

## Chest inspection source/live checkpoint

DataCenter/StoryManager.hangupTime1793234949105 and hangupReward(empty) discovered using bounded memory-only managerfield index. Local ChestPolicy+ChestInspectionFeature/mode maintenance-chest-preview checks stable timestamp before/after geometry, returns PREVIEW/FULL_INSPECTION_ONLY withclaimEnabledfalse. Live passed, no operation/completion saved. hangupTime meaning still needs an actual claimtransition before calling it provenlastclaimtoken. Evidence chest-story-state.json,chest-maintenance-preview.jsonl.

Added14scene-reference lifecycle regressions for tag/uservalues/payload/poolbounds/free-slots/stride/type; nativegetter diagnostic calls sharedpureguard. Fullvalidation72rules/69maintenance/16geometry/7error/17Python+18scenegeometry+14referencechecks passes. No sceneinput/claim enabled, no newAPK since0.27. Exactownerclass/freshness and popup/claimverification remain next.

## One journaled chest-open probe verified; no claim

Nativeopening guards revalidate scene1/level10001/no-modal/focus/UID, ownerclass, <=500msgeometry, stableXLuapool/ref/objectslots and expectedhangupTime. Single ordinarytap opened UIJeepAdventureMain route then actualUIStoryHangup. NoCollect; timestampunchanged. open_only journalverified. Probeupdated towaitexactUIStoryHangup (firsttestcapturedroutewindowearly). ChestReader/popup readonlypreviewadded; fieldsreceive_btn/receive_text/close_btn/title_text/time_text/time_desc_text and8loadedrewardrows. Currentphoneidlepopupopen forinspection; no claimcontrolpermission yet. Evidence chest-open-inspection.jsonl,chest-{jeep,hangup}-view.json,chest-jeep.png,chest-popup-preview.jsonl.0.27APKunchanged.

## Chest live guard/quarantine and receipt hardening

Fullfreeclaimprevieweligiblepassed. Firstliveattemptstoppedbeforeclaim duetoUIJeep routecleanup; exactstackowner/countfixadded. Secondattempt nativeguardrejectedtransientUINoticeTips beforegesture, storedUNCERTAIN. NoCollectsuccess; hangupTimeunchanged. Legacyattemptmustnotbebypassed/deleted; receiptlackedstructuredinputphase.

Newnative receipts markinputDispatched/phase/requestAction, conservativelytruebeforeeventcall. DeviceInputtypedpre-dispatchreject; MaintenanceStore explicitcancelBeforeInput requiresfalse-dispatch receipt+freshunchangedtimestamp, retainscancelledattempt andseparateretrykey; verifiedretrycannotrepeat. Chestusesonlyfuturetypedrejection, noautomaticretry.20Androidstorefixturecheckspass. Controller quarantinestatus nowrequiresnoinjection; nonexistentinjectorcheckpassed. Fullvalidation72rules/73maintenance/16geometry/7error/17Python+18scenegeometry+14reference.0.27installedunchanged. ChestUIunexposeduntilclaim/repeatverified. Knownpopup/routeclosedwithoutCollect; nextindependentphase1workwhilelegacyclaimquarantined.

## Completed-training inspection foundation

Memory-onlyqueue/building/bubble/armyjoin implemented TrainingPolicy/Reader/InspectionFeature,mode maintenance-training-preview. Default requiresInstrumentationtrue; trainingfalse and Context blocksnativeactions. Nonexistentinjector/agentlivepreviewpassed,readyBow1/CarFootwaiting2/excluded7inclfinishedHospital. ExactBow145unit107207/free56/train145,queue1256861624250155192,building1256861624241766514,buildingtype425000,bubblematches. Noinputorcompletionwrites. TypedpolicyrejectsHospital/ArmyUpgrade,unitfamilymismatch,invalidquantity,wrongbuilding,locked,staleBubble/futureend/inventorymismatch. Fullvalidation83maintenance+priorchecks passes. Evidence training-{all-queues,queue-types,completed-building,army-counts,ready-bubble}.json,training-memory-only-preview.jsonl.0.27APKunchanged. Nextboundedcompletedtroopcollectionviaexactbubble/collider/receipt; newtrainingremainslaterphase.

## Completed troop collection verified, release0.28 building

Nativequeue-boundgeometry+freshrefs/end/payload/armycounts and strictactualinputwindowguards implemented. OneBow145collectverifiedqueueFree/free56â†’201/train145â†’0,repeat0,CarFootHospitalqueuerecordsunchanged,exactlyoneverifiedjournal. Main/floatingCollectfinishedtroopsadded; manifest0.28signedbuildpending. Evidence training-collect-{preview,live,repeat}.jsonl,training-after-collection-queues.json,maintenance-after-training-collection.json. Fullvalidation72rules/85maintenance/16geometry/7error/17Python+18scenegeometry+14reference+8exactkeys.

Unverifiedmaintenance-chest consumingentrypointdisabledforrelease (sourcefeaturekept); legacyuncertainnotbypassed. Chestinspection/open-onlydiagnostics available, actualclaimstillunreleased. Nextfinish0.28preservinghashes+installedpreview, thennextphase1functionality; updatehandoffwithdeployedstatus.

##0.28 deployment complete / next Wanted claims

Signed28/0.28 updateinstalled; settingsXML/allJSONhashesidenticalbefore/afterinstallandinstalledservicepreview. InstalledCollectfinishedtroopspreviewpassed0ready; main/floatingbuttonshipped. Evidence deploy-028-{before,after,after-preview}.txt,training-installed-preview.jsonl. Noactivecontroller. Chestconsumingentrypointdisabled, legacyuncertainkept. Nextphase1PersonalWantedfinishedrewardmetadata; keepherodispatch/allyassistanceoutofscopeuntilownpolicies/receipts. Pythonimplementationreviewedbutnoimagecoordinatesported.


## Wanted reward discovery / memory-only preview verified

Wanted entry is MainUI_SU/View/bottomLayer/dispatchBtn -> UIActivityCenterTable activity400001 -> panelComponentList/400001 DispatchTask tab1. Data is ActDispatchTaskDataManager/singleTask, not HeroBountyDataManager. Exact table identity joins showDatalist to personal UUID; first current row UUID1430459261720215782/config600501 completed/unreceived, eight received, one stealing placeholder excluded. New maintenance-wanted-preview is memory-only and passed with nonexistent injector paths:1candidate/8received/1excluded, no claims or dispatch. Source-only;0.28 installed unchanged.91maintenance tests plus prior suites pass. Next exact Receive UI/free/row-recycle native pre-input guard and journal+rewarded transition receipt. See CURRENT_HANDOFF.md for current phone state and next actions.


## Wanted bounded live claim proof, source only

WrongUUID native pre-dispatch rejection, preview, one live Claim, reward dismissal and no-work repeat passed. UUID1430459261720215782/config600501 rewarded0->1; only that scalar flag changed across personal tasks, no added tasks. No GO/dispatch/stealing/assistance/refresh.93maintenance checks plus prior suites pass. Production entry/cleanup wrapper, UI and deploy remain. Evidence wanted-{negative-uuid,claim-preview,claim-live,claim-repeat,reward-close}.jsonl. CURRENT_HANDOFF.md has current state.


##0.29 deployed and installed preview verified

Collect Wanted rewards available main/floating. Exact single live claim and repeated no-work, negative UUID, viewport positive/wrongowner/offscreen, guarded clear reward dismissal verified. Nine XML/JSON hash maps unchanged across signed install and installed preview; version29/0.29 confirmed. Remaining limitations: no auto-scroll for offscreen ready task, empty/unloaded cache blocked, hidden shortcut status only covers loaded records. No GO/dispatch/assistance/stealing/refresh. Next agent work is memory-only Mail coverage and source-only screenshot retention/cache-policy improvements. CURRENT_HANDOFF.md supersedes historical pending deployment notes.


##0.30 deployed / current checkpoint

Memory-only Mailcoverage/headerdiagnostics, deferredWanted/traininginstrumentation, compatible-sessiongate, optionaldiagnosticcaptures and truthfulgeometryfailurestatus shipped. Fullreleasevalidationpassed. NineXML/JSONhashmapsunchanged acrosssignedinstall AND installedWantedpreview; no-workcorrect, no gameplayactions. Mail remainsdiagnosticonly/partial/noordinarycandidate, chestquarantined. Whole-codebaseauditcoverage documented separately;135manifestentriespattern-only remain. CURRENT_HANDOFF.md is currentauthority; noagents.


## Passive base inventory source proof, no collection

BaseBubblePolicy/Reader/InspectionFeature + diagnosticmaintenance-base-bubble-preview implemented locally, memoryonly/already-clear-ownbase/previewonly.46exactbuildingjoins,8singleitemreferencesjoinexactowninventorycounters; allunclassified/claimdisabled, nogetterinjection/input/persistedoutcome. Nonexistentinjectorlivepreviewpasses, nonpreviewrejects, basepolicy31checks+fullhelpervalidationpasses. Sourceonlyafterinstalled0.30, noUIbutton. Needexactproduction/amount/version andactionreceiptbeforeclaimslice. See BASE_BUBBLE_NEXT.md / CURRENTHANDOFF.


## Completed training coverage expanded

Car145 andFoot145 nowliveverifiedwithqueueFree+exactfreegain/traindrop. Hospital/allotherqueuerecordsunchanged. Footfirstattemptcancelledbeforeinputontransientoverlay,preserved;freshseparateboundedretryverified. Livezero-readyrepeatwithnonexistentinjectorreturnedNOTHING_TO_DO0,provingdeferredno-workpath. Onlymaintenancehistorychanged,allsettings/sharehistoriespreserved. Partial-resultcount/receiptfixlocallyvalidatedandAndroidfixture6checks;sourceafterinstalled0.31. No newtrainingstartenabled.
