# Android/Java migration: complete bot behavior and acceptance contract

Prepared 2026-10-30, Europe/Malta. Intended reader: the chat implementing the on-device Java helper.

## 1. Goal and scope

**User planning update 2026-10-30:** [ANDROID_BOT_REMAINING_PLAN.md](ANDROID_BOT_REMAINING_PLAN.md) now specifies the remaining delivery work, an explicit live **Run bot** action with separate Preview bot, all available feature preferences enabled by default (saved opt-outs preserved), and bounded automatic retry/game-worker restart recovery. Recovery must reconcile uncertain commits and never override STOP or exact account/ownership checks. These are planned requirements; installed 0.38 is unchanged. Read CURRENT_HANDOFF for the live checkpoint.


Replace the desktop Python maintenance bot with an on-phone application that automatically visits the explicitly selected Last Z accounts, performs each account's enabled maintenance work, keeps independent schedules/history, and repeats until STOP. The user must not open every game or press Run between accounts. Preserve the separate truck and World-bounty tools already implemented in the helper.

**Parity means the useful behavior and verified outcomes survive the migration, not that Python's coordinates, OCR, blind taps, optimistic success logs or recovery mistakes are translated to Java.** A feature which only inspects metadata, exists only in source, or clicks without confirming the outcome is not migrated.

This is documentation only. No phone interaction, deployment, bot restart, purchase, shield activation, claim or scan was performed to prepare it. This document does not authorize starting a worker or consuming anything. Existing user Run choices and feature-specific permissions still apply.

### Evidence and precedence

Reviewed the working-tree Python entry point/configuration, `bot/scheduler.py`, feature modules, tests and current Android migration documents. Python Git HEAD was `3d9e8ee`; important newer Java files and some Python changes are uncommitted. A Git SHA alone therefore does NOT reproduce the reviewed working tree.

Use these sources in order:

1. The user's latest instructions and actual current source.
2. [CURRENT_HANDOFF.md](CURRENT_HANDOFF.md), **its newest block**, for installed release, phone state and unfinished validation.
3. This document for the end-to-end parity target and feature acceptance criteria.
4. [MAINTENANCE_ROTATION_PLAN.md](MAINTENANCE_ROTATION_PLAN.md) for the current rotation implementation and pending release tests.
5. Feature-specific source/tests/evidence. Older historical sections are context, not current operational instructions.

[PYTHON_TO_ANDROID_MIGRATION_PLAN.md](PYTHON_TO_ANDROID_MIGRATION_PLAN.md) and [MIGRATION_STATUS_MATRIX.md](MIGRATION_STATUS_MATRIX.md) contain useful inventories but older statements that rotation is out of scope, or that release 0.31 is current, are superseded. Likewise README comments/source defaults do not prove the Mac's external environment or current live behavior. Inspect deployed configuration before any production cutover; never print its secrets.

## 2. Current Android checkpoint: do not restart from scratch

**Update 2026-10-30:** rotation release 0.38 is now installed. Post-reboot hashes, minimal preview, full two-account/five-feature preview, same-key preservation, profile UI/persistence, floating startup, STOP and overlay permission handling were verified. Wanted's exact nonmodal message-banner recognition was repaired. Hidden Wanted remains deferred; no claims were made by these tests. All five accounts are unselected; Python stopped/helper idle by explicit user choice. The newest CURRENT_HANDOFF.md block and rotation038-mac-evidence contain authoritative details. The prior checkpoint paragraph below is historical; full Python parity and later production slices remain pending.


Latest saved checkpoint reports **installed 0.37**, with a signed **0.38 candidate local only**. Rotation is implemented in source, not yet fully phone-verified or installed. An unexpected reboot interrupted its final two-account preview. The saved checkpoint says user 0 was credential-locked and no unattended controller remained; these are historical observations to recheck, not a live device-status claim.

Before further device work: confirm user unlock and health, verify settings/history against the saved baseline, investigate the unexplained reboot, then perform minimal preview validation before another full round. Inaccessible encrypted app storage is NOT evidence that data was deleted. Do not initialize replacement state, clear ledgers, update-install while preservation cannot be verified, or claim 0.38 is deployed.

Android already has production maintenance slices for:

- VIP free rewards, both categories.
- Alliance Help and Gifts; Help credit-cap and Rare Gift live coverage still have limitations.
- Finished troop collection, including three troop-building families. **No training starts.**
- Own completed personal Wanted rewards. **No hero dispatch or ally assistance.**

Source rotation wraps those five tasks. Mail and passive-resource inspection are not claim implementations. Training-start inspection does not permit training. The eight-hour chest has an unresolved legacy attempt and its consuming entry point is quarantined. Healing, construction, research, own-truck dispatch, gathering, radar, donations, shop purchasing and shield automation are not production-migrated merely because their Python counterparts exist.

