"""Portable rendering checks; launchd behaviour still requires macOS."""
import plistlib
import shlex
import unittest
from pathlib import Path

try:
    import jinja2
    import yaml
except ImportError:
    jinja2 = None

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(jinja2 is None, "Install Jinja2 and PyYAML for deployment checks")
class DeploymentTemplates(unittest.TestCase):
    def test_plists_render_with_paths_containing_spaces_and_xml_characters(self):
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(ROOT / "ansible" / "templates"),
            undefined=jinja2.StrictUndefined,
        )
        env.filters["quote"] = shlex.quote
        variables = yaml.safe_load((ROOT / "ansible" / "vars.yaml").read_text())
        variables["lastz_home"] = "/Users/Test & User"
        def render(value):
            if isinstance(value, dict):
                return {k: render(v) for k, v in value.items()}
            return env.from_string(value).render(**variables) if isinstance(value, str) else value
        for _ in range(5):
            variables = {key: render(value) for key, value in variables.items()}
        for name in ("com.garyrizzo.lastz.plist.j2", "logrotate.plist.j2"):
            result = plistlib.loads(env.get_template(name).render(**variables).encode())
            self.assertTrue(result["RunAtLoad"])
            self.assertIn("/Users/Test & User", str(result))
        agent = plistlib.loads(env.get_template("com.garyrizzo.lastz.plist.j2").render(**variables).encode())
        self.assertFalse(agent["KeepAlive"]["SuccessfulExit"])
        self.assertEqual(agent["ThrottleInterval"], 60)
        self.assertNotIn("/Documents/lastz", agent["StandardOutPath"])

    def test_preflight_is_an_ordinary_task(self):
        play = yaml.safe_load((ROOT / "ansible" / "playbook.yaml").read_text())[0]
        nested = [t for task in play["tasks"] for t in task.get("block", [])]
        preflight = next(t for t in nested if "preflight" in t["name"].lower())
        self.assertFalse(preflight["failed_when"])
        self.assertIn("--preflight", preflight["ansible.builtin.command"]["argv"])


if __name__ == "__main__":
    unittest.main()
