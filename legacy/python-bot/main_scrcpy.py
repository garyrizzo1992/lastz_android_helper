# --- ADB BOT FOR PHYSICAL DEVICE (ONEPLUS A5010) ---
"""
LastZ Bot — ADB-controlled automation for the mobile game LastZ (Android).

═══════════════════════════════════════════════════════════════════════════════
OVERVIEW
═══════════════════════════════════════════════════════════════════════════════
This bot connects to a physical Android phone over USB using ADB (Android Debug
Bridge).  It captures the game screen with `adb exec-out screencap -p`, decodes
the PNG into an OpenCV image, and injects touch events / key events back through
`adb shell input tap` / `adb shell input keyevent`.

The game (LastZ) is installed 4 times on the same handset via a parallel-space
app so that four independent game accounts can coexist.  Each install maps to a
different home-screen icon at a known (x, y) pixel coordinate.  The bot cycles
through all four slots ("game1" … "game4"), spending `rotation_minutes` (default
20 min) per slot before moving on.

═══════════════════════════════════════════════════════════════════════════════
PHYSICAL SETUP
═══════════════════════════════════════════════════════════════════════════════
  Device    : explicit LASTZ_DEVICE_SERIAL or one unique CONFIG["device_model"] match
  Host OS   : Windows 10/11, Linux / Raspberry Pi, or macOS.
              ADB and Tesseract are resolved from explicit environment
              overrides first, then from PATH.
  USB       : Single device; resolved via `adb devices` + model-name match.
              Falls back to the first available device if the model is not found.
  Resolution: Full phone screen captured at native res (typically 1080 × 2160).
              All hardcoded pixel coordinates in CONFIG assume this resolution.

═══════════════════════════════════════════════════════════════════════════════
GAME SLOT COORDINATES  (home-screen icons)
═══════════════════════════════════════════════════════════════════════════════
  game1 → (126, 1191)    game2 → (331, 1191)
  game3 → (549, 1191)    game4 → (745, 1191)

═══════════════════════════════════════════════════════════════════════════════
MAIN LOOP  (see main() and run_one_cycle())
═══════════════════════════════════════════════════════════════════════════════
Each outer rotation iteration:
  1. Shuffles game order randomly for variety.
  2. Calls launch_game(game_name)  — taps the home-screen icon, waits 15 s for
     the game to load, then calls ensure_base_view().
  3. Repeatedly calls run_one_cycle() for `rotation_minutes` seconds.
  4. Calls close_all_apps() before switching to the next game.

Each run_one_cycle() performs the following actions in priority order:
  1.  VIP reward and troop healing    urgent checks before long workflows
  2.  Visible passive actions         every minute
  3.  Full construction-marker sweep  once daily
  4.  Mail, troop training, chest     independent daily/interval gates
  5.  Construction and research       every 5 minutes
  6.  Alliance daily actions          persisted daily, 15-minute failure retry
  7.  Trade trucks                    every 2 minutes, after maintenance work
  8.  Gather troops (world map)       every 2 minutes

Personal bounty missions and ally assistance are enabled; world bounty hunting is disabled.

═══════════════════════════════════════════════════════════════════════════════
IMAGE MATCHING  (see find_template())
═══════════════════════════════════════════════════════════════════════════════
Two complementary OpenCV algorithms run in sequence per template lookup:

  SQDIFF  (cv2.TM_SQDIFF_NORMED)
    • Lower score = better match.  Accept if score ≤ threshold (default 0.05).
    • Supports alpha-channel masks (transparent-background PNGs).
    • Used for resource icons, troop icons, chests, VIP, etc.
    • Per-template thresholds can be overridden in CONFIG["template_thresholds"].

  CCOEFF  (cv2.TM_CCOEFF_NORMED)
    • Higher score = better match.  Accept if score ≥ 0.85 (configurable).
    • Runs in grayscale — faster than SQDIFF, used as the primary fast path.

Both methods iterate over a list of scale factors to tolerate minor resolution
differences.  Default fast mode uses [1.0] only; full mode adds ±3 % and ±6 %
variants.  Scaled template crops are cached in an LRU dict (max 200 entries).

═══════════════════════════════════════════════════════════════════════════════
OCR  (see extract_text_from_roi(), send_troops_gathering(), do_trucks())
═══════════════════════════════════════════════════════════════════════════════
Tesseract 5 is used for exactly two OCR tasks:

  Troop march count
    ROI pixels (982, 997) → (1051, 1033) in the world-map view.
    Expected text format: "X/Y"  (e.g. "2/3" meaning 2 marches active of 3 max).
    If the OCR result contains impossible values (any number > 3, or used > total)
    the reading is silently discarded to prevent sending marches when full.

  Truck trade count
    ROI pixels (80, 35) → (580, 125) inside the Truck building UI.
    Expected text format: "X/Y"  (e.g. "1/3" meaning 1 trade used of 3 max).
    Multiple Tesseract OEM × PSM combinations are attempted; the first result
    containing a valid fraction wins.  On OCR failure, trucks are skipped for
    this cycle and no cooldown is set (to retry next cycle).

═══════════════════════════════════════════════════════════════════════════════
TRUCK COOLDOWN LOGIC
═══════════════════════════════════════════════════════════════════════════════
Trade trucks reset once per day at CONFIG["daily_reset_hour"] (default 04:00
Europe/Malta, including DST). When OCR reads 0 remaining trades, or when all trades are consumed
during a dispatch loop, a per-game cooldown timestamp is recorded that equals
the next daily reset epoch.  Trucks are skipped for that game until that epoch.

Cooldowns are persisted to logs/trucks_state.json and reloaded on restart, so
the bot respects the cooldown even after a crash or manual restart.

═══════════════════════════════════════════════════════════════════════════════
OBSERVABILITY / TRACING
═══════════════════════════════════════════════════════════════════════════════
When CONFIG["internal_trace_enabled"] is True (default on):
  • Every significant bot event is appended as a JSON line to
    logs/trace_<timestamp>.jsonl  (see _obs_event()).
  • Optional screenshots are saved under debug/trace/<session>/ when
    internal_trace_screenshots is True (disabled by default to reduce I/O).

Discord webhook (optional): log records at or above discord_level (default INFO)
are forwarded to a Discord channel via stdlib HTTP in the emit() thread.
Simple rate limiting (min_interval) and auto-disable after 5 consecutive HTTP
errors prevent the Discord handler from hanging the bot.

═══════════════════════════════════════════════════════════════════════════════
KEY CONFIG SECTIONS  (all in the module-level CONFIG dict)
═══════════════════════════════════════════════════════════════════════════════
  game_coords             home-screen tap targets per game slot
  action_coords           all in-game UI tap targets (world, alliance, etc.)
  resource_levels         resource level filter button positions (levels 1–6)
  timing                  delays, periodic intervals, rotation cadence
  template_thresholds     per-template SQDIFF acceptance threshold overrides
  template_scales         scale variants to try during template matching
  image_paths             template name → PNG file path mapping
  game_settings           per-slot feature flags (e.g. train_troops)
  daily_reset_hour        local hour at which truck trades reset (default 4)
  screenshot_min_interval_ms  throttle: minimum ms between consecutive screencaps
"""
import cv2
import numpy as np
import time
import subprocess
import random
import os
import sys
import psutil
import datetime
import platform
import logging
import argparse
import json
from difflib import SequenceMatcher
from logging.handlers import RotatingFileHandler
import pytesseract
import re
from pathlib import Path
import shutil
import socket
import struct
from importlib import metadata as importlib_metadata
# NEW: stdlib-only HTTP + threading for Discord webhook
import urllib.request
import urllib.error
import threading
import tempfile

from status_store import ActionStatusStore, daily_period
from bot.observability import (
    setup_logging,
    DiscordWebhookHandler,
    NtfyLogHandler,
    AxiomLogHandler,
    dump_env_diagnostics,
    _discord_webhook_post,
    _discord_webhook_post_many,
    ObservabilityMixin,
)
from bot.scheduler import _rotation_timing_suggestion, run_one_cycle, _next_daily_reset_ts, SchedulerMixin
from bot.world_bounty import world_bounty_zoom_out, plunder_world_bounties
from bot.gathering import select_resource_level, search_and_gather_resource, send_troops_gathering
from bot.trucks import do_trucks, do_truck_plunder, TrucksMixin
from bot.research import do_research
from bot.alliance import help_allies, claim_all_mail_rewards, do_hourly_action
from bot.shop import do_alliance_shop_badges, do_alliance_shop_shields, do_alliance_shop_catalog
from bot.events import do_boomer_auto_join
from bot.daily_rewards import do_vip_rewards, do_personal_bounties
from bot.radar import _save_treasure_screenshot, _report_radar_treasure, process_radar_events, do_radar
from bot.healing import do_heal_troops
from bot.training import collect_completed_troops, train_latest_troops
from bot.shields import do_activate_peace_shield, process_scheduled_shields, shield_protection_active, shield_operations, shield_start_delay
from bot.detection import (
    _hex_to_hsv,
    _parse_fraction,
    _template_match_centers,
    _ocr_troop_capacity,
    _visible_troop_card_centers,
    _is_lower_tier_training_warning,
    _parse_shop_reset_seconds,
    _troop_tier_card_states,
    _highest_visible_unlocked_troop_card,
    _parse_power_value,
    _find_world_bounty_markers,
    _world_info_card_visible,
    _world_coordinate_form_visible,
    _alliance_help_point,
    _ocr_frame_text,
    _parse_healing_duration_seconds,
    _is_alliance_speedup_reward_dialog,
    _base_recovery_evidence,
    _ocr_healing_duration_seconds,
    _next_healing_slider_position,
    _find_masked_template_in_roi,
    _locate_available_builder_button,
    _locate_boomer_event_card,
    _hospital_row_availability,
    _find_ocr_word_center,
    _find_ocr_phrase_center,
    _is_unit_cap_message,
    _is_construction_resource_shortage_prompt,
    _is_construction_replenish_confirmation,
    _is_boomer_auto_join_enabled,
    _locate_green_builder_upgrade,
    _locate_builder_help_pin,
    _locate_green_rect_buttons,
    _alliance_shop_price_button,
    _locate_boomer_activate_button,
    _ocr_title_matches,
    _parse_attempts_fraction,
    find_template,
    wait_for_template,
    is_visible,
    extract_text_from_roi,
    DetectionMixin,
)
from bot.navigation import (
    confirm_screen,
    dismiss_navigation_blocker,
    ensure_base_view,
    close_all_apps,
    go_home,
    launch_game,
    NavigationMixin,
)
from bot.android import (
    get_device_id,
    adb_command,
    adb_screenshot,
    _is_usable_adb_candidate,
    _resolve_adb,
    _resolve_tesseract,
    capture_device_screen,
    _adb_screencap_pull,
    check_requirements,
    AndroidMixin,
)
from bot.construction import (
    handle_construction_resource_shortage,
    _builder_queue_is_open,
    open_builder_queue,
    do_build,
)
from bot.context import context
context.bind(globals())


