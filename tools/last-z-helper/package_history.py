"""Seed only a first installation; existing on-device history is never replaced."""
from pathlib import Path
import json
here=Path(__file__).resolve().parent
source=here.parents[1]/'runtime/bounty-investigation/world-shares.json'
original=json.loads(source.read_text()) if source.exists() else {}
entries={}
for key,value in original.items():
    kind=value.get('kind','bounty')
    identity=str(value.get('id',value.get('uuid',key)))
    entries[(key if ':'in key else kind+':'+identity)]=value
(here/'assets/initial-shares.json').write_text(json.dumps(entries,indent=2))
