# Alliance Shop purchases

Enable individual entries in `CONFIG["alliance_shop_catalog"]["products"]`.
Only Badge (10 bundles), 24h Peace Shield (1), and 8h Peace Shield (3)
are enabled by default. The game's remaining weekly allowance caps the
quantity selected with the dialog's plus button.

The flow matches item artwork in overlapping scrolling views, detects the
gold price footer beneath that artwork, and verifies the purchase-dialog
title before buying. Shield templates compete against each other to avoid
confusing the 8h and 24h variants. Fixed grid positions are not item selectors.

Success requires a Congratulations heading and the requested reward name.
They are OCR'd separately because the animated artwork and barbed wire
interfere with full-dialog OCR. Reaching the game's weekly purchase limit
is recorded as skipped/satisfied, not as a new purchase. Out-of-stock or
unconfirmed purchases are failures and are not marked weekly complete.

Troubleshooting logs include template matches, detected price buttons,
rejected dialog titles, and the reward heading/name. Trace screenshots are
stored under the configured data directory, subject to the trace budget.

October 2026 root causes: artwork taps opened information tooltips instead
of purchase dialogs; long scrolls clipped shield icons; whitespace-sensitive
title checks rejected `8hPeaceShield`; broad reward OCR missed successful
purchases. Regression tests: `python -m unittest tests.test_alliance_shop`.
