"""Freeze the staged S3 N41 circuit before construction."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
base=here.parent/'n41_w9_final_pair_quadratics_20261018'
old=json.loads((base/'build_protocol.json').read_text())
out=here/'build_protocol.json'
assert not out.exists()
paths=[here/'build.py',here/'audit_result.json',here/'sage_runtime_info.json',
       Path(old['states']),Path(old['fixture']),Path(old['panel']),
       base/'build_result.json']
record={'status':'FROZEN_BEFORE_N41_STAGED_S3_BUILD',
        'candidate_id':None,'curve_id':old['curve_id'],
        'states':old['states'],'fixture':old['fixture'],'panel':old['panel'],
        'wall_cap_seconds':300,'rss_cap_bytes':4294967296,
        'sources':{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in paths}}
out.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
