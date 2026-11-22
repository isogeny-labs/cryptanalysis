"""Freeze independent direct curve-sum check for every selected sign chart."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
p=json.loads((D/'panel.json').read_text())
r=json.loads((D/'result.json').read_text())
a=json.loads((D/'audit_result.json').read_text())
assert p['status']=='FROZEN_N131_AFFINE_FOUR_CODE_PANEL'
assert r['status']=='COMPLETE_N131_AFFINE_RR_RANK_SCREEN'
assert a['status']=='PASS_INDEPENDENT_N131_AFFINE_RR_REPLAY'
record={'schema':1,'worker_count':1,'wall_cap_s':600,'rss_cap_bytes':4*1024**3,
        'panel_sha256':sha(D/'panel.json'),
        'rank_result_sha256':sha(D/'result.json'),
        'determinant_audit_sha256':sha(D/'audit_result.json'),
        'group_audit_source_sha256':sha(D/'group_audit_sage.py')}
with (D/'group_protocol.json').open('x') as out:
    json.dump(record,out,sort_keys=True,indent=2);out.write('\n')
print(sha(D/'group_protocol.json'))