Existing Android truck/bounty modes are separate functionality to preserve, not work to replace with the older Go/Python scanners. Their latest rules are summarized in section 8.

## 3. Accounts and the automatic lifecycle

### Identity model

Legacy Python rotates four launcher positions named game1–game4; labels Farm 1/2/3 and Dassy are not secure identities. Earlier launcher inspection showed the icons can move. Java must not use those screen positions or infer a character from a slot name.

Read-only Android setup documented five registered Parallel Space shortcuts:

| Registered clone | Observed character | Exact UID |
| --- | --- | --- |
| 0 / Last Z+ | trucks by garix | 2059765822000064 |
| 1 / Last Z1+ | yn gaarix | 2059770776000064 |
| 2 / Last Z2+ | baby gaarix | 2059744163000064 |
| 3 / Last Z3+ | Dassy | 1850977487000064 |
| 4 / Last Z4+ | Garix922 | 1430578113000153 |

These are saved observations, NOT permission to select all five and NOT a definitive mapping of Python game slots. Historical names can change. Reconfirm profiles through exact live UID and clone/process identity. Gaarix's explicit truck-attack identity is separately pinned to UID `2028198887000064`; never substitute a similarly named profile or assume clone 4 is that account.

### Required run sequence

1. Opening the helper shows its floating controls, **not an automatically started job**. Overlay permission denial must remain actionable.
2. The user chooses registered accounts, per-account feature toggles, preview/live mode and visit duration, then presses Run.
3. Acquire one exclusive ownership lock for the whole session. Reject overlap with Python, Go, another helper worker or diagnostics that inject input. The existing Java lock alone does not establish cross-program ownership.
4. Open the selected account by its Android-registered shortcut intent. Verify the exact clone, foreground process/start and game UID before gameplay input.
5. Check overdue critical shield obligations first once that feature is migrated; otherwise run due maintenance in the order below. A verified UI/base state is a prerequisite, not a series of blind Back presses.
6. Run only enabled/due work for that UID. Finish bounded in-flight commits and verify their outcome before yielding.
7. Save outcome/next due/cursor. Release that account's input/instrumentation context successfully before switching.
8. Visit the next selected account; repeat until STOP. A normal visit defaults to a soft 20-minute budget. Yield early when no work is due; if every account is idle, wait for the earliest due task rather than spin.
9. STOP cancels waits and prevents later input/switching/restarts. Unknown focus/UID, blocked unsafe state, failed context detach or an uncertain commit requires attention, not a guessed fallback account.

Python shuffles accounts and recommends visit length using rolling P90 cycle duration, a 20% buffer and 5-minute rounding constrained to 15–45 minutes. Java's current plan uses deterministic selected order for validation; preserve fairness and configurable budgets, not necessarily randomization. The user-facing recommendation can be restored after real cycle samples exist.

Python's close-all-recent-apps step is an implementation detail to retire. Close/release only the proven game context as needed; do not clear unrelated phone apps. Preview visits selected accounts once without claims/spending/dispatch; normal rotation repeats. No silent restart/replay after process death/reboot.

## 4. Baseline maintenance order and timing

These are **source defaults**, not real-time guarantees. Long workflows and account rotation make checks late. Keep separate due times per UID and feature; do not treat check cadence as feature duration or proof of completion.

| Order | Work | Python default gate / important distinction |
| --- | --- | --- |
| Critical boundary | Due shield activation, coverage audit and alert delivery | Priority sweeps at safe cycle boundaries, across all target accounts; not behind four ordinary visits. |
| 1 | VIP rewards | Daily completion, 15-minute check/retry while incomplete. |
| 2 | Hospital healing | Every 60 seconds; target 2-hour batches, not a troop-count batch. |
| 3 | Visible passive resources, build completions, alliance Help | Every minute. Wider construction-completion scan only every 24 hours. |
| 4 | Mail | Once per Malta game day after all relevant tabs are checked; incomplete retry 15 minutes. |
| 5 | Finished troop collection, then new training | Every cycle; at most 3 collections and 3 training iterations; capacity-full start retry 1 hour, collection still allowed. |
| 6 | Personal Wanted | Every 15 minutes: ally assists, own rewards, hero dispatch. Android currently has only own finished rewards. |
| 7 | Eight-hour chest | Availability check every 10 minutes, not a claim every 10 minutes. Android consuming path currently quarantined. |
| 8 | Construction, then research | Independently every 5 minutes. |
| 9 | Alliance Tech donations and Gifts | Hourly; attempts/gifts regenerate, so a daily-complete flag is wrong. Help also runs opportunistically. |
| 10 | Enabled Alliance Shop catalog | 6-hour fallback; 15-minute failure retry; schedule next actual reset when read successfully. |
| 11 | Danger Lurks Auto Team-Up | 12 hours after confirmed success; failed attempt retries in 15 minutes. |
| 12 | Own trade trucks | Every 2 minutes until verified daily trades exhausted; cooldown to next reset. |
| 13 | Manual radar events | Every 15 minutes, up to 4 events; first use of free marches before gathering. |
| 14 | Resource gathering | While usable marches remain; busy-state recheck roughly every 2 minutes. |