PROJECT_ROOT = Path(__file__).resolve().parent


def _host_path(env_name: str, default: str | os.PathLike[str]) -> Path:
    """Resolve a host path consistently, independent of the launch directory."""
    configured = os.environ.get(env_name)
    path = Path(configured).expanduser() if configured else Path(default).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


DATA_ROOT = _host_path("LASTZ_DATA_DIR", PROJECT_ROOT)
LOGS_ROOT = _host_path("LASTZ_LOG_DIR", DATA_ROOT / "logs")
DEBUG_ROOT = _host_path("LASTZ_DEBUG_DIR", DATA_ROOT / "debug")
STATUS_PATH = _host_path("LASTZ_STATUS_FILE", DATA_ROOT / "runtime" / "action_status.json")

# --- LOGGING LEVELS ---
# Custom TRACE level below DEBUG
TRACE = 5
logging.addLevelName(TRACE, 'TRACE')

def trace(self, message, *args, **kwargs):
    if self.isEnabledFor(TRACE):
        self._log(TRACE, message, args, **kwargs)

logging.Logger.trace = trace

# Logging categories
LOG_CATEGORIES = {
    'bot': 'Main bot lifecycle',
    'adb': 'ADB commands and device interaction',
    'image': 'Template matching and OCR',
    'game': 'Game-specific actions',
    'state': 'State management and scheduling',
    'perf': 'Performance metrics and timing',
    'discord': 'Discord webhook integration'
}
HELPER_METHOD_NAMES = (
    "adb_command", "adb_screenshot", "find_template", "wait_for_template",
    "go_home", "launch_game", "ensure_base_view", "close_all_apps",
    "select_resource_level", "search_and_gather_resource", "send_troops_gathering",
    "do_radar", "process_radar_events", "do_research", "do_trucks", "do_truck_plunder", "claim_all_mail_rewards", "do_hourly_action", "do_alliance_shop_badges", "do_alliance_shop_shields", "do_alliance_shop_catalog", "run_one_cycle",
    "extract_text_from_roi", "confirm_screen", "is_visible",
    "plunder_world_bounties", "world_bounty_zoom_out",
    "do_heal_troops", "collect_completed_troops", "train_latest_troops", "dismiss_navigation_blocker",
    "handle_construction_resource_shortage",
    "do_boomer_auto_join", "help_allies", "open_builder_queue",
    "do_activate_peace_shield", "process_scheduled_shields", "shield_protection_active",
    "do_vip_rewards", "do_personal_bounties",
)


# --- BOT CLASS (reintroduced) ---
class ScrcpyBot(AndroidMixin, NavigationMixin, DetectionMixin, TrucksMixin, SchedulerMixin, ObservabilityMixin):
    """
    Core bot controller.  One instance manages all ADB interactions with a
    single connected Android device for the duration of the bot's lifetime.

    Architecture notes
    ------------------
    Helper functions (adb_command, find_template, do_trucks, etc.) are defined
    at module scope with a `self` first argument and then *bound* onto this
    class instance at construction time (see HELPER_METHOD_NAMES and
    __getattr__).  This keeps the file easy to edit as plain functions while
    still allowing `self.do_trucks(...)` call syntax.

    State kept per-instance
    -----------------------
    last_checks                  dict  check-name → float epoch; used by
                                       _should_check() / _mark_check() to
                                       implement simple interval timers.
    trucks_cooldown_until_by_game dict  game_name → float epoch; trucks are
                                       skipped for a game if now < this value.
    all_troops_busy              bool  True when last OCR confirmed all march
                                       slots are occupied; cleared every 2 min.
    total_cycles                 int   running count of run_one_cycle() calls.
    _tpl_cache                   dict  LRU cache of (name, kind, scale) →
                                       resized template array (max 200 entries).
    _last_screenshot             ndarray  last raw frame; reused within the
                                       screenshot throttle window.
    _perf_metrics                dict  running counters for screenshots taken,
                                       ADB commands issued, and cycle durations.
    """
    def __init__(self, device_id: str):
        """
        Initialise the bot for a specific ADB device.

        Parameters
        ----------
        device_id : str
            The ADB device serial string (e.g. "emulator-5554" or "ABC123XYZ").
            Obtain this via get_device_id() before constructing the bot.

        Actions performed during __init__
        ----------------------------------
        1. Sets up five category-specific loggers (bot, image, adb, game,
           state, perf) sourced from CONFIG["log_levels"].
        2. Loads all template PNG images listed in CONFIG["image_paths"] into
           self.templates (via _load_templates).  Missing files are logged as
           warnings but do not abort startup.
        3. Parses CONFIG["truck_plus_color"] and pre-converts it to HSV for
           use in _locate_truck_plus() colour-blob detection.
        4. Binds every function named in HELPER_METHOD_NAMES as an instance
           method via func.__get__(self, ScrcpyBot).
        5. Loads persisted truck cooldown timestamps from logs/trucks_state.json
           (expired entries are discarded).
        6. Initialises the trace/observability session directory and event log.
        """
        self.device_id = device_id
        # All gameplay shell commands share the native helper's ownership lock.
        from bot.phone_ownership import PhoneOwnership
        self._phone_ownership_required = True
        self._phone_ownership = PhoneOwnership(_resolve_adb() or "adb", device_id)
        self.running = True

        # Loggers - now using hierarchical categories
        self.logger = logging.getLogger('bot')
        self.image_logger = logging.getLogger('image')
        self.adb_logger = logging.getLogger('adb')
        self.game_logger = logging.getLogger('game')
        self.state_logger = logging.getLogger('state')
        self.perf_logger = logging.getLogger('perf')
        self._trace_logger = logging.getLogger('state')

        # State
        self.last_checks = {}
        self.last_2min_action_time = 0
        self.all_troops_busy = False
        self.total_cycles = 0

        # Templates
        self.templates = self._load_templates()
        self.logger.info(f"Bot initialized for device: {device_id}")
        # --- add missing perf caches and per-game cooldown map ---
        self._last_screenshot = None
        self._last_screenshot_ts = 0.0
        # ADDED: Limit template cache size
        self._tpl_cache = {}
        self._tpl_cache_max_size = 200
        self.trucks_cooldown_until_by_game: dict[str, float] = {}
        self._template_debug: dict[str, dict[str, float | None]] = {}
        self._trace_cycle_shots_left = int(CONFIG.get("internal_trace_max_shots_per_cycle", 6))
        self._trace_session_id = ""
        self._trace_dir = ""
        self._trace_events_path = ""
        self._trace_enabled = False
        self._trace_screenshots_enabled = False
        self._screen_ref_cache: dict[str, np.ndarray | None] = {}
        self._last_treasure_alert_ts = 0.0
        self._last_bounty_plunder_counter: tuple[int, int] | None = None
        # game_name -> (first-five hero power, monotonic cache timestamp).  Seed
        # this from a deliberately measured lineup so normal truck inspection
        # never has to open the hero selector.
        self._truck_plunder_power_cache: dict[str, tuple[float, float]] = {
            str(name): (float(power), time.monotonic())
            for name, power in CONFIG.get("truck_plunder_cached_power_by_game", {}).items()
        }
        self._treasure_missing_webhook_warned = False
        self._consecutive_screenshot_failures = 0
        self._last_adb_recovery_ts = 0.0
        self._adb_recovering = False
        self._stuck_counts: dict[str, int] = {}
        self._last_device_heal_check_ts = 0.0
        self._device_power_policy_configured = False
        self._device_heal_in_progress = False
        plus_cfg = CONFIG.get("truck_plus_color", {})
        self._truck_plus_color = {
            "hsv": _hex_to_hsv(plus_cfg.get("hex", "#52B842")),
            "h_tol": int(plus_cfg.get("h_tolerance", 3)),
            "s_tol": int(plus_cfg.get("s_tolerance", 10)),
            "v_tol": int(plus_cfg.get("v_tolerance", 10)),
            "min_area": int(plus_cfg.get("min_area", 80)),
        }

        # Bind existing top-level functions as instance methods
        for name in HELPER_METHOD_NAMES:
            func = globals().get(name)
            if callable(func):
                setattr(self, name, func.__get__(self, ScrcpyBot))
            else:
                logging.getLogger('bot').warning(f"Bind skipped: function '{name}' not found")
        # NEW: cycle abort flag
        self._abort_cycle = False
        # NEW: load persisted trucks cooldowns (prune expired)
        self._load_trucks_state()
        account_settings = {
            name: CONFIG.get("game_settings", {}).get(name, {})
            for name in CONFIG.get("game_coords", {})
        }
        self.status_store = ActionStatusStore(
            CONFIG.get("status_file", os.path.join("runtime", "action_status.json")),
            account_settings,
            timezone_name=CONFIG.get("status_timezone", "Europe/Malta"),
            reset_hour=CONFIG.get("daily_reset_hour", 4),
        )
        self.status_store.set_bot("running", "Bot initialized", device=self.device_id)
        self._init_observability()
        
        # Performance tracking
        self._perf_metrics = {
            'screenshots': 0,
            'template_matches': 0,
            'adb_commands': 0,
            'cycle_times': []
        }
        self._cycle_times_by_game: dict[str, list[float]] = {
            name: [] for name in CONFIG.get("game_coords", {})
        }


    # Small helpers used by scheduler


    # Missing simple ADB helpers (not present at top-level)


    # --- NEW: trucks cooldown persistence helpers ---


    # ADDED: Helper to manage cache size


    def __getattr__(self, name: str):
        func = globals().get(name)
        if callable(func):
            bound = func.__get__(self, ScrcpyBot)
            setattr(self, name, bound)
            self.logger.debug(f"Lazily bound helper '{name}'")
            return bound
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

