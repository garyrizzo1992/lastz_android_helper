# Truck cargo filters and shared destination —0.34

Installed2026-10-30, Europe/Malta. User clarified that the listed cargo combinations belong to ONE button (the repeated1frag/3boxes entry was a duplicate), and that ONE destination choice must apply to both trucks and bounties. No agents used.

## Controls

Main screen and floating controls now have one mutually exclusive radio selector: Trucks group / World Chat. It saves shareDestination immediately and is reused by every sharing button. Default is World when no prior value exists. Attack remains separate and ignores the selector.

Truck buttons: Share2+orange frags; Share3+orange frags; Share cargo combos; Attack3+onGaarix. Bounties: Share bounties. Removed destination-specific truck and bounty buttons from both interfaces.

Share cargo combos accepts ANY of:

- At least4Lv.3module chest icons.
- At least1orange-fragment icon and3module chest icons.
- At least2orange-fragment icons and2module chest icons.
- At least3orange-fragment icons, regardless of boxes.

Each module chest icon counts as ONE box for matching/communication, although its underlying quantity is2. Orange fragments are also counted by separate current reward icons/slots. Base and extra CURRENT goods are combined. Other chest types, other fragment grades and resources do not count. Only yellow/purple trucks qualify, as before. Group truck shares retain the strict configured power limit (default440m); World truck shares accept any known power. Skip state remains a World-only restriction, matching its UI label and earlier behavior. Main may post to its own trucks group; group posting is no longer incorrectly rejected as a private message to oneself. Combat still requires the exact explicit attack mode on Gaarix.

## Metadata and safety

Lv.3 module chest is item253102, observed icon car_compon_giftbox_blue. Its template name-value backing table includes language-key898551 with argument"3". Live read-only TruckProbe inspection on OnionRing92 UID2059765822000064, PID4389/start16784835 found12trucks and3module icons, each with quantity2. The current sample contained no cargo-combo match. No game input, share, attack, refresh or injector was used to read that sample.

TruckCargo validates item/type/quantity, counts each253102;7;2 entry once and rejects unexpected nonzero module quantities. TruckProbe now exports moduleBoxIcons/moduleBoxQuantity; stable snapshot signatures include both fields. Existing orange-slot quantities remain available separately.

TruckPolicy applies the selected filter to candidates. Actual share-menu payload AND final confirmation payload are revalidated for exact UUID/grade/power/orange slots/module icons in both World and group flows. Room/sender/empty-note/receipt checks remain. The big blue truck Share route and combat guards are unchanged. Dedup continues to use existing per-destination World/group ledger keys, so switching filters does not repost to the same destination. No ledger reset or uncertain-send retry.

Internal generic actions truck-share-2/truck-share-3/truck-share-cargo/bounties-share resolve once in JobRunner using the saved destination. Legacy explicit internal modes remain supported for diagnostics, but have no duplicate channel buttons in the UI.

## Validation and installation

Full validation passes86existing rule checks plus52new cargo/destination checks and all existing maintenance/native/geometry/Python suites. Cases cover every combination at both destinations, near misses, wrong item/grade/type/quantity, one-icon-vs-two-items, strict group power limits, missing metadata, main group posting, and no combat capability in any cargo sharing mode.

Signed versionCode34/versionName0.34 installed. All9XML/JSON settings/history/checkpoint hashes matched immediately before/after installation. Live Android UI hierarchy confirmed both selector options, all new truck sharing buttons and the single Share bounties button; channel-specific buttons were absent. Switched selector Group->World and verified immediate preference persistence, then restored the original/default World choice. Other run preferences unchanged. The new shareDestination field is the intentional settings addition from that UI test. No gameplay job was started.

Evidence in runtime/helper-build: cargo034-validation.txt, cargo034-build.txt, cargo034-install.txt, cargo034-{before,after}-persistent.json, cargo034-ui-verification.json, cargo-live-reader.json, module-template-253102.json and module-template-level-args.json. Local reproducible diagnostics cargo_reader_check.py and check_cargo_ui.py. No new live chat post is claimed; the available sample did not match the cargo combinations.

Current state: helper0.34 installed, floating controls open, destination World, no controller/injector running. Earlier migration STOP remains. Do not restart old bounty/truck jobs or switch/reopen clones implicitly. User can choose the destination and press Share cargo combos to run the new filter.