Daily baseline: **04:00 Europe/Malta**, with timezone/DST-aware period keys. Weekly shop limits must use the actual game's reset/remaining allowance, not an invented weekday. Refresh timestamps after long tasks. A waiting/full queue or no available reward is normal, not a failed action and not proof the feature is done forever.

Legacy Python **World-bounty hunting/plunder and truck plunder are disabled by default**. Do not enable them to claim parity. Personal Wanted remains enabled and is a different feature. The helper's explicitly selected Gaarix-only truck attack is a separate, newer capability, not permission to restore automatic legacy attacks in maintenance.

## 5. Maintenance feature contracts

Each subsection describes the intended behavior to preserve and the evidence required to declare migration complete. Stronger Android receipts are deliberate reliability improvements over optimistic Python logging.

### 5.1 VIP free rewards

Open VIP, inspect both daily login-points reward and Daily Freebies, claim each available free reward, dismiss only its recognized reward overlay and return to a known state. Record each category separately; daily completion requires both accounted for. Already claimed/cooldown is a valid no-work result.

**Never click paid Activate or a gift/shop offer as a substitute.** Existing Android implementation identifies `get_btn` as Activate, not a free claim. Acceptance: both free categories have independent claim/cooldown proof, repeat makes no extra claim, uncertain history blocks replay.

References: `bot/daily_rewards.py:do_vip_rewards`, `tests/test_daily_rewards.py`, Android `VipReader`/`VipPolicy`/`VipFeature`.

### 5.2 Alliance Help, Gifts and Tech donations

Keep three separate operations:

1. **Help teammates:** resolve available alliance requests, help a bounded set, confirm request/state changes; revisit as new requests arrive. This is not requesting help for one's own queue.
2. **Claim Gifts:** inspect Common/Rare categories and claim actual available gifts. Verify identity and depletion/claim receipt; partial category success must not mark all gifts complete. Gifts regenerate.
3. **Donate Tech:** open Alliance Techs, select the recommended eligible tech, read available attempts and permitted currency/cost, donate within attempts/budget, verify tech/attempt/currency changes. Stop at exhaustion or unverified cost; no premium fallback.

Use real menu row type/name/guild, not index 3/4. Current Android integration already corrected dynamic row readiness and performs native final-dispatch checks. Keep Help credit-cap ambiguity distinct from a real verified credit gain. Requesting help after construction/research/healing is separately verified even if the queue start already succeeded.

References: `bot/alliance.py:help_allies`, `do_hourly_action`, `tests/test_alliance_help.py`.

### 5.3 Mail rewards

Enumerate Report, Jungle, Alliance, System, Recharge and Favorite categories and all eligible attachment pages. Claim free available attachments under an explicit policy, confirm their exact claimed/reward transition, and track partial progress per tab. Daily completion requires coverage of all applicable tabs/pages, not an empty loaded cache or one successful Claim All.

Android currently has inspection-only coverage and no ordinary unclaimed sample; special `deal100` is excluded. Do not promote diagnostics into claiming, Read All or deletion. A visible UI header does not establish mailbox/server completeness.

References: `bot/alliance.py:claim_all_mail_rewards`, `docs/MAIL_COVERAGE_FINDINGS.md`, `tests/test_daily_rewards.py`.

### 5.4 Eight-hour chest

Inspect chest eligibility/version/next-ready time; claim once when proven ready, verify the reward plus cooldown/version transition. No guessed availability or success from disappearance alone. Resolve the existing Android uncertain attempt read-only before re-enabling this path; preserve it even through release upgrades. A timestamp that stayed unchanged does not authorize another claim.

References: chest block in `bot/scheduler.py`, current maintenance history and `CURRENT_HANDOFF.md`.

### 5.5 Passive base resources and construction completions

Inventory Python passive collection families: experience, food, electricity, Zent, wood, fuel and fuel variants. Resolve actual own buildings/production instances, not a generic actionable-looking bubble.

For resource collection, prove exact own building UUID, output item, currently collectible production amount/version and free action. Journal the production instance, tap its live control/verified projected target, then verify the exact production transition and resource receipt. An inventory counter, `isShow`, abbreviated amount or infinite production sentinel alone is not authority to collect. Existing Android base-resource work is inspection-only.

For finished buildings, accept completion and any recognized “Very Good” acknowledgement; verify the exact building's completion/level/state. Python checks visible markers every passive cycle and roams at most daily using paired outward/reverse swipes. Android should enumerate completion metadata where possible rather than reproduce drift-prone camera scans. Any necessary movement must derive from live scene geometry and leave a known view.

