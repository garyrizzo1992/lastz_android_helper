import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("input_audit", Path(__file__).resolve().parents[1] / "audit_input_positions.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class InputAuditTests(unittest.TestCase):
    def test_retired_api(self):
        self.assertTrue(audit.violations("x.java", "input.nativeTap(x,y);"))

    def test_literal_endpoint(self):
        self.assertTrue(audit.violations("x.java", '.put("endY",650)'))

    def test_raw_action(self):
        self.assertTrue(audit.violations("x.java", '.put("action","swipe")'))

    def test_shell_tap(self):
        self.assertTrue(audit.violations("x.java", 'exec(5,"/system/bin/input","tap","1","2");'))

    def test_scaled_reference(self):
        self.assertTrue(audit.violations("x.js", "const scale=width/540;"))

    def test_non_ui_numbers(self):
        self.assertFalse(audit.violations("x.java", 'power=440000000; pause(960); .put("tileX",500); .put("action","map-tap")'))

    def test_maintenance_preflight_before_injection(self):
        gate = 'if(options.has("expectedAccountUid"))throw new IOException("Expected maintenance character is not active");'
        self.assertFalse(audit.maintenance_preflight_violations(gate + 'legacy.input.foreground();'))
        self.assertTrue(audit.maintenance_preflight_violations('legacy.input.foreground();' + gate))
        self.assertTrue(audit.maintenance_preflight_violations('legacy.input.foreground();'))

    def test_current_sources(self):
        self.assertEqual(audit.audit(), [])

    def test_group_share_rejects_plunder_navigation(self):
        self.assertTrue(audit.group_route_violations('tapControl("infoPanel/goBtn");waitMapTruck(truck);'))
        self.assertTrue(audit.group_route_violations('truckShare();attackTruck(truck);'))
        self.assertFalse(audit.group_route_violations('truckShare();validateShare(truck,true);'))


if __name__ == "__main__":
    unittest.main()
