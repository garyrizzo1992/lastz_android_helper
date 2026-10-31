# Mail coverage findings

Updated 2026-10-29, Europe/Malta. This document records the saved evidence reviewed during the Mail coverage slice. Read `CURRENT_HANDOFF.md` for the latest installed version and phone state. The primary agent owns all phone actions; this source review performed no device commands.

## Current capability and boundaries

`MailCoverageInspectionFeature` is a diagnostic memory-only preview. It requires `dryRun:true` and an already-open Mail panel. It does not navigate, inject, claim attachments, mark all read, delete messages or persist a maintenance outcome. Existing shared discovery-cache infrastructure may refresh its cache file; this is separate from feature outcomes/settings/history.

The reader inspects only the selected tab's loaded headers and known paging/reward metadata. Every report explicitly sets:

- `claimEnabled:false`
- `completeMailboxProven:false`
- `serverCompletenessSemanticsVerified:false`
- `dailyCompletionEligible:false`

No production Mail claim button or consuming Mail capability is enabled by this work. `ORDINARY_CANDIDATE` is an inspection classification, not permission to claim. The current loaded sample contains no such candidate.

## Verified saved results

| Evidence under `runtime/helper-build` | Result |
| --- | --- |
| `mail-coverage-closed.jsonl` | With nonexistent injector/agent paths and Mail closed, returned `PREVIEW` / `UNINSPECTED`. Did not navigate to Mail or infer an empty mailbox. |
| `mail-coverage-reject-live.jsonl` | `dryRun:false` rejected with “Mail coverage inspection requires dryRun:true; no outcome will be persisted.” |
| `mail-coverage-wrong-uid.jsonl` | Expected-character mismatch rejected before instrumentation. |
| `mail-coverage-open-preview.jsonl` | Already-open System tab on OnionRing92 UID2059765822000064 returned stable `PARTIAL` through the memory-only path.21 loaded headers:0ordinary candidates,1special pending excluded,6already received,14without rewards,0blocked. |
| `mail-states-before-navigation.json`, `mail-states-after-entry.json` | Independent allowlisted header snapshots each contained189own headers plus3excluded synthetic placeholders. The primary agent's comparison found all common raw fields unchanged and no added/removed real headers after opening Mail. This proves only this observed entry transition, not every future navigation or paging operation. |

The System preview reported repository `_count=192`. This differs in scope from the21selected System headers. The189own headers plus3synthetic placeholders happen to total192 in this sample; that arithmetic does not prove `_count` represents the full server mailbox.

Six-tab navigation/coverage checks were being performed separately by the primary agent at this checkpoint. Do not infer their result from this System-only audit; use the latest handoff and actual completed log before recording broader navigation acceptance.

## Paging observations and what they do not establish

The fresh pre-open paging snapshot and open System preview agree on these observed shapes:

- `_tabReachedEnd` and `_tabLocalExhausted` are present but empty tables. Empty maps are not explicit terminal-page flags.
- `_loadContexts`, `_reqMoreTimeoutTimers` and `_reqMoreCallbacks` are empty in these samples. This does not establish all history loaded or confirm the lifecycle semantics of those fields.
- `_tabOldestCursor` contains integer/array keys. The selected System key `#1` has `time=1793259761165` and an empty UID. The reader retains exact integer text and key type rather than coercing large values through floating point.
- `_tabBeforeTime` is populated; `_headTime` is1793259761165 and `_headWindowDays` is7. The relationship between this window, cursors and full server history remains unverified.
- `_groupCountDict` is populated; selected System key `#1` has value50 while21System headers are loaded. The value's meaning is unknown: it must not be relabelled a verified server total or a target count to satisfy.
- `_isUsingNewLoadLogic` is true in the recorded sample. A boolean observation is not a verified paging protocol contract.
- Request-related entry counts are reported as observations. Nonempty callback/timer/reward-request tables would produce `PENDING_METADATA_OBSERVED`, not a claim that a particular request is actively in flight.

The reader therefore reports `PARTIAL`, even with stable repeated observations and zero ordinary candidates. It does not emit whole-mailbox no-work, completion or a daily completion marker.

## Source review and limits

Source: `tools/last-z-helper/src/dev/codex/lastzhelper/MailCoveragePolicy.java`, `MailCoverageReader.java`, `MailCoverageInspectionFeature.java`; regressions in `tools/last-z-helper/tests/MailCoverageTests.java`.

The policy preserves recipient identity, excludes `deal=100` and all other nonzero deal values from ordinary candidates, rejects unknown reward states for pending attachments, rejects unknown expiry semantics and retains exact positive mail identities. UI tab/group identity, explicit boolean types, active-window allowlist, selected batch state, table bounds and process/account identity are checked. No input/store call exists in the feature or reader.

Important limitations before reusing this diagnostic for claims or stronger guarantees:

1. **The report is not atomic.** The two reads compare selected header eligibility fields and serialized paging observations. `observedFieldsStableAcrossReads` does not cover every field in the game, repository `_count`, raw header `status`, unseen deeper tables or events that change and return between samples. Use the independent `MailHeaderStateProbe` before/after comparisons when assessing navigation/read-state changes.
2. **Eligibility is sampled.** Expiry classification uses the first snapshot time. A later consuming workflow must re-read current time and all exact message/attachment state immediately before input, with a native guard and precommit journal.
3. **Uniqueness is not established by this reader.** Coverage inventory counts repository rows and does not reject repeated UID aliases. `MailHeaderStateProbe` separately rejects duplicate real UIDs. A future claimant must explicitly require a unique exact message/attachment identity.
4. **Synthetic headers are narrowly excluded.** The coverage inventory currently reads `expireTime` before evaluating the synthetic-placeholder exception. A placeholder with no expiry field could safely reject a tab instead of being excluded; this is a compatibility gap, not permission to broaden the exception or hide rewards.
5. **Bounds are deliberate.** Header inventory is capped at2048rows, paging maps at64entries and child-field descriptions at24fields, with bounded Lua table shapes. Unsupported/truncated observations block conclusions. These are diagnostic limits, not evidence that the server has no further messages.
6. **Ordinary claiming remains unverified.** A special announcement is not a substitute for a real ordinary attachment sample. `_btnAllRead` is an observed `btnAllRead` control; its exact semantics must be established before any claim/read-all behavior is authorized.

## Validation and continuation

The primary agent's full validation passed the initial36Mail coverage checks. This source review added10meaningful pure fixtures in `MailCoverageTests.java`: the actual System mixture, empty loaded-tab conservatism, unstable/invalid observations taking precedence over pending metadata, missing recipient despite special deal, expiry boundary without overflow, noncanonical IDs, clone label rejection and closed selected context. Host compilation and all46Mail coverage checks passed. No other shared source file was edited by this review.

Next evidence needed: completed six-tab before/after raw-header comparison, bounded UI paging observations with cursor/end/loading transitions, and an ordinary unclaimed attachment sample. Keep preview-only semantics and `completeMailboxProven:false` until server coverage is independently established. Any later claim requires exact message/attachment ownership and free control, a durable precommit attempt, fresh native revalidation, an exact claimed-state/reward receipt, repeat no-work and uncertainty handling.
