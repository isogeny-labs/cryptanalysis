"""Freeze the ordered staged-S3 N41 public query and promotion gate."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
base=here.parent/'n41_w9_final_pair_quadratics_20261018'
old=json.loads((base/'query_protocol.json').read_text())
stage=json.loads((here/'build_result.json').read_text())
ordered=json.loads((here/'ordered_build_result.json').read_text())
probe=json.loads((here/'ordered_probe_result.json').read_text())
assert probe['status']=='COMPLETED_FROZEN_ABBA_PROBE'
arms=probe['arm_results']
assert all(row['status']=='INDETERMINATE_CONFLICT_CAP' and
           row['monitor_error'] is None for row in arms)
for i,j in ((1,0),(2,3)):
    assert arms[i]['reported_decisions'] <= .9*arms[j]['reported_decisions']
    assert arms[i]['wall_seconds'] <= .75*arms[j]['wall_seconds']
out=here/'query_protocol.json'
assert not out.exists()
paths=[here/'query.py',here/'ordered_build_result.json',
       here/'ordered_formula.xcnf',here/'build_result.json',
       here/'audit_result.json',here/'ordered_probe_result.json',
       here/'sage_runtime_info.json',Path(old['solver'])]
record={'status':'FROZEN_BEFORE_N41_ORDERED_STAGED_S3_PUBLIC_QUERY',
        'candidate_id':None,'curve_id':old['curve_id'],
        'public_point':old['public_point'],
        'solver':old['solver'],'worker_count':1,
        'solver_cap_seconds':590,'parent_wall_cap_seconds':600,
        'rss_cap_bytes':4294967296,
        'charged_build_seconds':stage['wall_seconds']+ordered['wall_seconds'],
        'sources':{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in paths}}
out.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
