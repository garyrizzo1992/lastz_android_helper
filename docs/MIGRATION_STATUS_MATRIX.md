# Migration status and next delivery

Updated 2026-10-29, Europe/Malta. Installed release is **0.31**. This is a compact status companion to `CURRENT_HANDOFF.md`; that handoff owns current device/operation state. This document was written from source and saved evidence, with no phone/build/source edits.

| Function | Installed capability | Latest source/evidence after0.31 | Remaining proof or restriction |
| --- | --- | --- | --- |
| Existing truck and World-bounty modes | Retained in0.31 | No replacement planned | Preserve initial blue truck Share, explicit Gaarix-only attack, bounty sharing-only and destination ledgers. Qualifying bounty receipt coverage remains evidence-dependent. |
| VIP rewards | Two free categories verified | None needed for current scope | Paid/Activate excluded; preserve cooldown and uncertain-attempt barriers. |
| Alliance Help/Gifts | Help and Common Gifts verified; repeat no-work | No new consuming extension | Help credit-cap receipt and live Rare Gift claim remain unverified. |
| Finished troops | Collection shipped; Bow145 verified earlier | Car145 and Foot145 also verified. Only those queues changed; Hospital/other records unchanged. Foot pre-dispatch cancellation retained beside verified retry. Zero-ready inspection/repeat passed with nonexistent injector. Partial-result reporting fix preserves prior verified count/receipts; six Android JSON fixtures passed, source-only | Next useful release should include partial-result fix. No new training, healing or upgrade capability. Do not discard cancelled attempt or duplicate verified collection. |
| Personal Wanted finished rewards | Deployed0.29, retained0.31; one exact task rewarded0→1 and repeat verified | Production entry/cleanup and hidden-shortcut cache rules verified | Own completed rewards only. GO, stealing, assistance, hero assignment and dispatch excluded. Loaded cache does not prove server completeness. |
| Mail | Preview diagnostics only; no consuming control | Memory-only coverage and six-tab/header-state diagnostics established | No ordinary unclaimed attachment sample; paging/server completeness unproven. Special deal100 excluded. No Claim/Read All/delete permission and no whole-mailbox completion. See `MAIL_COVERAGE_FINDINGS.md`. |
| Eight-hour chest | Consuming entrypoint disabled | Scene opening/full-popup inspection exists | Legacy uncertain attempt remains quarantined; unchanged timestamp is not permission to clear/retry. Read-only reconciliation or real independent version reset required. |
| Passive own-base inventory | Installed0.31 memory-only diagnostic;46unclassified bubbles/8exact counter joins | Production-version fields now observed as exact text; Long.MAX_VALUE retained as sentinel. Read-only resource geometry matched intended first-hit collider for exact own building | Inventory/isShow/counter identity/geometry alone do not authorize collection. No production claim button/action yet. |
| New troop training | No start capability | New memory-only template inspection:30unit templates/cost templates;24observed building requirements met,3science-requirement rows. All rows `startEnabled:false` | Highest unlocked tier, science/item requirements, runtime capacity, quantity, effective cost units/bonuses and exact spend/queue receipt remain unproven. Template counts are not runtime spend authority. |
| Healing/research/construction/own-truck dispatch/gathering/radar/shop/shields | Not migrated into production maintenance | Inventory/design in migration plan | Separate consuming vertical slices require costs/capacity/prerequisites/protection and exact receipts. Do not enable broad Python defaults. |
| Runtime assets |0.31 uses immutable content-SHA256 agent filename; install+preview preserved nine XML/JSON maps and old agent | Cross-controller ownership plan exists | Immutable asset fix is not a shared Python/Go/helper lease. Never run controllers concurrently. |
| Desktop Python hardening | Source changes only, not restarted/deployed |237mocked tests passed: selected-device recovery, bounded log delivery, payload-minimized ADB logs | Do not claim full legacy account guards or shared lease. Remaining source reviews/retention boundaries are tracked separately. |

## Next bounded delivery: finish one resource-collection vertical slice

Prioritize converting the existing own-production evidence into one correctly guarded, journaled action instead of opening more inspection-only feature areas. The current candidate is the verified own building731000/item200394 family, not every base bubble.

1. Establish the exact **free collection action identity** and the currently collectible **exact amount/version**. Building lastCollectTime, template cap15840 and abbreviated15.8K text are observations; none alone proves the receipt. Do not treat infinite produceEndTime as an ended production timer.
2. Bind one candidate to exact own building UUID, production version, item UUID/counter and current free action. Reuse fresh scene-reference/camera/collider/raycast/UI-blocker guards, but never reuse a saved candidate coordinate.
3. Persist an attempt keyed to account/building/production version before input. Revalidate the same action/version immediately before an ordinary tap. Unknown popup, focus/UID/geometry/version change must reject or quarantine without blind retry.
4. Verify an independent **exact version transition plus resource amount/counter receipt** accounting for ongoing production. A vanished bubble, new timestamp or counter increase alone is insufficient if identity/amount cannot be tied to the action.
5. Perform one bounded live claim, repeat no-work, stale-version/false-dispatch and interruption tests. Only then add a useful helper control and release with installed preview plus preserved settings/history. If amount/action proof is unavailable, explicitly leave the resource claimant disabled and stop that slice rather than collecting speculative evidence indefinitely.

Source entry points: `BaseBubbleReader.java`, `BaseResourceGeometryFeature.java`, `input-agent-tail.js` native read-only resource geometry; evidence `base-production-version-preview.jsonl`, `base-resource-geometry-preview3.jsonl`, `resource-template-production-values.json`. All are under the helper source or `runtime/helper-build`.

## Bounded alternative: one highest-tier training start

If resource free-action/amount semantics cannot be established, finish the training-start vertical slice already begun. Resolve the effective runtime selected-unit/quantity cost and capacity, exact science/item unlocks and highest eligible tier before any spending. Require current free queue and permitted resource budget, journal first, then verify exact new queue unit/quantity identity **and** matching resource/item debit. Insufficient capacity, changed cost, lower-tier warning or uncertain result must stop without fallback/premium spending. Reuse the existing completed-troop collector; do not fold healing or upgrades into this feature.

Source: `TrainingStartReader.java` / `TrainingStartPolicy.java`; evidence `training-start-preview.jsonl`, `new-training-unit-costs-unlocks.json`. These currently expose unresolved flags honestly and enable no start. A single verified bounded start plus busy/full/no-work/error receipts is the next deliverable, not another catalog-only button.

Mail claims and chest retry are not substitutes for either slice while their stated blockers remain. Finish one consuming feature and its deployment proof before starting another broad discovery area.
