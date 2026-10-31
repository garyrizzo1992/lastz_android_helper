# Feature audit — 5 October 2026

Personal-bounty navigation was removed at the user's request: the scheduled
call, method, feature flag, and navigation-specific template/config entries
are gone. World-bounty hunting remains disabled. Existing images and
historical action records were preserved.

Other issues investigated using Mac logs, retained screenshots, and source:

- Training: game 1's failure screenshot shows the modal "Higher-tier units
  unlocked. Continue training lower-tier ones?" The routine selected tier VI,
  did not handle this modal, and reported an unconfirmed start. Carousel
  movement is currently disabled; highest-tier selection needs correction,
  not automatic acceptance of lower-tier training.
- Manual radar: game 3's screenshot shows a valid dispatch panel, positive
  capacity (1,924/1,924), a free march, and a blue March button. OCR missed the
  label and the fallback searches only green buttons, explaining the abort.
- Shop: all accounts' last recorded checks were 3 October. The scheduler
  uses a 604,800-second interval from the last completed scan, not the game's
  weekly limit reset. This can postpone shopping after allowances refresh.
- Boomer: the configured check interval is one hour despite the activation
  lasting twelve hours; today's logs contained 47 successful activation
  messages, indicating unnecessary repeat work.
- Construction/research: starts are confirmed, but alliance-help handshakes
  are still intermittently missing. Base recovery also logged home-view
  timeouts and needs a separate review.

These findings are diagnostics, not implemented fixes. The code change in
this revision is limited to removing personal-bounty navigation.