References: passive section of `bot/scheduler.py`, `docs/BASE_BUBBLE_NEXT.md`, `docs/SCENE_OBJECT_GEOMETRY_PLAN.md`.

### 5.6 Troop collection and highest-tier training

1. Inspect all three training-building families; collect every completed queue before attempting starts, even if the Military Center is full.
2. Verify exact queue/building/unit/quantity and the matching free-unit gain/queued-unit drop. Keep verified partial collections if a later queue fails.
3. For each eligible empty queue, resolve the **highest actually unlocked troop tier** using building/science/item requirements, runtime capacity and effective costs. Do not equate a template list with current eligibility.
4. Select the intended unit and allowed quantity, journal the spend, start at most the configured bound, then verify exact new queue/unit/quantity and matching debit.
5. Busy is normal. Full capacity suppresses new starts for about an hour but never suppresses completed collection. Shortage, unknown costs or lower-tier warning must not trigger diamonds, speedups or an accidental lower-tier start.

Android collection exists; training-start inspection is NOT this flow. Acceptance must cover three building families, multiple simultaneous completions, full capacity, resources missing, tier changes, stale/recycled UI and interruption after commit.

References: `bot/training.py`, `troop_training` config, `tests/test_troop_training.py`, Android `TrainingStartReader`/`TrainingStartPolicy`.

### 5.7 Healing

Enter World; inspect the lower-left Hospital/bandage shortcut and allow its transition to settle. First collect finished healing using any of the three troop-dependent completion variants. If healing is active, inspect it and request alliance help if available rather than starting again.

For wounded troops and a free hospital queue: read all troop types/tiers and sliders, select a nonzero batch, and adjust using the **actual Heal-button duration**. Default target **7200 seconds**, tolerance **300 seconds**, hard maximum **8100 seconds**, bounded to six legacy adjustment attempts. Heal everything if the available batch is shorter; do not manufacture a fixed troop count or insist on a two-hour minimum.

Before confirming, prove wounded counts, selected quantities, duration and costs. After committing, verify the exact healing queue/units/timer and request alliance help with its own receipt. Handle only recognized healing reward confirmations. Return to a known base state. No auto-speedup or premium spending.

References: `bot/healing.py`, `healing` config, `tests/test_healing.py`. This is not new troop training and must not reuse its queue identity.

### 5.8 Construction

Inspect the full builder list; game4 can have multiple available Build controls. Distinguish free builders from occupied rows and rentals. Resolve a recommended eligible own building/upgrade and its prerequisites/cost. Start permitted work only with a free actual builder; verify the building/level and assigned queue/timer, then request alliance help.

Resource shortage: legacy **Replenish All is enabled by default**, using owned inventory packs. Carry this capability forward as an explicit bounded per-account policy. Read the required deficit, pack item/quantity and expected conversion before consuming; verify pack/resource changes and then the actual upgrade. If insufficient inventory, unknown offer, rental or premium purchase appears, skip safely. Replenishment success alone is not a started construction.

Completion acknowledgement and new construction are separate tasks. Test mixed busy/free builder rows, several Build buttons, all busy, shortage/insufficient packs and a start that succeeds while Help fails.

References: `bot/construction.py`, `tests/test_builder_detection.py`, shortage/replenishment screenshot fixtures.

### 5.9 Research

Inspect the current research queue, recommended eligible tech, prerequisites and effective resource costs. If queue free and policy permits, start the exact tech and verify its new queue/timer/debit. Request alliance help separately and return to known base state. No research available/busy is normal; absent Help does not erase a verified research start or justify starting it again.

References: `bot/research.py`, `tests/test_reliability.py`.

### 5.10 Personal Wanted: three distinct operations

These are **not World-map bounty scanning** and are not troop-march radar events.

1. Ally tab: inspect remaining daily assist allowance, help an eligible exact ally mission, verify counter increases by one and its receipt.
2. Personal tab: claim own finished/unreceived missions; verify exact task UUID/config rewarded transition. Existing Android implementation covers only this part.
3. Personal dispatch: inspect a dispatchable mission/remaining counter and hero requirements, select available suitable heroes (legacy Quick Deploy), confirm Dispatch and verify exact mission status plus expected remaining-count change. If a GO task opens a World objective rather than hero selection, leave it alone; do not attack it.

No premium refresh, stealing or world plunder. Unloaded/hidden personal cache is deferred inspection, not proof of no rewards. Android source rotation now defers such inspections 15 minutes. Retain duplicate/uncertain-task barriers and empty-note/no-spam rules for unrelated sharing modes.

References: `bot/daily_rewards.py:do_personal_bounties`, `tests/test_daily_rewards.py`, current Wanted feature in Java.

### 5.11 Own trade trucks

