# Plan: remove remaining hardcoded UI positions



Status: coordinate migration implemented and version0.22 deployed (2026-10-29). One qualifying bounty server-receipt test remains pending because no eligible target was found. Saved 2026-10-28. Resume from this document.



## Implementation progress



- Steps1–7 implemented: own automatic-input sources contain no reference-pixel tap/gesture paths; mandatory source audit passes. Map surface geometry includes camera pixelRect, safe area and rendered UI raycast blockers. Native gestures are computed immediately before input. List scrolling uses the measured viewport. Fixed text/numeric helpers, raw input APIs, image templates/classes/generator scripts and obsolete pixel tests removed.

- Fresh compiler staging plus a single newly compiled class archive prevents stale/deleted classes entering dex. APK version22 update-installed; settings/history/checkpoint hashes matched before/after. Main app heading now reads its package version.

- Validation passed:62 retained policy/identity checks,16 geometry scenarios,4 error-text cases,15 Python tests and JS syntax. Twelve old pixel/image fixture assertions were removed rather than preserved as meaningless coverage.

- OnionRing92 live checks passed: map-region discovery (32 blockers), movement confirmed by changed tile coordinates, State17 and22 approved-zoom short preview sweeps, truck UUID selection and group scrolling/reveal. No messages/attacks in these previews. No agents used.

- Unavailable-state errors now read active Unity text; recognized messages skip, unknown/unconfirmed navigation stops. Synthetic text recognition passes; a real unavailable-state response was not reproduced (State22 was accessible).

- Bounded one-share bounty check completed State17 around historical X230/Y794:19 positions,142 observations,shared0,attacked0; no eligible12/15 fixture. This receipt validation remains pending, not a code-migration failure. Fresh camera-projected bounty selection and live-popup dismissal passed afterward without sharing or plundering. Final installed-app short dry run passed:oktrue,scanned3,planned0,shared0,attacked0. No injector remains, awake released and floating controls reopened.





## Goal and completion criteria



Every automated control click resolves a named control or verified target from fresh game metadata and measures its actual screen bounds. Map selection uses live camera projection and verifies the selected UUID. Gestures derive from a verified live map viewport, not a reference resolution or fixed pixel endpoints. Missing, hidden, ambiguous or stale targets stop safely; there is no guessed-coordinate fallback.



Normalized gesture proportions, timing limits and map coordinate conversion constants are not button locations. They may remain only when applied inside freshly measured geometry and documented. Merely scaling the existing 540x960 coordinates does not satisfy this plan.



## Starting point



Installed helper: 0.21. Main truck, bounty, sharing and battle controls already use live exported bounds. Victory and defeat were tested; defeat returns through UIParkourBattleLose/View/continueTipText. Preserve these paths. A completed available 12/15-box bounty still needs an end-to-end World share receipt test.



Confirmed remaining items from the source audit:



- AutomationController.bountyRun and BountySendCheck duplicate a route of fixed swipe endpoints.

- input-agent-tail.js pinch uses fixed finger positions 110/430; generic input still assumes logical width540, reference height960 and heuristic Y anchors.

- DeviceInput.chatText and pasteLink tap220,910. numericField uses fixed editor/keyboard taps. Some callers are legacy diagnostics, not normal production delivery.

- DeviceInput retains tapAnchored, tapCanvas, nativeTap and related reference-layout APIs. Audit all callers before removing them.

- PhoneCheck's old chat diagnostic still types a power draft. Normal World sharing must continue to send only a native tile with an empty note.



## Implementation sequence



1. **Complete a repository-wide input inventory.** Trace every tap, swipe, pinch, screenshot/template target and shell input command, including diagnostics, assets and scripts. Classify each as live metadata, live viewport gesture, explicit manual diagnostic input, or obsolete fixed location. Record exact callers; do not assume all old helpers are unused. Check FrameChecks/template-position assets and LayoutMath references too.



