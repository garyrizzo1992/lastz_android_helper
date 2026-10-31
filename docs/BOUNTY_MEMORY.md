# World bounty metadata and sharing investigation

Verified on 2026-10-27 in LDPlayer (`emulator-5556`), Last Z 1.250.731 (3161), 540×960. Truck work is paused. The user authorized searching state 17 and sharing 12/15-box locations to World; **plundering is explicitly prohibited**.

## Read-only discovery

The saved helper's `StateProbe` validates the IL2CPP library SHA-256, PID/start identity and Lua manager before reading `/proc/PID/mem`. Investigation sources, raw JSON and screenshots are under ignored `runtime/bounty-investigation/`. These are runtime observations from the existing probe, not decompiled source or REA Evidence. REA was unavailable in this session.

Relevant Lua paths:

- `DataCenter.WorldPointManager.allViewPoints`: loaded map tiles, including bounty records; multiple tiles can reference one object's `mainIndex`, so deduplicate by UUID.
- Bounty `pointType = 22` (`WorldPointType.HERO_DISPATCH`).
- `mainIndexV2.x/y`: map coordinates. Prefer these explicit fields over decoding the numeric tile ID.
- `pointInfo.serverId`, `srcServerId`, `uuid`, `dispatchMission.missionId`, `ownerUid`, `allianceId`, `startTime`, `finishTime`, `stealUids`, `doubleReward`.
- `DataCenter.WorldPointManager.aoiServerId` and `reqPos`: independently confirm the viewed state and requested position.
- `package.loaded["LuaDatatable.aps_dispatch_tasks"]`: `index` maps column names to positional row indexes; `data` maps mission IDs to rows. Do not infer rewards from the mission ID digits.
- `DataCenter.ActDispatchTaskDataManager.todayStealNum`: observed 0 before and after opening the calibration bounty; no plunder performed.

