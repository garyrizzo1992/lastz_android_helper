# Scene-object geometry foundation

Status: design only2026-10-29. Required for eight-hour chest/passive/troop collection. Do not add a pixel fallback or arbitrary pointer input.

## Evidence

SceneManager/World/ObjMgr/mapObjectLLHangUp is MapObjectLLHangUp. The visible chest is not a standard exported UI wrapper: bubble_trigger_obj,timeDes,bubble/gameObject are Lua userdata. Existing exported-path resolver permits UIManagerInstance/windows paths and wrapper.instanceId only, so it rejects the scene reference. This is correct current behavior. Native Lua userdata payload is not established; do not guess its pointer layout or treat it as a managed Unity Object pointer.

## Staged implementation

1. Determine the pinned build's XLua userdata-to-managed-object mapping from existing binary metadata or verified runtime object translator data. The pinned lib hash check must remain. Use read-only field/getter inspection; never invoke Lua/game action handlers. Record exact evidence, managed type and ownership chain. REA tools were absent on the resumed session; no configuration/install repair was performed.
2. Add a diagnostic-only scene-reference reader restricted to exact observed chest reference paths. Return Unity instance identity/type/name/active and owner process/UID/scene. Reject nil, destroyed or unknown objects and mismatched types. Do not accept caller-supplied pointers/instance IDs as an input capability.
3. Establish geometry by the real component type: Canvas RectTransform geometry if applicable, or collider bounds projected through the actual base camera. Validate near/far planes, viewport and visibility. A world Transform point alone is not proof the intended object receives input. Account for occlusion/HUD blockers and Unity raycast/trigger identity. Refresh geometry and identity immediately before ordinary input.
4. Separate read-only diagnostics from a scene-tap capability. Initially permit only the observed chest trigger path, base scene1, known level10001, no modal, current UID/PID/start/focus, single lease, fresh geometry and expected owner class. Keep truck combat guard and maintenance feature allowlists unchanged; other features get no scene input implicitly.
5. Add mutation tests: different object/PID/start/UID, wrong scene/window/focus, destroyed/reused reference, hidden/clipped/occluded target, invalid camera, offscreen/depth and stale measurements. Failed resolution must send no input. STOP must detach.
6. Preview on current bot without collecting. Then separately implement chest reader/policy: actual accumulation cap/last claim metadata, precise free-claim popup and cost identity, precommit journal and confirmed reset/reward receipt. Run one bounded free claim then no-work repeat. Do not classify08:00:00 alone as eligibility or infer last-claim identity from local time.
7. Extend to identified resource/training bubbles only after separate policies/receipts; no blanket base sweep.

## Completion criteria

Documented userdata mapping and independent native object identity; read-only diagnostic verified; meaningful stale/occlusion tests; exact input capability; no fixed UI coordinates or handler calls; bounded free chest claim+receipt and repeat; signed install with unchanged settings/history and installed preview. Until then chest collection remains unavailable.

## Saved evidence

runtime/helper-build/chest-hangup-object.json,chest-hangup-car.json,chest-city-world.json,chest-obj-mgr.json,chest-all-bubbles.json,base-discovery.png. Most broad manager searches already performed; read the saved results before repeating them. Standard TMP/UI.Text discovery did not find the08:00:00 label.

## Runtime mapping discovery checkpoint

Read-only xlua-metadata enumerated actual declarations: LuaEnv.translator offset32, ObjectTranslator.objects offset40, ObjectPool.list offset16; Slot[] length32768, Slot.next/obj declared boxed offsets16/24 and native value stride16. Chest bubble_trigger_obj userdata length4,nuvalue1; payload index5447 at offset56, slot next-2,managedtypeTransform. This is a DIAGNOSTIC CANDIDATE, not an input capability. Evidence xlua-{metadata,scene-metadata2,scene-candidate}.jsonl. No game handlers called/no clicks.

Lua5.4 source supports the variable userdata payload layout (nuvalue + aligned UValue array): https://www.lua.org/source/5.4/lobject.h.html . Do not confuse with5.3 layout; initial5.3 source comparison did not match the observed prefix. Pinned runtime/library guard still required. Next independently verify multiple exact chest references/native names on Unity thread and validate metadata-derived fields plus pool lifecycle; no arbitrary caller pointers. Diagnostic source newer than deployed0.27.

Four-reference Unity-thread verification passed: chest-reference-names2.jsonl resolves Trigger Transform, desText SuperTextMesh, bubble Transform and LLHangUp_Build(Clone) root to one hierarchy. The label's SuperTextMesh type explains why ordinary TMP/UI.Text scanning missed it. Reference name diagnostic permits only hardcoded observed field identifiers (not screen positions), validates userdata/pool lifecycle and makes no input available. Next inspect Trigger component and label declaredfields (chest-reference-components.jsonl) before geometry. No chest UI opened/claimed.

## Geometry candidate milestone

chest-reference-components.jsonl identifies BoxCollider/TouchObjectEventTrigger and SuperTextMesh._text field128. chest-reference-cameras2.jsonl confirms08:00:00, Main Camera and HudCamera; chest-collider-projection.jsonl validates Main layer0visibility vsHUDexcluded. scene-geometry.js conservative pure candidates have18tests and return requiresRaycast:true; not connected to input or APK. Next native exactcollider raycast and fresh context/occlusion guards; no click authorized by candidate math alone.

## Read-only live geometry preview passed

chest-collider-raycast.jsonl: exact Physics.Raycast(Ray,RaycastHit&,Single,Int32,QueryTriggerInteraction) runtime-signature selection; first collider-46154 equals intended-46154. chest-geometry-preview.jsonl combines live projection with safearea/viewport/UIraycastblockers and activeUID/basecontext. Observed08:00:00,claimEnabled:false, noinput. Native collider math/projection candidate aligns with screenshot. scene-geometry.js now bundled in diagnostic agent; production APK still0.27.18puretests+fullvalidationpass.

Still missing before input: robust freshness/re-resolution at commit, reference-mutability tests, source resolver refactor, exact owner/knownclass validation independent of diagnostic refs, confirmation of camera/trigger behavior if other colliders overlap, accumulation/reset metadata and popup/freeclaim identity. Do not interpret previewpass as completed chest migration or enableclick from a stored candidate.
