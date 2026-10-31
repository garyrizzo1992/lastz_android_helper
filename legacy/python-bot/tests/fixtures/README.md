# Detector fixtures

These are real game-screen regions from operator-authorized validation.
Everything outside the relevant ROI is blacked out: no account names, chat,
currency balances, credentials or full-screen captures are retained.

- `training_viii.png`: centered tier VIII selection followed by locked IX/X.
- `training_shifted_viii.png`: shifted tier VIII selection, testing dynamic centers.
- `radar_blue_march.png`: blue March button missed by the former green-only fallback.
- `builders_mixed_rows.png`: four workers, first two occupied and third available.
- `construction_shortage.png`: Get More title and Replenish All control.
- `replenishment_insufficient.png`: inventory still cannot cover the upgrade.
- `training_unit_cap_toast.png`: short-lived refusal immediately after Train.
- `truck_two_fragments.png`: Go scanner's four purple/yellow trucks, power,
  two fragment icons and static panel controls; surrounding identity UI masked.
- `truck_three_high_power.png`: three actual fragment icons and 522.17M power;
  verifies World sharing instead of an eligible-target alert. Identity masked.
- `truck_world_share.png`: World globe, World label and repeated share controls,
  testing icon-relative channel selection without owner names or coordinates.
- `truck_world_confirmation.png`: second World confirmation's globe, label,
  Share and Cancel, with surrounding identity/chat/UI masked.
- `truck_world_receipt.png`: selected World tab and truck-card control/cargo
  regions for receipt matching; player names and avatars are excluded.
- `training_completed_queues.png`: cropped portraits/checkmarks, including a
  checkmark touching a queue timer; no account HUD or chat is included.
- `shield_buff_info.png`: shield inventory/status panel, with all surrounding
  account UI blacked out; verifies durations, plain Use and rejection of Purchase & Use.
- `shield_replacement_prompt.png`: observed generic existing-buff replacement
  warning and Confirm/Cancel controls; the live probe was cancelled without
  consuming an 8h shield or shortening the active 24h protection.

Use the screenshot crop utility to prepare assets; sanitize fixtures by blacking
out every region outside the detector ROI before committing. Detector tests do
not require a phone, network or Tesseract installation. Preserve native screen
dimensions for fixtures whose detectors use scoped ROIs.
