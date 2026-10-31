# Manual model work queue

User preference: GPT-6.1 Sol for demanding work and GPT-6 Luna for routine batches. The user changes the model in this chat and says **continue**. This is a saved work queue, not an automatic model router or permission to start the bot.

## Current handoff

**Status: waiting for the user to switch to Luna and say continue.**

Next batch: L1 below. Do not execute it on the planning model merely to avoid waiting for a switch. No game action or deployment is part of this batch. Helper/Python remain stopped under the user's standing instruction.

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

## L1 — next Luna batch: align factual status documents

Status: READY, awaiting manual model switch.

Inputs:

- Newest CURRENT_HANDOFF checkpoint and source checkpoint7c75f4e.
- AUTO_BOOMER_NEXT.md and ANDROID_BOT_REMAINING_PLAN.md.
- Existing private validation reports, when present, only to confirm already-recorded facts. Do not publish raw reports.

Steps:

1. Correct the stale current-progress paragraph at the top of ANDROID_BOT_REMAINING_PLAN.md. It still says real Boomer activation awaits an account choice. The newest handoff records successful diagnostic activation/repeat, isolated receipt recovery and transaction fixtures; production enrollment/deployment is still pending.
2. Correct the current-status account-rotation table row that still says installed0.38. Installed Run bot/Preview/defaults/recovery are0.39. Preserve explicitly historical baseline/version paragraphs and their dates.
3. Cross-check that current-status sections agree: installed0.39; Boomer source diagnostics verified but not in installed Run bot;141transaction checks use simulated input/STOP with real files;5Android detach checks use an owned shell, not a real injected-session failure; original signing key is a deployment prerequisite, last known unavailable on the Mac.
4. Update CURRENT_HANDOFF with the factual documentation result and this queue's next state. No source behavior changes.
5. Run git diff --check and verify any edited file links. Do not rerun unchanged application test suites just because the model changed. If source has unexpectedly changed since the cited baseline, record it and stop for Sol review instead of guessing which results apply.
6. Commit the documentation directly to main, preserving remote changes. Mark L1 DONE with the commit/checks; mark S1 READY. Ask for Sol6.1 and stop the batch.

Acceptance: no contradictory current-status claims; historical checkpoints preserved; no new claims of installed Boomer/full parity; no app, runtime, phone or history changes; only factual documentation/queue edits committed.

Escalate to Sol before making a behavior decision, interpreting a new validation failure, resolving substantive merge conflicts or inventing missing evidence. Missing existing logs are not permission to fabricate a pass or rerun phone actions.

## S1 — next Sol batch: rotation receipt-recovery integration

Status: QUEUED after L1. Suggested effort: high.

Read BoomerEngine, BoomerReceiptNavigation, BoomerReconcileCheck, MaintenanceRunner, MaintenanceReconciler, RotationController, RecoveryEngine and their tests.

Design and implement the bounded non-consuming recovery path for pending Boomer operations. Preserve the attempt barrier until exact evidence is durably saved; never proceed directly from an ambiguous attempt to activation. Preserve actual expiry, saved opt-outs, STOP, UID/focus checks, one owner and detach guards. Keep the new worker outside production enrollment until its release gates are satisfied. Add meaningful negative/orchestration coverage.

Sol owns design, critical implementation, root-cause analysis and final behavior review. Do not hand Luna an unresolved safety decision disguised as a mechanical edit. When a precise validation batch is ready, write its commands, expected results and stop conditions under L2, then checkpoint and request Luna.

## L2 — validation/reporting batch after S1

Status: BLOCKED on Sol supplying an exact validation packet.

Run only prescribed build/test commands against the specified commit/diff. Collect concise results, distinguish simulated/JVM/Android/installed evidence, update the handoff and queue. Do not weaken tests or alter guards to make a failure pass. A new failure returns to Sol with command, first relevant error, affected files and preserved evidence.

Android fixtures require the explicitly selected rooted device and idle controller state. Missing device/key/setup should block only dependent checks. No installation or live game action is included unless Sol has prepared an exact authorized procedure and the user's existing authorization covers it.

## S2 — review, enrollment and signed release

Status: BLOCKED on S1/L2 evidence and original signing key for deployment.

Sol reviews results, implements/reviews explicit registry mapping, scheduling and the matching default-enabled UI choice while preserving false opt-outs. Complete same-signer candidate/installed Run/Preview/STOP checks within authorized selected-account bounds. Never generate a replacement key, uninstall to bypass signing, clear ambiguous history or turn protection Off to manufacture samples. Do not confuse source/fixture proof with installed-path completion.

## Remaining feature pattern

Use Sol for behavior discovery/design and critical implementation for gathering/radar, training/healing, construction/research, donations/shop, Wanted dispatch/assists, own trucks, remaining collections and shields/reporting. Queue repetitive approved edits, prescribed test execution and factual reporting for Luna. Return new ambiguity, failed tests and risky behavior changes to Sol; review meaningful feature behavior with Sol before release.
