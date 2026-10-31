"""Observability services extracted from the application facade."""
import cv2
import numpy as np
import time
import subprocess
import os
import sys
import psutil
import datetime
import platform
import logging
import json
from logging.handlers import RotatingFileHandler
import pytesseract
import re
import socket
import urllib.request
import urllib.error
import urllib.parse
import threading
from bot.context import context


def setup_logging():
    """Set up hierarchical logging with per-category level control and Discord forwarding."""
    # Create logs directory
    os.makedirs(context.CONFIG["logs_dir"], exist_ok=True)
    
    # Get global log level
    global_level_name = context.CONFIG.get("log_level", "INFO").upper()
    global_level = getattr(logging, global_level_name, logging.INFO)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)-8s - %(levelname)-8s - [%(funcName)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Set up root logger at TRACE to allow everything through
    root_logger = logging.getLogger()
    root_logger.setLevel(context.TRACE)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler - uses global level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(global_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler - always DEBUG or below for complete history
    log_file = os.path.join(context.CONFIG["logs_dir"], "lastz_bot.log")
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Configure category-specific loggers
    category_levels = context.CONFIG.get("log_levels", {})
    for category in context.LOG_CATEGORIES:
        logger = logging.getLogger(category)
        # Get category-specific level or fall back to global
        level_name = category_levels.get(category)
        if level_name:
            level = getattr(logging, level_name.upper(), global_level)
            logger.setLevel(level)
        else:
            logger.setLevel(global_level)
        
        # Don't propagate to avoid duplicate messages
        logger.propagate = True

    # Tesseract emits one DEBUG record for every subprocess invocation. Those
    # records drown out the bot's action/state logs during a live run (and are
    # especially noisy because the file handler intentionally retains DEBUG
    # history). Keep OCR outcomes visible through the bot/game loggers while
    # requiring an explicit logger-level override for library internals.
    logging.getLogger("pytesseract").setLevel(logging.WARNING)
    logging.getLogger("pytesseract.pytesseract").setLevel(logging.WARNING)

    # NEW: Optional Discord handler
    webhook = (context.CONFIG.get("discord_webhook") or os.environ.get("DISCORD_WEBHOOK_URL") or "").strip()
    discord_enabled = bool(context.CONFIG.get("discord_enabled", False) or (webhook and context.CONFIG.get("discord_enabled") is not False))
    if webhook and discord_enabled:
        # Map level name to numeric
        lvl_name = str(context.CONFIG.get("discord_level", "INFO")).upper()
        lvl = getattr(logging, lvl_name, logging.INFO)
        try:
            dh = context.DiscordWebhookHandler(
                webhook_url=webhook,
                username="LastZ Bot",
                timeout=float(context.CONFIG.get("discord_timeout", 4.0)),
                min_interval=float(context.CONFIG.get("discord_min_interval", 0.25)),
            )
            # Concise format for Discord
            discord_formatter = logging.Formatter('[%(levelname)s] %(name)s - %(message)s')
            dh.setFormatter(discord_formatter)
            dh.setLevel(lvl)
            root_logger.addHandler(dh)
            logging.getLogger('bot').info("Discord logging enabled at level %s", lvl_name)
        except Exception as e:
            logging.getLogger('bot').warning("Failed to initialize Discord logging handler: %s", e)
    elif discord_enabled:
        logging.getLogger('bot').warning(
            "Discord logging is enabled but no webhook is configured. "
            "Set DISCORD_WEBHOOK_URL or pass --discord-webhook."
        )

    # Log initial configuration
    main_logger = logging.getLogger('bot')
    main_logger.info(f"Logging initialized - Global level: {global_level_name}")
    for category in context.LOG_CATEGORIES:
        logger = logging.getLogger(category)
        main_logger.debug(f"  {category}: {logging.getLevelName(logger.level)}")

    # Central Axiom handler.  Credentials stay in AXIOM_TOKEN rather than
    # CONFIG or command-line arguments.
    axiom_token = os.environ.get("AXIOM_TOKEN", "").strip()
    axiom_dataset = str(context.CONFIG.get("axiom_dataset", "")).strip()
    axiom_enabled = bool(context.CONFIG.get("axiom_enabled", False))
    if axiom_enabled and axiom_dataset and axiom_token:
        axiom_lvl_name = str(context.CONFIG.get("axiom_level", "INFO")).upper()
        axiom_lvl = getattr(logging, axiom_lvl_name, logging.INFO)
        try:
            ah = context.AxiomLogHandler(
                dataset=axiom_dataset,
                token=axiom_token,
                endpoint=str(context.CONFIG.get("axiom_endpoint", "https://api.axiom.co")),
                timeout=float(context.CONFIG.get("axiom_timeout", 4.0)),
                min_interval=float(context.CONFIG.get("axiom_min_interval", 0.5)),
            )
            ah.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
                datefmt='%Y-%m-%dT%H:%M:%S',
            ))
            ah.setLevel(axiom_lvl)
            root_logger.addHandler(ah)
            logging.getLogger('bot').info(
                "Axiom logging enabled: dataset=%s level=%s", axiom_dataset, axiom_lvl_name
            )
        except Exception as e:
            logging.getLogger('bot').warning("Failed to initialize Axiom logging handler: %s", e)
    elif axiom_enabled:
        logging.getLogger('bot').warning(
            "Axiom logging is enabled but AXIOM_TOKEN or axiom_dataset is missing."
        )

    # Optional legacy ntfy.sh handler.
    ntfy_topic = (context.CONFIG.get("ntfy_topic") or "").strip()
    ntfy_enabled = bool(context.CONFIG.get("ntfy_enabled", False)) and bool(ntfy_topic) and "CHANGEME" not in ntfy_topic.upper()
    if ntfy_enabled:
        ntfy_lvl_name = str(context.CONFIG.get("ntfy_level", "INFO")).upper()
        ntfy_lvl = getattr(logging, ntfy_lvl_name, logging.INFO)
        try:
            nh = context.NtfyLogHandler(
                topic=ntfy_topic,
                server=str(context.CONFIG.get("ntfy_server", "https://ntfy.sh")),
                timeout=float(context.CONFIG.get("ntfy_timeout", 4.0)),
                min_interval=float(context.CONFIG.get("ntfy_min_interval", 0.5)),
            )
            ntfy_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
                datefmt='%H:%M:%S',
            )
            nh.setFormatter(ntfy_formatter)
            nh.setLevel(ntfy_lvl)
            root_logger.addHandler(nh)
            logging.getLogger('bot').info(
                "ntfy.sh logging enabled: topic=%s level=%s", ntfy_topic, ntfy_lvl_name
            )
        except Exception as e:
            logging.getLogger('bot').warning("Failed to initialize ntfy.sh logging handler: %s", e)


