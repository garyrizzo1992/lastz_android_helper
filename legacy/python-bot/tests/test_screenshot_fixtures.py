"""Sanitized real-screen regression coverage; no ADB or OCR binary required."""
import unittest
from pathlib import Path
import cv2
import numpy as np
import main_scrcpy as app

FIXTURES = Path(__file__).parent / "fixtures"


class ScreenshotFixtureTests(unittest.TestCase):
    def frame(self, name):
        frame = cv2.imread(str(FIXTURES / name))
        self.assertIsNotNone(frame)
        self.assertFalse(np.any(frame[:250]))  # identifiers/currency are removed
        return frame

    def test_latest_tier_on_shifted_real_carousel(self):
        frame = self.frame("training_shifted_viii.png")
        centers = app._visible_troop_card_centers(frame,(1690,1875),(150,370,585,805,1015))
        states = app._troop_tier_card_states(frame,centers,card_y=(1690,1875))
        highest = app._highest_visible_unlocked_troop_card(states)
        self.assertAlmostEqual(highest["center"][0],468,delta=10)
        self.assertTrue(highest["selected"])
        self.assertTrue(any(not state["unlocked"] and state["center"][0] > highest["center"][0] for state in states))

    def test_latest_tier_on_centered_real_carousel(self):
        frame = self.frame("training_viii.png")
        centers = app._visible_troop_card_centers(frame,(1690,1875),(150,370,585,805,1015))
        states = app._troop_tier_card_states(frame,centers,card_y=(1690,1875))
        highest = app._highest_visible_unlocked_troop_card(states)
        self.assertAlmostEqual(highest["center"][0],591,delta=10)
        self.assertTrue(highest["selected"])

    def test_real_blue_radar_march_button(self):
        frame = self.frame("radar_blue_march.png")
        points = app._locate_green_rect_buttons(frame,(250,1350,750,1750),min_width=250,max_width=520,min_height=65,max_height=180,hsv_lower=(90,70,70),hsv_upper=(130,255,255))
        self.assertEqual(len(points),1)
        self.assertAlmostEqual(points[0][0],500,delta=10)
        self.assertAlmostEqual(points[0][1],1585,delta=10)

    def test_real_four_builder_queue_skips_busy_rows(self):
        frame = self.frame("builders_mixed_rows.png")
        template = cv2.imread(str(app.PROJECT_ROOT/app.CONFIG["image_paths"]["builder_build"]),cv2.IMREAD_UNCHANGED)
        x,y,score = app._locate_available_builder_button(frame,template)
        self.assertEqual((x,y),(775,1193))
        self.assertLess(score,.02)

    def test_real_builder_count_measures_only_free_workers(self):
        from bot.construction import _available_builder_count
        frame=self.frame("builders_mixed_rows.png")
        template=cv2.imread(str(app.PROJECT_ROOT/app.CONFIG["image_paths"]["builder_build"]),cv2.IMREAD_UNCHANGED)
        self.assertEqual(_available_builder_count(frame,template),2)

    def test_shortage_title_is_inside_the_configured_ocr_roi(self):
        frame=self.frame("construction_shortage.png")
        _,y1,_,y2=app.CONFIG["construction_shortage_prompt_roi"]
        self.assertLessEqual(y1,300)
        self.assertGreaterEqual(y2,1850)
        self.assertTrue(np.any(frame[300:400]))

    def test_resource_replenishment_requires_both_title_and_button_templates(self):
        from bot.construction import _construction_shortage_controls
        frame=self.frame("construction_shortage.png")
        templates={name:cv2.imread(str(app.PROJECT_ROOT/app.CONFIG["image_paths"][name]))
                   for name in ("construction_get_more_title","construction_replenish_all")}
        point=_construction_shortage_controls(frame,templates)
        self.assertIsNotNone(point)
        self.assertAlmostEqual(point[0],542,delta=10)
        frame[250:450]=0
        self.assertIsNone(_construction_shortage_controls(frame,templates))

    def test_real_inventory_warning_is_not_safe_to_confirm(self):
        frame=self.frame("replenishment_insufficient.png")
        template=cv2.imread(str(app.PROJECT_ROOT/app.CONFIG["image_paths"]["construction_replenish_insufficient"]))
        self.assertTrue(app._template_match_centers(frame,template,(80,500,1000,800),threshold=.9,max_matches=1))

    def test_short_lived_unit_cap_toast_blocks_training(self):
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        from bot.detection import DetectionMixin
        frame = self.frame("training_unit_cap_toast.png")
        bot = SimpleNamespace(game_logger=MagicMock())
        self.assertTrue(DetectionMixin._troop_unit_cap_reached(bot, frame))
        frame[620:850] = 0
        template = cv2.imread(str(app.PROJECT_ROOT / app.CONFIG["image_paths"]["troop_unit_cap_toast"]))
        self.assertFalse(app._template_match_centers(frame, template, (200,620,900,850), threshold=.9, max_matches=1))

    def test_real_shield_icons_distinguish_durations(self):
        from types import SimpleNamespace
        from bot.shield_ui import BuffShieldUI
        frame = self.frame("shield_buff_info.png")
        templates = {name:cv2.imread(str(app.PROJECT_ROOT/path))
                     for name,path in app.CONFIG["image_paths"].items() if name.startswith("shield_")}
        bot = SimpleNamespace(templates=templates)
        ui = BuffShieldUI(bot,app.CONFIG["shield_activation"])
        # Pixel matching is real; only the OCR binary call is replaced.
        from unittest.mock import patch
        with patch.object(app,"_ocr_frame_text",return_value="Owned: 1"):
            count, roi24 = ui.row(frame,24)
            _, roi8 = ui.row(frame,8)
        self.assertEqual(count,1)
        self.assertEqual(ui.use_target(frame,roi24),(837,1500))
        self.assertEqual(ui.use_target(frame,roi8),(837,1286))
        self.assertNotEqual(roi24,roi8)

    def test_purchase_and_use_is_not_plain_use_fallback(self):
        from types import SimpleNamespace
        from bot.shield_ui import BuffShieldUI, ShieldUIError
        frame=self.frame("shield_buff_info.png")
        template=cv2.imread(str(app.PROJECT_ROOT/app.CONFIG["image_paths"]["shield_use_button"]))
        ui=BuffShieldUI(SimpleNamespace(templates={"shield_use_button":template}),app.CONFIG["shield_activation"])
        with self.assertRaises(ShieldUIError):
            ui.use_target(frame,(700,1630,975,1800))

    def test_real_shield_panel_identity_does_not_depend_on_outlined_text_ocr(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from bot.shield_ui import BuffShieldUI
        frame=self.frame("shield_buff_info.png")
        template=cv2.imread(str(app.PROJECT_ROOT/app.CONFIG["image_paths"]["shield_panel_identity"]))
        ui=BuffShieldUI(SimpleNamespace(templates={"shield_panel_identity":template}),app.CONFIG["shield_activation"])
        with patch.object(app,"_ocr_frame_text",return_value="Peace Shiele!"):
            self.assertTrue(ui.is_shield_panel(frame))

    def test_live_replacement_dialog_requires_both_warning_and_confirm_button(self):
        from types import SimpleNamespace
        from bot.shield_ui import BuffShieldUI
        frame=self.frame("shield_replacement_prompt.png")
        templates={name:cv2.imread(str(app.PROJECT_ROOT/app.CONFIG['image_paths'][name]))
                   for name in ('shield_replacement_prompt','shield_replacement_confirm')}
        ui=BuffShieldUI(SimpleNamespace(templates=templates),app.CONFIG['shield_activation'])
        self.assertEqual(ui.replacement_confirm_target(frame),(330,1265))
        missing_warning=frame.copy();missing_warning[940:1100]=0
        self.assertIsNone(ui.replacement_confirm_target(missing_warning))
        missing_button=frame.copy();missing_button[1200:1330]=0
        self.assertIsNone(ui.replacement_confirm_target(missing_button))
