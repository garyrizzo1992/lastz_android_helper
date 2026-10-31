# Shared controller ownership plan

Status: design only. Existing Android helper controllers share an OS FileLock on /data/local/tmp/codex-lastz-helper/control.lock. Python and Go raw ADB input do not participate. Do not run them together. A desktop mutex or remote LaunchAgent pause protects a different scope.

## Required invariant

Only one controller may execute gameplay input on the device. Ownership must remain held through the complete input/receipt interval, including cancellation and child-process cleanup. PID alone is not identity: retain process start time and validate owned children. Active game/account checks are independent requirements and must remain before input.

A check-only 'try lock, release, then tap' is unsafe: another controller may acquire between check and input. A heartbeat holder that releases its lease while detached legacy ADB commands can still execute is also unsafe. Do not claim shared ownership from those designs.

## Proposed integration boundary

Route legacy input through one device-side owned bridge holding the same FileLock as helper controllers. The bridge accepts a bounded allowlist of input operations, explicit expected serial/account/process identity and unique sequence IDs. It must reject unknown commands, changed foreground/account, stale sequence/context and STOP. Do not expose arbitrary shell execution or direct game method calls.

Host disconnect/heartbeat expiry must stop accepting new operations, finish or cancel its currently owned OS input safely, then release the lease. A reconnect cannot silently choose another account or device. Never kill unrelated processes or rely on a stale PID. The host must not retain a direct raw-input fallback after bridge failure.

Read-only discovery may be a separate capability, but injected getter sessions still obey exclusive runtime ownership. Asset extraction/replacement and injector lifecycle need coordination: do not overwrite an active session's agent file before acquiring ownership. Prefer immutable content-addressed assets and preserve old files until no owner references them; cleanup requires a separate safe retention policy.

## Acceptance fixtures before any live use

- Two controllers competing: exactly one input owner, loser sends zero events.
- Race between prepare and execution: no active runtime file overwritten.
- STOP during input and during receipt wait: no subsequent events, ownership released after owned cleanup.
- Disconnect, heartbeat timeout, stale PID reuse and process restart: fail closed, no orphan input or unrelated kill.
- Account/window change and reconnect: no fallback game/serial or silent retry.
- Native compatibility failure caught by cleanup: no requested action can bypass the compatible-session gate.
- Ordinary completion, uncertainty, duplicate journal and ledger preservation: no repeated consuming operation.

Start with pure protocol/lease state fixtures and local competing-process tests, then one non-consuming device probe. Preserve current helper FileLock/account/STOP/journal behavior. Do not add a production bridge button before these tests and ownership semantics are proven.
