# World truck sharing:0.33 checkpoint

2026-10-29, Europe/Malta. User requested investigation of Share2+toWorld failing and a separate3+World option.

## Deployed

Signed versionCode33/versionName0.33 installed on f7c5e6fe. All9settings/history/checkpoint XML/JSON SHA256 values matched across install. Floating controls opened with the new choices. No controller/injector remains running. Do not restart the earlier bounty job implicitly.

Both MainActivity and floating HelperService now expose Share2+toWorld (`truck-world`) and Share3+toWorld (`truck-world-3`). Both accept yellow/purple only, require known power, share at any power, preserve Skip state, use the same World truck ledger key (`truck:<uuid>`), send the truck tile with an empty note and never grant attack permissions. Group/attack rules are unchanged. The new classifier is used both while finding candidates and while revalidating the share payload.

## Original error and recovery

The saved actual user run (`truck-world`, OnionRing92 UID2059765822000064, PID20644) failed with PreDispatchRejected/Exported control is hidden. At inspection, Others' Trucks was open but objInfoPanel.activeSelf wasfalse/selectTrain absent: selection had not reached the truck detail/share screen. Subsequent bounded diagnostics located the selection path at UILWTrainScene/View/trainCells/#12/btn. Lua activeSelf/activeCached were true for all12cells; these flags alone do not establish native visibility.

openTruck now catches ONLY structured native_pre_dispatch/ui-tap receipts with inputDispatched:false and exact hidden/disabled/offscreen errors. It returns to the existing bounded-by-user refresh loop rather than terminating on an unavailable cell. Possible input, identity/focus failure, unexpected errors and callback timeouts still STOP. It does not retry a share or clear any pending/uncertain ledger. Native control-path context is now included in receipts/errors so future failures identify the actual control.

## Live verification limit: game stopped rendering

The test bot remains OnionRing92 UID2059765822000064, PID20644/start12373636. During subsequent live tests, the game stopped producing new presented frames. SurfaceFlinger history was identical across two reads2seconds apart. Old127-frame histories still calculate~30FPS, so an unchanged history MUST NOT be presented as current FPS. Bounded getter probes observed0calls to Canvas render callbacks, synchronization tasks, Time wrappers and Camera callbacks over4seconds. This establishes no usable callback during that sample; it does not establish why the game stopped updating or which individual operation caused it.

WorldSendCheck tests made no selection input/share/attack: native geometry timed out with explicit pre-dispatch rejection on #12/btn. No successful World share is claimed for this release. The existing engine callback and visibility checks were preserved; experimental callback replacement/flush attempts did not help and were reverted. No fixed coordinates or blind-tap fallback was added.

Temporarily opening helper MainActivity and returning with Back restored focus to the same game instance, but did not restore callback progress. No game/account was relaunched or switched. The intended game needs to be reopened manually before another bounded live sharing verification. Do not automatically choose/reopen a Parallel Space clone. Leave all controllers stopped until the intended bot is visibly running again.

## Validation/evidence

Full validate.ps1 passes86rule tests (including new3+World thresholds/grade/power/combat cases and conservative hidden-cell retry cases),93maintenance,76Wanted,29cache,46Mailcoverage,36Mailheader,36basebubble,18training-start, runtime-asset checks,16geometry,7unavailable-state,157native-field-cache,27Python,18scene,14reference and8integer-key scenarios. Source audit/native syntax passed. Signed APK built and version verified.

Evidence in runtime/helper-build: truck-world033-validation.txt, truck-world033-build.txt, truck033-install.txt, truck033-{before,after}-persistent.json, truck-world-error-{view,selection,sharebtn,cells}.json, truck-world-probe-*.txt, truck-frame-profile.jsonl. A diagnostic screenshot truck-error-screen.png was explicitly captured for this investigation. Diagnostic assets were staged in unique /data/local/tmp/lastz-truck-world-* and lastz-frame-profile-* folders; installed immutable assets were not overwritten.

Next verification once the user reopens the intended bot: confirm account/focus and NEW frames, ensure no controller, run at most one World truck share with the real dedup ledger, verify exact World receipt/empty note, then test3+filtering. Preserve the big blue Share route; never use Plunder or share only a location.
