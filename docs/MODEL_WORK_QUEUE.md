# Manual model work queue

User preference: GPT-6.1 Sol for demanding work and GPT-6 Luna for routine batches. The user changes the model in this chat and says **continue**. This is a saved work queue, not an automatic model router or permission to start the bot.

**Active model: GPT-6 Luna, medium effort (user-confirmed 2026-10-31).** Update this field only from explicit session metadata or user confirmation. Group related implementation and checks to reduce manual switches; always specify the next model and effort and ask before changing batches.

## Current handoff

**Status: L2 complete; waiting for Sol6.1/high review.**

Next batch: S2 below. Helper/Python remain stopped under the user's standing instruction. No game action or deployment is included.

## Model allocation

| Model | Suggested effort | Work assigned |
| --- | --- | --- |
| GPT-6 Luna | Low for mechanical edits; medium for a specified batch | Factual documentation alignment, bounded file inventories, approved repetitive edits, running already-defined validation, collecting results and checkpoint updates. |
| GPT-6.1 Sol | Medium normally; high for difficult recovery/transaction work | Architecture, unfamiliar game/runtime investigation, designing receipts and failure handling, root-cause debugging, changes to native guards, account identity, ownership, retries, STOP, scheduling, resource consumption and release decisions. |

This is project-specific allocation, not a claim that a small edit is always easy. A one-line guard/default change can require Sol; a long prescribed validation run can remain a Luna task. Model guidance: https://developers.openai.com/api/docs/guides/model-selection . Product model availability and usage limits are not inferred from API pricing.

## Switch procedure

1. Finish or checkpoint the current coherent step. Preserve a reviewable diff; do not abandon a partially understood change in the middle of a consuming operation.
2. Save task IDs/status, requested model/effort, exact files, bounded steps, acceptance checks, evidence and escalation conditions here. Record meaningful project results in CURRENT_HANDOFF too. Never copy keys/private reports into Git.
3. End with a short message such as **Switch to Luna, then say continue. Queued: L1.** The user handles the model picker. Do not auto-select a model, create a separate chat or spawn model-specific agents to imitate routing.
4. On continue, read AGENTS, the newest CURRENT_HANDOFF checkpoint and this queue. Resume the queued batch. If model metadata is not exposed, use the user's switch-and-continue as their confirmation; do not claim the actual selected model was independently verified.
5. Complete a batch of related routine work before requesting another switch. Avoid switching for every command. Preserve regular checkpoints and commit directly to main; no PR.
6. At a model boundary, asking for a switch is now explicitly authorized by the user. If the user is away, leave the queue pending rather than inventing a response or spending the heavier model on the queued routine batch. Other missing-information questions still follow the user's no-questions preference unless they change it.
7. A model switch/continue resumes development work only. It never clears STOP, selects accounts, starts gameplay or authorizes a deployment by itself. All existing device/receipt/ownership rules remain in force.

## L1 — completed Luna batch: align factual status documents

Status: DONE on 2026-10-31; documentation-only commit recorded below.

Inputs:

- Newest CURRENT_HANDOFF checkpoint and source checkpoint7c75f4e.
- AUTO_BOOMER_NEXT.md and ANDROID_BOT_REMAINING_PLAN.md.
- Existing private validation reports, when present, only to confirm already-recorded facts. Do not publish raw reports.

Steps:

1. Updated the current-progress paragraph at the top of ANDROID_BOT_REMAINING_PLAN.md with the verified diagnostic activation/repeat, isolated receipt recovery and transaction-fixture status; production enrollment/deployment remains pending.
2. Corrected the current-status account-rotation row from installed0.38 to installed0.39 while preserving historical baseline/version paragraphs and dates.
3. Cross-checked current-status wording: installed0.39; Boomer diagnostics are not in installed Run bot; 141 transaction checks use simulated input/STOP with real files; five Android detach checks use an owned shell; the original signing key remains a deployment prerequisite and is unavailable on this Mac.
4. Updated CURRENT_HANDOFF with this factual documentation result and the next queue state. No source behavior changes.
5. Ran git diff --check and link checks; no application suites or device actions were rerun.
6. Committed directly to main and marked S1 READY. Ask for Sol6.1/high before starting S1.

Evidence: commit `21ce6f1a3cb27ab5acd3dcacb8fe084dc4e469bf`; `git diff --check` passed; edited links resolve within the repository.

Acceptance: no contradictory current-status claims; historical checkpoints preserved; no new claims of installed Boomer/full parity; no app, runtime, phone or history changes; only factual documentation/queue edits committed.

