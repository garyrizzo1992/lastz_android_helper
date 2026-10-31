# Weekly peace shields

Do not enable unattended activation before the operator approves a live test.
`shield_activation.enabled`, `ui_calibrated` and `schedule_enabled`
default to false. Normal deployment does not turn
them on, activate shields or send shield reports. Automated tests mock all taps
and Discord requests.

The operator authorized an automatic four-account rollout on 2026-10-16 and
confirmed that Auto Team-Up does not break shields. It is not switched off.
Arming is host-specific in external bot.env, not committed source defaults:

```dotenv
LASTZ_SHIELD_ACTIVATION_ENABLED=true
LASTZ_SHIELD_UI_CALIBRATED=true
LASTZ_SHIELD_SCHEDULE_ENABLED=true
```

For weekly operation, remove dated `LASTZ_SHIELD_START_AT` and
`LASTZ_SHIELD_8H_START_AT` overrides and account-subset overrides from bot.env.
Both weekly operations target all four accounts. Europe/Malta handles daylight
saving changes automatically. Weekly operation was authorized on 2026-10-17.

The dated start above is an example, not the deployed start time. Set it to the
desired future time with an explicit UTC offset. It replaces the Friday start
for that operation only (including the first hour's catch-up, bounded by Saturday
03:30), does not recur next week, and retains the Saturday 21:00 schedule.
Without dated overrides the weekly schedule applies.
The scheduler, not an operator's ADB session, performs all activation taps.
`LASTZ_SHIELD_ROLLOUT_ACCOUNTS` limits only the 24h rollout. Omit it to target all
four accounts. Excluding an already-protected account does not exclude its
Saturday 8h renewal: the fixed weekly renewal targets all configured accounts.
An explicit `LASTZ_SHIELD_8H_START_AT` schedules an 8-hour rollout for the
listed `LASTZ_SHIELD_8H_ROLLOUT_ACCOUNTS` (all four when omitted). It is a
one-hour catch-up window and uses the same evidence and Discord reporting as
the normal scheduler. During this explicit rollout, an active shield shorter
than eight hours may be replaced to extend protection. The fixed Saturday
21:00 rollout also extends a shorter active shield; legacy expiry-based
renewals retain the conservative near-expiry guard.
For a dated start less than ten minutes away, the bot holds normal rotation
until the due time rather than starting a potentially lengthy maintenance cycle.

## Schedule

- Target accounts: game1, game2, game3 and game4.
- Friday: one 24-hour shield per account, starting at 23:00 Europe/Malta.
- A due sweep takes priority at cycle boundaries; it does not wait through all
  four normal 20-minute rotation slots. It cannot interrupt an in-progress tap.
- Startup catch-up for the Friday run is bounded to Saturday 03:30 Malta time.
- Saturday: one 8-hour shield per account, starting at 21:00 Europe/Malta,
  with a one-hour catch-up window. This runs even without a verified Friday
  manifest. A shorter active shield is replaced to extend protection.
- Each week's dated operation records prevent repeat consumption, including
  after restarts. This Saturday's completed 8-hour operations remain completed.
- Retry pre-activation failures after five minutes; never repeat an uncertain Use.

Exact event-end/reset behavior around daylight saving time still needs operator
confirmation before unattended scheduling. No claim of uninterrupted protection
is made while the Mac, phone or USB connection is unavailable.

## Activation and evidence

The live-observed path is base -> World -> own HQ -> Buff -> Peace Shield. Buff
and Peace Shield navigation use live-captured templates because their outlined
labels were unreliable with OCR. Only the World toggle and HQ navigation tap
use calibrated coordinates. Duration selection uses separate live-captured
24h/8h icon templates and rejects competing matches; Owned and a full plain-Use
button template are scoped to that detected row, not its position in a shop/grid.
The different Purchase & Use button is never an activation fallback.

