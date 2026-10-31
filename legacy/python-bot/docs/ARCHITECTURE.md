# Bot architecture

`main_scrcpy.py` is the composition root: host paths, configuration, bot
initialization, compatibility exports and command-line lifecycle. Launchers and
Ansible continue invoking the same entry point. Runtime data stays outside the
checkout when `LASTZ_DATA_DIR` is set.

## Modules

| Module | Responsibility |
| --- | --- |
| `bot/android.py` | ADB discovery, input, screenshots, USB recovery, tool preflight |
| `bot/detection.py` | Pure visual/OCR helpers, screen classification and march evidence |
| `bot/navigation.py` | Confirmed transitions, popup recovery, base recovery, account launch |
| `bot/construction.py` | Builder queue, resource replenishment, upgrade/help workflow |
| `bot/training.py`, `bot/healing.py` | Troop completion, tier selection, queues and Hospital batches |
| `bot/radar.py`, `bot/events.py` | Manual radar dispatch and Danger Lurks activation |
| `bot/shop.py`, `bot/alliance.py` | Template-driven purchases, alliance actions and mail |
| `bot/shields.py`, `bot/shield_ui.py` | Disarmed weekly shield activation, consumption verification and grouped Discord evidence |
| `bot/research.py`, `bot/trucks.py`, `bot/gathering.py` | Research, truck and gathering workflows |
| `bot/world_bounty.py` | Preserved disabled configurable world-bounty workflow |
| `bot/scheduler.py` | Account cycles, persisted due times and retry policies |
| `bot/observability.py` | Log handlers, traces, failure evidence and action status |
| `status_store.py`, `workflow_result.py` | Atomic status/schedules and normalized outcomes |

## Compatibility boundary

`bot/context.py` is a deliberate transitional dependency seam, bound once by
the entry point. Modules do not import `main_scrcpy`, avoiding circular imports.
Configuration and legacy cross-feature helpers resolve through this context at
call time; existing configuration overrides, dynamically bound helpers and
patch-based tests remain compatible. Standard dependencies are module-local.

This is module extraction, not a claim of complete dependency isolation. New
services should accept explicit dependencies; the context can be reduced as
interfaces mature. Existing boolean/string workflow returns are preserved for
compatibility. Persisted statuses additionally expose `completed`,
`nothing_to_do`, `blocked` and `failed`, with reasons, last success, consecutive
failures, screenshot evidence and next-check timestamps.

## Scheduling and safety

- Schedule timestamps survive restarts, including confirmed 12-hour Boomer runs.
- Failed actions receive bounded shorter retries instead of a success cooldown.
- Shop scheduling uses the labelled game reset countdown when readable; otherwise
  it rechecks every six hours. A failed catalog check retries after 15 minutes.
  Sold-out limits are checked before any Buy action; no weekday is guessed.
- USB availability is probed with a three-second timeout, with 15–300 second
  backoff while disconnected. Normal gameplay stops during a known outage.
- Highest-tier selection follows detected card outlines after scrolling, requires
  selected-border evidence and rejects lower-tier confirmation warnings.
- Radar dispatch still requires a free march, positive troop capacity and a
  confirmed march-state change. Blue-button recognition does not bypass safety.

## Verification

Run `python -m unittest discover -s tests -v`. Tests include sanitized real-screen
fixtures, simulated workflows, navigation evidence, USB recovery and persisted
status. GitHub runs regression tests on Linux, macOS and Windows. Mac deployment
also runs the suite before stopping the existing service.

For a read-only deployment preflight, invoke:

```sh
scripts/run_bot.sh --preflight
```

Preflight checks host tools, configured templates and the phone connection without
updating Git or dependencies. For live gameplay validation, stop the normal
service and use the application itself under operator supervision; restore the
service afterwards. A successful test suite or button tap is not proof of a live
game outcome. Standalone validation/debug scripts have been removed.

## Repository scope

Keep only the bot, configured game assets, tests, documentation and deployment
configuration. `scripts/` contains exactly the required service launcher
`run_bot.sh` and the screenshot crop utility `scrcpy_crop_screenshot.py`.
Generated logs, captures, bytecode and runtime state are ignored, not versioned.
The explicitly requested `LastZRemotePhone/` utility is separate from `scripts/`:
it opens Windows scrcpy through SSH and temporarily stops/restores the Mac bot.
It is not part of the bot runtime or automatic deployment startup.