class DiscordWebhookHandler(logging.Handler):
    def __init__(self, webhook_url: str, username: str = "LastZ Bot", timeout: float = 4.0, min_interval: float = 0.25, max_length: int = 1900):
        super().__init__()
        self.webhook_url = webhook_url
        self.username = username
        self.timeout = timeout
        self.min_interval = max(0.0, float(min_interval or 0.0))
        self.max_length = max_length
        self._last_sent = 0.0
        self._lock = threading.Lock()
        self._failure_count = 0  # ADDED: Track consecutive failures
        self._max_failures = 5   # ADDED: Disable after N failures

    def emit(self, record: logging.LogRecord) -> None:
        # ADDED: Stop trying if too many failures
        if self._failure_count >= self._max_failures:
            return
            
        try:
            msg = self.format(record)
            # Truncate to fit Discord content limit
            if len(msg) > self.max_length:
                msg = msg[: self.max_length - 20] + " …(truncated)"
            with self._lock:
                now = time.time()
                wait = self.min_interval - (now - self._last_sent)
                if wait > 0:
                    try:
                        time.sleep(wait)
                    except Exception:
                        pass
                self._last_sent = time.time()

            try:
                ok = context._discord_webhook_post(
                    content=msg,
                    webhook_url=self.webhook_url,
                    timeout=self.timeout,
                )
                if ok:
                    self._failure_count = 0  # ADDED: Reset on success
                else:
                    self._failure_count += 1
                    if self._failure_count >= self._max_failures:
                        # Log to console (not recursively to Discord)
                        print(f"Discord webhook disabled after {self._max_failures} failures", file=sys.stderr)
            except Exception:
                self._failure_count += 1  # ADDED: Increment on any error
        except Exception:
            pass


