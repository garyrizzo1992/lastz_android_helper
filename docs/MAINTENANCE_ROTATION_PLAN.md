# Maintenance rotation and immediate floating controls

## Current release checkpoint (supersedes older status below)

2026-10-30: signed 0.38 installed; minimal VIP and full two-account/five-feature preview passed with no claims or reboot. Wanted nonmodal message-banner recognition fixed with exact prefab/modal-stack guards and ten regression checks; full validation passed. Launcher/reopen, real app-UID profile read/write/persistence, collapsed STOP, overlay denial/return/restoration verified. Twelve data files survived installation unchanged. UI tests added only rotationMinutes=20/rotationPreview=true to old preferences; all five accounts restored unselected. Python stopped and helper idle by explicit user choice. Read the newest CURRENT_HANDOFF.md block and runtime/helper-build/rotation038-mac-evidence/ for limits/evidence. Hidden Wanted remains deferred, not a completed inspection. Repeated/live consuming rounds and full Python parity are not newly verified.


Updated 2026-10-30. Status: rotation implemented in source; 0.38 candidate being packaged, NOT installed. Installed release remains 0.37. Read-only setup opened and identified all five games. Full task-round verification was interrupted by an unexpected phone reboot; no unattended rotation is running.

## Implementation checkpoint

- Startup/grouped UI: implemented. MainActivity opens the floating panel on resume, including reopening the helper; no job starts automatically. Starting rotation from configuration restores its collapsed floating STOP bar.
- Account discovery: VERIFIED on phone. Android shortcut export supplies distinct clone launch IDs 0–4; process maps independently prove the clone, and game/chat player metadata supplies the UID. All five profiles were enrolled unselected in app-private `rotation-profiles.json`.
- Serial rotation: implemented in RotationController; one global control.lock across launches, task visits and waits; old input scope must detach before the next launch. Exact selected UID is required before game input. Soft visit limit defaults to 20 minutes, early yield when no task is due, waits for earliest due task, and continuous repetition until STOP. No automatic restart after process death/reboot. Existing individual task commits retain their own receipts/barriers.
- Tasks/UI: VIP, Help, Gifts, completed troop collection and Wanted claims grouped under Maintenance rotation with per-account checklists. Pending Python migrations remain pending; scanners/combat/chest excluded. Setup is inspection-only; preview inspects one round without claims.
- Existing feature fixes found by integration: Help/Gifts resolve actual menu rows by type/name/guild with a bounded readiness wait, not fixed row indices. Native dispatch rechecks the semantic row and guild. Hidden Wanted with unloaded/empty cache defers inspection for 15 minutes; it never reports complete/no rewards from absent evidence. Other unknown/blocked/failed/uncertain outcomes stop rotation.
- Tests: full validation passes including 19 rotation policy cases, 13 native menu guard cases, rolling UTF-8 log retention and existing suites. Android profile/shortcut fixture originally passed 19 checks; final fixture adds 3 deferred-Wanted checks. Live isolated tests verified unresolved history blocks BEFORE launch, STOP during waiting, and wrong UID rejection BEFORE instrumentation (nonexistent injector/agent supplied). Two-account full task preview is NOT yet verified.
- Live preview evidence: first bot passed VIP, Help, Gifts and one completed troop's geometry inspection with zero claims. Initial transient Help-menu failure was fixed and verified. Hidden-Wanted scheduling change was added afterward; next full preview died with shell exit 255 during VIP, coinciding with phone reboot. No successful final round is claimed.

Five discovered profiles: Last Z+ / trucks by garix / 2059765822000064; Last Z1+ / yn gaarix / 2059770776000064; Last Z2+ / baby gaarix / 2059744163000064; Last Z3+ / Dassy / 1850977487000064; Last Z4+ / Garix922 / 1430578113000153. These are observations, not permission to auto-select them.

### Immediate next steps after the phone is available

Phone reports user 0 RUNNING_LOCKED after reboot; credential-encrypted helper files cannot currently be inspected. Do NOT interpret inaccessible CE files as data deletion or initialize replacement state. No install while settings/history preservation cannot be verified. Reboot reason reports `reboot`; no pstore or system_server_watchdog evidence was found, so cause is UNKNOWN. No reboot command was issued by this implementation/test.

After unlock, first inspect device health and preserved helper state. Investigate the reboot before repeating full instrumentation. Retest minimally (one bot/one preview task), then a full two-account preview, including final dynamic-menu guards and Wanted deferral. Verify the live UI, startup overlay/reopening and STOP. Only then consider installing the signed 0.38 candidate at an idle boundary with before/after settings/history hashes. Do not start unattended rotation or automatically select accounts. Keep this file and CURRENT_HANDOFF.md current.

