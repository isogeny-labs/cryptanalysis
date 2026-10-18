"""Freeze the sparse-code exception circuit before construction."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
root=here.parent
out=here/'sparse_build_protocol.json'
assert not out.exists()
design=root/'n41_n131_fivepair_w9_w29_20261017/circuit_n131_3p2.py'
field=root/'n131_w23_sixpair_shared_circuit_20261017/circuit.py'
sample=root/'n41_n131_pairroot_functional_20261018/n131_result.json'
paths=[here/'sparse_build.py',here/'sage_runtime_info.json',design,field,
       sample,here/'build_result.json']
record={'status':'FROZEN_BEFORE_N131_W29_SPARSE_EXCEPTION_BUILD',
        'candidate_id':None,'curve_id':'EC1N131Ckb1heb5f1998f20b',
        'sample':str(sample),'wall_cap_seconds':120,
        'rss_cap_bytes':4294967296,
        'sources':{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in paths}}
out.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
