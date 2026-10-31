"""Portable equivalent of validate.ps1. All checks fail closed."""
import hashlib
import os
from pathlib import Path
import re
import sys
import urllib.request
from build import BUILD, HERE, ROOT, build, java_tool, run


def main():
    classes = build()
    tests = BUILD / "validation-tests"
    tests.mkdir(exist_ok=True)
    # Share the suite inventory with Windows so the two entry points stay aligned.
    windows = (HERE / "validate.ps1").read_text(encoding="utf-8")
    names = list(dict.fromkeys(re.findall(r'"\$PSScriptRoot/tests/([A-Za-z0-9]+Tests)\.java"', windows)))
    for name in [name for name in names if name not in ("BoomerReceiptPermissionsTests", "MaintenanceRegistryTests")]:
        run(java_tool("javac"), "-encoding", "UTF-8", "-cp", classes, "-d", tests, HERE / "tests" / (name + ".java"))
        run(java_tool("java"), "-cp", os.pathsep.join(map(str, [tests, classes])), "dev.codex.lastzhelper." + name)
    run("node", "--check", HERE / "assets/input-agent.js")
    for name in sorted((HERE / "tests").glob("*.test.js")):
        run("node", name)
    run(sys.executable, "-m", "unittest", "discover", "-s", HERE / "tests", "-p", "test_*.py")
    jar = BUILD / "json-20240303.jar"
    digest = "3cf6cd6892e32e2b4c1c39e0f52f5248a2f5b37646fdfbb79a66b46b618414ed"
    if not jar.exists():
        data = urllib.request.urlopen("https://repo.maven.apache.org/maven2/org/json/json/20240303/json-20240303.jar", timeout=60).read()
        if hashlib.sha256(data).hexdigest() != digest:
            raise SystemExit("Pinned JSON dependency mismatch")
        jar.write_bytes(data)
    if hashlib.sha256(jar.read_bytes()).hexdigest() != digest:
        raise SystemExit("Pinned JSON dependency mismatch")
    jvm = BUILD / "recovery-jvm"
    jvm.mkdir(exist_ok=True)
    inventory = (HERE / "tests/validate_recovery_storage.ps1").read_text(encoding="utf-8")
    files = re.search(r"\$files=@\((.*?)\) \|", inventory).group(1)
    source_names = re.findall(r"'([A-Za-z]+)'", files)
    sources = [HERE / "src/dev/codex/lastzhelper" / (name + ".java") for name in source_names]
    sources += sorted((HERE / "tests/jvm").glob("*.java"))
    run(java_tool("javac"), "-encoding", "UTF-8", "-cp", jar, "-d", jvm, *sources)
    for name in re.findall(r"dev\.codex\.lastzhelper\.([A-Za-z]+Tests)", inventory):
        run(java_tool("java"), "-cp", os.pathsep.join(map(str, [jvm, jar])), "dev.codex.lastzhelper." + name)
    permission_classes = BUILD / "receipt-permission-tests"
    permission_classes.mkdir(exist_ok=True)
    permission_cp = os.pathsep.join(map(str, [classes, jar]))
    for name in ("BoomerReceiptPermissionsTests", "MaintenanceRegistryTests"):
        run(java_tool("javac"), "-encoding", "UTF-8", "-cp", permission_cp, "-d", permission_classes, HERE / "tests" / (name + ".java"))
        run(java_tool("java"), "-cp", os.pathsep.join(map(str, [permission_classes, classes, jar])), "dev.codex.lastzhelper." + name)
    print("All portable validation suites passed")


if __name__ == "__main__":
    main()