# --- CONFIGURATION ---
# Single source of truth for all tunable parameters.  All pixel coordinates
# assume a 1080 x 2160 screen.  Change values here; the code reads from this
# dict at runtime, so no code edits are needed for most tuning tasks.
CONFIG = {
    # ------------------------------------------------------------------ device
    "device_model": "ONEPLUS A5010",  # Model string matched against `adb shell getprop ro.product.model`
    # ---------------------------------------------------------- device healing
    "device_auto_heal_enabled": True,
    "device_pin": os.environ.get("LASTZ_DEVICE_PIN", "1992"),
    "device_configure_stay_awake": True,
    "device_screen_timeout_ms": 1800000,
    "device_heal_check_interval_seconds": 20.0,
    "device_unlock_max_attempts": 3,
    "device_wake_delay_seconds": 0.8,
    "device_swipe_delay_seconds": 0.45,
    "device_pin_delay_seconds": 1.0,
    "device_unlock_swipe": (540, 1850, 540, 420, 350),
    # ---------------------------------------------------------------- paths
    "debug_dir": str(DEBUG_ROOT),       # Root folder for debug artefacts
    "internal_trace_dir": str(DEBUG_ROOT / "trace"),
    "logs_dir": str(LOGS_ROOT),         # Rotating bot log + trace JSONL + trucks state
    "status_file": str(STATUS_PATH),
    "shield_state_dir": str(DATA_ROOT / "runtime" / "shields"),
    "status_timezone": "Europe/Malta",
    # Shield activation is implemented but must remain disarmed until the
    # operator approves live calibration/testing. No generic Confirm clicks.
    "shield_activation": {
        "enabled": os.environ.get("LASTZ_SHIELD_ACTIVATION_ENABLED", "false").lower() == "true",
        "ui_calibrated": os.environ.get("LASTZ_SHIELD_UI_CALIBRATED", "false").lower() == "true",
        "schedule_enabled": os.environ.get("LASTZ_SHIELD_SCHEDULE_ENABLED", "false").lower() == "true",
        # Optional dated override: never commit an armed start time into source.
        "one_off_start_at": os.environ.get("LASTZ_SHIELD_START_AT", ""),
        # Optional explicit 8-hour rollout. This is separate from the normal
        # Saturday renewal, which is derived from verified 24-hour expiry.
        "one_off_8h_start_at": os.environ.get("LASTZ_SHIELD_8H_START_AT", ""),
        "accounts": ("game1", "game2", "game3", "game4"),
        # This limits only the 24h rollout, not verified accounts' 8h renewals.
        "rollout_accounts": tuple(value.strip() for value in os.environ.get(
            "LASTZ_SHIELD_ROLLOUT_ACCOUNTS", "game1,game2,game3,game4").split(",") if value.strip()),
        "rollout_8h_accounts": tuple(value.strip() for value in os.environ.get(
            "LASTZ_SHIELD_8H_ROLLOUT_ACCOUNTS", "").split(",") if value.strip()),
        "friday_time": (23, 0),
        "saturday_time": (21, 0),
        "saturday_renewal_enabled": True,
        "replacement_lead_seconds": 1800,
        "allow_replacement": True,
        "protect_marches": True,
        "retry_seconds": 300,
        "report_retry_seconds": 300,
        "discord_timeout": 15,
        "health_enabled": True,
        "health_check_interval": 900,
        "timer_tolerance_seconds": 180,
        "transition_delay": 1.5,
        # Read-only live inspection: World -> own HQ -> Buff -> Peace Shield.
        # Use remains disarmed. Wrong HQ/missing label aborts, never taps Attack.
        "buff_steps": [
            {"point": (920, 2070), "confirm_screen": "world"},
            {"point": (540, 1040)},
            {"template": "shield_buff_button", "roi": (250, 900, 1000, 1700)},
            {"template": "shield_formation_row", "roi": (80, 480, 1000, 900)},
        ],
        "inventory_title_roi": (350, 310, 750, 410),
        "inventory_roi": (100, 1150, 975, 1800),
        "confirmation_roi": (100, 650, 1000, 1600),
        "replacement_text_roi": (130, 850, 950, 1190),
        "timer_roi": (100, 390, 1000, 700),
        "countdown_roi": (500, 615, 800, 660),
    },
    # --------------------------------------------------------------- tracing
    "internal_trace_enabled": True,           # Write trace JSONL events to logs/
    # Retaining full-screen failure evidence is opt-in through --trace.
    # In-memory vision capture remains available for normal bot operation.
    "internal_trace_screenshots": False,
    "internal_trace_max_shots_per_cycle": 8,  # Budget: max screenshots saved per run_one_cycle() call
    "base_recovery_timeout_seconds": 30.0,
    "base_stability_seconds": 1.5,
    "base_marker_grace_seconds": 8.0,
    "base_min_sanity_matches": 2,
    "base_recovery_poll_seconds": 0.35,
    # ------------------------------------------------------------ log levels
    # Global default: CRITICAL, ERROR, WARNING, INFO, DEBUG, TRACE
    "log_level": "INFO",  # Global default: CRITICAL, ERROR, WARNING, INFO, DEBUG, TRACE
    "log_levels": {  # Per-category overrides (None = inherit global)
        "bot": None,      # None = use global
        "adb": None,
        "image": None,
        "game": None,
        "state": None,
        "perf": "INFO",   # Performance metrics at INFO
        "discord": "WARNING"  # Discord only for warnings+
    },
    # ------------------------------------------------------- template images
    # Maps logical template name -> PNG file path (resolved against project root).
    # PNG files may include an alpha channel; the alpha is used as a mask in
    # SQDIFF matching to ignore transparent background pixels.
    "image_paths": {
        "home": "images/home.png",
        "endless_night_close": "images/endless_night_close.png",
        "hero_progression": "images/hero_progression.png",
        "hq": "images/hq.png",
        "hq2": "images/hq2.png",
        "quit_game": "images/quit_game.png",
        "exp": "images/exp.png",
        "food": "images/food.png",
        "electric": "images/electric.png",
        "zent": "images/zent.png",
        "raider": "images/troops/raider.png",
        "troop_completion_tick": "images/troops/completion_tick.png",
        "troop_completion_tick_timer": "images/troops/completion_tick_timer.png",
        "assulter": "images/troops/assulter.png",
        "shooter": "images/troops/shooter.png",
        "help": "images/help.png",
        "alliance_help_handshake": "images/alliance_help_handshake.png",
        "wood": "images/wood.png",
        "empty_troops": "images/troops/empty.png",
        "fuel": "images/fuel.png",
        "fuel2": "images/fuel2.png",
        "fuel_can": "images/fuel_can.png",
        "lumberyard": "images/lumberyard.png",
        "farmyard": "images/farmyard.png",
        "zentyard": "images/zentyard.png",
        "research_recommended": "images/research_recommended.png",
        "research_recommended2": "images/research_recommended2.png",
        "research_complete": "images/research_complete.png",
        "research_help": "images/research_help.png",
        "research_alliance_help": "images/research_alliance_help.png",
        "research_speed_up": "images/research_speed_up.png",
        "boomer_event": "images/archive/boomer.png",
        "builder_build": "images/builder_build.png",
        "builder_hardhat": "images/builder_hardhat.png",
        "builder_queue_title": "images/builder_queue_title.png",
        "builder_upgrade_menu": "images/builder_upgrade_menu.png",
        "builder_upgrade_menu_glow": "images/builder_upgrade_menu_glow.png",
        "builder_upgrade_confirm": "images/builder_upgrade_confirm.png",
        "construction_get_more_title": "images/construction/get_more_title.png",
        "construction_replenish_all": "images/construction/replenish_all.png",
        "construction_replenish_insufficient": "images/construction/replenish_insufficient.png",
        "troop_unit_cap_toast": "images/training/unit_cap_toast.png",
        "builder_construction_help": "images/builder_construction_help.png",
        "build_complete": "images/build_complete.png",
        "troops_2_of_2": "images/gather/3_3.png",
        "collect_8hrs": "images/collect_8hours.png",
        "research_free": "images/research_free.png",
        "research_confirm": "images/research_confirm.png",
        "vip_collect": "images/vip_collect.png",
        "vip_freebies_claim": "images/vip_freebies_claim.png",
        "daily_reward_banner": "images/daily_reward_banner.png",
        "bounty_wanted": "images/bounty/wanted.png",
        "bounty_help": "images/bounty/bounty_help.png",
        "bounty_go": "images/bounty/bounty_go.png",
        "bounty_claim": "images/bounty/bounty_claim.png",
        "bounty_quick_deploy": "images/bounty/quick_deploy.png",
        "bounty_dispatch": "images/bounty/dispatch.png",
        "truck": "images/truck.png",
        "truck_chest": "images/truck_chest.png",
        "truck_plus": "images/truck_plus.png",
        "radar": "images/radar.png",
        "radar_check": "images/radar_check.png",
        "radar_event_head": "images/radar_events/radar_event_head.png",
        "radar_event_pickaxe": "images/radar_events/radar_event_pickaxe.png",
        "chat": "images/chat.png",
        "treasure": "images/treasure.png",
        "heal": "images/heal/heal.png",
        "heal_help": "images/heal/heal_help.png",
        "heal_idle": "images/heal/heal_idle.png",
        "heal_active": "images/heal/heal_active.png",
        "heal_help_state": "images/heal/heal_help_state.png",
        "heal_complete_brutal": "images/archive/heal/accept1.png",
        "heal_complete_variant_2": "images/archive/heal/accept2.png",
        "heal_complete_variant_3": "images/archive/heal/accept3.png",
        # Tight card-art crop, deliberately excluding the card frame, rank
        # badge, price and stock text.  It finds Peace Shield items regardless
        # of their position in the scrolling Alliance Shop.
        "alliance_shop_peace_shield": "images/shop/peace_shield_icon.png",
        "alliance_shop_peace_shield_24h": "images/shop/peace_shield_24h.png",
        "shield_buff_button": "images/shields/buff_button.png",
        "shield_formation_row": "images/shields/formation_shield.png",
        "shield_panel_identity": "images/shields/panel_identity.png",
        "shield_inventory_8h": "images/shields/inventory_8h.png",
        "shield_inventory_24h": "images/shields/inventory_24h.png",
        "shield_use_button": "images/shields/use_button.png",
        "shield_replacement_prompt": "images/shields/replacement_prompt.png",
        "shield_replacement_confirm": "images/shields/replacement_confirm.png",
        "alliance_shop_badge": "images/shop/badge.png",
        "alliance_shop_supply_chest": "images/shop/catalog/alliance_advanced_supply_chest.png",
        "alliance_shop_miranda_fragment": "images/shop/catalog/miranda_fragment.png",
        "alliance_shop_prime_ticket": "images/shop/catalog/prime_recruitment_ticket.png",
        "alliance_shop_katrina_fragment": "images/shop/catalog/katrina_fragment.png",
        "alliance_shop_modification_blueprint": "images/shop/catalog/modification_blueprint.png",
        "alliance_shop_rename_card": "images/shop/catalog/rename_card.png",
        "alliance_shop_speedup_choice_box": "images/shop/catalog/speedup_choice_box.png",
        "alliance_shop_relocation_item": "images/shop/catalog/relocation_item.png",
        "alliance_shop_resource_chest": "images/shop/catalog/shop_resource_chest.png",
        "alliance_shop_advanced_teleporter": "images/shop/catalog/advanced_teleporter.png",
        "alliance_shop_alliance_teleporter": "images/shop/catalog/alliance_teleporter.png",
    },
    # ---------------------------------------- game slot home-screen coordinates
    # Each game slot is a separate LastZ install accessed via parallel-space.
    # Coordinates are the (x, y) pixel position of each app icon on the Android
    # home screen.  Tap order is shuffled every rotation for variety.
    "game_coords": {
        "game1": (126, 1191) #farm
        ,"game2": (331, 1191) #farm
        ,"game3": (549, 1191) #farm
        ,"game4": (745,1191) # Dassy
        #,"game5": (957,1191)  # 64
    },
    # -------------------------------------------- per-slot feature flags
    # train_troops: if True, the bot collects every completed troop-building
    # marker, then fills available queues with the highest unlocked tier.
    "game_settings": {
        "game1": {"label": "Farm 1", "train_troops": True, "heal_troops": True},
        "game2": {"label": "Farm 2", "train_troops": True, "heal_troops": True},
        "game3": {"label": "Farm 3", "train_troops": True, "heal_troops": True},
        "game4": {"label": "Dassy", "train_troops": True, "heal_troops": True},
        "game5": {"label": "Account 5", "train_troops": True, "heal_troops": True}
    },
    # ----------------------------------------- in-game UI tap coordinates
    # All (x, y) pixel positions on the 1080 x 2160 screen.
    # Names are used throughout the code as CONFIG["action_coords"]["<key>"].
    "action_coords": {
        "open_world": (920, 2070),       # World / Headquarters toggle (bottom-right HUD)
        "search_button": (64, 1746),     # Search / Gather magnifier (world map)
        "world_state_field": (295, 282), # State number in the world coordinate search bar
        "world_x_field": (520, 282),     # X coordinate in the world coordinate search bar
        "world_y_field": (720, 282),     # Y coordinate in the world coordinate search bar
        "world_state_search": (865, 282), # Magnifier at the right of the coordinate form
        "world_bounty_reward_dismiss": (540, 1750), # Outside/continue tap on reward overlay
        "alliance": (1000, 1634),        # Alliance button on the base HUD
        "alliance_techs": (305, 1375),   # Alliance Techs button in the Alliance panel
        "alliance_tech_donate": (750, 1585), # Zents Donate button in recommended tech
        "alliance_gifts": (800, 1375),   # Alliance Gifts button in the Alliance panel
        "alliance_gifts_rare": (800, 790), # Rare tab inside Alliance Gifts
        "alliance_gifts_claimall": (540, 2065), # Common-tab Claim All button
        # Alliance Shop / Badge weekly purchase flow (native 1080x2160 coordinates).
        "alliance_shop": (300, 1570),
        "alliance_shop_modal_plus": (654, 1375),
        "alliance_shop_modal_buy": (540, 1598),
        "mail": (1000, 1740),            # Mail button on the base HUD
        "mail_claim_all": (830, 2010),   # Claim All button inside Mail
        "mail_reward_dismiss": (540, 1070),  # Congratulations overlay dismissal
        "gather_search": (565, 2062),    # Search button inside gather resource panel
        "gather_confirm_march": (500, 1578),  # Fallback center of March button in troop dispatch popup
        "train_troops_cap_close": (908, 795), # Close X on the Military Center unit-cap warning
        "gather_button": (540, 1240),    # Gather button on a resource node info card
        "middle_screen": (540, 1072),   # Generic centre-screen tap (world map)
        "8hrs_chest_collect": (558, 1594),  # Collect button inside 8-hr chest popup
        "clear_all": (532, 1933), # NOTE: Adjust these coordinates for your device's "Clear All" button
        "vip_claim_1": (950, 504),       # First VIP reward claim button
        "vip_claim_2": (824, 1537),      # Second VIP reward claim button
        "event_center": (997, 194),      # Event center button (not currently used in main loop)
        "truck_plunder_entry": (70, 1390), # Wanted-board entry for Others' Trucks
        "truck_plunder_back": (70, 2050),  # In-panel back button
        "truck_plunder_loot": (367, 1855), # Loot on a selected truck's detail panel
        "truck_plunder_panel_dismiss": (540, 1100), # Empty road above detail panel
        "truck_plunder_fight": (540, 2050),# Fight button after a safe comparison
        "radar_clear_all": (540, 2062),  # Clear All button inside the Radar panel
        "research_confirm": (802, 1591), # Start Research confirm button
        # Native coordinates for the centres of the Hospital footer buttons.
        "hospital_heal_confirm": (860, 1875),
        "hospital_select_all": (220, 1875),
        "healing_reward_confirm": (540, 1275),
    },
    # The Endless Night event overlays the base HUD, so its close button must
    # be handled before coarse home/world screen classification.
    # Endless Night's close X is centred at about (932, 325).  Keep this ROI
    # tight enough to exclude panel close buttons such as Bounty's (905, 356).
    "endless_night_close_roi": (875, 270, 990, 380),
    "endless_night_close_backdrop_dark_ratio": 0.45,
    # Hero Progression is a full-screen, non-actionable-at-startup event.
    # Match only its static heading rather than dynamic tasks and countdown.
    "hero_progression_roi": (0, 40, 650, 210),
    "research_help_roi": (400, 1900, 700, 2140),
    "research_alliance_help_roi": (600, 550, 950, 900),
    "truck_trade_counter_roi": (80, 35, 580, 125),
    "truck_open_trade_roi": (450, 1750, 1050, 2140),
    "vip_rewards": {"enabled": True, "entry": (65, 250), "check_interval": 900},
    "personal_bounties": {"enabled": True, "check_interval": 900},
    "alliance_shop_badges": {
        "enabled": False,  # invoked internally by alliance_shop_catalog
        "check_interval": 604800,
        "weekly_bundle_limit": 10,
        # Items are found from their art templates, never a card grid.  This
        # is the scrollable portion of the Shop, not item coordinates.
        "scan_roi": (45, 790, 1035, 1900),
        "template_threshold": 0.88,
        # Keep overlap so an icon clipped by the sticky header becomes fully
        # visible on the next view (especially the 24h shield row).
        "scroll": (540, 1780, 540, 1180),
        "max_scrolls": 9,
    },
    "alliance_shop_shields": {
        "enabled": False,  # superseded by alliance_shop_catalog
        "check_interval": 604800,
        "products": (("24h peace shield", 1), ("8h peace shield", 3)),
    },
    # Add a product here to make it eligible.  Disabled entries are catalogued
    # but never purchased. Titles are read from the purchase dialog, so product
    # ordering and scroll position do not matter.
    "alliance_shop_catalog": {
        "enabled": True,
        # Used only when the game's labelled weekly reset is unreadable.
        "check_interval": 21600,
        "retry_interval": 900,
        "reset_countdown_roi": (0, 250, 1080, 790),
        "products": (
            # Every observed purchasable Shop card has an individual template
            # and switch.  Entries without a confirmed title are still safe:
            # when enabled, their own template is opened and its dialog title
            # becomes the expected reward name for that one purchase.
            {"title": "Alliance Advanced Supply Chest", "weekly_limit": 1, "enabled": False,
             "template": "alliance_shop_supply_chest"},
            {"title": "Miranda Fragment", "weekly_limit": 20, "enabled": False,
             "template": "alliance_shop_miranda_fragment"},
            {"title": "Prime Recruitment Ticket", "weekly_limit": 10, "enabled": False,
             "template": "alliance_shop_prime_ticket"},
            {"title": "Katrina Fragment", "weekly_limit": 5, "enabled": False,
             "template": "alliance_shop_katrina_fragment"},
            {"title": "Modification Blueprint", "weekly_limit": 30, "enabled": False,
             "template": "alliance_shop_modification_blueprint"},
            {"title": "Badge", "weekly_limit": 10, "enabled": True,
             "template": "alliance_shop_badge"},
            {"title": "", "label": "Relocation item", "weekly_limit": 5, "enabled": False,
             "template": "alliance_shop_relocation_item"},
            {"title": "Advanced Teleporter", "weekly_limit": 2, "enabled": False,
             "template": "alliance_shop_advanced_teleporter"},
            {"title": "Alliance Teleporter", "weekly_limit": 5, "enabled": False,
             "template": "alliance_shop_alliance_teleporter"},
            {"title": "24h Peace Shield", "weekly_limit": 1, "enabled": True,
             "template": "alliance_shop_peace_shield_24h"},
            {"title": "8h Peace Shield", "weekly_limit": 3, "enabled": True,
             "template": "alliance_shop_peace_shield"},
            {"title": "Rename Card", "weekly_limit": 4, "enabled": False,
             "template": "alliance_shop_rename_card"},
            {"title": "1-hr Speedup Choice Box", "weekly_limit": 80, "enabled": False,
             "template": "alliance_shop_speedup_choice_box"},
            {"title": "", "label": "Resource chest", "weekly_limit": 80, "enabled": False,
             "template": "alliance_shop_resource_chest"},
        ),
    },
    # Keep disabled until the first march has sufficient power to plunder safely.
    "truck_plunder_enabled": False,
    "truck_plunder_check_interval": 600,
    "truck_plunder_power_cache_ttl": 21600,
    # Measured from the first-five lineup.  Update via the explicit calibration
    # flow after meaningful hero upgrades; never calibrate while scanning trucks.
    "truck_plunder_cached_power_by_game": {"game4": 3_510_000},
    "truck_plunder_max_targets": 12,
    # Panel OCR can read a few percent low.  Require a clear margin before
    # spending a daily plunder attempt.
    "truck_plunder_min_power_ratio": 1.20,
    "truck_plunder_our_power_roi": (180, 35, 450, 110),
    # The selected-truck detail panel exposes its power before Loot is tapped.
    "truck_plunder_opponent_power_roi": (300, 1470, 720, 1570),
    "truck_plunder_target_points": [
        (350, 370), (730, 370), (350, 550), (730, 550),
        (270, 720), (720, 720), (270, 880), (720, 880),
        (270, 1080), (720, 1080), (340, 1280), (740, 1280),
    ],
    "truck_plunder_first_five_cards": [
        (145, 1485), (340, 1485), (535, 1485), (740, 1485), (930, 1485),
    ],
    "builder_navigation": {"max_attempts": 3, "open_timeout": 3.0},
    "alliance_help": {
        "enabled": True,
        "roi": (760, 1450, 980, 1750),
        "threshold": 0.88,
        "max_attempts": 2,
    },
    "alliance_tech_attempts_roi": (570, 1430, 970, 1535),
    "troop_unit_cap_message_roi": (150, 900, 930, 1120),
    # The training panel exposes current/max unit capacity even before an
    # attempted Train tap.  Read it first so a full Military Center is an
    # explicit, expected result rather than a misleading missing-button error.
    "troop_training_capacity_roi": (60, 1160, 420, 1300),
    "gather_search_panel_light_ratio": 0.50,
    "gather_march_button_roi": (250, 1450, 750, 1660),
    # Selected/max unit count appears at one of these two vertical positions
    # depending on whether the dispatch card includes extra combat controls.
    "troop_capacity_value_rois": (
        (420, 1215, 600, 1280),
        (420, 1310, 600, 1380),
    ),
    "troop_training": {
        "max_queues_per_cycle": 3,
        # Finished queues show one of these three character-and-tick markers
        # directly on the base.  Collect all of them before trying to fill
        # newly empty queues, rather than treating them as generic passives.
        "completion_templates": ("raider", "assulter", "shooter"),
        "max_collections_per_cycle": 3,
        # A full Military Center can become available after troops are lost;
        # do not suppress training for an entire day.
        "unit_cap_retry_interval": 3600,
        "tier_centers": (150, 370, 585, 805, 1015),
        "tier_card_y": (1690, 1875),
        "tier_card_half_width": 75,
        "unlocked_color_ratio": 0.15,
        "selected_yellow_ratio": 0.005,
        # Re-detect card centres after each swipe; never reuse old positions.
        "max_selector_swipes": 5,
        "selector_swipe": (900, 1780, 300, 1780),
        "selector_swipe_duration": 350,
        "selector_settle_delay": 0.8,
        "selection_settle_delay": 0.8,
        "train_button_roi": (550, 1900, 1080, 2150),
        "train_button_min_width": 300,
        "train_button_max_width": 500,
        "train_button_min_height": 70,
        "train_button_max_height": 180,
        "panel_open_delay": 1.5,
        "post_train_delay": 2.0,
        "completion_action_roi": (450, 600, 1050, 1900),
    },
    "mail_tabs": {
        "report": (88, 185),
        "jungle": (260, 185),
        "alliance": (430, 185),
        "system": (600, 185),
        "recharge": (770, 185),
        "favorite": (940, 185),
    },
    # World-map bounty plundering. Zoom is intentionally disabled: the scan
    # operates at whichever normal map scale the game currently uses.
    "world_bounty": {
        "enabled": False,
        "hotspots": (
            {"state": 1, "x": 497, "y": 647},
            {"state": 10, "x": 540, "y": 357},
            {"state": 47, "x": 138, "y": 77},
            {"state": 18, "x": 561, "y": 397},
        ),
        "daily_limit": 5,
        "check_interval": 900,
        # Coordinate jumps restore the default map scale. Two calibrated
        # two-finger pinches produce the user-approved bounty-search scale.
        "zoom_enabled": True,
        "zoom_steps": 2,
        "zoom_settle_delay": 1.5,
        "min_zoom_frame_delta": 5.0,
        "zoom_control_port": 27183,
        "zoom_server_remote_path": "/data/local/tmp/scrcpy-server-v1.24.jar",
        "state_banner_roi": (150, 250, 550, 350),
        "state_submit_retries": ((865, 282), (842, 282), (820, 282)),
        # Stop before x=720: the animated event/HUD column begins around 730.
        "scan_roi": (120, 340, 720, 1720),
        "plunder_ocr_roi": (80, 700, 1000, 1900),
        "reward_ocr_roi": (50, 250, 1030, 1950),
        "reward_title_ocr_roi": (100, 400, 1000, 800),
        "reward_keywords": ("reward", "congratulations", "obtained", "acquired"),
        "min_reward_frame_delta": 8.0,
        "max_candidate_taps": 24,
        "max_swipes_per_hotspot": 4,
        "swipe_delay": 1.2,
        "candidate_settle_delay": 1.2,
        "reward_settle_delay": 2.0,
        "swipes": [
            (780, 900, 260, 900),
            (540, 720, 540, 1320),
            (260, 900, 780, 900),
            (540, 1320, 540, 720),
        ],
    },
    # Time-based troop healing.  The blue Heal button is the source of truth;
    # troop counts are used only to choose a row with enough injured units.
    "healing": {
        "enabled": True,
        "check_interval": 60,
        "target_seconds": 7200,
        "tolerance_seconds": 300,
        "hard_max_seconds": 8100,
        "max_slider_adjustments": 6,
        "world_icon_roi": (100, 1500, 450, 1900),
        # The lower-left world toolbar is animated and can temporarily show a
        # different shortcut just after entering the map.  Do not mistake
        # that transition frame for the absence of a Hospital action.
        "world_icon_wait_seconds": 8.0,
        "world_icon_poll_interval": 0.75,
        "idle_match_score": 0.03,
        "active_match_score": 0.03,
        "help_match_score": 0.03,
        "hospital_title_roi": (350, 0, 730, 110),
        "hospital_row_header_y": (669, 887, 1105, 1323),
        # Native 1080x2160 coordinates.  These must point at the centre of
        # the draggable pause-shaped handle, not at the cyan bar beside it.
        # The previous values came from a resized preview and missed every
        # handle, leaving Select All's duration unchanged.
        "hospital_slider_y": (755, 973, 1191, 1409),
        "hospital_slider_min_x": 358,
        "hospital_slider_initial_x": 404,
        "hospital_slider_max_x": 642,
        "hospital_heal_time_roi": (730, 1850, 960, 1940),
        "slider_settle_delay": 0.8,
        "post_heal_delay": 2.0,
        "post_help_delay": 1.5,
        "base_timeout": 30.0,
        "world_transition_timeout": 10.0,
        "completion_match_score": 0.03,
        # The completion portrait follows the majority troop type.  All three
        # live variants must be accepted before looking for the normal
        # idle/active/help Hospital controls.
        "completion_templates": (
            "heal_complete_brutal",
            "heal_complete_variant_2",
            "heal_complete_variant_3",
        ),
    },
    # Right-side march sidebar in world view.  Slots are top-to-bottom.
    "march_sidebar": {
        "count_roi": (925, 990, 1060, 1048),
        "slots": [
            {"time_roi": (945, 1125, 1030, 1175), "idle_roi": (1000, 1020, 1075, 1090)},
            {"time_roi": (945, 1243, 1030, 1295), "idle_roi": (1000, 1145, 1075, 1210)},
            {"time_roi": (935, 1363, 1035, 1410), "idle_roi": (1000, 1275, 1075, 1340)},
        ],
    },
    # Manual radar tasks that require a healthy, trained troop march.  Marker
    # matching is grayscale so blue/grey/other colour variants are equivalent.
    "radar_events": {
        "enabled": True,
        "check_interval": 900,
        "max_events_per_check": 4,
        "marker_roi": (250, 450, 900, 1350),
        "detail_text_roi": (200, 1550, 1000, 1900),
        "go_button": (540, 2045),
        "attack_fallback": (540, 1450),
        "attack_word_roi": (300, 1100, 800, 1700),
        "march_word_roi": (250, 1350, 750, 1700),
        "march_button_roi": (250, 1350, 750, 1750),
        "march_button_min_width": 250,
        "march_button_max_width": 520,
        "march_button_min_height": 65,
        "march_button_max_height": 180,
        # A specific marker template is stronger evidence than OCR of the
        # animated radar-detail card. Keep OCR as telemetry, not a hard gate.
        "require_detail_ocr": False,
        "post_go_delay": 2.5,
        "post_attack_delay": 1.5,
        "post_march_delay": 2.0,
        "events": (
            {
                "kind": "head",
                "template": "radar_event_head",
                "threshold": 0.80,
                "detail_keywords": ("enemy military", "plunder"),
            },
            {
                "kind": "pickaxe",
                "template": "radar_event_pickaxe",
                "threshold": 0.85,
                "detail_keywords": ("battle the bloods", "resources"),
            },
        ),
    },
    # A confirmed Danger Lurks activation lasts twelve hours.
    "boomer_auto_join": {
        "enabled": True,
        "check_interval": 43200,
        # A failed renewal is a UI or timing problem, not proof that the
        # existing 12-hour renewal window should be abandoned.
        "retry_interval": 900,
        "event_center": (997, 194),
        "carousel_swipe": (820, 2020, 520, 2020),
        "carousel_reverse_swipe": (520, 2020, 820, 2020),
        "carousel_max_swipes": 8,
        "danger_page_title_roi": (0, 30, 500, 150),
        "danger_lurks_roi": (500, 1850, 1060, 2160),
        "boomer_portrait_roi": (0, 1850, 1080, 2160),
        "boomer_portrait_scale": 0.75,
        "boomer_portrait_threshold": 0.82,
        "auto_team_up_roi": (140, 1400, 980, 2050),
        "activate_roi": (500, 1500, 1000, 2000),
        "auto_team_up_timeout": 5.0,
        "auto_team_up_poll": 0.5,
        "post_event_center_delay": 2.5,
        "post_carousel_delay": 1.0,
        "post_action_delay": 1.2,
    },
    # Reference screenshots used for coarse screen-state sanity checks.
    # ROIs target stable UI chrome rather than changing timers/content.
    "screen_sanity": {
        "chat": {
            "path": "images/screen_sanity/chat.png",
            "rois": [(0, 0, 1080, 250), (0, 1850, 1080, 2160)],
            "threshold": 0.74,
            "min_avg": 0.72,
            "min_matches": 2,
        },
        "home": {
            "path": "images/screen_sanity/home.png",
            "rois": [(850, 1840, 1080, 2160), (0, 310, 130, 760)],
            "threshold": 0.55,
            "min_avg": 0.48,
            "min_matches": 1,
        },
        "mail": {
            "path": "images/screen_sanity/mail.png",
            "rois": [(0, 0, 1080, 250), (0, 1850, 1080, 2160)],
            "threshold": 0.74,
            "min_avg": 0.72,
            "min_matches": 2,
        },
        "radar": {
            "path": "images/screen_sanity/radar.png",
            "rois": [(0, 0, 260, 260), (300, 1840, 760, 2130), (880, 1840, 1080, 2130)],
            "threshold": 0.68,
            "min_avg": 0.66,
            "min_matches": 2,
        },
        "trucks": {
            "path": "images/screen_sanity/trucks.png",
            "rois": [(0, 0, 1080, 220), (0, 1850, 1080, 2160)],
            "threshold": 0.74,
            "min_avg": 0.72,
            "min_matches": 2,
        },
        "world": {
            "path": "images/screen_sanity/world.png",
            "rois": [(850, 1840, 1080, 2160), (875, 930, 1075, 1490), (0, 1380, 140, 1760)],
            "threshold": 0.50,
            "min_avg": 0.45,
            "min_matches": 1,
        },
    },
    # ---------------------------------------- resource level filter buttons
    # Discrete positions on the gather panel's level slider. Levels 3-6 are
    # preferred (higher-yield nodes); the level is chosen randomly.
    "resource_levels": {
        1: (305, 1933),
        2: (400, 1933),
        3: (495, 1933),
        4: (590, 1933),
        5: (685, 1933),
        6: (775, 1933),
    },
    # ---------------------------------------------------------- timing (seconds)
    "timing": {
        "interval": 1,                  # Sleep at end of each run_one_cycle() iteration
        "rotation_minutes": 20,         # Covers the historical per-game P90 cycle duration
        "rotation_cycle_buffer_ratio": 1.20,
        "rotation_suggestion_min_minutes": 15,
        "rotation_suggestion_max_minutes": 45,
        "rotation_suggestion_round_minutes": 5,
        "rotation_history_samples": 20,
        "action_delay": 2,              # Standard post-tap wait (UI animation settle)
        "long_delay": 5,                # Longer wait for slow animations (research, trucks)
        "swipe_duration": 300,          # Duration in ms for adb_swipe calls
        "fast_click_delay": 0.3,        # Short delay between rapid successive taps
        "periodic_action_interval_2min": 120,   # Gather / troop-busy reset interval
        "periodic_action_interval_hourly": 3600, # Legacy alliance-action interval
        # Interval-based checks (seconds between re-runs)
        "train_troops_check_interval": 0,   # 0 = every cycle
        "collect_8hrs_check_interval": 600, # 10 minutes
        "passive_checks_interval": 60,      # 1 minute
        # Full base roaming is much more expensive than checking the visible
        # viewport, so it gets an independent cadence and runs once per day.
        "construction_completion_scan_interval": 86400,  # 24 hours
        "construction_check_interval": 300,            # 5 minutes
        "research_check_interval": 300,                # 5 minutes
        "mail_retry_interval": 900,                    # 15 minutes
        "alliance_check_interval": 3600,               # Tech attempts and gifts regenerate
        "trucks_check_interval": 120,       # At most every 2 minutes
        "trucks_cooldown_when_empty": 900   # Legacy: was a fixed cooldown; now uses daily reset
    },
    # When a recommended building is short of resources, consume eligible
    # inventory resource packs before giving up on that construction attempt.
    "construction_replenish_all_enabled": True,
    "construction_shortage_prompt_roi": (60, 250, 1020, 1950),
    "click_offset": 1, # Max random pixels to add to each click coordinate
    # Improve template matching robustness
    "template_thresholds": {  # per-template SQDIFF thresholds (lower = stricter match; default 0.05)
        "truck_plus": 0.08,
        "truck_chest": 0.08,
        "vip_collect": 0.05,
        "collect_8hrs": 0.08,
        "treasure": 0.06,
        "home": 0.10,  # ADDED: Slightly relaxed for base view detection
        "endless_night_close": 0.08,
        "hero_progression": 0.08,
        "fuel_can": 0.08,
        "research_free": 0.10,
        "research_help": 0.08,
        "research_alliance_help": 0.08,
        "research_speed_up": 0.08,
        "builder_build": 0.02,
        "builder_upgrade_menu": 0.12,
        "builder_upgrade_menu_glow": 0.12,
        "builder_upgrade_confirm": 0.10,
        "builder_construction_help": 0.12,
        "build_complete": 0.08,
    },
    # scale variants tried per template (only scale=1.0 in fast mode)
    "template_scales": [1.0, 0.97, 1.03, 0.94, 1.06],  # scales to try
    # Optional per-template scale overrides (broaden for sensitive icons)
    "template_scales_per_template": {
        "collect_8hrs": [1.0, 0.95, 1.05, 0.9, 1.1, 0.85, 1.15],
        "home": [1.0, 0.97, 1.03],  # ADDED: Allow slight scale variations for base view
        # Construction checkmarks render about 10% larger on the handset than
        # the saved reference image.
        "build_complete": [1.1, 1.0],
    },
    # NEW: fast scales mode to speed up matching
    "template_scales_fast": [1.0],      # minimal scales for speed
    "use_fast_scales": True,            # toggle fast vs full scales
    "max_scale_attempts": 0,            # 0 means no cap; >0 caps number of scales tried
    "template_coeff_threshold": 0.85,  # CHANGED: Lowered from 0.88 to 0.85 for more lenient CCOEFF matching
    # "template_rotate_degrees": [-5, 5],
    # --- NEW performance knobs ---
    "matching_downscale": 0.6,          # 1.0 = off; 0.5..0.75 recommended on Pi
    "grayscale_only": False,            # allow SQDIFF+mask (fix passive icon clicks)
    "screenshot_min_interval_ms": 350,  # throttle screencaps; reuse last image if called sooner
    # `adb exec-out screencap` can remain blocked indefinitely after a brief
    # USB/ADB transport interruption.  Keep it comfortably above normal
    # capture time, but always allow the caller to fall back and recover.
    "adb_screenshot_timeout_seconds": 12.0,
    "adb_screenshot_failure_recovery_threshold": 3,
    "adb_recovery_min_interval_seconds": 15.0,
    "stuck_recovery_threshold": 3,
    # --- NEW: trucks reset behavior ---
    "daily_reset_hour": 4,            # 4 AM local time
    # --- NEW: toggle for matching downscale ---
    "enable_matching_downscale": False, # default OFF; enable via --downscale or config
    # Templates that deviate from the global SQDIFF path are forced here.
    # Any template in this list always goes through SQDIFF (even when
    # grayscale_only is True), ensuring alpha-mask support for icon PNGs.
    "force_sqdiff": False,
    "force_sqdiff_templates": [
        "exp","food","electric","zent","wood","fuel","help","build_complete",
        "raider","assulter","shooter","collect_8hrs","vip_collect",
        "endless_night_close",
        "hero_progression",
        "fuel_can",
        "research_help",
        "research_alliance_help",
        "research_speed_up",
        "treasure"  # Force SQDIFF for precise matching
    ],
    # --------------------------------------------------------- Discord webhook
    # Optional: forward log records to a Discord channel for remote monitoring.
    # Set discord_enabled=True and discord_webhook to your webhook URL, or
    # pass --discord-webhook and --discord-enable on the command line.
    # NEW: Discord logging options (can be overridden by CLI or env)
    "discord_enabled": False,                # enable only when a webhook is configured
    "discord_webhook": "",                    # set env DISCORD_WEBHOOK_URL or pass --discord-webhook
    "discord_level": "INFO",                  # INFO, WARNING, ERROR, DEBUG
    "discord_timeout": 4.0,                   # seconds HTTP timeout
    "discord_min_interval": 0.25,             # min seconds between posts (simple rate limiting)
    # Radar treasure alerts (set a dedicated webhook for #last-z-treasures)
    "treasure_alert_enabled": True,
    "discord_treasures_webhook": "",         # set env DISCORD_TREASURES_WEBHOOK_URL or pass --discord-treasures-webhook
    "treasure_alert_cooldown_seconds": 180.0,
    "treasure_screenshot_dir": os.path.join("debug", "treasures"),
    # ----------------------------------------------------------- ntfy.sh logging
    # ntfy.sh is a free, zero-account pub/sub service.  The bot POSTs log
    # records to a topic URL; anyone (including this AI assistant) can GET the
    # cached message stream from the same URL to read recent logs.
    # Free tier retains messages for 12 hours.
    # HOW TO USE:
    #   1. Pick a unique, non-guessable topic name below (change from default!).
    #   2. Set ntfy_enabled to True.
    #   3. Run the bot — logs will appear at https://ntfy.sh/<your-topic>
    #   4. Read logs through the topic's web UI or HTTP API.
    # Axiom is the primary central log backend.  The secret is supplied only
    # through AXIOM_TOKEN, never checked into the repository.
    "axiom_enabled": False,                  # enable only when AXIOM_TOKEN is provisioned
    "axiom_dataset": "lastz-bot",
    "axiom_endpoint": "https://eu-central-1.aws.edge.axiom.co",
    "axiom_level": "INFO",
    "axiom_timeout": 4.0,
    "axiom_min_interval": 0.5,
    # ntfy remains available only as an explicit rollback option.
    "ntfy_enabled": False,
    "ntfy_topic": "lastz-bot-gary-a7f3d2",   # CHANGE THIS to a unique non-guessable string
    "ntfy_server": "https://ntfy.sh",
    "ntfy_level": "INFO",                     # minimum level to forward
    "ntfy_timeout": 4.0,
    "ntfy_min_interval": 0.5,                 # seconds between posts (avoid rate limits)
    "truck_grade_refresh": {
        "grade_roi": (150, 350, 920, 820),
        "ticket_roi": (780, 800, 990, 1030),
        "target_min_ratio": 0.10,
        "refresh_button": (887, 1050),
        "warning_cancel": (715, 1165),
        "refresh_delay": 2.0,
        "max_refreshes": 50,
    },
    "trucks_default_trades_when_unknown": 2,
}

