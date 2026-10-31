# Mandatory “Hide trucks of this state” —0.35

## Readiness correction deployed0.37,2026-10-30

User's truck-world-cargo run stopped immediately with “Hide trucks of this state checkbox unavailable; stopped”. Original error omitted the individual active/interactable/toggleOn flags, so its exact failed flag cannot be recovered. Fresh memory/native inspection found saved:true, active:true, interactable:true, toggleOn:true on mini gaarix UID2059765822000064, PID2906/start18037170. No sharing/attack had started in the failed run. The old implementation immediately rejected a missing/inactive/noninteractive checkbox while a screen could still be opening, and unnecessarily required an already-checked box to be clickable.

0.37 waits up to5seconds for native/memory state to agree and for an OFF checkbox to become usable. An ON checkbox with matching savedtrue is accepted without requiring active/interactable, because no click is necessary. There is at most ONE enable request during the bounded wait; it never repeatedly toggles. Actual input still requires an active, interactable, currently OFF checkbox and all existing native/account/window/age guards. Unknown/mismatched state does not grant input. Native/account/focus errors still stop. Timeout now includes saved/checked/active/interactable flags for diagnosis.

Full suite passes19truck-filter checks (previous9 plus10readiness cases) and all other suites. Fresh live setting-only check found enabledBefore:true/enabledAfter:true with0enable clicks and0repeat clicks; no game preferences changed. Signed0.37 installed,10existing XML/JSON state files preserved. Floating controls opened, no scan/controller restarted. Evidence filter-error-native-state.jsonl, filter-error-view.json, filter037-live-setting-check.jsonl, filter037-validation.txt, filter037-build.txt, filter037-install.txt and filter037-{before,after}-persistent.json.

User requirement2026-10-30: ALWAYS tick this game checkbox in the Trucks screen; it should stay enabled across restarts. This is mandatory for every truck mode, not a helper option. Never blindly click/toggle a setting that is already enabled.

## Implemented and deployed

Signed helper0.35 installed on f7c5e6fe; all9helper XML/JSON settings/history/checkpoint hashes preserved. Same OnionRing92 UID2059765822000064, PID4389/start16784835. The user's running cargo-to-trucks-group scan was stopped normally, retaining its two verified group shares, then resumed with identical options after validation. No attacks or account changes. Shared selector remains Group.

Game metadata: DataCenter/LWTrainDataManager/filterLocalServer is a strict Lua boolean; target control is exported UILWTrainScene/View/outSeverToggle, name ToggleFilter. Native UnityEngine.UI.Toggle.get_isOn confirms the actual checkbox state. activeSelf is not used as proof of being checked.

AutomationController.ensureTrucks now enforces the setting on entry. ensureTruckFilter verifies native checkbox plus manager state at the start of every controller, clicks only if both arefalse, and requires bothtrue afterward. A proof is cached only within that controller; subsequent truck snapshots reread the actual manager boolean and repair it if it becomesfalse. New truck-screen entries invalidate the native proof. Unknown/contradictory/hidden/noninteractive states stop safely. Final World/group truck-payload validation also requires filterLocalServertrue before sharing.

Native ensureTruckHide input flag allows only the exact truck toggle path, correct scene/window/others tab/normal modal state and a strict false manager boolean. It is checked before geometry and again before ordinary input. The Unity-thread geometry getter refuses an already-on Toggle. Current account, focus, instance and geometry age checks remain. Race-to-already-enabled is accepted only with a structured no-input rejection and fresh positive state proof. No fixed coordinates or game action handlers invoked.

Preview truck runs also enforce this UI setting; preview still sends no chat messages/attacks. Memory-only standalone readers remain read-only.

## Live verification and persistence

Initial live statefalse. Exactly one metadata-positioned checkbox click changed it totrue. A repeat ensureTrucks call sent0extra clicks. The game itself wrote the durable per-character PlayerPrefs key TrainFilterLocalServer2059765822000064=1 under ParallelSpace clone0's com.readygo.barrel.gp.v2.playerprefs.xml. It also updated its normal REFRESH_TRAIN_LIST_TIME key when applying the filter. No game preference file was edited by the helper/agent.

After installing/restarting the helper as0.35, a fresh controller process/native read again found enabledBefore:true/enabledAfter:true, enableClicks:0, repeatExtraClicks:0. No relevant game preferences changed on that repeat. A full game/phone reboot was not performed; the persisted game key and per-controller mandatory recheck provide the restart behavior. Other accounts receive the same enforcement when their truck controller starts, and the game stores their own per-character setting.

Validation: full suite passes86rule,52cargo/destination,9new mandatory-filter checks and all prior maintenance/native/geometry/Python suites. Negative cases reject unknown Lua tags and mismatched native/memory states; true/true never requests a click. Live setting-only diagnostic never scanned/shared/attacked/refreshed via helper; the game refreshed naturally after its checkbox changed.

Evidence in runtime/helper-build: hide035-validation.txt, hide035-build.txt, hide035-install.txt, hide035-{before,after}-persistent.json, truck-hide-first-enable.jsonl, truck-hide-first-persistence.json, truck-hide-after-helper-restart.jsonl, truck-hide-persistence.json. Sources TruckHidePolicy/TruckHideCheck, native guard/getter and shared AutomationController precondition.

Current state: original truck-group-cargo job resumed, same bot, Group destination, power440m, Skip state0, live mode, maxRefreshes-1. Leave it running; do not inject, overwrite assets, hot-install or start another controller. Do not implicitly restart old bounty scans. Earlier migration STOP remains.