The Buff Info panel contains an explicit Owned count for each duration, even
when zero. This is the shield-inventory view used for the reports. The workflow:

1. Read current protection and save the inventory BEFORE image.
2. Save a durable activation-attempt fence, then click Use on the verified row.
3. Accept only an authorized replacement confirmation for the selected shield;
   cancel unknown, purchase or diamonds prompts.
4. Save the inventory AFTER image and require exactly one fewer shield.
5. Take a fresh third screenshot of the shield status/countdown and require a
   duration consistent with the requested shield.

If existing protection already covers the requested duration, save the evidence
but do not consume another item.
A Friday 24-hour shield may extend an existing shorter shield.

## Discord delivery

Each account gets one message with three ordered attachments and image previews:
before inventory, after inventory and countdown. The message identifies the
account, duration, operation/date, verified remaining time and Malta expiry.

Use the existing treasure-channel `DISCORD_TREASURES_WEBHOOK_URL` (or
`discord_treasures_webhook`). There is deliberately no fallback to the general
log channel. A channel name alone cannot authorize a webhook post. The dedicated
webhook was restored to the Mac's external bot.env (mode 0600) on 2026-10-16.
The launcher loads that file on the next bot start. Never commit the URL/token.

Discord multipart delivery uses `wait=true` and requires a returned message ID
and every requested image filename in returned attachments or Discord-hosted
embed images. Discord may return an empty attachments list when displaying the
uploaded files inside embeds. The request format follows the
[official webhook API](https://docs.discord.com/developers/resources/webhook#execute-webhook).
Failure/partial evidence is explicitly NOT VERIFIED, not a success report.

Reports and transaction state are retained under `shield_state_dir`, defaulting
to `LASTZ_DATA_DIR/runtime/shields/<account>/<Friday-date>-24h/` (or `-8h/`).
Discord failures retry delivery only, without repeating activation. Delivery is
at-least-once if an acknowledgement is lost; operation IDs identify duplicates.

## Recovery and coverage alerts

Added after the Game 2 incident on 2026-10-24:

- After Use, the UI retries fresh timer reads before interpreting background
  Purchase & Use text as a confirmation. Unknown dialogs are still cancelled.
- An uncertain activation is reconciled without another Use: require the
  inventory to decrease by exactly one and two fresh timers whose expiry
  matches the original activation. The original manifest is archived first.
  Failed verification retains `failure.png` and subsequent observations.
- An old ambiguous operation whose maximum possible duration has elapsed is
  archived as `expired_unverified` following a fresh live check. Its historical
  consumption is not claimed as verified, and that operation is never repeated.
- Every blocked renewal queues an urgent Discord notice, even if navigation
  or activation never begins. Blocked attempts persist a retry timestamp to
  prevent repeatedly interrupting normal game rotation.
- The Saturday coverage monitor runs independently of activation outcomes and
  continues after the activation catch-up window closes. With the scheduler
  armed, it reads one due account's live timer per sweep, at a default interval
  of 15 minutes per account (`health_check_interval`). These checks never Use
  an item. The scheduler relaunches the appropriate account after an audit.
- Between live checks, expiry warnings use the last verified deadline. Alerts
  trigger at 60, 30 and 10 minutes remaining, on expiry, or when protection is
  unknown. After Saturday 21:10, any account lacking verified coverage through
  Sunday 04:00 Malta also generates an overnight-coverage warning. DST is
  handled using Europe/Malta. Live checks and warning generation continue
  through Sunday 06:00 Malta so the overnight shield's expiry is monitored;
  queued delivery retries continue afterwards. These alerts never activate
  or replace a shield.
- Four-account summaries report ALL FOUR VERIFIED or identify every missing
  account. An incomplete summary is sent after a ten-minute grace period;
  a complete summary follows when all accounts are verified.

Alert records and immutable evidence live under `runtime/shields/_health/`.
Failed Discord deliveries persist across restarts and retry with backoff
(60 seconds up to 15 minutes). At most two notices are attempted per sweep.
Verified recovery cancels obsolete queued warnings without recording a false
delivery acknowledgement; another failure can open a new incident that week.

This monitor runs in the bot process. It cannot send new observations if the
Mac or bot is offline, and a failed delivery cannot notify anyone until network
access returns. An external heartbeat monitor is needed to cover host outages.

## Safety and rollout

The live Buff Info screen explicitly warns that initiating an attack deactivates
Peace Shield. The normal scheduler suppresses new radar marches, gathering,
world-bounty/truck plunder while recorded protection is active or a Use attempt
is uncertain. Auto Team-Up has no shield-related gates or suppression, based on
the operator's confirmation that it does not break shields. Existing in-game
Auto Team-Up activation is not cancelled. Manual attacks are
outside the bot's control.

Per-account locks prevent overlapping activation. A crash/uncertain Use, corrupt
transaction state or stale lock requires checking the actual timer/inventory
before reconciliation. Do not delete those fences simply to retry a Use tap.

Read-only live checks are separate from consumption tests. The active countdown,
replacement popup and before/after consumption proof remain unverified until
the user approves activation. Test one account under supervision before arming
the four-account schedule. Restore the normal bot after exclusive inspection.

Read-only inspection on 2026-10-16 visited all four accounts' Buff Info panels.
Games 1-3 showed 1 x 24h and 17 x 8h shields; game4 showed 3 x 24h and 25 x 8h.
All four were Inactive. Actual captured frames verify both duration matches and
distinct Use targets; outlined labels required template-based detection. No Use
or replacement confirmation was pressed and no Discord report was sent.

Subsequent webhook setup sent clearly labelled delivery tests using the saved
read-only Game 4 inventory screenshot. Discord returned the uploaded image in
an embed, exposing and correcting a false-negative delivery acknowledgement.
These test messages are not shield-activation evidence. Activation remains disarmed.

## First scheduled rollout findings (2026-10-16)

The operator authorized a dated 23:30:35 Malta rollout. Game 1 consumed its final
24h shield successfully, but its now-empty item row changed to Purchase & Use.
The original broad confirmation guard mistook that background inventory text
for an unknown modal and recorded an uncertain result. Live manual review
confirmed Owned 1 -> 0 and an active countdown consistent with the original
scheduled Use; no additional shield was consumed. The original uncertain
manifest is retained alongside the reconciled verified record, and a corrected
three-image report was acknowledged by Discord.

Activation now recognizes the identified Buff Info panel with a matching active
countdown before treating background purchase text as a confirmation. The
controller still independently verifies exactly one consumed shield and a fresh
timer. Timer reading also uses two agreeing numeric OCR preparations of the
countdown bar, with bounded fresh-frame retries for unreadable results.

The bot was stopped and the host-specific activation flags were disarmed at the
operator's request for investigation. Other accounts' uncertain/missing records
were not cleared or consumed during the Game 1 review. Resume requires an
explicit operator decision. The one-off 23:45 audit remains read-only.

### Existing-shield replacement prompt

An authorized live Game 1 probe opened the 8h Use control while its 24h shield
was active. The game displayed: "Some Buff activated already. Further activation
will replace the current one. Continue?" with Confirm/Cancel buttons. This is
replacement, not an addition to the existing countdown. The probe was cancelled;
8h inventory stayed 17 and the 24h countdown continued unchanged apart from
elapsed time. No replacement was confirmed early.

The bot recognizes this exact warning plus its Confirm button using captured
templates. Confirmation is allowed only after the requested duration's verified
inventory row was selected, existing protection was observed, replacement is
authorized, and the controller's 30-minute renewal guard permits the attempt.
Purchase/diamond prompts and unknown controls remain blocked. The existing
inventory-delta and fresh-countdown checks still follow any actual confirmation.
Actual replacement consumption remains to be verified when renewal is due.