# --- UTILITY FUNCTIONS ---


# --- NEW: Minimal Discord webhook logging handler (no extra deps)


# --- ADB Helper METHODS ---


# --- Image Recognition ---


# --- Screen assertions (new) ---


# --- Game Actions ---


# --- NEW: helper to compute next daily reset epoch ---

# --- Configuration validation function (MOVED BEFORE main())
def _validate_config(logger):
    """Validate critical configuration values."""
    errors = []
    
    # Check required directories
    if not CONFIG.get("logs_dir"):
        errors.append("logs_dir not configured")
    
    # Check image paths exist
    missing_images = []
    for name, path in CONFIG.get("image_paths", {}).items():
        resolved_path = Path(path).expanduser()
        if not resolved_path.is_absolute():
            resolved_path = PROJECT_ROOT / resolved_path
        if not resolved_path.exists():
            missing_images.append(f"{name}: {resolved_path}")
    if missing_images:
        errors.append(f"Missing template images: {', '.join(missing_images[:5])}" + 
                     (f" ... and {len(missing_images)-5} more" if len(missing_images) > 5 else ""))
    
    # Check game coordinates
    if not CONFIG.get("game_coords"):
        errors.append("No game_coords configured")
    
    # Check timing values are positive
    for key, val in CONFIG.get("timing", {}).items():
        if not isinstance(val, (int, float)) or val < 0:
            errors.append(f"Invalid timing value for {key}: {val}")
    
    # Log warnings for non-critical issues
    if CONFIG.get("screenshot_min_interval_ms", 0) > 1000:
        logger.warning("screenshot_min_interval_ms > 1000ms may cause stale screenshots")
    
    if errors:
        logger.critical("Configuration validation failed:")
        for err in errors:
            logger.critical(f"  - {err}")
        sys.exit(1)
    else:
        logger.info("Configuration validation passed")

