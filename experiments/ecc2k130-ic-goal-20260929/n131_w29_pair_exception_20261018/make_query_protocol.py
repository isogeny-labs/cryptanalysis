"""Freeze a one-worker bounded full-W29 exception search."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
base=here.parent/'n41_w9_final_pair_quadratics_20261018'
old=json.loads((base/'probe_protocol.json').read_text())
solver=Path(old['solver'])
out=here/'query_protocol.json'
assert not out.exists()
paths=[here/'query.py',here/'build_result.json',here/'formula.xcnf',
       here/'sage_runtime_info.json',solver]
record={'status':'FROZEN_BEFORE_N131_W29_RECIPROCAL_EXCEPTION_QUERY',
        'candidate_id':None,'curve_id':'EC1N131Ckb1heb5f1998f20b',
        'input_law':'all 28-bit W29 product codes, distinct and nonzero; source-validity constraints omitted, so UNSAT proves the stronger product-subspace exclusion',
        'solver':str(solver),'worker_count':1,
        'solver_cap_seconds':590,'parent_wall_cap_seconds':600,
        'rss_cap_bytes':4294967296,
        'sources':{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in paths}}
out.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
