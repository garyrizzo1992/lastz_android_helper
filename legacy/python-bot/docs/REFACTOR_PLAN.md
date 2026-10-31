# Reliability and incremental refactor

## Baseline: 2026-10-09

- Local and Mac deployment initially at `477cd0a`.
- Mac LaunchAgent running, PID 7284 at inspection; local runtime logs advancing.
- Full baseline suite: 102 tests, 100 passed, one failure and one error.
- Existing training test error: mock lacks `_troop_unit_cap_reached`.
- Existing training test failure: expects one visual button scan, although the
  implementation scans both green and blue controls.
- Recent game 3 logs confirm builder queue navigation. No free green Build
  action was available; training was deferred at 7820/7820 unit capacity.
  These are blocked/unavailable states, not proof of broken workflows.
- Recent logs also show base recovery and account cycles progressing. This
  inspection is not a live verification of every feature or every account.

## Execution checklist

- [x] Record revision, service state, baseline test results and current logs.
- [x] Remove proven dead bounty counter helpers, unused tracing wrapper,
  obsolete configuration and unused local/state bindings.
- [x] Repair stale training test fixtures in a separate commit. Mock the
  capacity check and assert both colour scans, actual taps and collection status.
- [x] Repair highest-unlocked-tier training and reject lower-tier warnings.
- [x] Repair manual radar blue March detection and add dispatch-state regression tests.
- [x] Align shop scheduling with observed game weekly reset, with bounded fallback.
- [x] Reconcile Boomer timing with its 12-hour activation period.
- [x] Investigate remaining navigation failures and test USB outage recovery.
- [x] Standardize completed/nothing-to-do/blocked/failed workflow results.
- [x] Add per-account outcome summaries, retries and failure evidence.
- [x] Extract construction first, preserving the existing entry point.
- [x] Extract Android control, detection/navigation, remaining workflows,
  scheduler and logging in independently tested commits.
- [x] Add sanitized screenshot regression fixtures and multi-account validation.

## Field verification and limits

Implementation covers all planned phases. Live success is recorded separately
from game conditions that prevent an action; this checklist is not a claim
that every account performed every action during validation.

| Feature | Evidence on the connected Mac Android |
| --- | --- |
| Navigation | Stable base recovery on all four games during exclusive tests. |
| Training | Game 1 showed an active tier VIII queue; games 2, 3 and 4 refused training at unit cap. Game 2's short-lived toast now has its own detector and passed a repeated live test; game 3 correctly stopped before tapping Train at 7820/7820. |
| Construction | Game 4's Get More screen is recognized visually. Replenish All reveals that inventory is insufficient; cancel without consuming packs. No success unless help handshake or reduced free-worker count confirms a start. |
| Boomer | Game 4 yellow Auto Team-Up and Activate confirmed enabled for 12 hours, then returned to base. |
| Shop | Game 2 badges and both shield types are already sold out for the week. New purchase success cannot be live-tested until stock resets. |
| Manual radar | Game 4 had no dispatchable events. Blue March and post-dispatch validation are covered by workflow and screenshot tests; a new live dispatch remains opportunity-dependent. |
| Healing | Mac logs contain a confirmed Game 1 batch and alliance-help handshake. The restarted deployment accepted its completion; recording completion as success rather than overwriting it with nothing-to-do now has a regression test. |
| USB recovery | Disconnect, bounded timeout, exponential retry and reconnect are tested with mocked transport; the working phone was not physically disconnected. |

Cross-platform CI runs the full suite on Linux, macOS and Windows. Mac deployment
also runs the suite before stopping the service. See ARCHITECTURE.md for module
ownership, compatibility boundaries and the exclusive live-validation command.

Final pre-deployment regression runs: 129 passing tests on Windows; 129 run on
the Mac candidate, passing with two deployment-template tests skipped because
its runtime environment lacks test-only Jinja2/PyYAML. Deployment CI installs
those dependencies and runs the full suite. The entry point is reduced from
10,234 lines to 1,636; workflows remain available through compatibility exports.

All three CI platforms subsequently passed. The first deployment exposed tracked
Python bytecode as a dirty-checkout blocker. Preserve the Mac's generated-file
change in a named Git stash, stop tracking the three `.pyc` artifacts (retain
local copies), and redeploy. `.gitignore` already excludes future bytecode.

Deployment at `2829a2e` succeeded; the Mac service resumed with connected ADB and
fresh Game 1 cycle logs. Post-deployment completion-status regression brings the
local suite to 130 tests. All changes are committed and delivered through the
normal GitHub deployment workflow, not by editing the production checkout.

## Safety and verification

Do not delete helpers solely because static references are absent: helper
registration and logging callbacks use dynamic dispatch. Preserve disabled
configurable world-bounty/truck features. Leave unrelated working-tree changes
alone, including the pre-existing tracked bytecode change.

Keep cleanup, test repairs, behaviour fixes and module extraction in separate
commits. Run relevant tests before pushing. A successful test suite is not proof
of a live game outcome; confirm purchases, dispatches and queue starts from the
resulting screen/state. Record unavailable opportunities separately. Stop the
normal bot only for exclusive live testing, then restore the LaunchAgent.

After each deployment verify the Mac checkout revision, running service and
fresh runtime log entries. Continue marking phases complete only when their
verification is done.