This is daily **dispatch of our own trucks**, not the other-player finder.

Open the owned-truck UI, collect eligible returned trucks, read the real remaining daily trade count and exact truck IDs. For an available truck, inspect its grade and refresh using known available refresh tickets toward purple/orange; preserve an already high-grade truck. Legacy bound is 50 refreshes. Stop safely on exhausted/unknown ticket costs, premium prompts or unconfirmed grade rather than dispatching a lower grade as a substitute.

Dispatch the exact approved owned truck and verify its in-transit state plus trade-counter change. When zero trades remain, persist cooldown until next 04:00 Malta reset. Unknown counter is not “two trades left” even though a legacy fallback setting exists. Do not copy Python's first-refresh unreadable-ticket exception into Java.

References: `bot/trucks.py:do_trucks`, `_refresh_truck_until_target`, persisted `trucks_state.json`, counter tests.

### 5.12 Gathering and manual radar

Share a fresh account-scoped march-capacity reader and healthy trained troop availability. Positive selected “Troop Capacity” is mandatory before dispatch. Never guess a free march from an absent sidebar/cache. Honor the shield/protection policy before any manual march.

**Radar first:** inspect exact daily radar event IDs/kinds, including human-head/NPC-HQ and pickaxe/resource contest events across colors. Navigate the permitted event, select its actual target, confirm allowed Attack/March with nonzero healthy troops, then verify the new march identity/destination and event-state transition. At most four events per check. Generic all-attack permission is forbidden; introduce a scoped radar capability without weakening truck/bounty guards.

**Gathering second:** use remaining march slots, search permitted resource types/levels, select a verified available node and troops, dispatch and verify exact march/node plus used-slot change. Python's current Food/Wood/Zent weights are **50/50/0** (Zent is therefore not selected by that default); retain configurable resource preference/level rather than its search swipes. Stop when all slots are proven busy; recheck later.

References: `bot/radar.py:process_radar_events`, `bot/gathering.py`, `tests/test_radar_events.py`, troop-capacity/counter tests. Trace actual callers before treating any older `do_radar` helper as another scheduled feature.

### 5.13 Danger Lurks / Boomer Auto Team-Up

From HQ/base, open Event Center, find **Danger Lurks** through its scrollable carousel, resolve Auto Team-Up (green or yellow), then Activate. Wait for readiness rather than treating the first missing control as permanent absence. Verify enabled/expiry state; only then set the 12-hour due time. Failed activation retries in 15 minutes, not 12 hours. Return to base.

**Auto Team-Up does not break shields. Do not disable or block it under shield protection.** This is separate from initiating a manual attack/march.

References: `bot/events.py`, `boomer_auto_join` config, `tests/test_reliability.py`.

### 5.14 Alliance Shop purchasing

Use a per-item enabled catalog, actual item IDs/durations, live remaining weekly allowance, currency/price and inventory. The shop scrolls: select by semantic item identity and live controls, never fixed slot coordinates. Opening an artwork tooltip is not opening a purchase dialog.

Default enabled purchases: **Badge: 10 bundles/week; 24h Peace Shield: 1/week; 8h Peace Shield: 3/week**, capped by the game's actual remaining allowance, stock and balance. Badge bundle contents and bundle count are different units. Quantity selector may use slider or plus, but read back the exact quantity and total cost before Buy. Verify exact reward/item/quantity plus inventory/currency outcome; sold out is satisfied/skipped, not a new purchase. Unknown result keeps an unresolved attempt, not weekly completion.

Retain disabled catalog choices: Alliance Advanced Supply Chest, Miranda Fragment, Prime Recruitment Ticket, Katrina Fragment, Modification Blueprint, relocation item, Advanced Teleporter, Alliance Teleporter, Rename Card, 1-hr Speedup Choice Box and resource chest. The two unnamed entries remain disabled until their actual identities are resolved. Runtime shop may differ; do not invent item IDs from these display names.

Purchasing a shield **never activates it**. Legacy separate badges/shields wrappers are superseded by the catalog; port one implementation, not three competing scheduled buyers.

References: `bot/shop.py`, catalog in `main_scrcpy.py`, [ALLIANCE_SHOP.md](ALLIANCE_SHOP.md), `tests/test_alliance_shop.py`.

## 6. Critical shield service: not an optional happy-path task

### Schedule and coverage

- All explicitly enrolled equivalents of the legacy four farm accounts: **Friday 23:00 Europe/Malta, 24-hour shield; Saturday 21:00 Europe/Malta, 8-hour shield**.
- A safe-boundary due sweep visits all target accounts promptly; it must not wait through four 20-minute visits. Resolve the UID mapping first, never assume all discovered clones are targets.
- Friday startup catch-up is bounded to Saturday 03:30; Saturday catch-up is one hour. Saturday renewal runs even without a verified Friday manifest. Dated one-off overrides/account subsets exist and must not accidentally become weekly schedules.
- Weekly operation IDs survive process death/update/restart and prevent repeat consumption. Recheck live protection before applying an overdue operation; do not blindly replay a stale Use.
- Source arming/calibration/schedule switches default off and external deployment may override them. Do not transfer “armed” into Java automatically; separately validate and explicitly enable it.

