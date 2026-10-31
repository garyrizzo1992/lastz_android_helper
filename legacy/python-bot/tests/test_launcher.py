"""Exercise startup sequencing without touching a real checkout or phone."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash") if os.name != "nt" else r"C:\Program Files\Git\bin\bash.exe"


@unittest.skipUnless(BASH and Path(BASH).exists(), "Bash required")
class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lastz-launcher-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("scripts", ".venv/bin", "bin", ".git", "data"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "scripts/run_bot.sh", self.root / "scripts/run_bot.sh")
        (self.root / "requirements-runtime.txt").write_text("example==1\n")
        self.stub(self.root / ".venv/bin/python", 'echo "python $*"\nif [[ "$*" == *"pip install"* ]]; then exit "${FAIL_PIP:-0}"; fi\n')
        self.stub(self.root / "bin/git", 'echo "git $*"\nif [[ "$*" == *fetch* ]]; then exit "${FAIL_FETCH:-0}"; fi\n')
        self.stub(self.root / 'bin/shasum', 'echo fixture-hash\n')
        self.env = dict(os.environ)
        for key in list(self.env):
            if key.startswith("LASTZ_"):
                del self.env[key]
        self.env["LASTZ_DATA_DIR"] = self.root.joinpath("data").as_posix()

    def stub(self, path, body):
        path.write_text("#!/usr/bin/env bash\n" + body, newline="\n")
        path.chmod(0o755)

    def run_launcher(self, *args):
        # Let Bash add the fixture executable path, including on Git for Windows.
        return subprocess.run(
            [BASH, "-c", 'fixture="$1"; if command -v cygpath >/dev/null; then fixture="$(cygpath -u "$fixture")"; fi; export PATH="$fixture/bin:$PATH"; shift; exec bash "$@"',
             "test", self.root.as_posix(),
             self.root.joinpath("scripts/run_bot.sh").as_posix(), *args],
            env=self.env, capture_output=True, text=True, timeout=15,
        )

    def test_preflight_skips_sync_and_deployment_lock(self):
        (self.root / "data/deploy.lock").mkdir()
        result = self.run_launcher("--preflight")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--preflight", result.stdout)
        self.assertNotIn("git ", result.stdout)
        self.assertNotIn("pip ", result.stdout)

    def test_deployment_lock_blocks_startup(self):
        (self.root / "data/deploy.lock").mkdir()
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("git ", result.stdout)

    def test_fetch_failure_prevents_reset_and_bot_start(self):
        self.env["FAIL_FETCH"] = "7"
        result = self.run_launcher()
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertNotIn("reset --hard", result.stdout)
        self.assertNotIn("main_scrcpy.py", result.stdout)

    def test_dependency_failure_prevents_bot_start(self):
        self.env["LASTZ_GIT_SYNC"] = "false"
        self.env["FAIL_PIP"] = "8"
        result = self.run_launcher()
        self.assertEqual(result.returncode, 8, result.stderr)
        self.assertNotIn("main_scrcpy.py", result.stdout)
        self.assertFalse((self.root / ".venv/lastz-requirements.sha256").exists())

    def test_retry_mode_fetch_failure_cannot_reset_or_start(self):
        self.env.update(LASTZ_RETRY_ON_FAILURE='true',FAIL_FETCH='7')
        self.stub(self.root/'bin/sleep','exit 93\n')
        result=self.run_launcher()
        self.assertEqual(result.returncode,93,result.stderr)
        self.assertIn('retrying in 60s',result.stderr)
        self.assertNotIn('reset --hard',result.stdout)
        self.assertNotIn('main_scrcpy.py',result.stdout)

    def test_retry_mode_dependency_failure_cannot_stamp_or_start(self):
        self.env.update(LASTZ_RETRY_ON_FAILURE='true',LASTZ_GIT_SYNC='false',FAIL_PIP='8')
        self.stub(self.root/'bin/sleep','exit 93\n')
        result=self.run_launcher()
        self.assertEqual(result.returncode,93,result.stderr)
        self.assertNotIn('main_scrcpy.py',result.stdout)
        self.assertFalse((self.root/'.venv/lastz-requirements.sha256').exists())


if __name__ == "__main__":
    unittest.main()
