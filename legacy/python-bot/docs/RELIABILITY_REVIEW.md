# Reliability changes — 25 October 2026

Five issues identified in the live-log/code review are addressed:

1. Shield health checks run throughout Saturday and until Sunday 06:00 in
   `Europe/Malta`, covering both DST folds. Expiry notices are not cancelled
   simply because an expiring shield previously covered reset. No change to
   Friday 23:00 / Saturday 21:00 activation schedules or Use safeguards.
2. Troop collection runs even during the one-hour full-cap training cooldown.
   Strict portrait templates have a scoped green-check shape fallback, with
   two real-screen variants. Collection success requires the clicked marker
   to disappear; an unchanged marker stops the scan without another click.
3. Personal bounties retry the Wanted shortcut and fall back to its visible
   sidebar label. Opening must still verify Bounty Missions. Missing entry
   is reported as unavailable/not inspected, never as completed missions.
   No speculative coordinate navigation or world bounty hunting is enabled.
4. Healing success requires observing the active/request-help Hospital state,
   with bounded transition polling. Alliance-help confirmation is recorded
   separately. Panel Claim/Collect also requires its control to disappear.
5. The Bash launcher explicitly propagates failure from Git, environment,
   dependency and working-directory steps. This works even when its function
   is called inside an `if` by the USB retry loop (where Bash suppresses
   implicit `set -e` handling). Failed dependencies cannot write a success
   fingerprint or launch the bot.

Deployment validation also encountered a Galaxy artifact HTTP 403 (a stale
download redirect). The Mac's exact pinned `community.general:11.4.0` artifact
was fetched with a fresh URL and checked against Galaxy's SHA-256 metadata
before installation. Deployment retains visibility of the user's collection
cache when Galaxy legitimately skips installing an already-satisfied pin.

Regression tests cover overnight/DST alerts, full-cap collection, unchanged
markers, real checkmark crops, delayed/absent healing confirmation, bounty
label navigation, and launcher failures in retry mode.

Limitations: shield alerts still depend on the bot process and network being
alive. Missing Wanted does not prove daily missions are exhausted; it remains
eligible for the regular retry. Live action tests can only prove collection
or healing when the game actually offers those actions.