### Exact activation workflow per account

1. Verify selected UID, active protection expiry and inventory of the requested duration. Legacy path: World -> own HQ -> Buff -> Peace Shield. Warehouse is an alternative user-described path, not a reason to implement two unverified activators.
2. Save **before-inventory screenshot** and exact owned count. If existing protection already covers the requested duration, prove coverage and do not waste an item.
3. Validate ordinary **Use** for the exact owned 24h/8h item. Reject Purchase & Use, diamonds, unknown ownership and wrong HQ. Persist an operation fence **before** Use.
4. Handle only a recognized replacement confirmation for that same requested shield. Replacement is not duration stacking. Friday 24h and scheduled Saturday 8h may replace shorter protection to extend it; never shorten already sufficient protection. Legacy near-expiry renewal has a conservative lead-time rule distinct from scheduled extension.
5. Save **after-inventory screenshot**; require exactly one item consumed. Save a third **shield-timer screenshot**, with fresh duration/expiry consistent with that exact operation. A clicked Use, missing popup or changed countdown alone is insufficient.
6. Record verified protection and queue the Discord report, or record NOT VERIFIED/manual attention with immutable evidence. Never retry uncertain Use; reconcile read-only using the original before count and consistent fresh timers.

### Alerts and evidence delivery

Per account, group the three ordered images (before, after, timer) into one report with UID/label, requested duration, operation ID, Malta timestamp/expiry and verification result. Use the existing **last-z-treasure** dedicated webhook configuration, not an arbitrary channel-name fallback. Credentials remain private; no URLs/tokens in source/docs/diagnostic logs.

Persist report delivery separately from gameplay. Require message/attachment acknowledgement; retry **delivery only**, never another activation. Lost acknowledgement may yield duplicate reports with the same operation ID, not duplicate shields.

Keep the independently scheduled coverage monitor even when activation failed or its catch-up window ended:

- Default live timer audit every 15 minutes per account, including overdue/missing accounts.
- Warnings at 60, 30 and 10 minutes, expiry and unknown protection.
- After Saturday 21:10, warn if coverage through Sunday 04:00 Malta is unverified.
- Monitor through Sunday 06:00, with queued delivery retries continuing afterward. This overnight extension is required; “Saturday only” must not silently stop at midnight.
- Blocked renewal gets urgent notice. Four-account summary says ALL FOUR VERIFIED only when every target is verified; otherwise enumerate missing accounts after the ten-minute grace period and follow up after recovery.
- Persist alert outbox, incident/dedup keys and backoff (legacy 60 seconds to 15 minutes; at most two notices per sweep). Cancel obsolete pending warnings after verified recovery without inventing delivery receipts.

While protection/uncertain Use requires the gate, suppress new manual radar, gathering and legacy plunder actions according to policy. Do not generalize that into disabling Auto Team-Up. Keep queue maintenance, Help, Gifts and other proven non-breaking actions independent.

Android background scheduling must report delays/unavailable accounts honestly under lock, reboot, Doze, battery restrictions or game focus loss. No phone-only process can notify while the phone is off/networkless; an independent heartbeat/dead-man monitor is needed for outage detection. Never promise protection from an alarm registration alone. Exact DST/event-end assumptions require explicit tests/operator confirmation.

References: `bot/shields.py`, `shield_ui.py`, `shield_health.py`, [SHIELDS.md](SHIELDS.md), `tests/test_shields.py`, `tests/test_shield_health.py`.

## 7. Foundation, persistence and operational parity

### Execution and UI contracts

Use Android APIs for application lifecycle/registered intents, foreground ownership, service/overlay, durable storage, notifications and ordinary input where supported. A Java rewrite does not imply all Unity game controls are native accessibility nodes; the current helper uses read-only metadata, exported live Unity geometry and guarded input. Preserve that verified adapter rather than inventing undocumented game APIs.

Keep readers, pure decision policies, workflows, scheduler, input guards and receipts separate. Every input must recheck foreground process/start/UID, expected scene/panel, semantic target, visible/interactable bounds and current operation arguments. Coordinates must come from fresh UI geometry/camera projection. Handle virtualized rows and live field locations; cache verified field LOCATIONS with validation, never stale account/queue/reward values. Keep callbacks bounded so safety guards do not freeze game rendering.

Known reward/confirmation dialogs may be handled in the exact feature context. Do not port a global “Confirm anything similar” clicker. Unknown modal/login-on-another-device/changed build/account/focus stops safely. Recovery is bounded, preserves receipts and must not silently choose another account or unlock/bypass device credentials.

