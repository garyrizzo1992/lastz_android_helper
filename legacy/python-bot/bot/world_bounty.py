"""World_Bounty services extracted from the application facade."""
import cv2
import numpy as np
import time
import subprocess
import re
from pathlib import Path
import socket
import struct
from importlib import metadata as importlib_metadata
from bot.context import context


def world_bounty_zoom_out(self) -> bool:
    """Apply the calibrated, Pi-safe two-finger world-map zoom-out gesture.

    The game resets map scale whenever a coordinate search completes.  Android's
    ``input`` utility cannot create a real two-pointer gesture, so this uses the
    control socket from the already-required ``scrcpy-client`` package without
    opening a desktop window.  It works the same on Windows and Raspberry Pi.
    """
    cfg = context.CONFIG.get("world_bounty", {})
    if not cfg.get("zoom_enabled", False):
        return True

    candidates = []
    try:
        candidates.append(
            Path(importlib_metadata.distribution("scrcpy-client").locate_file(
                "scrcpy/scrcpy-server-v1.24.jar"
            ))
        )
    except importlib_metadata.PackageNotFoundError:
        pass
    candidates.append(Path(__file__).resolve().parent / "scrcpy" / "scrcpy-server-v1.24.jar")
    server_jar = next((path for path in candidates if path.is_file()), None)
    if server_jar is None:
        self.game_logger.error("World bounty zoom needs scrcpy-client's control-server JAR.")
        return False

    adb = context._resolve_adb() or "adb"
    port = int(cfg.get("zoom_control_port", 27183))
    remote_path = str(cfg.get("zoom_server_remote_path", "/data/local/tmp/scrcpy-server-v1.24.jar"))
    steps = max(1, int(cfg.get("zoom_steps", 2)))
    settle_delay = max(0.2, float(cfg.get("zoom_settle_delay", 1.5)))
    video_socket = control_socket = None
    server_process = None
    server_pid = None

    def receive_exact(sock: socket.socket, size: int) -> bytes:
        data = b""
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                raise ConnectionError(f"scrcpy control socket closed at {len(data)}/{size} bytes")
            data += chunk
        return data

    try:
        push = self.adb_command("push", str(server_jar), remote_path)
        if push is None or push.returncode != 0:
            raise RuntimeError("could not deploy scrcpy control server")
        self.adb_command("forward", "--remove", f"tcp:{port}")
        forward = self.adb_command("forward", f"tcp:{port}", "localabstract:scrcpy")
        if forward is None or forward.returncode != 0:
            raise RuntimeError("could not forward scrcpy control socket")

        server_command = (
            f"echo $$; exec env CLASSPATH={remote_path} app_process / "
            "com.genymobile.scrcpy.Server 1.24 log_level=warn bit_rate=1000000 "
            "max_size=0 max_fps=1 lock_video_orientation=-1 tunnel_forward=true "
            "control=true display_id=0 show_touches=false stay_awake=false "
            "clipboard_autosync=false"
        )
        server_process = subprocess.Popen(
            [adb, "-s", self.device_id, "shell", server_command],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        pid_line = server_process.stdout.readline().strip() if server_process.stdout else ""
        if pid_line.isdigit():
            server_pid = pid_line

        # ADB may accept its local TCP connection a moment before the Android
        # server has bound its abstract socket. Retry the *whole* handshake in
        # that short window rather than treating the early closed socket as a
        # failed zoom.
        last_handshake_error = None
        for _ in range(30):
            try:
                video_socket = socket.create_connection(("127.0.0.1", port), timeout=1.0)
                if receive_exact(video_socket, 1) != b"\x00":
                    raise ConnectionError("scrcpy control server returned an invalid handshake byte")
                control_socket = socket.create_connection(("127.0.0.1", port), timeout=1.0)
                receive_exact(video_socket, 64)  # device name
                width, height = struct.unpack(">HH", receive_exact(video_socket, 4))
                break
            except (OSError, ConnectionError, struct.error) as exc:
                last_handshake_error = exc
                if control_socket is not None:
                    control_socket.close()
                    control_socket = None
                if video_socket is not None:
                    video_socket.close()
                    video_socket = None
                time.sleep(0.1)
        else:
            raise ConnectionError(f"scrcpy control handshake did not complete: {last_handshake_error}")
        if width <= 0 or height <= 0:
            raise RuntimeError("scrcpy control server returned an invalid display size")

        before = self.adb_screenshot()

        def touch(action: int, touch_id: int, x: float, y: float) -> None:
            control_socket.sendall(struct.pack(
                ">BBqiiHHHi", 2, action, touch_id, int(x), int(y), width, height, 0xFFFF, 1
            ))

        # A symmetric inward pinch: two gestures is the approved bounty scale.
        for _ in range(steps):
            left_start, right_start = 260, 820
            left_end, right_end, y = 450, 630, 1000
            touch(0, 0, left_start, y)
            touch(0, 1, right_start, y)
            time.sleep(0.12)
            for move in range(1, 16):
                touch(2, 0, left_start + (left_end - left_start) * move / 15, y)
                touch(2, 1, right_start + (right_end - right_start) * move / 15, y)
                time.sleep(0.025)
            touch(1, 0, left_end, y)
            touch(1, 1, right_end, y)
            time.sleep(settle_delay)

        after = self.adb_screenshot()
        if before is None or after is None:
            raise RuntimeError("could not capture map frames around zoom gesture")
        x1, y1, x2, y2 = (int(value) for value in cfg.get("scan_roi", (120, 340, 720, 1720)))
        frame_delta = float(np.mean(cv2.absdiff(before[y1:y2, x1:x2], after[y1:y2, x1:x2])))
        if frame_delta < float(cfg.get("min_zoom_frame_delta", 5.0)):
            raise RuntimeError(f"zoom gesture was not visually confirmed (delta={frame_delta:.2f})")
        self.game_logger.info("World bounty zoom confirmed: %d inward pinch(es), frame delta %.2f.", steps, frame_delta)
        self._obs_event("world_bounty_zoom", steps=steps, frame_delta=round(frame_delta, 2))
        return True
    except Exception as exc:
        self.game_logger.warning("World bounty zoom failed: %s", exc)
        self._obs_capture("world_bounty_zoom_failed", error=str(exc))
        return False
    finally:
        if control_socket is not None:
            control_socket.close()
        if video_socket is not None:
            video_socket.close()
        if server_pid:
            self.adb_command("shell", "kill", server_pid)
        if server_process is not None:
            try:
                server_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                server_process.terminate()
        self.adb_command("forward", "--remove", f"tcp:{port}")


def plunder_world_bounties(self, game_name: str | None = None) -> int:
    """Visit configured map hotspots and plunder up to five confirmed bounties."""
    game_label = game_name or "unknown"
    cfg = context.CONFIG.get("world_bounty", {})
    if not cfg.get("enabled", False):
        return 0

    hotspots = []
    for raw in cfg.get("hotspots", ()):
        try:
            hotspot = {
                "state": int(raw["state"]),
                "x": int(raw["x"]),
                "y": int(raw["y"]),
            }
        except (KeyError, TypeError, ValueError):
            self._record_action(game_label, "world_bounty_plunder", "failed", "Invalid hotspot configuration")
            return 0
        if not (1 <= hotspot["state"] <= 63 and 0 <= hotspot["x"] <= 1200 and 0 <= hotspot["y"] <= 1200):
            self._record_action(
                game_label,
                "world_bounty_plunder",
                "failed",
                "Hotspot is outside supported map bounds",
                hotspot=hotspot,
            )
            return 0
        hotspots.append(hotspot)
    if not hotspots:
        self._record_action(game_label, "world_bounty_plunder", "failed", "No hotspots configured")
        return 0

    daily_limit = max(1, int(cfg.get("daily_limit", 5)))
    counter = getattr(self, "_last_bounty_plunder_counter", None)
    if counter is not None:
        used, total = counter
        effective_total = min(total, daily_limit)
        if used >= effective_total:
            self._mark_daily_action_complete(
                game_label,
                "world_bounty_plunder",
                "Bounty panel confirms the daily plunder limit is full",
                counter=f"{used}/{total}",
            )
            return 0
        remaining = effective_total - used
    else:
        remaining = daily_limit

    confirmed = 0
    candidate_taps = 0
    total_views = 0
    visited_hotspots: list[dict] = []
    route_failed = False
    max_candidate_taps = int(cfg.get("max_candidate_taps", 24))
    max_swipes = int(cfg.get("max_swipes_per_hotspot", 4))
    swipes = list(cfg.get("swipes", []))
    action_delay = float(context.CONFIG["timing"]["action_delay"])
    fast_delay = float(context.CONFIG["timing"]["fast_click_delay"])

    if not self.ensure_base_view():
        fallback_frame = self.adb_screenshot()
        toggle_text = context._ocr_frame_text(fallback_frame, (820, 1840, 1080, 2160), psm=11)
        if "world" not in re.sub(r"[^a-z]+", "", toggle_text.lower()):
            self._record_action(game_label, "world_bounty_plunder", "failed", "Base view was not confirmed")
            return 0
        self.game_logger.info("Accepted base view from the visible World toggle after stability timeout.")

    def enter_coordinate(field_name: str, value: int) -> bool:
        self.adb_tap(*context.CONFIG["action_coords"][field_name])
        time.sleep(fast_delay)
        self.adb_keyevent(123)  # KEYCODE_MOVE_END
        for _ in range(6):
            self.adb_keyevent(67)  # KEYCODE_DEL
        result = self.adb_command("shell", "input", "text", str(value))
        if result is None or result.returncode != 0:
            return False
        self.adb_keyevent(66)  # KEYCODE_ENTER / IME Done
        time.sleep(max(action_delay, fast_delay))
        return True

    def navigate_to_hotspot(hotspot: dict) -> bool:
        self.adb_tap(*context.CONFIG["action_coords"]["search_button"])
        time.sleep(action_delay)
        form_frame = self.adb_screenshot()
        if not context._world_coordinate_form_visible(form_frame):
            self.game_logger.warning("Coordinate form did not open for hotspot %s.", hotspot)
            return False
        for field_name, value in (
            ("world_state_field", hotspot["state"]),
            ("world_x_field", hotspot["x"]),
            ("world_y_field", hotspot["y"]),
        ):
            if not enter_coordinate(field_name, value):
                return False

        state_frame = None
        banner_text = ""
        for submit_point in cfg.get(
            "state_submit_retries",
            (context.CONFIG["action_coords"]["world_state_search"],),
        ):
            self.adb_tap(*submit_point)
            time.sleep(action_delay)
            state_frame = self.adb_screenshot()
            # The short banner is one line, but PSM 7 often confuses two-digit
            # state numbers with letters when a building overlaps its edge.
            banner_text = context._ocr_frame_text(state_frame, tuple(cfg["state_banner_roi"]), psm=6)
            normalized = re.sub(r"[^a-z0-9]+", "", banner_text.lower())
            if f"state{hotspot['state']}" in normalized:
                self.game_logger.info(
                    "Hotspot confirmed: State #%d X:%d Y:%d.",
                    hotspot["state"], hotspot["x"], hotspot["y"],
                )
                return True
            if not context._world_coordinate_form_visible(state_frame):
                break
        self.game_logger.warning("Hotspot navigation was not confirmed (%s, OCR=%r).", hotspot, banner_text)
        self._obs_capture(
            "world_bounty_hotspot_unconfirmed",
            image=state_frame,
            game=game_label,
            hotspot=hotspot,
        )
        return False

    try:
        self.game_logger.info(
            "Starting calibrated-zoom bounty route across %d hotspot(s); remaining=%d.",
            len(hotspots),
            remaining,
        )
        self.adb_tap(*context.CONFIG["action_coords"]["open_world"])
        time.sleep(action_delay)
        if not self.confirm_screen(must_screen="world", timeout=3.0, where="world bounty: open world"):
            self._record_action(game_label, "world_bounty_plunder", "failed", "World view did not open")
            return 0

        for hotspot in hotspots:
            if confirmed >= remaining or candidate_taps >= max_candidate_taps:
                break
            if not navigate_to_hotspot(hotspot):
                route_failed = True
                break
            if cfg.get("zoom_enabled", False) and not self.world_bounty_zoom_out():
                route_failed = True
                break
            visited_hotspots.append(dict(hotspot))
            seen_views: set[bytes] = set()

            for view_index in range(max_swipes + 1):
                if confirmed >= remaining or candidate_taps >= max_candidate_taps:
                    break
                frame = self.adb_screenshot()
                if frame is None:
                    route_failed = True
                    break
                total_views += 1
                sx1, sy1, sx2, sy2 = (
                    int(value) for value in cfg.get("scan_roi", (120, 340, 720, 1720))
                )
                map_crop = frame[sy1:sy2, sx1:sx2]
                if map_crop.size:
                    tiny = cv2.resize(map_crop, (24, 24), interpolation=cv2.INTER_AREA)
                    signature = (tiny // 16).astype(np.uint8).tobytes()
                    if signature in seen_views and view_index > 0:
                        break
                    seen_views.add(signature)

                candidates = context._find_world_bounty_markers(frame, cfg)
                self.game_logger.info(
                    "Hotspot #%d (%d,%d), view %d/%d: %d candidate(s).",
                    hotspot["state"], hotspot["x"], hotspot["y"],
                    view_index + 1, max_swipes + 1, len(candidates),
                )
                self._obs_event(
                    "world_bounty_view",
                    game=game_label,
                    hotspot=hotspot,
                    view=view_index,
                    candidates=len(candidates),
                )

                if candidates:
                    candidate = candidates[0]
                    candidate_taps += 1
                    self.adb_tap(*candidate["center"])
                    time.sleep(float(cfg.get("candidate_settle_delay", 1.2)))
                    action_frame = self.adb_screenshot()
                    plunder_center = context._find_ocr_word_center(
                        action_frame,
                        "plunder",
                        tuple(cfg.get("plunder_ocr_roi", (80, 700, 1000, 1900))),
                    )
                    if plunder_center is None:
                        if candidate_taps <= 4:
                            self._obs_capture(
                                "world_bounty_candidate_rejected",
                                image=action_frame,
                                game=game_label,
                                hotspot=hotspot,
                                candidate=candidate,
                            )
                        if context._world_info_card_visible(action_frame):
                            self.adb_keyevent(111)
                            time.sleep(fast_delay)
                        if not self.confirm_screen(
                            must_screen="world",
                            timeout=1.2,
                            where="world bounty: candidate rejected",
                        ):
                            route_failed = True
                            break
                    else:
                        self.game_logger.info("Confirmed Plunder action at %s; executing.", plunder_center)
                        self.adb_tap(*plunder_center)
                        time.sleep(float(cfg.get("reward_settle_delay", 2.0)))
                        reward_frame = self.adb_screenshot()
                        reward_roi = tuple(cfg.get("reward_ocr_roi", (50, 250, 1030, 1950)))
                        reward_text = context._ocr_frame_text(reward_frame, reward_roi, psm=11)
                        # The illustrated reward cards confuse sparse-text OCR.
                        # The title alone is high contrast and reliably reads
                        # "Congratulations!" with a single-block OCR pass.
                        reward_title_text = context._ocr_frame_text(
                            reward_frame,
                            tuple(cfg.get("reward_title_ocr_roi", (100, 400, 1000, 800))),
                            psm=6,
                        )
                        normalized_reward = re.sub(
                            r"[^a-z]+", " ", f"{reward_text} {reward_title_text}".lower()
                        )
                        keyword_found = any(
                            str(keyword).lower() in normalized_reward
                            for keyword in cfg.get("reward_keywords", ())
                        )
                        rx1, ry1, rx2, ry2 = (int(value) for value in reward_roi)
                        before = action_frame[ry1:ry2, rx1:rx2]
                        after = reward_frame[ry1:ry2, rx1:rx2]
                        frame_delta = 0.0
                        if before.shape == after.shape and before.size:
                            frame_delta = float(np.mean(cv2.absdiff(
                                cv2.cvtColor(before, cv2.COLOR_BGR2GRAY),
                                cv2.cvtColor(after, cv2.COLOR_BGR2GRAY),
                            )))
                        reward_confirmed = (
                            keyword_found
                            and frame_delta >= float(cfg.get("min_reward_frame_delta", 8.0))
                        )
                        if reward_confirmed:
                            confirmed += 1
                            self.game_logger.info("World bounty reward confirmed (%d/%d).", confirmed, remaining)
                            self._obs_event(
                                "world_bounty_reward",
                                game=game_label,
                                hotspot=hotspot,
                                confirmed=confirmed,
                            )
                        else:
                            self.game_logger.warning(
                                "Reward was not confirmed (keyword=%s, frame_delta=%.2f); not counting it.",
                                keyword_found,
                                frame_delta,
                            )
                            self._obs_capture(
                                "world_bounty_reward_unconfirmed",
                                image=reward_frame,
                                game=game_label,
                                hotspot=hotspot,
                            )
                        self.adb_tap(*context.CONFIG["action_coords"]["world_bounty_reward_dismiss"])
                        time.sleep(action_delay)
                        if not self.confirm_screen(
                            must_screen="world",
                            timeout=1.2,
                            where="world bounty: reward dismissed",
                        ):
                            route_failed = True
                            break

                if view_index < max_swipes and swipes:
                    swipe = swipes[view_index % len(swipes)]
                    self.adb_swipe(*swipe, duration_ms=context.CONFIG["timing"]["swipe_duration"])
                    time.sleep(float(cfg.get("swipe_delay", 1.2)))

            if route_failed:
                break

        if confirmed >= remaining:
            self._mark_daily_action_complete(
                game_label,
                "world_bounty_plunder",
                "Daily world bounty plunders confirmed",
                confirmed=confirmed,
                prior_counter=f"{counter[0]}/{counter[1]}" if counter else "unknown",
                hotspots=visited_hotspots,
            )

        outcome = "success" if confirmed else ("failed" if route_failed else "unavailable")
        message = (
            f"Confirmed {confirmed} world bounty reward(s)"
            if confirmed
            else "No confirmed world bounty reward found on hotspot route"
        )
        self._record_action(
            game_label,
            "world_bounty_plunder",
            outcome,
            message,
            confirmed=confirmed,
            candidates_checked=candidate_taps,
            views_scanned=total_views,
            hotspots=visited_hotspots,
            route_failed=route_failed,
            zoom=bool(cfg.get("zoom_enabled", False)),
        )
        return confirmed
    except Exception as exc:
        self.game_logger.error("World bounty route failed: %s", exc, exc_info=True)
        self._obs_capture("world_bounty_exception", game=game_label, error=str(exc))
        self._record_action(game_label, "world_bounty_plunder", "failed", str(exc))
        return confirmed
    finally:
        self.ensure_base_view()
