"""Freeze ordered staged-S3 versus quadratic reference solver arms."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
base=here.parent/'n41_w9_final_pair_quadratics_20261018'
old=json.loads((base/'probe_protocol.json').read_text())
out=here/'ordered_probe_protocol.json'
assert not out.exists()
formulas={'quadratic':base/'formula.xcnf',
          'ordered_staged':here/'ordered_formula.xcnf'}
paths=[here/'ordered_probe.py',here/'ordered_build_result.json',
       here/'build_result.json',here/'audit_result.json',
       here/'sage_runtime_info.json',base/'build_result.json',
       *formulas.values(),Path(old['solver'])]
record={'status':'FROZEN_BEFORE_N41_ORDERED_STAGED_S3_ABBA_PROBE',
        'candidate_id':None,'curve_id':old['curve_id'],
        'public_point':old['public_point'],
        'arms':['quadratic','ordered_staged','ordered_staged','quadratic'],
        'formulas':{key:str(value) for key,value in formulas.items()},
        'solver':old['solver'],'worker_count':1,
        'max_conflicts':20000,'solver_wall_cap_seconds':170,
        'parent_wall_cap_seconds':180,'rss_cap_bytes':4294967296,
        'promotion_gate':'All arms reach conflict cap with monitors passing; each ordered staged-S3 arm has at most 90 percent of adjacent quadratic decisions and at most 75 percent of adjacent wall; a verified SAT relation also passes.',
        'sources':{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in paths}}
out.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
