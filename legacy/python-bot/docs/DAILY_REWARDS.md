# VIP and personal bounty automation

Restored and live-tested on 2026-10-23. The earlier personal-bounty removal
(`f038e63`) also removed ally assistance. The replacement lives in
`bot/daily_rewards.py` and opens the Wanted sidebar shortcut with an image
template, avoiding the old building-list navigation.

`CONFIG["personal_bounties"]["enabled"]` controls personal dispatch, reward
collection and ally assistance. It defaults to true, with a 15-minute check
interval per account. Ally Help actions require an increased Assist Ally
counter. Hero dispatch requires the hero-selection screen and a decreased
remaining-mission counter after returning to the list. World-objective GO
cards are skipped; world bounty hunting remains disabled separately.

`CONFIG["vip_rewards"]["enabled"]` controls daily login points and Daily
Freebies. The bot opens VIP even if the old notification template does not
match. Both rewards must produce a reward confirmation or show a readable
cooldown before the account is marked complete for the daily reset period.
Incomplete checks retry after 15 minutes; they are not marked complete merely
because a tap was sent. Daily completion persists across bot restarts.

The Wanted icon, outlined bounty buttons, Daily Freebies Claim and animated
reward banner use image templates. OCR confirms panel titles, tabs, counters,
cooldowns and hero-selection controls. All workflows return to the base after
completion or failure. Action status distinguishes `bounty`, `bounty_assist`
and `vip_rewards` for account-by-account troubleshooting.
