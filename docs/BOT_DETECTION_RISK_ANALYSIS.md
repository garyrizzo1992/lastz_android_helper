# Bot-detection risk analysis

Updated2026-10-29. Source-based assessment; actual detection probabilities are UNKNOWN. No anti-bot probing was performed. Read-only memory does not mean unobservable execution.

## Shared runtime evidence

StateProbe and GameMemory read /proc/PID/mem with read-only handles. When a feature needs geometry or input, DeviceInput launches an injector against the active PID. unity-ui.js hooks a Unity render callback temporarily and invokes getters; input-agent-tail.js supplies ordinary Android input. Geometry/UI previews use this injected runtime, while explicitly memory-only training and Wanted inspections do not. Root, memory access, injected components and hooking are potential on-device observables; whether Last Z checks any specific signal is unverified. Gameplay actions generate server-visible activity. No evidence supports numeric probabilities, invisibility or absence of enforcement.

## Per-function exposure matrix

| Function | Local mechanism | Observable gameplay effect | Evidence / uncertainty |
|---|---|---|---|
| Truck inspection/refresh | Memory readers; injected bounds/input | Repeated truck refresh requests | Runtime established; detection rules unknown |
| Truck sharing | Same plus share UI and receipt reads | World/group posts tied to truck IDs | Verified sharing architecture; reports/moderation possible, actual detectors unknown |
| Truck attacks | Same plus battle UI | Attack/battle records | Verified victory/defeat; enforcement likelihood unknown |
| World bounty scans | Memory tile data; injected projection/gestures | Navigation/state visits; posts only for matches | Loaded tiles are scoped; no claim of full-map access or invisibility |
| VIP claims | Memory state; injected getter/input | Free claim transactions and cooldown | Two categories verified; few actions do not establish low detection probability |
| Alliance Help | Memory request list; injected button | Help acknowledgements/points | Verified10helps; credit-cap receipt gap remains |
| Alliance Gifts | Memory gift IDs; injected Claim All | Gift receive transactions |155Common verified; Rare live claim unverified |
| Mail inspection | Memory headers; injected navigation/getters | Tab requests; no explicit claim/read-all/delete | Six-tab preview verified; opening screens may still have normal game side effects |
| Finished-troop inspection | Memory-only queue/building/bubble/army joins; native input denied by feature capability | No collection, training, healing or dispatch | Included in installed0.28; preview passed with nonexistent injector/agent paths. Memory access still occurs; detection probability unknown |
| Finished-troop collection | Memory eligibility plus injected live collider/camera/raycast getters and ordinary Android tap | Completed queue becomes free; trained units transfer to free units | Installed0.28; Bow145 collection verified, repeat zero, Car/Foot/Hospital queue records unchanged. New training/healing/upgrade/dispatch excluded |
| Chest inspection/open-only diagnostic | Memory timestamp/state plus injected scene-reference/geometry getters; one guarded opening tap tested | Opening the idle-reward screen; no successful collection recorded | Consuming mode disabled in installed0.28; legacy uncertain claim remains quarantined. No retry or ledger bypass. Inspection/opening is not evidence of low detection risk |
| Other passive-base collection | Not yet migrated beyond finished troops and chest discovery | No new automated passive-resource collection established | Each resource/completion action still needs its own identity, geometry and receipt evidence |
| Personal Wanted inspection | Memory-only inspection of already-open activity400001/DispatchTask personal tab, exact task UUID joins | No navigation, claim, stealing, assistance or dispatch | Source-only; passed with nonexistent injector/agent paths. Separate from World bounty sharing and HeroBountyDataManager |
| Personal Wanted finished-reward claim | Memory task eligibility; injected Claim label/bounds, repeated task/window identity guards and ordinary Android tap | Exact personal task rewarded flag changes0 to1 | Source-only bounded live claim and repeat verified. One task changed, other task scalar records unchanged. Production entry/cleanup integration and deployment still pending |