## Requested behavior

**User clarification: reproduce the Python bot's automatic game-to-game loop.** The delivered Run maintenance rotation action must open the first selected game/clone, verify its character, run that account's enabled bot features for its visit, switch to the next selected game, and repeat the account list continuously until STOP. The user must not manually open each account or press Run between accounts. The single-account phase below is an implementation milestone, not the final product or a replacement for automatic switching.

Concrete flow: Run rotation -> open game A -> verify A -> run A's enabled maintenance cycle(s) -> close/release A's worker -> open game B -> verify B -> run B's cycle(s) -> remaining games -> back to A. Like Python, use a configurable per-game visit window (initial default 20 minutes), checking due tasks during the visit; yield early when nothing is due rather than repeatedly claiming or polling. Close only the relevant game when required by proven launch behavior, not unrelated phone apps. Preserve per-account cooldowns and receipts across visits.

Opening Last Z Helper immediately opens its expanded floating controls and backgrounds the activity. Android overlay permission is the only first-use prerequisite. Showing controls never starts automation. This means opening the helper, not silently launching it whenever any game opens or the phone boots.

Keep truck scanning/sharing/attack and world-map bounty finding as separate manual modes. Group every other production feature into **Maintenance rotation**, with per-account feature selection. Rotate the selected game accounts as the Python bot does. Inspection tools remain diagnostics, not rotation actions.

This request authorizes implementing account rotation and its setup/preview tests; it supersedes the older migration plan's decision to defer rotation. Existing manual modes continue to pin the active account and stop on changes. Only explicit rotation/setup tests may switch enrolled/registered games at a safe boundary. No account fallback is permitted.

## Current code and reuse

- `MainActivity` previously required pressing Show floating controls. Its new `openFloating()` on-resume path shows the existing service panel without saving/revalidating settings or launching a worker. Permission-return handling survives activity recreation. Manual Show still saves edits. Installed release remains 0.37 until a separately verified build/install.
- `HelperService` owns overlay/STOP; `JobRunner` now routes maintenance-enroll and maintenance-rotation to the new RotationController. Other existing modes retain their controllers.
- `MaintenanceRunner` serializes features with priority and enabled/due checks, records outcomes, and stops on uncertainty. `MaintenanceStore` and `MaintenanceSchedule` already supply per-UID history, unresolved-operation gates and reset/retry rules. Audit their actual semantics before using them for a loop; single-feature entry points currently bypass enabled/due selection deliberately.
- `MaintenanceController` currently runs one feature against one pinned active account under the shared controller lock. Reuse features, not multiple competing controller processes. A context cannot survive switching accounts: close it and its instrumentation before creating the next context.
- Python references: `main_scrcpy.py` outer loop around lines 1628–1715; `bot/scheduler.py`; `tests/test_rotation_timing.py`. Python shuffles configured slots, launches each, runs cycles within a configured 20-minute visit budget, and closes apps between visits. Its timing recommendation uses recent P90 cycle time plus buffer. Carry forward task scheduling and fairness; do not copy fixed launch coordinates, close-all-apps behavior or assume slot names identify characters.

## Feature enrollment

| Feature | Rotation v1 |
| --- | --- |
| VIP free rewards | Available; use claim/cooldown proof and per-UID due state. |
| Alliance Help | Available; bounded checks, retain cap-related limitations. |
| Alliance Gifts | Available; recheck regenerating gifts; Rare live-claim coverage still pending. |
| Collect finished troops | Available; collection only, no new training. |
| Collect finished Wanted rewards | Available; own rewards only, no dispatch/assist. |
| Mail, passive resources, training starts, healing and other pending Python migrations | Show as pending in the plan; enroll only after a separately verified production feature exists. |
| Eight-hour chest | Quarantined UNCERTAIN; excluded until reconciled and fixed. Never reset its history to enable rotation. |
| Trucks and World-map bounty finder | Excluded; retain dedicated manual controls, destination selector and histories. |

Future production maintenance features join the same registry with capability, priority, due-time policy, bounded execution and outcome receipt. No separate top-level action is needed for each feature; keep manual run/preview in a diagnostics/details section.

## Delivery phases

### 0. Finish floating startup

Build signed next release and install only after proving no controller is running. Preserve signing key and all settings/ledger files. Verify launcher -> expanded overlay, reopening, activity recreation, overlay permission denied/granted, busy-job behavior and STOP. A denied permission leaves an actionable helper screen; returning with permission opens the panel. No worker starts and no game/account changes. Source implementation is ready; live checks/install are pending.

### 1. One-account maintenance cycle