# --- MAIN EXECUTION ---

def main():
    """
    Entry point.  Parses CLI arguments, initialises logging, validates config,
    detects the Android device, and runs the main game-rotation loop.

    CLI flags (all optional)
    ------------------------
    --log-level LEVEL       Global log level: CRITICAL / ERROR / WARNING / INFO
                            / DEBUG / TRACE.  Default comes from CONFIG.
    --log-adb / --log-image / --log-game / --log-state / --log-perf
                            Per-category level overrides.
    -d 0|1|2                Legacy debug flag (0=WARNING, 1=INFO, 2=DEBUG).
    --trace                 Enable trace-level logging + screenshot capture.
    --no-downscale          Force full-resolution template matching.
    --downscale FLOAT       Override matching downscale factor (0.4 – 1.0).
    --match-fast            Use only scale 1.0 (fastest matching).
    --match-full            Use all configured scale variants (most robust).
    --max-scale-attempts N  Cap number of scales tried per template.
    --discord-webhook URL   Discord webhook URL for live log forwarding.
    --discord-enable        Enable Discord forwarding even without a new URL.
    --discord-level LEVEL   Minimum level to forward to Discord (default INFO).
    --preflight             Validate host tools, templates, and phone connection,
                            then exit without starting the game rotation.

    Startup sequence
    ----------------
    1. CLI args are parsed and applied to CONFIG before anything else runs.
    2. setup_logging() installs console + rotating file + optional Discord
       handlers with per-category level control.
    3. _validate_config() checks that required images exist, coordinates are
       present, and timing values are sane.  Exits on fatal errors.
    4. dump_env_diagnostics() logs platform / library / adb / tesseract info
       (only when DEBUG or below is active).
    5. check_requirements() ensures `adb` and `tesseract` are on PATH (or in
       the local scrcpy/ folder).  Exits with instructions if missing.
    6. get_device_id() discovers the USB-connected device with up to 8 retries.
    7. ScrcpyBot is instantiated for that device.
    8. close_all_apps() clears any leftover apps from a previous run.
    9. The game-rotation loop starts: for each iteration, game order is
       shuffled, then each game slot is launched, cycled, and closed in turn.
       Runs forever until Ctrl+C or an unhandled exception.

    Exit codes
    ----------
    0   Clean shutdown (Ctrl+C).
    1   Unexpected exception (logged at CRITICAL before exiting).
    """
    parser = argparse.ArgumentParser(description="A bot for LastZ (ADB-only; scrcpy removed).")
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Validate dependencies, templates, and ADB device access, then exit.",
    )
    
    # --- NEW: Logging level arguments ---
    parser.add_argument(
        "--log-level",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"],
        help="Set global logging level (overrides config)."
    )
    parser.add_argument(
        "--log-adb",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"],
        help="Set ADB logger level."
    )
    parser.add_argument(
        "--log-image",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"],
        help="Set image/template matching logger level."
    )
    parser.add_argument(
        "--log-game",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"],
        help="Set game actions logger level."
    )
    parser.add_argument(
        "--log-state",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"],
        help="Set state management logger level."
    )
    parser.add_argument(
        "--log-perf",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"],
        help="Set performance logger level."
    )
    
    # Keep backward compatibility with old -d flag
    parser.add_argument(
        "-d", "--debug",
        type=int,
        choices=[0, 1, 2],
        help="DEPRECATED: Use --log-level instead. 0=WARNING, 1=INFO, 2=DEBUG."
    )
    
    # --- NEW: --trace flag ---
    parser.add_argument(
       
        "--trace",
        action="store_true",
        help="Enable extra verbose tracing (use with -d 2 for maximum detail)."
    )
    # --- NEW: downscale controls ---
    parser.add_argument(
        "--no-downscale",
        action="store_true",
        help="Disable matching downscale (use full-resolution template matching)."
    )
    parser.add_argument(
        "--downscale",
        type=float,
        help="Override matching downscale factor (0.4..1.0). Implies downscale enabled."
    )
    parser.add_argument(
        "--match-fast",
        action="store_true",
        help="Use minimal template scales (fast)."
    )
    parser.add_argument(
        "--match-full",
        action="store_true",
        help="Use full/per-template scales (slower, more robust)."
    )
    parser.add_argument(
        "--max-scale-attempts",
        type=int,
        help="Clamp number of scales attempted per template (0 = unlimited)."
    )
    parser.add_argument(
        "--discord-webhook",
        help="Discord webhook URL to forward logs (or set DISCORD_WEBHOOK_URL env var)."
    )
    parser.add_argument(
        "--discord-enable",
        action="store_true",
        help="Enable forwarding logs to Discord (will auto-enable if webhook is provided)."
    )
    parser.add_argument(
        "--discord-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=CONFIG.get("discord_level", "INFO"),
        help="Minimum log level to forward to Discord."
    )
    parser.add_argument(
        "--discord-treasures-webhook",
        help="Discord webhook URL for treasure alerts (recommended: #last-z-treasures)."
    )
    
    args = parser.parse_args()
    
    # --- NEW: Apply logging level overrides ---
    if args.log_level:
        CONFIG["log_level"] = args.log_level
    elif args.debug is not None:
        # Backward compatibility mapping
        level_map = {0: "WARNING", 1: "INFO", 2: "DEBUG"}
        CONFIG["log_level"] = level_map.get(args.debug, "INFO")

    if args.trace:
        CONFIG["internal_trace_enabled"] = True
        CONFIG["internal_trace_screenshots"] = True
        if args.log_level is None and args.debug is None:
            CONFIG["log_level"] = "DEBUG"
    
    # Apply per-category overrides
    if args.log_adb:
        CONFIG.setdefault("log_levels", {})["adb"] = args.log_adb
    if args.log_image:
        CONFIG.setdefault("log_levels", {})["image"] = args.log_image
    if args.log_game:
        CONFIG.setdefault("log_levels", {})["game"] = args.log_game
    if args.log_state:
        CONFIG.setdefault("log_levels", {})["state"] = args.log_state
    if args.log_perf:
        CONFIG.setdefault("log_levels", {})["perf"] = args.log_perf
    
    # --- NEW: apply downscale flags ---
    if getattr(args, "no_downscale", False):
        CONFIG["enable_matching_downscale"] = False
    if getattr(args, "downscale", None) is not None:
        CONFIG["matching_downscale"] = max(0.4, min(1.0, float(args.downscale)))
        CONFIG["enable_matching_downscale"] = True

    # Discord args
    if args.discord_webhook:
        CONFIG["discord_webhook"] = args.discord_webhook.strip()
    elif os.environ.get("DISCORD_WEBHOOK_URL"):
        CONFIG["discord_webhook"] = os.environ["DISCORD_WEBHOOK_URL"].strip()
    if args.discord_treasures_webhook:
        CONFIG["discord_treasures_webhook"] = args.discord_treasures_webhook.strip()
    elif os.environ.get("DISCORD_TREASURES_WEBHOOK_URL"):
        CONFIG["discord_treasures_webhook"] = os.environ["DISCORD_TREASURES_WEBHOOK_URL"].strip()
    CONFIG["discord_level"] = args.discord_level
    CONFIG["discord_enabled"] = bool(args.discord_enable or CONFIG.get("discord_enabled"))

    # Matching scales
    if getattr(args, "match_fast", False):
        CONFIG["use_fast_scales"] = True
    if getattr(args, "match_full", False):
        CONFIG["use_fast_scales"] = False
    if getattr(args, "max_scale_attempts", None) is not None:
        CONFIG["max_scale_attempts"] = max(0, int(args.max_scale_attempts))

    # Setup logging with new system
    setup_logging()
    main_logger = logging.getLogger('bot')

    # ADDED: Validate critical config before starting
    _validate_config(main_logger)
    shield_cfg = CONFIG["shield_activation"]
    if not shield_cfg["rollout_accounts"] or not set(shield_cfg["rollout_accounts"]).issubset(shield_cfg["accounts"]):
        raise ValueError("Shield rollout accounts must be a nonempty subset of configured shield accounts")
    if shield_cfg.get("one_off_start_at") or shield_cfg.get("one_off_8h_start_at"):
        # Reject malformed/unzoned dates before touching the phone.
        shield_operations(datetime.datetime.now(datetime.timezone.utc), shield_cfg, "game1")
    main_logger.info("Shield scheduler: enabled=%s calibrated=%s scheduled=%s start=%s accounts=%s",
                     shield_cfg["enabled"], shield_cfg["ui_calibrated"], shield_cfg["schedule_enabled"],
                     shield_cfg.get("one_off_start_at") or "weekly Friday 23:00 Europe/Malta",
                     ",".join(shield_cfg["accounts"]))
    main_logger.info("24h shield rollout targets: %s (8h renewals retain all configured accounts).",
                     ",".join(shield_cfg["rollout_accounts"]))
    main_logger.info("8h shield schedule: %s; accounts=%s",
                     shield_cfg.get("one_off_8h_start_at") or "weekly Saturday 21:00 Europe/Malta",
                     ",".join(shield_cfg.get("rollout_8h_accounts") or shield_cfg["accounts"]))

    # Log environment diagnostics at DEBUG level
    if logging.getLogger('bot').isEnabledFor(logging.DEBUG):
        dump_env_diagnostics()

    # Preflight checks
    check_requirements()

    if args.preflight:
        device_id = get_device_id(retries=1, delay=0.0)
        if not device_id:
            main_logger.critical(
                "Preflight failed: no authorized Android device is visible through ADB."
            )
            sys.exit(1)
        main_logger.info(
            "Preflight passed: platform=%s python=%s adb=%s tesseract=%s device=%s",
            platform.system(),
            sys.version.split()[0],
            _resolve_adb(),
            _resolve_tesseract(),
            device_id,
        )
        sys.exit(0)

    # Create directories
    os.makedirs(CONFIG["debug_dir"], exist_ok=True)

    main_logger.info("=" * 60)
    main_logger.info(f"LastZ Bot starting - Log Level: {CONFIG['log_level']}")
    main_logger.info("=" * 60)

    startup_status = ActionStatusStore(
        CONFIG.get("status_file", os.path.join("runtime", "action_status.json")),
        {
            name: CONFIG.get("game_settings", {}).get(name, {})
            for name in CONFIG.get("game_coords", {})
        },
        timezone_name=CONFIG.get("status_timezone", "Europe/Malta"),
        reset_hour=CONFIG.get("daily_reset_hour", 4),
    )
    startup_status.set_bot("starting", "Discovering Android device")

    # Detect device (with retries)
    device_id = get_device_id(retries=8, delay=2.0)
    if not device_id:
        main_logger.critical("No suitable Android device found. Ensure USB is connected and 'adb devices' lists it.")
        main_logger.info("If unauthorized, check your phone for the RSA dialog and accept it.")
        startup_status.set_bot("failed", "No connected Android device was found")
        sys.exit(1)

    # scrcpy removed: do not start or check scrcpy; proceed ADB-only
    bot = ScrcpyBot(device_id)
    bot.configure_device_power_policy()
    bot.ensure_device_awake_unlocked(force=True, where="startup")

    # Close all apps at startup
    main_logger.info("Performing startup cleanup...")
    bot.close_all_apps()
    time.sleep(2)

    # Main game rotation
    game_names = list(CONFIG["game_coords"].keys())
    timing_cfg = CONFIG["timing"]
    rotation_seconds = timing_cfg["rotation_minutes"] * 60

    main_logger.info(f"Starting game rotation: {game_names}")
    main_logger.info(f"Rotation interval: {CONFIG['timing']['rotation_minutes']} minutes per game")

    # --- NEW: track exit code for systemd ---
    error_code = 0

    try:
        waiting_for_shields = False
        while True:
            delay = shield_start_delay(CONFIG["shield_activation"])
            if delay:
                if not waiting_for_shields:
                    main_logger.info("Holding normal rotation for scheduled shield rollout at %s (%.0fs remaining).",
                                     "Europe/Malta weekly/dated schedule", delay)
                    waiting_for_shields = True
                time.sleep(min(delay, 5.0))
                continue
            waiting_for_shields = False
            bot.process_scheduled_shields(game_names)
            # Randomize the order of games for each rotation
            game_names_shuffled = game_names[:]
            random.shuffle(game_names_shuffled)
            for game in game_names_shuffled:
                main_logger.info(f"{'='*20} Starting {game} {'='*20}")
                if not bot.launch_game(game):
                    main_logger.warning("Skipping %s because launch/base confirmation failed.", game)
                    bot._record_action(game, "game_launch", "failed", "Launch or base confirmation failed")
                    bot.close_all_apps()
                    continue
                bot._record_action(game, "game_launch", "success", "Game launched and base view confirmed")
                
                start_time = time.time()
                cycle_count = 0
                
                while True:
                    # A due shield sweep visits every account at the next cycle
                    # boundary, rather than waiting through four 20-minute slots.
                    if bot.process_scheduled_shields(game_names):
                        break  # sweep changes the foreground account; relaunch normally
                    elapsed_before_cycle = time.time() - start_time
                    remaining_seconds = rotation_seconds - elapsed_before_cycle
                    if remaining_seconds <= 0:
                        break

                    timing = _rotation_timing_suggestion(
                        bot._cycle_times_by_game.get(game, []), timing_cfg
                    )
                    if (
                        cycle_count > 0
                        and timing is not None
                        and remaining_seconds < timing["buffered_cycle_seconds"]
                    ):
                        main_logger.info(
                            "Rotating %s without starting another cycle: %.1fs remain, "
                            "estimated cycle allowance is %.1fs.",
                            game,
                            remaining_seconds,
                            timing["buffered_cycle_seconds"],
                        )
                        break

                    cycle_count += 1
                    main_logger.debug(f"Cycle {cycle_count} for {game}")
                    bot.run_one_cycle(game)
                
                elapsed = time.time() - start_time
                main_logger.info(f"Finished {game} after {elapsed:.1f}s ({cycle_count} cycles)")
                timing = _rotation_timing_suggestion(
                    bot._cycle_times_by_game.get(game, []), timing_cfg
                )
                if timing is not None:
                    main_logger.info(
                        "Rotation timing suggestion for %s: samples=%d avg=%.1fs "
                        "p90=%.1fs current=%dm recommended=%dm.",
                        game,
                        timing["samples"],
                        timing["average_seconds"],
                        timing["p90_seconds"],
                        timing_cfg["rotation_minutes"],
                        timing["recommended_minutes"],
                    )
                
                main_logger.info("Closing apps before rotation...")
                bot.close_all_apps()

    except KeyboardInterrupt:
        main_logger.info("Bot stopped by user (Ctrl+C)")
        bot.status_store.set_bot("stopped", "Bot stopped by user")
        # error_code stays 0
    except Exception as e:
        main_logger.critical(f"Unexpected error occurred: {e}", exc_info=True)
        bot.status_store.set_bot("failed", str(e))
        error_code = 1
    finally:
        if error_code == 0:
            bot.status_store.set_bot("stopped", "Bot process exited")
        main_logger.info("Bot shutdown complete")
        sys.exit(error_code)

# ADDED: Missing entry point
if __name__ == "__main__":
    main()