2. **Introduce one live map gesture API.** Resolve the actual map surface/camera viewport plus visible UI occlusion/safe area from the current export/Unity state. Select a usable gesture region inside it. Compute native-pixel drag/pinch endpoints from that measured region; validate both fingers and all endpoints. Preserve fresh foreground/PID/start/UID checks, context checks and bounded input lifetime. Avoid pressing a HUD control or letting an overlay consume a gesture. If a usable region cannot be established, stop.



3. **Replace map scan movement.** Express the existing capital sweep as semantic directions/steps, not pixel tuples. Use the shared map gesture API in both production and BountySendCheck. Read live map coordinates before/after each move to verify movement and coverage; bound retries and avoid repeated stationary scans. Preserve the approved bounty zoom, state17–64 bounds and capital-area behavior.



4. **Replace zoom gestures.** Derive both finger positions and travel from the live map region. Keep feedback from live camera height/LOD and bounded convergence to the approved zoom. Migrate every pinch caller, including preparation for Trucks and coordinate search. Reject invalid/occluded geometry; no reference-canvas fallback.



5. **Remove or migrate obsolete text/input paths.** Remove retired private-link/power-draft diagnostics if they are no longer needed, along with their callers and CLI options. If retained for explicit diagnostics, resolve the actual exported input field, require its focused native editor, preserve readback/clipboard validation and clear the draft without sending. Use numericControl and IME actions; delete obsolete numericField. Do not restore private-link production delivery or World power announcements.



6. **Retire reference-layout machinery.** Remove unused fixed-position tap helpers, Y-anchor mapping, width540/height960 assumptions, template coordinate lookups and dead assets/classes. Keep live-native bounds input and world-point projection. Explicit user-supplied manual coordinates, if retained, must be isolated and unavailable to automatic flows. Clean the compiler output in the verified build directory so deleted Java classes cannot remain in the APK.



7. **Add a repeatable source audit.** Add a targeted audit for numeric UI tap locations, fixed gesture endpoints, reference-layout mapping and fixed template targeting in automatic flows. Avoid banning unrelated numbers such as item IDs, power limits, timeouts and map coordinates. Add meaningful tests for gesture geometry, clipping, occlusion, invalid bounds and small/tall viewports; retain existing policy, ledger and receipt tests. Document any intentional remaining geometry constants.



8. **Validate and deploy.** Run Java rule tests, analyzer tests, agent syntax checks and the source audit. On a user-selected bot, test map/search fields, zoom, movement, bounty selection and truck refresh/selection. Check sharing recipient/channel and empty note without sending during previews. Then find one qualifying12/15 bounty and verify exactly one World receipt, with no plunder. Do not repeat truck attacks solely for this coordinate cleanup; reuse the already verified victory/defeat behavior unless those paths change. Build a new signed update, compare settings/history/checkpoint hashes before/after install, verify version, stop controllers, release awake lease and update this plan plus NEXT_SESSION.md.



## Constraints throughout



- Work alone; the user stopped agent use.

- Only one phone input controller at a time. Never overwrite diagnostic dex/agent assets during a running session.

- Use the currently active account only; never launch/switch clones/accounts automatically. Gaarix stays free unless the user explicitly opens it for a test.

- No bounty plunder. No automatic retry of uncertain shares or attacks; preserve exact UUIDs and durable ledgers.

- Keep current group/World/main attack rules, saved options, signing key and all history intact.

- Use ordinary input after getter-based geometry lookup; do not invoke game action handlers.



## Resume pointers



- Source: tools/last-z-helper/src/dev/codex/lastzhelper/DeviceInput.java and AutomationController.java.

- Geometry/input: tools/last-z-helper/unity-ui.js and input-agent-tail.js.

- Diagnostics: BountySendCheck.java, PhoneCheck.java, PrivateDraftCheck.java; audit the rest too.

- Build: tools/last-z-helper/build.ps1. Phone ADB: scrcpy/adb.exe, serial f7c5e6fe; reverify connection and active identity.

- History: docs/NEXT_SESSION.md, docs/PHONE_SETUP.md, docs/BOUNTY_MEMORY.md.



Completion report must distinguish source-audited removal, live-tested flows and any remaining unverified coverage. Do not claim zero hardcoded positions until the full audit passes.

