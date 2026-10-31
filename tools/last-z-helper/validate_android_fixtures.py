"""Run filesystem/ownership fixtures on an explicitly selected rooted Android device.

Never opens games, reads game memory, injects an agent or changes app settings/history.
The detach fixture uses a short-lived owned shell with an injector-shaped filename.
"""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import uuid
from build import BUILD, HERE, build, java_tool, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--adb", default="adb")
    options = parser.parse_args()
    adb = [options.adb, "-s", options.serial]

    def root(command, timeout=60):
        result = subprocess.run(adb + ["shell", "su -c " + shlex.quote(command)],
                                capture_output=True, text=True, timeout=timeout, check=True)
        return result.stdout

    def idle():
        if root("id -u").strip() != "0":
            raise SystemExit("Root is required for the isolated fixtures")
        processes = root("ps -A -o ARGS")
        workers = ("dev.codex.lastzhelper.AutomationController", "dev.codex.lastzhelper.RotationController",
                   "dev.codex.lastzhelper.MaintenanceController", "dev.codex.lastzhelper.BoomerReconcileCheck",
                   "dev.codex.lastzhelper.LegacyLease", "dev.codex.lastzhelper.LegacyOwnershipSession",
                   "injector-arm64-17.24.3 -i", "injector-17.24.3 -i")
        if any(name in processes for name in workers):
            raise SystemExit("Another controller/input owner is running; fixtures refused")
        consent = root("if test -f /data/user/0/dev.codex.lastzhelper/files/bot-run-request.json; then cat /data/user/0/dev.codex.lastzhelper/files/bot-run-request.json; fi")
        if consent.strip() and json.loads(consent).get("requestedRunning"):
            raise SystemExit("A bot run is requested; stop it before running fixtures")

    idle()
    classes = build()
    sdk = Path(os.environ.get("LASTZ_ANDROID_SDK", os.environ.get("ANDROID_HOME", str(Path.home() / "Library/Android/sdk"))))
    fixture_classes = BUILD / ("android-fixtures-" + uuid.uuid4().hex)
    fixture_classes.mkdir()
    sources = [HERE / "tests/jvm/BoomerEngineTests.java", HERE / "tests/jvm/BoomerReconciliationTests.java",
               HERE / "tests/android/RecoveryDetachFixture.java"]
    run(java_tool("javac"), "-encoding", "UTF-8", "-source", "8", "-target", "8",
        "-cp", os.pathsep.join(map(str, [classes, sdk / "platforms/android-35/android.jar"])),
        "-d", fixture_classes, *sources)
    archive = fixture_classes / "fixtures.jar"
    run(java_tool("jar"), "cf", archive, "-C", fixture_classes, "dev")
    dex = fixture_classes / "dex"
    dex.mkdir()
    run(java_tool("java"), "-cp", sdk / "build-tools/35.0.1/lib/d8.jar", "com.android.tools.r8.D8",
        "--lib", sdk / "platforms/android-35/android.jar", "--classpath", BUILD / "compiled-classes.jar",
        "--min-api", "26", "--output", dex, archive)
    idle()
    token = uuid.uuid4().hex
    remote = "/data/local/tmp/lastz-offline-fixtures-" + token
    root("mkdir " + remote + " && chmod 700 " + remote)
    for source, name in [(BUILD / "dex/classes.dex", "source.dex"), (dex / "classes.dex", "fixtures.dex")]:
        staging = "/data/local/tmp/lastz-fixture-" + token + "-" + name
        run(*adb, "push", source, staging)
        root("mv " + staging + " " + remote + "/" + name + " && chmod 600 " + remote + "/" + name)
    results = []
    for name in ("BoomerEngineTests", "BoomerReconciliationTests", "RecoveryDetachFixture"):
        result = root("CLASSPATH=" + remote + "/source.dex:" + remote + "/fixtures.dex app_process /system/bin dev.codex.lastzhelper." + name + " " + remote)
        print(result.strip(), flush=True)
        results.append({"fixture": name, "output": result.strip()})
    report = BUILD / "android-fixtures-latest.json"
    report.write_text(json.dumps({"directory": remote, "gameInput": False, "gameMemory": False,
                                  "results": results}, indent=2), encoding="utf-8")
    print("Passed; private fixture report:", report)


if __name__ == "__main__":
    main()
