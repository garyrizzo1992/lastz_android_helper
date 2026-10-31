"""Fetch both official pinned Frida injectors and verify decompressed binaries."""
import hashlib
import lzma
from pathlib import Path
import urllib.request

VERSION = "17.24.3"
ASSETS = {
    "x86_64": ("injector.dat", 62, "a76888ee76394b5909d4b3cbb81761ead1f87e14178e6ed3252e60755f664240"),
    "arm64": ("injector-arm64.dat", 183, "3133d798ef48aa10fec06594ad9b69d80220038ebdaa4775c836741bfc3bf5a4"),
}


def main():
    folder = Path(__file__).resolve().parent / "assets"
    folder.mkdir(exist_ok=True)
    for architecture, (name, machine, digest) in ASSETS.items():
        target = folder / name
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise SystemExit(f"Existing {name} failed its pinned checksum; no replacement made")
            print(f"Verified {name}")
            continue
        url = f"https://github.com/frida/frida/releases/download/{VERSION}/frida-inject-{VERSION}-android-{architecture}.xz"
        request = urllib.request.Request(url, headers={"User-Agent": "Last-Z-Helper-build"})
        with urllib.request.urlopen(request, timeout=120) as response:
            data = lzma.decompress(response.read())
        if data[:4] != b"\x7fELF" or int.from_bytes(data[18:20], "little") != machine or hashlib.sha256(data).hexdigest() != digest:
            raise SystemExit(f"Pinned {name} validation failed; no file written")
        temporary = target.with_suffix(".download")
        temporary.write_bytes(data)
        temporary.replace(target)
        print(f"Verified and installed {name}")


if __name__ == "__main__":
    main()
