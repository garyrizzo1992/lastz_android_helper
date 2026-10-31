"""Fetch the pinned official ARM64 injector; never replace the emulator asset."""
import hashlib
import json
import lzma
from pathlib import Path
import urllib.request

VERSION = "17.24.3"
DIGEST = "0ef2d078a5519e79736fdff7f5c0a35074cb2a8245af5101d84d373a72255ded"
asset = f"frida-inject-{VERSION}-android-arm64.xz"
request = urllib.request.Request(
    f"https://api.github.com/repos/frida/frida/releases/tags/{VERSION}",
    headers={"User-Agent": "Last-Z-Helper-build"},
)
release = json.load(urllib.request.urlopen(request, timeout=30))
entry = next(a for a in release["assets"] if a["name"] == asset)
if entry.get("digest") != "sha256:" + DIGEST:
    raise SystemExit("Official release digest changed")
compressed = urllib.request.urlopen(entry["browser_download_url"], timeout=120).read()
if hashlib.sha256(compressed).hexdigest() != DIGEST:
    raise SystemExit("Download checksum mismatch")
binary = lzma.decompress(compressed)
if binary[:4] != b"\x7fELF" or int.from_bytes(binary[18:20], "little") != 183:
    raise SystemExit("Expected ARM64 ELF")
destination = Path(__file__).parent / "assets/injector-arm64.dat"
destination.write_bytes(binary)
print(f"ARM64 injector: {len(binary)} bytes, sha256 {hashlib.sha256(binary).hexdigest()}")
