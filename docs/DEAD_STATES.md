# Persistent dead states —0.36

User requirement2026-10-30: dead states do not return; remember a state after its first definitive dead-state message and skip it in future runs.

Installed signed helper0.36. Cache path: /data/user/0/dev.codex.lastzhelper/files/dead-states.json. It is created on the first new confirmed permanent error, not prepopulated from guesses or old generic unavailable logs. Shared by World/group bounty runs and all accounts using this helper installation. No expiry, independent of bounty checkpoints and run ranges. App updates preserve it like other helper state.

DeadStatePolicy accepts the actual definitive message “The State you are searching for does not exist.” (ignoring case, rich-text tags and harmless whitespace). Temporary unavailable/not-yet-open messages, network errors, timeouts and unknown messages are NOT permanent evidence. Existing skip-this-attempt behavior for recognized temporary messages remains.

The existing coordinate search clears old notices before submitting the requested state. Only newly observed recognized error messages after that request may be recorded. New permanent records are written immediately with state number, normalized evidence message and confirmedAtMs using fsync/atomic replacement. Duplicate confirmations preserve the original record. Invalid schema, invalid state entries, unsupported messages or corrupt storage fail rather than silently inventing/resetting a skip list.

Bounty iteration checks this cache before opening state search/navigation, logs a remembered-state skip and advances the normal checkpoint. go() also short-circuits before worldReady/zoom/search for remembered states. Both sharing destinations use the same file. No share/attack/eligibility rules changed.

Validation:12new pure policy checks plus18Android fixture checks verify recording, reload, duplicate preservation, temporary-message exclusion, corrupt-file rejection, skip without an injector/native request, and checkpoint advancement/completion for BOTH destinations. These use a synthetic state40 record ONLY in isolated /data/local/tmp/lastz-deadstate-test-* directories. They are not real game evidence and do not seed the real app cache. Full existing helper suites also pass. No live navigation, chat post or game account change for this feature.

Signed0.36 installed and version verified; all9existing helper XML/JSON settings/history/checkpoint files matched before/after installation. Real dead states learned by this test:0. The next live permanent error will create/extend the app's actual dead-states.json.

Evidence runtime/helper-build/dead036-validation.txt, dead036-phone-fixture.jsonl, dead036-build.txt, dead036-install.txt, dead036-{before,after}-persistent.json. Sources DeadStatePolicy, DeadStateStore and shared AutomationController navigation.

Current state: no controller/injector running. The user had stopped their newer truck-world-cargo run (last log4shares/0attacks); it was NOT restarted. Latest observed active character is baby gaarix UID2059744163000064, PID32112, selected by the user; the agent did not switch accounts. Helper floating controls opened after install. Earlier cargo-resumed notes are historical. Migration remains stopped. No agents used.