Escalate to Sol before making a behavior decision, interpreting a new validation failure, resolving substantive merge conflicts or inventing missing evidence. Missing existing logs are not permission to fabricate a pass or rerun phone actions.

## S1 — next Sol batch: rotation receipt-recovery integration

Status: IMPLEMENTED, pending L2 evidence and Sol release review. Suggested effort: high.

Read BoomerEngine, BoomerReceiptNavigation, BoomerReconcileCheck, MaintenanceRunner, MaintenanceReconciler, RotationController, RecoveryEngine and their tests.

Design and implement the bounded non-consuming recovery path for pending Boomer operations. Preserve the attempt barrier until exact evidence is durably saved; never proceed directly from an ambiguous attempt to activation. Preserve actual expiry, saved opt-outs, STOP, UID/focus checks, one owner and detach guards. Keep the new worker outside production enrollment until its release gates are satisfied. Add meaningful negative/orchestration coverage.

Sol owns design, critical implementation, root-cause analysis and final behavior review. Do not hand Luna an unresolved safety decision disguised as a mechanical edit. When a precise validation batch is ready, write its commands, expected results and stop conditions under L2, then checkpoint and request Luna.

## L2 — validation/reporting batch after S1

Status: DONE on 2026-10-31. Model: Luna, medium effort. Evidence and hardware limitation recorded below; ask for Sol6.1/high.

Packet (from repository root, using the existing private toolchain):

1. Read the newest handoff and verify the checkout contains the S1 receipt recovery checkpoint. Preserve any unrelated changes.
2. Set JAVA_HOME to parent work/toolchain/jdk-17.0.21+9/Contents/Home, LASTZ_ANDROID_SDK to parent work/toolchain/sdk, and prepend JAVA_HOME/bin and parent work/toolchain/node-v22.14.0-darwin-arm64/bin to PATH. These paths are relative to the chat workspace, not this repository.
3. Run `python3 tools/last-z-helper/validate.py`, retaining its output privately under runtime/helper-build. Expected: all portable suites pass, including 29 Boomer reconciliation, 141 transaction fault, 36 receipt permission and 16 registry checks. No APK signing or installation.
4. If explicit serial f7c5e6fe is connected and the script's idle/root preflight passes, run `python3 tools/last-z-helper/validate_android_fixtures.py --serial f7c5e6fe`. Expected: 141 transaction and five owned-shell detach checks. This does not exercise live rotation navigation. Do not bypass preflight, clear STOP or start a controller if blocked; report the hardware-dependent check unavailable and continue documentation.
5. Run `git diff --check`, record actual results and limitations in CURRENT_HANDOFF, update this queue and commit directly to main. Do not change source or weaken failing tests. Ask for Sol6.1/high for adapter/rotation review and release planning.

Evidence: `runtime/helper-build/l2-validation.txt`; portable validation passed with 29 Boomer reconciliation, 141 transaction fault, 36 receipt-permission, 16 registry, all recovery/ownership suites and 35 Python tests. `git diff --check` passed. `adb devices` showed no connected device, so `validate_android_fixtures.py --serial f7c5e6fe` was not run; no phone action occurred.

Run only prescribed build/test commands against the specified commit/diff. Collect concise results, distinguish simulated/JVM/Android/installed evidence, update the handoff and queue. Do not weaken tests or alter guards to make a failure pass. A new failure returns to Sol with command, first relevant error, affected files and preserved evidence.

Android fixtures require the explicitly selected rooted device and idle controller state. Missing device/key/setup should block only dependent checks. No installation or live game action is included unless Sol has prepared an exact authorized procedure and the user's existing authorization covers it.

## S2 — review, enrollment and signed release

Status: READY for Sol review; deployment remains blocked on original signing key and installed-path evidence.

Sol reviews results, implements/reviews explicit registry mapping, scheduling and the matching default-enabled UI choice while preserving false opt-outs. Complete same-signer candidate/installed Run/Preview/STOP checks within authorized selected-account bounds. Never generate a replacement key, uninstall to bypass signing, clear ambiguous history or turn protection Off to manufacture samples. Do not confuse source/fixture proof with installed-path completion.

## Remaining feature pattern

Use Sol for behavior discovery/design and critical implementation for gathering/radar, training/healing, construction/research, donations/shop, Wanted dispatch/assists, own trucks, remaining collections and shields/reporting. Queue repetitive approved edits, prescribed test execution and factual reporting for Luna. Return new ambiguity, failed tests and risky behavior changes to Sol; review meaningful feature behavior with Sol before release.
