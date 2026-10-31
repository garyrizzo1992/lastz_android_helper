"""Build on macOS/Linux/Windows without installing or creating signing keys."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BUILD = ROOT / "runtime/helper-build"


def run(*args, **kwargs):
    subprocess.run([str(arg) for arg in args], check=True, **kwargs)


def java_tool(name):
    home = os.environ.get("JAVA_HOME")
    path = Path(home) / "bin" / (name + (".exe" if os.name == "nt" else "")) if home else shutil.which(name)
    if not path or not Path(path).is_file():
        raise SystemExit("Java 17 is required; set JAVA_HOME")
    return path


def build(apk=False, keystore=None):
    sdk = Path(os.environ.get("LASTZ_ANDROID_SDK", os.environ.get("ANDROID_HOME", str(Path.home() / "Library/Android/sdk"))))
    platform = sdk / "platforms/android-35/android.jar"
    tools = sdk / "build-tools/35.0.1"
    if not platform.is_file() or not (tools / "lib/d8.jar").is_file():
        raise SystemExit("Set LASTZ_ANDROID_SDK to Android platform 35 / build-tools 35.0.1")
    if apk and (not keystore or not Path(keystore).is_file()):
        raise SystemExit("APK signing requires the existing --keystore; no replacement key is generated")
    if apk and not os.environ.get("LASTZ_KEYSTORE_PASSWORD"):
        raise SystemExit("Set LASTZ_KEYSTORE_PASSWORD for the existing key")
    run(sys.executable, HERE / "audit_input_positions.py")
    for name, digest in [("injector.dat", "a76888ee76394b5909d4b3cbb81761ead1f87e14178e6ed3252e60755f664240"), ("injector-arm64.dat", "3133d798ef48aa10fec06594ad9b69d80220038ebdaa4775c836741bfc3bf5a4")]:
        target = HERE / "assets" / name
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise SystemExit("Missing or mismatched pinned injector: run fetch_assets.py")
    agent = [HERE / "assets/java-bridge-prefix.js"] + [HERE / name for name in ["gesture-geometry.js", "scene-geometry.js", "unity-ui.js", "input-agent-tail.js"]]
    (HERE / "assets/input-agent.js").write_text("".join(path.read_text(encoding="utf-8") for path in agent), encoding="utf-8")
    for name in ["FRIDA-LICENSE.txt", "FRIDA-JAVA-BRIDGE-LICENSE.txt"]:
        shutil.copyfile(HERE / name, HERE / "assets/licenses" / name)
    run(sys.executable, HERE / "package_history.py")
    BUILD.mkdir(parents=True, exist_ok=True)
    classes = Path(tempfile.mkdtemp(prefix="compile-classes-", dir=BUILD))
    sources = sorted((HERE / "src").rglob("*.java"))
    run(java_tool("javac"), "-encoding", "UTF-8", "-source", "8", "-target", "8", "-classpath", platform, "-d", classes, *sources)
    archive = BUILD / "compiled-classes.jar"
    run(java_tool("jar"), "cf", archive, "-C", classes, ".")
    dex = BUILD / "dex"
    dex.mkdir(exist_ok=True)
    run(java_tool("java"), "-cp", tools / "lib/d8.jar", "com.android.tools.r8.D8", "--lib", platform, "--min-api", "26", "--output", dex, archive)
    (BUILD / "latest-classes.txt").write_text(str(classes), encoding="utf-8")
    if not apk:
        print("Built", dex / "classes.dex")
        return classes
    suffix = ".exe" if os.name == "nt" else ""
    unsigned, aligned = BUILD / "unsigned.apk", BUILD / "aligned.apk"
    run(tools / ("aapt" + suffix), "package", "-f", "-A", HERE / "assets", "-M", HERE / "AndroidManifest.xml", "-I", platform, "-F", unsigned)
    with zipfile.ZipFile(unsigned, "a") as package:
        package.write(dex / "classes.dex", "classes.dex")
    run(tools / ("zipalign" + suffix), "-f", "4", unsigned, aligned)
    output = ROOT / "bin/last-z-helper.apk"
    output.parent.mkdir(exist_ok=True)
    signer = [java_tool("java"), "-jar", tools / "lib/apksigner.jar"]
    run(*signer, "sign", "--ks", keystore, "--ks-pass", "env:LASTZ_KEYSTORE_PASSWORD", "--out", output, aligned)
    run(*signer, "verify", "--verbose", "--print-certs", output)
    print("Built", output)
    return classes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", action="store_true", help="Package and sign using an existing key")
    parser.add_argument("--keystore", type=Path)
    options = parser.parse_args()
    build(options.apk, options.keystore)