Join each live mission ID to its task row. Parse **`steal_reward_show`**, not `base_reward_show` (the owner's reward). The first displayed box item in the calibrated bounty corresponds to item 252006. Other fields include `steal_reward`, `steal_maxtimes`, `color`, `model_name`, `task_star`, `level`, `is_special`, `is_season` and `protect_times`.

| Mission | Boxes in loot preview | Model | Special | Level |
| --- | ---: | --- | ---: | ---: |
| 600401 | 12 | paiqian_5 | 1 | 4 |
| 600501 | 15 | paiqian_5 | 1 | 5 |
| 1103001 | 15 | paiqian_5 | 1 | 6 |
| 1102001 | 6 | paiqian_4 | 0 | 6 |

All four rows use task-table `color = 4`; the generic `HeroBountyRarity` enumeration is a different system and must not be used to relabel task colors. A separate row 1000001 also has a 15-box preview, model `paiqianxiangzi2`, color 1 and special 0; identify it by actual reward data if encountered. Availability/lootability is not proved by a cached record alone.

## Confirmed navigation

At normal map scale, tap magnifier near (28,778). Top search bar has state, X, Y fields near (160,133), (265,133), (365,133). Tapping a field opens an Android text editor and clears its existing text; enter the value, then tap OK near (459,907). Allow UI transitions to settle between fields. The coordinate-search magnifier is near (424,132), distinct from the large monster/resource Search button below.

Changing the state field to 17 and submitting produced the visible `State #17` banner and memory `aoiServerId = 17`. This views the state remotely; it does not teleport the player's city.

For calibration, searching state 64 X592 Y604 and opening its chest showed **Perimeter Patrol**, six boxes and a separate Plunder control. Memory `UIManagerInstance.windows.UIWorldPoint.Ctrl.pointId = 604593` matched mission 1102001. The share icon was near (405,303); this position belongs to that observed popup and is not a general fixed target.

## Zoom findings

Android/scrcpy synthetic pinch attempts did not change the displayed map in this emulator. Do not count these as successful zoom tests. A bounded Frida agent calling UnityPlayer's Java `injectEvent` with genuine two-pointer MotionEvents did change zoom; every owned injector must receive SIGTERM and detach afterward. No Lua gameplay function calls or game memory writes are used by this input path.

- Normal detail: `lodLv = 1`, `aoiLodLevel = 0`, 14 loaded tile records at the tested sparse state-17 location.
- Wider view: `lodLv = 3`, `aoiLodLevel = 1`, 322 loaded tile records and seven bounty records.
- Farthest tested view: `lodLv = 7`, `aoiLodLevel = 3`, 763 tile records, territory/city overview, same seven retained bounty records. Further pinches left this view unchanged.

Thus zooming expands the local data area, but the farthest territory overview **does not establish whole-server bounty coverage**. Old bounty records remain cached at wider LODs; a retained record does not prove fresh coverage. Compare UUID sets, timestamps/finish state and positions after map movement. Returning toward detail reached `lodLv = 2`, `aoiLodLevel = 0`.

## Automation requirements

### User-approved scanning zoom

The user visually approved the map scale saved in `runtime/bounty-investigation/after-small-adjustment.json` and `user-approved-zoom.json`: **`lodLv = 4`, `aoiLodLevel = 1`**. Use this scale for the state-17 search. The final adjustment was a single inward pinch with pointers moving from X110/X430 to X125/X415 at Y480 over 20 steps. These LOD values identify a band, not an exact continuous camera zoom; preserve the current approved camera scale during exploration rather than assuming any scale in that band is identical. No further zoom changes are needed unless requested.

The continuous value was subsequently found at **`SceneManager.World.Camera._lastHeight = 746.01416015625`**, matching `_zoomWhenCalculatePadding`. This is the approved scale's reproducible numeric reference (`approved-camera-details.json`). Temporarily zooming in to revisit a known coordinate is distinct from exploring at the approved scale; restore the scanning scale afterward.

Keep map exploration separate from publishing. Read a stable state-17 snapshot, join mission templates, filter actual 12/15-box loot previews, deduplicate UUIDs and retain coordinates plus observation times. Count `dispatchMission.stealUids` and compare with the template's `steal_maxtimes` (3 for the target rows); exclude exhausted records and recheck immediately before sharing. Other players can loot between discovery and publishing.

Record each visited camera position/LOD; bound retries, unchanged-camera observations and coverage claims. Map data updates can lag gestures: successive snapshots sometimes return the same `reqPos`, followed by a changed position. Do not assume every swipe produced a freshly loaded region or treat all gestures as separate coverage.

Before sharing, revisit the coordinate, verify UUID/mission and the visible reward preview. Never tap Plunder. World sharing needs channel verification, a durable pending/verified ledger and a success receipt before retrying an uncertain send. Use the bounty-specific flow verified below; truck-share coordinates must not be reused.

## Verified bounty-to-World sharing

First verified post: state 17 **X230 Y794**, UUID `1430458915153252747`, mission 1103001, **Receive Supplies, 15 boxes**. The popup preview showed 15 and the selected `UIWorldPoint.Ctrl` UUID/pointId matched the live record. No looters were recorded immediately before opening it.

**User correction after that post:** future World shares must have **no added text**; do not type “15 boxes”, “12 boxes”, or quantities into chat. The first post included `15 boxes` before this instruction arrived. Keep the note field empty for subsequent shares.

1. At detailed zoom, open the identified bounty. Confirm selected UUID and the visible box quantity.
2. Tap its share icon (observed (405,302)). The Share menu must show the exact state/X/Y and bounty title.
3. Select the row explicitly labeled **World** with its globe icon (observed share button (417,342)); do not assume the other rows' channels.
4. The second confirmation must again show **World** and exact coordinates. Visually verify that the optional note field is empty; clear any retained text, as explicitly requested by the user. Leave “Don't remind me today” unchecked.
5. Persist a pending UUID-keyed ledger entry **before** attempting the send. Tap the gold Share button only after confirming the channel/coordinates (observed (174,617)).
6. The game displayed **Share Successful**. Save the screenshot and mark the ledger verified; do not resend pending/verified UUIDs. The current ledger is `runtime/bounty-investigation/world-shares.json`, receipt `fifteen-world-sent.png`.

These coordinates describe the tested 540×960 layout and require visual validation. Sharing itself does not plunder. The ordinary-world 6-box calibration popup and exhausted/missing 15-box records were not posted.

After that post, the scan scale was restored by small input adjustments with memory feedback: `SceneManager.World.Camera._lastHeight = 746.3043212890625`, within 0.04% of the approved 746.014 value (`restored-approved-final.json`). Pinch response must be measured after settling; repeating a fixed gesture is not an exact camera-height setter. Guard the approved LOD and compare the continuous height when restoring after coordinate search.

World bounds observed in `SceneManager.World`: `WorldSize = 1000`, X/Y minimum 0, maximum 999. The coverage journal records sampled camera positions, not proof that every tile in those bounds was searched.

Further verified World shares (both with an empty note field):

| State | X | Y | UUID | Receipt |
| --- | ---: | ---: | --- | --- |
| 17 | 610 | 184 | 1430458939098534170 | second-world-sent.png |
| 17 | 598 | 163 | 1430458874451726772 | third-world-sent.png |

Both previews showed 15 boxes and both sends produced **Share Successful**. The latter had two recorded looters before sharing. This metadata is time-sensitive; the journal must not be reused as a list of still-lootable targets.

`restore_zoom.py` is an exploratory, bounded controller: it measures `_lastHeight`, makes small two-pointer input adjustments, and remeasures until within one height unit of the user-approved reference. It stops if convergence fails or a modal/other scene appears. These helpers are session prototypes, not a production scheduler; production integration must also bind input to the freshly validated PID/start identity, persist ownership/cleanup, guard UI state and verify every external send.

## Result of this sweep

The saved session report (`runtime/bounty-investigation/session-report.json`) contains **275 snapshots, 236 distinct sampled camera positions and 317 distinct bounty UUIDs**. Six records had 15-box template previews; three were verified and shared to World. Other matching records were exhausted or no longer present when revisited. No 12-box preview was found in the sampled records. This is a broad sampled sweep, not an exhaustive claim about all 1,000×1,000 tiles or future spawns.

Final verification: `todayStealNum = 0`, World scene, no open modal, no owned Frida injector left running. Camera height was **746.7255859375**, LOD 4, within one height unit of the user-approved 746.014 reference. Raw evidence is in `final-plunder-counter.json` and `final-camera.json`. The two posts after the user's correction had empty note fields.

## Capital-area follow-up and current automation status

The user requested capital-area sweeps while incrementing states, initially through 25, then explicitly extended the end state to **64**. The active authorized range is **17–64 inclusive**. State 17 and state 18 capital metadata both identify cityId 1, cityLevel 7, tile anchor (496,496). The scan centers at (500,500), restores the approved zoom and sweeps a nearby ring. Check each state's own city record and `aoiServerId`; do not trust a stale capital list after a server change.

`capital_series.py` automates bounded state navigation, capital verification, zoom restoration and the nearby scan through the authorized end state. It writes `capital-series-progress.json`. If it finds a qualifying unattempted bounty, it **stops before publishing** with exit code 10 and saves `share-next.json` for verification. Actual World sends are still operator/agent-driven with screenshots and the durable share ledger.

## Installed Helper 0.6 (2026-10-28)

The historical desktop prototype above is superseded by `tools/last-z-helper/`. Helper 0.6 packages **Run bounties** (default states 17 through 64), **Run trucks**, and Stop controls. The signed APK is `bin/last-z-helper.apk`. It runs on rooted Android without a desktop controller, discovers the current game process, serializes actions, and validates the tested game build and 540x960 layout.

Bounty runs navigate the capital area at the approved camera height, skip unavailable states and exhausted/unfinished targets, and recheck UUID, rewards and coordinates before sharing. Camera coordinates come from `curCameraTarget`; AOI `reqPos` can remain several tiles stale after navigation. Dry and live runs use separate checkpoints. Dry run is enabled by default; disable it to allow World posts.

World sends require an empty note and recognized World controls. A typed UUID ledger records pending attempts **before selecting a channel**, since the truck World row can publish immediately. Delivery verification requires the own sender UID, expected post type and a new server-assigned World-chat sequence. Pending attempts are never blindly retried.

Validation: 18 rule checks and 11 Android screenshot/ledger/receipt checks passed. Live selection rejected an ineligible truck before channel selection. Device dry runs exercised a truck refresh and bounty states 21-22, including an unavailable-state skip, qualifying share-menu validation and return to the approved scan position. The installed Run trucks button completed a loaded-list scan after a fresh game process. The installed Stop service cancelled a bounty worker with `stopped:true`; the main Stop button created its cancellation signal. A subsequent login-on-another-device dialog stopped the truck refresh without confirmation. Automated publishing has not been exercised end-to-end; dry tests sent no posts.

During earlier truck-channel exploration, one non-qualifying truck was inadvertently posted when the World row published immediately. Its verified receipt and identity remain in the share ledger. Eligibility checks and the pending ledger write now precede channel selection. No plunder occurred.

Close game startup popups before running. Unexpected dialogs, lost focus, changed build, uncertain receipts or failure to restore zoom stop the run. See `tools/last-z-helper/README.md` for controls and build instructions.

## Floating controls in Helper 0.7

The floating panel now includes Run/Resume bounties, Run trucks, Inspect loaded trucks, state range, refresh limit and Dry run, with status and a fixed Stop button. It shares settings with the main helper, saves them before launch, and collapses for game input. Opening the panel during a run leaves game focus intact and disables settings/start controls. Status updates preserve edits instead of rebuilding the panel.

Installed-device checks verified editing and saving overlay settings, returning input focus to the game, and starting a truck dry run from the panel (12 loaded trucks, zero World posts). A second run was cancelled using the floating STOP button and returned `stopped:true`. Default settings remain states 17-64, refresh limit -1, Dry run enabled.

## Truck changes in Helper 0.10 (2026-10-28)

The user explicitly authorized truck attacks and separate World text after truck shares, superseding the earlier truck-only alert/no-text behavior. Bounty behavior remains unchanged: no plunder and no added chat text.

Truck attack power is now parameterized in millions, default **440**. Purple/yellow trucks with 3+ orange-fragment slots strictly below the limit are attacked; exactly two slots still share at any power, and 3+ at/above the limit share. Skip state applies to World sharing only. Attack attempts have a separate durable UUID ledger (`truck-attacks.json`) and are not repeated after completion or uncertain interruption. Dry run prevents attacks and posts.

The verified flow is truck-detail Plunder (190,827), map Plunder (270,550), then Fight (295,916). Before Fight, the controller checks the selected truck UUID, battle level 25003, exact enemy power and five selected heroes. Existing formation is reused; an empty formation takes the first five visible heroes. An incomplete formation stops. A 463.77m manual test and a 576.57m automated test both ended in defeat. The result-close check now waits for the animation to settle; a truck map popup (point type 28) closes at (100,600), unlike the bounty popup close point. A victory result has not yet been observed in testing; an unrecognized result/close control stops for manual handling.

The final requested World text is **power only**, e.g. `154m`, rounded to a whole million. The earlier fragment/box summary was tested once before the user changed this requirement. Text is sent only after the truck card's server acknowledgement. The country room is verified by its room ID; chat input uses the native keyboard path, checks the editor before and after typing, and never overwrites an existing draft. Pending and verified text receipts are stored on the truck's ledger entry. An uncertain text result is not automatically retried.

A live power-only follow-up `752m` was verified by its exact text, sender UID and new server sequence; returning to the truck list took approximately 12 seconds including chat entry, message verification and navigation. The card itself was not reposted when the follow-up was retried after a pre-send focus check. The updated rule suite has 31 passing checks, including custom attack boundaries, state filtering and power-only formatting.

Wrap-up: the user requested stopping for the day. The final additional high-power diagnostic was cancelled before it found another attack target. No automation was left running. Helper 0.10 was rebuilt with the final power-only text, editable 440m default, result-animation wait and type-28 popup-close fix. The full attack/return loop after those final fixes and a victory result still need live verification in the next session. Preserve the on-device share and attack ledgers; do not clear them to repeat tests.

## Helper 0.12: separate truck modes and active account (2026-10-28)

Supersedes the combined 0.10 attack/share rule above. Both the app and floating panel now expose three exclusive modes: Send 3+ to Gaarix privately below the power limit; Attack 3+ below the limit only while Gaarix is active; Share 2+ to World at any known power, with power-only text. Default power is 440m, strictly below. Skip state affects World only. Bounty rules remain unchanged.

Always use the currently focused game. No game launch, clone selection or resolution change is allowed. Pin window-owner PID, process start and character UID, cross-checking chat/player identities. The user explicitly permits running on main when they choose it; no permanent main block. Gaarix recipient/main UID is 2028198887000064. Private sends use a separate recipient-qualified dedup key and require an exact private room, an empty draft, copied-link identity and a new server acknowledgement.

0.12 installed on OnePlus f7c5e6fe. Native 1080x2160 retained. Persistent interactive input replaces repeated attach/detach after a development detach timeout froze the game; the user manually reopened the intended clone. Copy / Private Chat / Friends / Gaarix / paste / readback / clear passed without sending. World preview verified a qualifying truck; an installed-app floating World preview scanned 28 records over three lists, then the floating STOP button returned stopped:true and left no injector/controller. Same game PID 15684 and OnionRing92 UID 2059765822000064 remained selected. Three live identity guards and 59 host tests passed. Settings restored to Preview off, power440, skip0, states17-64.

Truck details do not need to close before selecting another road truck or refreshing. Removed the old bottom-panel dismissal taps; Refresh and the road remain usable with details open. Startup also closes a recognized old Share menu; an unfinished confirmation requires manual dismissal. Private live acknowledgement and phone battle/result return remain unverified. See PHONE_SETUP.md for the latest delivery coverage and limitations.

## Helper 0.13: World tile only (latest instruction)

The user removed the power-announcement requirement because World truck tiles already display power. World mode now shares only the tile, with an empty share note, and never opens chat to type power. The briefly proposed share-note shortcut was abandoned before any note was sent. Production follow-up code and its recovery diagnostic were removed. Preserve all existing share-ledger entries; do not resend historical cards or pending power messages. Private Gaarix links and main-only attacks retain their separate rules. Final rule/image suite: 62 passed. Live World card receipt was verified; private server delivery and phone battles remain unverified.

## Helper 0.15: live control positions

0.14's canvas-scaled bounty inputs were a temporary correction. The user clarified the intended architecture: resolve controls from the live game UI export and click their measured positions. Implemented unity-ui.js using exported instance IDs, runtime IL2CPP metadata and Unity geometry getters on a bounded render-thread callback. No hardcoded native function addresses or game action handlers. RectTransform world corners project through the actual Canvas camera; ordinary input clicks the current center after focus/account/instance/age checks. Inactive, disabled and off-screen controls stop without guessed-position fallback.

Migrated bounty map Search, State/X/Y fields, search confirmation, base-to-World, bounty Share, common share close/copy, World row and final confirmation. World row selection binds the active country room ID to the live rendered World label; confirmation verifies room/post/target plus empty input text. Server receipt now matches target identity too. Bounty map selection uses the live main camera projection of the tile position and then verifies UUID. Map conversion retains the pinned build's calibrated hex representation; map scan/zoom gestures and remaining truck/battle/private navigation are not all migrated.

Phone tests: State17/X500/Y500 fields opened via measured bounds, numeric text read back and committed game fields verified. Bounded capital scan plus one move completed, latest26 records, zero shares/attacks. A2-box bounty was used only for selection and preview: projected selection UUID matched; live Share opened menu; room/World-label matched; World confirmation opened and its note was empty. No confirmation Send or Plunder pressed. No qualifying12/15 bounty was posted in this test. Popup dismissal uses a bounds-derived short map drag: background clicking selected a neighboring base, and Back was ignored, so both were removed from that path. Hidden Search was rejected correctly at far zoom. 65 host tests and generated JavaScript syntax passed. Current build0.15 preserves settings, ledgers, native1080x2160 and the active account.