class _SingleFlightLogHandler(logging.Handler):
    """One in-flight delivery, no pending queue; excess records are counted/dropped."""

    def __init__(self):
        super().__init__()
        self._delivery_slot = threading.BoundedSemaphore(1)
        self._dispatch_lock = threading.Lock()
        self._delivery_closed = False
        self.dropped_records = 0

    def emit(self, record: logging.LogRecord) -> None:
        with self._dispatch_lock:
            if self._delivery_closed or self._failure_count >= self._max_failures:
                return
            if not self._delivery_slot.acquire(blocking=False):
                self.dropped_records += 1
                return
        try:
            threading.Thread(target=self._deliver_one, args=(record,), daemon=True).start()
        except Exception:
            self._delivery_slot.release()
            with self._dispatch_lock:
                self.dropped_records += 1

    def _deliver_one(self, record: logging.LogRecord) -> None:
        try:
            with self._dispatch_lock:
                if self._delivery_closed:
                    return
            self._send(record)
        finally:
            self._delivery_slot.release()

    def close(self) -> None:
        # An already-running request retains its configured timeout; shutdown
        # never waits for the network or starts delivery of another record.
        with self._dispatch_lock:
            self._delivery_closed = True
        super().close()


class NtfyLogHandler(_SingleFlightLogHandler):
    """
    Logging handler that POSTs records to an ntfy.sh topic in a background
    thread so it never blocks the bot.

    ntfy.sh is a free, no-account-required pub/sub notification service.
    Messages are cached for 12 hours on the public server.

    Write:  POST https://ntfy.sh/<topic>   (done here automatically)
    Read:   GET  https://ntfy.sh/<topic>/json?since=12h&poll=1
            (use the topic web UI or an HTTP client)

    The topic should be a non-guessable string (treat it like a password)
    because anyone who knows it can read the message stream.
    """

    # Map Python log levels to ntfy priority integers (1=min … 5=max)
    _PRIORITY = {
        logging.CRITICAL: "5",
        logging.ERROR:    "4",
        logging.WARNING:  "3",
        logging.INFO:     "2",
        logging.DEBUG:    "1",
    }

    def __init__(self, topic: str, server: str = "https://ntfy.sh",
                 timeout: float = 4.0, min_interval: float = 0.5):
        super().__init__()
        self.url = f"{server.rstrip('/')}/{topic}"
        self.timeout = timeout
        self.min_interval = max(0.0, float(min_interval))
        self._last_sent = 0.0
        self._lock = threading.Lock()
        self._failure_count = 0
        self._max_failures = 5

    def _send(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            if len(msg) > 4096:
                msg = msg[:4076] + " …(truncated)"

            priority = self._PRIORITY.get(record.levelno, "2")
            title = f"LastZ [{record.levelname}] {record.name}"

            with self._lock:
                now = time.time()
                wait = self.min_interval - (now - self._last_sent)
                if wait > 0:
                    time.sleep(wait)
                self._last_sent = time.time()

            req = urllib.request.Request(
                self.url,
                data=msg.encode("utf-8"),
                headers={
                    "Content-Type": "text/plain; charset=utf-8",
                    "User-Agent": "lastz-bot/1.0",
                    "X-Priority": priority,
                    "X-Title": title,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp.read(0)
            self._failure_count = 0
        except Exception:
            self._failure_count += 1
            if self._failure_count >= self._max_failures:
                print(f"ntfy.sh handler disabled after {self._max_failures} failures", file=sys.stderr)


class AxiomLogHandler(_SingleFlightLogHandler):
    """One asynchronous delivery at a time; burst records are counted and dropped."""

    def __init__(self, dataset: str, token: str, endpoint: str,
                 timeout: float = 4.0, min_interval: float = 0.5):
        super().__init__()
        self.dataset = dataset
        self.token = token
        self.url = f"{endpoint.rstrip('/')}/v1/ingest/{dataset}"
        self.timeout = timeout
        self.min_interval = max(0.0, float(min_interval))
        self._last_sent = 0.0
        self._lock = threading.Lock()
        self._failure_count = 0
        self._max_failures = 5

    def _send(self, record: logging.LogRecord) -> None:
        try:
            with self._lock:
                now = time.time()
                wait = self.min_interval - (now - self._last_sent)
                if wait > 0:
                    time.sleep(wait)
                self._last_sent = time.time()

            event = {
                "_time": datetime.datetime.fromtimestamp(
                    record.created, datetime.timezone.utc
                ).isoformat(),
                "service": "lastz-bot",
                "host": socket.gethostname(),
                "level": record.levelname,
                "logger": record.name,
                "message": self.format(record),
            }
            req = urllib.request.Request(
                self.url,
                data=json.dumps([event]).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                    "User-Agent": "lastz-bot/1.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response.read(0)
            self._failure_count = 0
        except Exception:
            self._failure_count += 1
            if self._failure_count >= self._max_failures:
                print(f"Axiom handler disabled after {self._max_failures} failures", file=sys.stderr)


def dump_env_diagnostics():
    """Log detailed environment info to help debug Linux issues."""
    bot_log = logging.getLogger('bot')
    try:
        import platform
        bot_log.info("Env: platform=%s release=%s python=%s", platform.system(), platform.release(), sys.version.split()[0])
    except Exception as e:
        bot_log.debug(f"Env detect failed: {e}")
    # Versions and paths
    try:
        bot_log.info("OpenCV=%s numpy=%s psutil=%s pytesseract=%s", cv2.__version__, np.__version__, psutil.__version__, getattr(pytesseract, "__version__", "unknown"))
    except Exception:
        pass
    adb_path = context._resolve_adb()
    bot_log.info("adb path=%s", adb_path or "<not found>")
    tess_bin = context._resolve_tesseract()
    bot_log.info("tesseract path=%s", tess_bin or "<not found>")
    # Tesseract version (safe)
    if tess_bin:
        try:
            out = subprocess.run([tess_bin, "--version"], capture_output=True, text=True, timeout=5)
            first = out.stdout.splitlines()[0] if out.stdout else ""
            bot_log.info("tesseract version=%s", first)
        except Exception as e:
            bot_log.debug(f"Tesseract version query failed: {e}")
    # adb version (safe)
    if adb_path:
        try:
            out = subprocess.run([adb_path, "version"], capture_output=True, text=True, timeout=5)
            line = out.stdout.splitlines()[0] if out.stdout else ""
            bot_log.info("adb version=%s", line)
        except Exception as e:
            bot_log.debug(f"adb version query failed: {e}")


def _discord_webhook_post(content: str, webhook_url: str, timeout: float = 4.0,
                          file_bytes: bytes | None = None, file_name: str | None = None) -> bool:
        """Post a message to a Discord webhook, optionally with one image attachment."""
        if not webhook_url:
            return False
        try:
            if file_bytes is None:
                payload = {"content": content}
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    webhook_url,
                    data=data,
                    headers={"Content-Type": "application/json", "User-Agent": "lastz-bot/1.0"},
                    method="POST",
                )
            else:
                boundary = f"----LastZBoundary{int(time.time() * 1000)}"
                payload = json.dumps({"content": content}, ensure_ascii=False).encode("utf-8")
                part1 = (
                    f"--{boundary}\r\n"
                    f"Content-Disposition: form-data; name=\"payload_json\"\r\n"
                    f"Content-Type: application/json\r\n\r\n"
                ).encode("utf-8")
                fname = file_name or "treasure.png"
                part2_header = (
                    f"\r\n--{boundary}\r\n"
                    f"Content-Disposition: form-data; name=\"files[0]\"; filename=\"{fname}\"\r\n"
                    f"Content-Type: image/png\r\n\r\n"
                ).encode("utf-8")
                part3 = f"\r\n--{boundary}--\r\n".encode("utf-8")
                data = part1 + payload + part2_header + file_bytes + part3
                req = urllib.request.Request(
                    webhook_url,
                    data=data,
                    headers={
                        "Content-Type": f"multipart/form-data; boundary={boundary}",
                        "User-Agent": "lastz-bot/1.0",
                    },
                    method="POST",
                )

            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp.read(0)
            return True
        except Exception:
            return False


def _discord_webhook_post_many(content, webhook_url, files, timeout=15.0):
    """Send one ordered evidence group, requiring Discord's message acknowledgement.

    files contains (safe_filename, png_bytes, caption) tuples. Never log the
    webhook URL: its path contains a credential. Existing treasure posts retain
    their original single-file implementation.
    """
    if not webhook_url or not 0 <= len(files) <= 10:
        return False
    try:
        parsed = urllib.parse.urlsplit(webhook_url)
        if parsed.scheme != "https" or parsed.hostname not in {"discord.com", "discordapp.com"}:
            return False
        if not parsed.path.startswith("/api/webhooks/"):
            return False
        query = dict(urllib.parse.parse_qsl(parsed.query))
        query["wait"] = "true"
        url = urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(query)))
        boundary = "----LastZEvidence" + os.urandom(12).hex()
        attachments, embeds = [], []
        for index, (name, data, caption) in enumerate(files):
            if not re.fullmatch(r"[A-Za-z0-9_.-]+\.png", name) or not data or len(data) > 8 * 1024 * 1024:
                return False
            attachments.append({"id": index, "filename": name, "description": caption})
            embeds.append({"title": caption, "image": {"url": "attachment://" + name}})
        payload = {"content": content[:2000], "attachments": attachments,
                   "embeds": embeds, "allowed_mentions": {"parse": []}}
        parts = [(f'--{boundary}\r\nContent-Disposition: form-data; name="payload_json"\r\n'
                  'Content-Type: application/json\r\n\r\n').encode(),
                 json.dumps(payload, ensure_ascii=False).encode("utf-8")]
        for index, (name, data, _) in enumerate(files):
            parts.extend([(f'\r\n--{boundary}\r\nContent-Disposition: form-data; '
                           f'name="files[{index}]"; filename="{name}"\r\n'
                           'Content-Type: image/png\r\n\r\n').encode(), data])
        parts.append(f"\r\n--{boundary}--\r\n".encode())
        request = urllib.request.Request(url, data=b"".join(parts), method="POST",
                    headers={"Content-Type": "multipart/form-data; boundary=" + boundary,
                             "User-Agent": "lastz-bot/1.0"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            message = json.load(response)
        if not message.get("id"):
            return False
        delivered = {attachment.get("filename") for attachment in message.get("attachments", [])}
        # Discord can move uploaded images into embeds and return attachments=[].
        # Require every requested image by filename, not merely an embed count.
        for embed in message.get("embeds", []):
            uploaded = embed.get("image", {})
            parsed_image = urllib.parse.urlsplit(uploaded.get("url", ""))
            if (parsed_image.scheme == "https"
                    and parsed_image.hostname in {"cdn.discordapp.com", "media.discordapp.net"}
                    and uploaded.get("width", 0) > 0 and uploaded.get("height", 0) > 0):
                delivered.add(urllib.parse.unquote(parsed_image.path.rsplit("/", 1)[-1]))
        return all(name in delivered for name, _, _ in files)
    except Exception:
        return False


class ObservabilityMixin:
    def _init_observability(self):
        """
        Set up the per-session trace directory and event log file.

        Called once from __init__.  Creates:
          debug/trace/<trace_session_id>/   directory for optional screenshots
          logs/<trace_session_id>.jsonl     newline-delimited JSON event log

        The session ID is a timestamp string ("trace_YYYYMMDD_HHMMSS").  All
        paths come from CONFIG so they can be redirected without code changes.
        Does nothing if CONFIG["internal_trace_enabled"] is False.
        """
        self._trace_enabled = bool(context.CONFIG.get("internal_trace_enabled", True))
        self._trace_screenshots_enabled = bool(context.CONFIG.get("internal_trace_screenshots", False))
        if not self._trace_enabled:
            return

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._trace_session_id = f"trace_{ts}"
        base_dir = context.CONFIG.get("internal_trace_dir", os.path.join("debug", "trace"))
        self._trace_dir = os.path.join(base_dir, self._trace_session_id)
        self._trace_events_path = os.path.join(context.CONFIG.get("logs_dir", "logs"), f"{self._trace_session_id}.jsonl")

        os.makedirs(self._trace_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self._trace_events_path), exist_ok=True)
        self._obs_event("trace_session_started", device=self.device_id, trace_dir=self._trace_dir)
        self.logger.info(
            "Internal trace enabled: events=%s screenshots=%s",
            self._trace_events_path,
            self._trace_dir,
        )

    def _obs_event(self, event: str, **data):
        """
        Append a single JSON-formatted trace event to the session event log.

        The record always includes:
          ts       ISO-8601 timestamp with millisecond precision
          event    caller-supplied event name (e.g. "cycle_start", "trucks_end")
          session  trace session ID string
          **data   any additional keyword args the caller wants to record

        Silently ignored if tracing is disabled or if the file write fails.
        """
        if not self._trace_enabled:
            return
        payload = {
            "ts": datetime.datetime.now().isoformat(timespec="milliseconds"),
            "event": event,
            "session": self._trace_session_id,
            **data,
        }
        try:
            with open(self._trace_events_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=True, default=str) + "\n")
        except Exception as e:
            self._trace_logger.debug("Trace event write failed: %s", e)

    def _obs_capture(self, tag: str, image: np.ndarray | None = None, **data) -> str | None:
        """
        Save a debug screenshot to the trace directory and log a "screenshot"
        event pointing to the saved file.

        Parameters
        ----------
        tag : str
            Descriptive label used in the filename and event record.
            Non-alphanumeric characters are replaced with underscores.
        image : ndarray, optional
            If supplied, this frame is saved directly.  Otherwise a fresh
            screencap is taken via adb_screenshot().
        **data
            Extra fields included in the "screenshot" trace event.

        Returns
        -------
        str or None
            Relative path of the saved PNG, or None if capture was skipped
            (tracing off, budget exhausted, or screenshot failed).

        Budget
        ------
        Each cycle resets self._trace_cycle_shots_left to
        CONFIG["internal_trace_max_shots_per_cycle"] (default 8).  Once
        exhausted, no more screenshots are saved until the next cycle.
        """
        if not (self._trace_enabled and self._trace_screenshots_enabled):
            return None
        if self._trace_cycle_shots_left <= 0:
            return None

        frame = image if image is not None else self.adb_screenshot()
        if frame is None:
            return None

        safe_tag = re.sub(r"[^A-Za-z0-9_.-]+", "_", tag)[:64] or "shot"
        shot_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        name = f"{shot_ts}_{safe_tag}.png"
        path = os.path.join(self._trace_dir, name)
        ok = cv2.imwrite(path, frame)
        if not ok:
            return None
        self._trace_cycle_shots_left -= 1
        rel_path = path.replace("\\", "/")
        self._obs_event("screenshot", tag=safe_tag, file=rel_path, shots_left=self._trace_cycle_shots_left, **data)
        return rel_path

    def _record_action(self, game_name: str, action: str, outcome: str, message: str = "", **details) -> None:
        """Persist an account action without allowing status I/O to stop the bot."""
        try:
            if outcome == "failed":
                try:
                    evidence = self._obs_capture(f"failed_{action}_{game_name}", game=game_name, reason=message)
                except Exception as exc:
                    self.state_logger.warning("Failure capture unavailable: %s", exc)
                    evidence = None
                if evidence:
                    details.setdefault("evidence", evidence)
            self.status_store.record(game_name, action, outcome, message, **details)
            self.state_logger.info("[%s] %s: %s — %s", game_name, action, outcome, message)
        except Exception as exc:
            self.state_logger.warning("Unable to persist %s status for %s: %s", action, game_name, exc)

    def _log_perf_metrics(self):
        """Log performance metrics at INFO level."""
        metrics = self._perf_metrics
        avg_cycle = sum(metrics['cycle_times'][-10:]) / len(metrics['cycle_times'][-10:]) if metrics['cycle_times'] else 0
        self.perf_logger.info(
            f"Performance: screenshots={metrics['screenshots']} "
            f"templates={metrics['template_matches']} "
            f"adb_cmds={metrics['adb_commands']} "
            f"avg_cycle_time={avg_cycle:.2f}s"
        )
