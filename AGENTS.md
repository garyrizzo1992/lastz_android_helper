# Working on this repository

Read `docs/CURRENT_HANDOFF.md` first, then the current remaining plan. Its newest checkpoint is authoritative; older blocks are historical. Record meaningful changes, verification, limitations and the next concrete action in that handoff.

Android source is under `tools/last-z-helper`. Python parity/reference code and its shared ownership adapter are under `legacy/python-bot`; this checkout does not depend on a neighboring Python repository. The original Last Z Python repository must not accumulate Android helper files or migration notes again.

Preserve device settings, operation/share histories and the signing key. Do not commit anything under runtime, bin or scrcpy, or publish keys, credentials, backups or device evidence. Keep generated agent/injector/history assets ignored. Do not rebuild a signed installed artifact merely to move repositories.

Never start a controller, switch accounts, claim, share, attack or activate a feature just because a historical note says a job was active. Confirm current user authorization and current device/controller state. One controller owns the phone; do not inject, install or replace live runtime assets while a job runs. Preserve STOP, UID/focus checks and unresolved-attempt barriers. No coordinate or screenshot fallback for game controls.

Use only selected accounts. Truck shares use the initial blue Share button, never Plunder. Bounties are sharing-only, never plunder. Combat remains restricted to the explicitly authorized Gaarix attack mode and its rules. Pending/inspection-only features cannot be silently enrolled as production.

## Manual model handoffs

The user requests GPT-6.1 Sol for demanding work and GPT-6 Luna for routine batches, with manual model changes in this chat. Read `docs/MODEL_WORK_QUEUE.md` after the newest handoff and follow its next batch on "continue". Checkpoint and request the specified switch at batch boundaries; do not automatically route, create chats or spawn model-specific agents. Sol owns design, critical bot behavior and review; Luna executes sufficiently specified routine work. Escalate new ambiguity/failures instead of improvising a risky fix. A model switch is not permission to start the stopped bot or deploy. User overrides take precedence.