Current automated gameplay actions and geometry/UI inspections use the instrumentation runtime; the explicitly memory-only inspections above are an exception. Lower action counts or successful previews are not evidence that any mechanism is undetectable. OpenCV can avoid game-memory/injection mechanisms when implemented through external capture/input, but automation and server-visible behavior remain; no claim that it is safe or undetectable.

## Improvements and status

Independent source audit and prioritized implementation queue: [BOT_DETECTION_IMPROVEMENTS.md](BOT_DETECTION_IMPROVEMENTS.md). ACCESS-01 makes diagnostic screenshots explicit opt-in/default-off in source after installed0.29; four mocked tests passed, no phone commands or deployment by that audit. Other tasks cover lazy instrumentation, narrow getter batches, memory-read transactions, retention schemas and supported interfaces. Actual detection probabilities remain unknown.

1. DONE locally: reject unexpected maintenance UID before input.foreground() starts injected inspection. Mismatched UID with deliberately nonexistent injector path rejected correctly; evidence maintenance-uid-preflight-rejection.jsonl. Deployed in0.27; installed-class rejection passed with nonexistent injector and all persistent hashes unchanged. Mandatory build audit/regression protects ordering.
2. Existing: exact active account/focus/process validation, one controller, STOP, bounded feature input allowlists, durable attempts and uncertain-result blocking. These prevent unwanted actions; they are not anti-detection techniques.
3. PARTIAL: training inspection shipped as memory-only in0.28; Wanted memory-only inspection passed locally and is not yet deployed. Quarantined-feature status and unexpected-UID rejection also avoid injection. Continue this per-feature inventory and clearly distinguish memory-only preview from injected UI/geometry preview; memory-only does not mean unobservable.
4. TODO: retain explicit feature opt-ins/defaultoff and bounded operation. Offer disabling unsupported functions; seek supported game interfaces or publisher permission where available.
5. TODO: minimize retained unrelated player/chat information and bound logs/journals without losing unresolved attempts or duplicate prevention.

## Official policy evidence

Florere terms https://last-z.com/terms/tos.htm, effective February28,2025, reviewed earlier in this session: section16 restricts unauthorized automation, circumvention and reverse engineering. This establishes account-policy exposure, not technical detector capability. No supported gameplay automation API was established by this review. Recheck official material if making current policy claims later.

No concealment, anti-cheat patching, protection bypass, production detection experiment or undetectability promise is part of these improvements.

## Resumed implementation additions

- The controller reports quarantined selected features without injection; nonexistent-injector check passed (`chest-quarantine-preflight.jsonl`). No real attempt was bypassed. Consuming `maintenance-chest` is disabled in installed0.28; its legacy uncertain operation remains intact.
- Memory-only training inspection declares `requiresInstrumentation:false`; Context rejects native actions for it. Nonexistent-injector/agent preview passed (`training-memory-only-preview.jsonl`). Finished collection itself uses injected geometry/input and is installed in0.28; evidence `training-collect-{preview,live,repeat}.jsonl` and `training-installed-preview.jsonl`. The distinction prevents unnecessary instrumentation during inspection; it does not establish undetectability.
- Native phase receipts conservatively record `inputStarted` before the Android event call; explicit no-dispatch cancellation retains audit evidence. This addresses duplicate/accidental actions, not anti-bot detectors.20 Android persistence fixture checks passed.
- Chest scene geometry/readers require injection/getters/raycast. One opening tap was tested; no successful collection was recorded. A transient-window rejection remains quarantined because the legacy receipt lacks structured no-dispatch proof. Do not clear it merely because the error appears benign.
- Wanted memory-only preview passed with nonexistent injector/agent paths (`wanted-memory-preview.jsonl`). The separate injected claim diagnostic passed exact Claim-control preview, wrong-UUID native pre-dispatch rejection, one verified rewarded0-to1 transition and no-work repeat (`wanted-{claim-preview,negative-uuid,claim-live,claim-repeat}.jsonl`). These local tests establish action correctness, not detection likelihood. Wanted remains source-only at this checkpoint; see `CURRENT_HANDOFF.md` for later release status.