### Durable data to retain or explicitly map

| Data | Migration rule |
| --- | --- |
| Python slot preferences, status periods, due checks and `trucks_state.json` | Export/inspect from actual configured data root; map slots to verified UID explicitly. Some Python checks are memory-only, others stored in action status: audit each, do not claim all cooldowns already survive restart. |
| Python shield manifests, operation fences, last verified expiries, evidence and alert/report outboxes | Preserve operation identity/uncertainty; transfer or reconcile before enabling native shields. Never reset to “not attempted.” |
| Helper settings XML and private JSON | Preserve signing key, app data and schema across update-install; compare before/after hashes at idle. No uninstall/clear-data release procedure. |
| Helper share/attack ledgers and destination checkpoints | Retain existing keys and unresolved attempts. Filter/destination changes do not reset duplicate history. |
| `maintenance-state.json`, per-UID due/attempt records | Keep verified partial results and unresolved barriers. Use the actual source-defined filenames/schema when importing/exporting. |
| Rotation profiles/progress/selection | Explicit enrollment and feature choices; new profiles unselected. Verify helper app UID can read/write root-created files privately. |
| `dead-states.json` | Preserve definitive permanent evidence across accounts/runs; never seed it with synthetic test states. |
| Secrets | Use private configuration/provisioning, never Git, screenshots of env files, logs or public portfolio artifacts. |

Python runtime uses configurable `LASTZ_DATA_DIR` and external environment setup; do not copy a repository folder and assume it contains production state. An inaccessible credential-encrypted directory after reboot is not an empty database.

Persist a versioned pre-commit attempt before any non-idempotent claim/spend/dispatch/post/Use, then independently verify the result. Keep completed, nothing-to-do, waiting, blocked, failed, cancelled-before-input and uncertain distinctions. Preserve a successful earlier action if later cleanup/help fails. On explicit Resume after interruption, reconcile unresolved operations read-only; never replay them just because a timeout occurred.

### Scheduling and observability

Use monotonic time for elapsed budgets and zone-aware wall time for calendar obligations. Test reset boundaries, DST, missed windows, clock changes, device suspension and restart. Prioritize overdue protection without interrupting an in-flight commit; make inability to reach an account visible.

Expose per UID: current task, last verified result/reason, next due, unresolved operation, running/idle/stopped/needs-attention, last real progress and evidence links. Log exact target IDs and before/after values, bounded counters and durations. Distinguish unique targets from repeated observations and explain eligibility rejection; thousands of scans with zero shares is not a success metric by itself.

Bound log/screenshot storage, minimize input payloads/account-private text, and make tracing opt-in except required shield evidence. External log delivery must have timeouts/backoff and must not block gameplay. Host launchd/Ansible/Git-pull-on-start logic is not gameplay to port: replace it with signed APK distribution/update checks and an explicit Android lifecycle. Process restart must not silently resume a risky job. Existing SSH/scrcpy/pause tools may remain development conveniences.

## 8. Preserve the helper's separate truck and World-bounty modes

These supplement, not replace, maintenance parity. The old standalone Go scanner's sound-and-stop behavior is not the authority for current helper sharing/combat policy.

### Trucks

- Preserve one destination selector (**Trucks group / World Chat**) shared with bounties, separate Share 2+, Share 3+, cargo-combo and explicit Attack controls.
- Yellow/purple only; count current orange-fragment reward icons/slots, not a guessed aggregate quantity. Combine current base/extra cargo.
- Cargo OR rules: 4+ Lv.3 module icons; OR 1+ orange + 3 module icons; OR 2+ orange + 2 module icons; OR 3+ orange. Item `253102` with raw quantity 2 counts as **one module icon**, not two.
- Group sharing uses strict configured power limit (default below 440M); World sharing accepts any known power. Skip-state setting applies to World only. Main may post to its own group.
- Always ensure **Hide trucks of this state** enabled in every truck mode, including preview; wait for readiness, verify native/manager agreement, never blindly toggle an already enabled control.
- Truck sharing goes directly through the initial **big blue Share** control and the verified destination. No Plunder/goBtn/map detour, attacks, extra chat text or added note in sharing modes.
- Persist per-destination UUID fences before send; match exact room/sender/target and a new server receipt. Do not resend pending/uncertain entries or clear history when filters change.
- Explicit attack is separate, only on exact Gaarix UID in the authorized attack mode, 3+ orange below configured limit, never preview. Keep formation/defender checks, attack ledger and verified victory/defeat return. Sharing modes must never acquire that capability.

### World-map bounty finder