Create a production feature registry for the five available features above. Add one Maintenance rotation control, a feature checklist and Run one pass/Preview options. Initially support current account only. Resolve UID before reading its configuration; keep existing account/focus guards for every input. Call the serial runner with enabled/due policy, not five independent JobRunner launches.

Audit/fill nextDue values for each outcome: verified completion, no work, cooldown, blocked and transient failure. Alliance Help/Gifts must be revisited, not marked permanently complete for the day. Preserve verified partial results. Persist cursor and feature results atomically per UID. A feature time budget only yields at safe points; it never cancels an input/commit halfway through. Unknown UI, identity changes and uncertain commits stop the rotation in v1. No blind retry or automatic dismissal of unknown dialogs.

Exit: one bot completes a selected pass, repeat skips not-due tasks, preview sends no input, STOP works during a feature and between features, existing ledgers remain intact.

### 2. Account profiles and launcher discovery

Add explicit enrollment of the currently open character: UID, display name, state, verified host package/clone identity and last-observed launch target. Labels are cosmetic. Store profiles and per-account feature flags in a versioned private JSON file, separate from gameplay receipts. No Google credentials/passwords in profiles.

Discover how this phone's Parallel Space instances can be opened distinctly. Prefer stable Android component/intent identities; if its picker is necessary, resolve current native UI nodes/bounds. Never use clone-list indices, cached coordinates, OCR or package name alone as proof of character identity. After a launch wait for the game's real UID and compare exactly with the selected profile BEFORE instrumentation/game input. If deterministic selection is unavailable, keep rotation blocked or offer manual handoff; do not guess a clone. No fallback to main or another device.

Exit: read-only discovery documents launch mapping; deliberately wrong UID fails before action. Unknown or changed profile mapping blocks. Main is neither automatically enrolled nor prohibited: only explicitly selected profiles can be visited.

### 3. Multi-account coordinator

Build one rotation coordinator: IDLE -> VALIDATE -> VISIT_ACCOUNT -> RUN_DUE_FEATURES -> CHECKPOINT -> RELEASE_CONTEXT -> SWITCH_ACCOUNT -> VERIFY_UID -> next visit; also WAITING, STOPPED and NEEDS_ATTENTION states. Switching is permitted only after all pending input/native requests finish, the current context/instrumentation closes, and commits have verified outcomes. Preserve one ownership lease across the rotation, refactoring child lock acquisition as needed; never release a gap for another controller or start nested conflicting locks.

Use selected profile order initially for reproducible behavior. Round-robin fairness; configurable soft maximum visit duration, provisionally 20 minutes to match Python. Advance sooner if no due work remains. Finish a bounded in-flight action before leaving. Sleep until the earliest due task when all accounts are idle; no tight UI/memory polling. Use monotonic time for elapsed budgets and verified wall/reset timestamps for due records. Adaptive P90 timing is optional after real samples, not a prerequisite.

Persist rotation selection, profile/feature cursor, last result, next due, run generation and explicit stopped state. A process death must not silently resume or replay an unresolved operation; on explicit Resume, inspect/reconcile read-only first. STOP prevents any later switch/restart and cancels waiting promptly. Manual account changes pause/stop rather than trying to switch back. A switch timeout or lost connection reports NEEDS_ATTENTION without choosing a fallback.

Exit: two enrolled bots complete repeated passes with exact UID joins and separate histories. Stop during waiting/loading/after claim prevents further input or switching. No due work sleeps. Interrupted claims preserve uncertainty. No duplicate claims from restart. No Python/helper overlap.

### 4. Consolidate controls and release

Top-level controls: Trucks, Bounties, Maintenance rotation, STOP. Maintenance contains selected accounts, feature checklists, current/next account, current task, due times, last verified outcome and pause/resume. Retain sharing destination only for truck/bounty use. Put individual maintenance actions and previews behind Details/Diagnostics until rotation validation is complete, then remove redundant top-level buttons.

Run appropriate pure scheduler/state-machine tests, storage schema/restart fixtures and targeted device tests. Cover one account unavailable, wrong UID, stale launch target, due/reset transitions, interrupted commit, process death, lock conflict, unknown modal, STOP and settings preservation. Device tests need enrolled bots, not an inferred account. Build/install at an idle boundary, record version, hashes and evidence in CURRENT_HANDOFF.md. Starting an unattended rotation is a separate explicit Run action.

## Next implementation checkpoint

1. Finish phase 0 packaging/live verification without starting a scan.
2. Implement phase 1 registry and one-pass controller before touching clone switching.
3. Capture read-only evidence for phase 2 launch mapping; this is the main unknown and blocks reliable multi-account rotation, not the existing maintenance features.

Update this file's phase status and CURRENT_HANDOFF.md after each meaningful milestone. Do not describe the rotation as implemented or installed while it is still a plan.
