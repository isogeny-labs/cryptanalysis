"""Freeze exceptional-sum audit inputs and resource limits."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
root=here.parent
out=here/'audit_protocol.json'
assert not out.exists()
n41=root/'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'
n131=root/'n41_n131_pairroot_functional_20261018/n131_result.json'
paths=[here/'audit_sage.py',here/'sage_runtime_info.json',n41,n131]
record={'status':'FROZEN_BEFORE_FIRST_TWO_PAIR_EXCEPTION_AUDIT',
        'candidate_id':None,'n41_states':str(n41),'n131_roots':str(n131),
        'n131_curve_id':'EC1N131Ckb1heb5f1998f20b',
        'wall_cap_seconds':120,'rss_cap_bytes':4294967296,
        'sources':{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in paths}}
out.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
