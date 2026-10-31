"""Recover the pinned injector from an existing helper APK without network access."""
from pathlib import Path
import argparse,hashlib,zipfile
p=argparse.ArgumentParser();p.add_argument('--apk',required=True);a=p.parse_args()
with zipfile.ZipFile(a.apk)as z:data=z.read('assets/injector.dat')
expected='a76888ee76394b5909d4b3cbb81761ead1f87e14178e6ed3252e60755f664240'
if hashlib.sha256(data).hexdigest()!=expected:raise SystemExit('Unexpected injector; no files written')
target=Path(__file__).resolve().parent/'assets/injector.dat';target.write_bytes(data)
print('Pinned injector recovered:',target)