- Separate manual range runner, selected states/destination and resumable destination-specific checkpoints. Not personal Wanted, not legacy disabled Python world plunder.
- Preserve approved zoom/LOD and camera-derived movement, exact object UUID/coordinates and currently completed available 12/15-box eligibility; skip exhausted/unfinished entries.
- Share native bounty tile to verified World or pinned Gaarix-owned trucks group, with empty note and exact server receipt. **No bounty plunder.** Qualifying-send coverage remains evidence-dependent; do not call a dry preview a live verified post.
- Definitive freshly observed “The State you are searching for does not exist.” is persisted immediately as permanently dead and skipped across accounts/future runs. Temporary unavailable/network/timeouts are not permanent evidence. Clear stale notices before associating a new error with a submitted state.
- Hidden/offscreen/recycled controls and uncertain navigation fail safely. Do not reintroduce fixed-coordinate or template selectors removed from the helper.

References: `tools/last-z-helper/`, [TRUCK_CARGO_FILTERS.md](TRUCK_CARGO_FILTERS.md), [TRUCK_HIDE_STATE.md](TRUCK_HIDE_STATE.md), [TRUCK_WORLD_RECOVERY.md](TRUCK_WORLD_RECOVERY.md), [DEAD_STATES.md](DEAD_STATES.md), [BOUNTY_PERFORMANCE.md](BOUNTY_PERFORMANCE.md).

## 9. Concrete remaining delivery order

Do not expand every feature into another inspection-only button. Finish one bounded production slice with its receipt, then enroll it in rotation.

1. **Stabilize/release the existing rotation:** inspect post-reboot health/state, minimal one-feature preview, complete two-account preview, same-key update-install, app-UID file access, floating startup/reopen/permissions, persisted selections and STOP during loading/switching/waiting. No unattended run just to prove installation.
2. **Finish safe claims:** current passive resource slice when exact action/amount/version are provable; Mail only with real attachment coverage; chest only after uncertainty reconciliation. Close remaining Rare Gifts/Help receipt gaps.
3. **Training starts:** highest-tier/capacity/effective-cost and queue/debit proof, reusing completed collection. Do not bundle healing/upgrade spending into this slice.
4. **Healing, research and construction:** each separately; shared alliance-help request component, inventory-pack replenishment policy, busy/full/shortage outcomes.
5. **Personal Wanted dispatch and ally assist, donations and Auto Team-Up:** separate permissions, mission/attempt/expiry receipts.
6. **Own-truck dispatch, gathering and each radar event kind:** exact ticket/march/capacity policies, radar-before-gathering, shield gate, no broadened combat bypass.
7. **Shop, shield activation and scheduled multi-account protection:** purchase allowlists first, then controlled activation/replacement proof, independent health/outbox/alerts, restart and missed-window testing before arming unattended protection.
8. **End-to-end cutover:** selected accounts run all enabled proven maintenance features through repeated visits and a game reset; validate weekly/reset/shield logic with controlled clock fixtures and separately approved real operations. Keep truck/bounty tools exclusive. Disable the old Python controller on that phone before native production use, preserve rollback state, and never run both to compare outputs live.

A user may prioritize critical protection earlier, but it still requires the same receipts and account rotation guarantees. This order is not authorization to weaken safety or perform an unapproved consuming live test.

## 10. Definition of done and validation checklist

For **every feature**, the other chat must record: source entry points; enabled/default policy; exact observed fields and controls; costs/capacity; before/after receipt; durable key; due/reset rule; remaining unknowns; source/build/installed versions; and evidence of:

- One permitted successful live action on the selected account plus a no-work/repeat check.
- Busy/exhausted/full/insufficient resources and unknown/changed costs.
- Wrong UID, changed process/start, focus loss, stale/recycled target and unexpected modal rejected before commit.
- STOP before input, between features, during waits/switches and after an in-flight commit; no later restart or extra action.
- Interrupted/uncertain commit survives restart and is not repeated; earlier verified partial results retained.
- Isolated fixtures do not modify real production history. Preview does not consume/post/dispatch; any explicit setting-only exception is documented.
- Same-key install preserves settings, enrollment, receipts, unresolved history and checkpoints. Installed UI/service entry points are tested, not only diagnostic classes.

Use Python's tests as behavior regressions and the helper's `validate.ps1`/`build.ps1` suites for implementation checks; assertions/mocks cannot substitute for missing live coverage. Keep the current phone checkpoint in `CURRENT_HANDOFF.md`; update this parity checklist as features actually graduate. Do not delete Python until every desired row is verified or explicitly deferred by the user.

### Final product in one sentence

**A user-started, on-phone Last Z assistant that continuously rotates verified selected accounts, collects free rewards and finished queues, develops/heals/trains them within configured limits, assists the alliance, manages personal missions and permitted marches/trade trucks, buys selected weekly supplies, and provides verified scheduled weekend shield protection with evidence/alerts—while keeping explicit truck/bounty sharing tools separate, preserving state across updates, and stopping safely whenever identity, cost or outcome is uncertain.**
