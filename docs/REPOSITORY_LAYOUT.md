# Standalone Android helper repository

Created 2026-10-31 at the user's request. Repository: https://github.com/garyrizzo1992/lastz_android_helper.

| Work | Location here |
| --- | --- |
| Android Java app, floating overlay, native agent and tests | `tools/last-z-helper/` |
| Current continuation checkpoint | `docs/CURRENT_HANDOFF.md` |
| Full migration contract and remaining plan | `docs/ANDROID_BOT_PARITY_HANDOFF.md`, `docs/ANDROID_BOT_REMAINING_PLAN.md` |
| Feature investigations, audit and historical migration notes | `docs/`, `docs/archive/` |
| Preserved Python source used for migration and compatibility work | `legacy/python-bot/` |
| Local signed release and signature sidecar | `bin/` (ignored) |
| Local build evidence, signing key and test cache | `runtime/helper-build/` (ignored) |
| Local bounty research, rooting files and phone backups | `runtime/` (ignored) |
| Local ADB dependencies | `scrcpy/` (ignored) |

The Android source layout is preserved so existing root-relative build scripts and evidence utilities work from the new checkout. The one cross-repository ownership-test import now points to the preserved Python snapshot. The standalone build no longer needs the neighboring Last Z checkout.

The reference includes the former uncommitted Python device-selection, bounded-log delivery, screenshot-default and shared-ownership changes, plus their tests. Those changes belong to the migration work; the original Python checkout is restored to its tracked baseline. That reference must not be mistaken for an already deployed Mac service.

Signing keys, credentials, device state, backups, generated assets and APKs stay local. Preserve the existing key to update an installed helper; a fresh clone does not contain it. `fetch_assets.py` downloads official checksum-pinned injector dependencies when needed.

Published source was checked for private keys, tokens and literal credentials. Earlier Git history of the original Python repository is retained; cleanup removes Android migration material from its current branch tree rather than rewriting past commits.

Local transfer verification and manifests live under ignored `runtime/migration-transfer`. No phone actions or deployment are needed merely to move source repositories.
