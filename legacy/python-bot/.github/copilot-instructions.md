# LastZ Bot - Project Guidelines

## What is this bot?

The bot runs four Last Z Android installs through one USB-connected phone. It
uses ADB screenshots, OpenCV template matching, OCR, and ADB input to keep the
accounts progressing while avoiding unsafe clicks when a screen cannot be
confirmed. A feature is successful only when its intended post-condition is
verified; a workflow that merely tapped its controls is recorded separately as
incomplete or unavailable.

## Game accounts / profiles

| Key | Coordinates | Account type | Special behaviour |
|---|---:|---|---|
| game1 | (126, 1191) | Farm 1 | Standard farm automation |
| game2 | (331, 1191) | Farm 2 | Standard farm automation |
| game3 | (549, 1191) | Farm 3 | Standard farm automation |
| game4 | (745, 1191) | Dassy | Standard automation |

## Function intent and success criteria

### `send_troops_gathering` - Gather resources

Start from a confirmed base, open World, search for Food or Wood, select a
resource node, and dispatch a march.

**Success:** World is confirmed; the march counter is readable; a free march
is confirmed; a node is selected; the dispatch control is tapped; and the new
march appears in the sidebar or the march count increases. The bot then
returns to a confirmed base.

**Acceptable failure:** No valid node or no free march is available after the
configured search attempts. Record this as `unavailable`, not a failure. OCR
that cannot prove a free march must never cause a dispatch tap.

**Observed issue:** Aggregate OCR correctly read `3/3` during the 2026-07-31
live run, but individual march states were `unknown`. This is safe, but limits
dispatch precision and is the next OCR improvement target.

### `do_trucks` - Trade truck dispatch

Open the Truck UI from a confirmed base, confirm the truck page, OCR the daily
trade counter, collect completed trucks, and dispatch only as many new trucks
as the counter allows.

**Success:** Truck UI is confirmed; OCR returns a valid `used/total` counter;
completed trucks are collected when present; no more than `total - used` trades
are dispatched; when `trades_left == 0`, daily completion and the next-reset
cooldown are persisted; and the bot returns to base.

**Acceptable failure:** OCR failure is an observable safe skip. The bot must
not guess a trade count or set a daily cooldown when the counter is unknown.

**Observed result:** The live run parsed `Today's Trade Count: 4/4`, set the
daily cooldown, and returned to base successfully.

### `do_bounty` - Bounty dispatch

Open the bounty building, assist ally missions, collect completed claims, and
dispatch a new bounty when one is available.

**Success:** Every attempted sub-action is screen-confirmed. Dispatch is
successful only when `bounty_go` is no longer visible after the dispatch flow.
No available bounty is `unavailable`, not a failure.

Partial work is acceptable when a normal screen state explains the missing
sub-action, but status details must say which of assist, claim, and dispatch
completed. Reward-value verification is not yet implemented.

### `plunder_world_bounties` - State-map bounty hunting

This is a separate workflow from personal bounty dispatch. From a confirmed
base, open World and visit the configured hotspot route through the bottom-left
coordinate search. The initial route is State 1 X497 Y647, State 10 X540 Y357,
State 47 X138 Y77, then State 18 X561 Y397. Each coordinate jump resets the map
scale, so at every hotspot the bot makes two calibrated inward two-finger pinches
through the headless scrcpy control channel before scanning. This is Raspberry
Pi-compatible and reaches the user-approved bounty-search zoom level.

**Success:** Each destination state is confirmed before scanning; each bounty
marker is positively detected before tapping; the resulting target card shows
the Plunder action; Plunder is tapped once; the reward overlay appears and is
dismissed; and its high-contrast "Congratulations!" title is read before the
marker is counted. Stop immediately after five
confirmed rewards, then restore the base view and record `5/5` daily complete.

**Acceptable failure:** No marker is found after the bounded scan, a selected
marker has no Plunder action, or a reward overlay does not appear. These cases
must not increment the daily count. A lost/unknown screen aborts the scan and
recovers to base.

**Safety bounds:** Never navigate outside States 1-63 or map coordinates 0-1200;
never use an unconfirmed coordinate-search form; cap map swipes and candidate
taps; exclude the animated HUD/event column; re-detect after every UI transition;
and stop if the same screen state repeats without progress. Android-client
calibration is required because the supplied marker examples came from a
differently scaled Windows client.

### `do_hourly_action` - Alliance help

Open Alliance, visit Techs, exhaust the verified donation counter, and visit
the configured Gifts views.

**Success:** Alliance, Techs, and Gifts screens are confirmed; OCR verifies
the Tech counter reaches its expected end state; configured gift views are
visited; and the bot restores base. A normal zero-work state is `unavailable`;
a lost screen or failed confirmation is a failure.

### `run_one_cycle` - Action priority

The current priority is accepted for now:

1. Recover/confirm base and collect VIP rewards.
2. Run due trucks, passive notifications, Mail, troop training, and the
   8-hour chest.
3. Attempt construction and research.
4. Gather troops, then complete Alliance Tech/Gifts work.
5. Dispatch personal bounty work, run any due world-bounty plunder scan, and
   finish by restoring the base view.

The next optimization target is cycle duration. The first live cycle with
multiple daily flows due exceeded six minutes, largely because Mail, OCR, and
Alliance flows each perform multiple stability checks. Measure more cycles
before changing this order.

## Template reliability notes

Observed during the 2026-07-31 live run:

- `home` was reliable enough to confirm the base after launch and recovery.
- `truck` opened successfully and the trade counter OCR parsed correctly.
- Mail navigation and Mail-screen confirmation worked across all six tabs.
- March aggregate OCR was safe but did not classify individual slots.
- Tesseract library DEBUG output was excessively noisy; runtime logging now
  keeps that library at WARNING while retaining the bot's OCR result logs.

## Features that are incomplete or need stronger evidence

- Mail verifies tab traversal and return-to-Mail, but not that every available
  reward balance changed after Claim All.
- Research and construction report `unavailable` when no confirmed action is
  visible; completion-value verification is not implemented.
- Per-march OCR does not yet classify each sidebar slot reliably.
- The fifth launcher icon is visible on the phone but `game5` remains disabled.

## Environment

**OS:** Windows PowerShell workspace

**Device:** USB ADB device `f7c5e6fe`, OnePlus 5T

**Tesseract:** available to the active Python environment/PATH

**ADB:** available in PATH; the repo also includes `scrcpy/adb.exe`

**Cycle baseline:** still being measured; the first live cycle on 2026-07-31
exceeded six minutes because multiple daily flows were due.

## Evidence

Live evidence is stored under `debug/live_*.png`, including the launcher, a
confirmed game base, Truck UI (`4/4` exhausted), Mail System tab, and World
view with `3/3` marches busy.
