"""Ordering regressions for lazy startup and the mandatory native compatibility gate.

These inspect source contracts; they do not replace the device no-work/unsupported-
surface checks. No ADB, injector, game process, compiler or build is invoked.
"""
from pathlib import Path
import re
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "src/dev/codex/lastzhelper"


def source(name):
    return (SOURCE / name).read_text(encoding="utf-8")


class DeferredInstrumentationTests(unittest.TestCase):
    def test_deferral_is_explicit_for_only_the_two_audited_features(self):
        self.assertIn("default boolean deferInstrumentationUntilAction(){return false;}", source("MaintenanceFeature.java"))
        opted_in = {
            path.name for path in SOURCE.glob("*.java")
            if "boolean deferInstrumentationUntilAction(){return true;}" in path.read_text(encoding="utf-8")
        }
        self.assertEqual(opted_in, {"WantedFeature.java", "TrainingCollectionFeature.java"})

    def test_controller_preserves_uid_and_unresolved_preflight_before_eager_start(self):
        text = source("MaintenanceController.java")
        condition = "if(feature.requiresInstrumentation()&&!feature.deferInstrumentationUntilAction()&&!context.store.unresolved(context.uid,feature.id()))legacy.input.foreground();"
        self.assertIn(condition, text)
        self.assertLess(text.index('if(options.has("expectedAccountUid")'), text.index(condition))

    def test_first_hello_must_be_successful_and_explicitly_compatible_before_send(self):
        text = source("DeviceInput.java")
        self.assertIn("boolean sessionCompatible=false;", text)
        start = text.index("if(session==null){")
        success = text.index("requireSuccess(inspection);", start)
        compatible = text.index('if(!inspection.optBoolean("compatible",false))throw', success)
        confirmed = text.index("sessionCompatible=true;", compatible)
        mandatory_gate = text.index('if(!sessionCompatible)throw', confirmed)
        requested_send = text.index("send(args);", mandatory_gate)
        self.assertLess(success, compatible)
        self.assertLess(compatible, confirmed)
        self.assertLess(confirmed, mandatory_gate)
        self.assertLess(mandatory_gate, requested_send)
        self.assertEqual(text.count("sessionCompatible=true;"), 1)

    def test_caught_failed_hello_cannot_bypass_gate_on_existing_session(self):
        text = source("DeviceInput.java")
        # The guard must be OUTSIDE the new-session block: a caller can catch an
        # unsupported inspection and call action() again during cleanup/retry.
        self.assertRegex(text, r"sessionCompatible=true;\s*}\s*if\(!sessionCompatible\)throw")
        # Only owned shutdown may use send directly without the action guard.
        sends = re.findall(r"(?<![\w.])send\((\w+)\);", text)
        self.assertEqual(sends, ["args", "bye"])
        self.assertIn('put("action","shutdown")', text)

    def test_training_surface_check_occurs_after_ready_and_before_journal(self):
        text = source("TrainingCollectionFeature.java")
        confirmed_ready = text.index('if(!target.getString("decision").equals("READY_TO_COLLECT"))continue;')
        surface = text.index("context.input.foreground();")
        barrier = text.index("pending=context.begin(")
        action = text.index('put("action","training-collect")')
        self.assertLess(confirmed_ready, surface)
        self.assertLess(surface, barrier)
        self.assertLess(barrier, action)
        self.assertEqual(text.count("context.input.foreground();"), 1)

    def test_memory_only_capability_still_rejects_native_requests(self):
        context = source("MaintenanceContext.java")
        self.assertIn('!activeFeature.requiresInstrumentation())throw new IOException("Memory-only feature cannot start instrumentation")', context)
        device = source("DeviceInput.java")
        self.assertLess(device.index("if(requestGuard!=null)requestGuard.verify(args);"), device.index("if(session==null){"))


if __name__ == "__main__":
    unittest.main()
