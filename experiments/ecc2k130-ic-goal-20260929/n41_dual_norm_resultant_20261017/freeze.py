"""Freeze the six-code public resultant circuit before building it."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
ROOT=D.parent
SOURCE=ROOT/'n41_w8_quotient_first_pair_20261015'
NORM=ROOT/'n41_three_code_nested_norm_20261015'
WITNESS=ROOT/'n41_sixpair_shared_target_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


sources=[SOURCE/'circuit.py',SOURCE/'build.py',SOURCE/'norm_gate_early.py',
         NORM/'three_norm.py',
         ROOT/'n41_n131_sixpair_rr_root_span_20261016'/'SignDegree.lean',
         ROOT/'n41_w8_fixed_sum_table_20261009'/'geometry.json',
         WITNESS/'join_audit_result.json',WITNESS/'SixPairJoin.lean',
         ROOT/'n41_basis_aware_quartic_20261011'/'replay.py',
         ROOT/'n131_w20_selector_elimination_v2_20261013'/'selector.py']
record={'schema':1,'candidate_id':None,'curve_id':'EC1N41Ckb1h7d5e80d3c4d0',
        'public_raw_target':json.loads((WITNESS/'join_audit_result.json').read_text())['raw_target'],
        'first_slot_count':3,'second_slot_count':3,
        'producer_sha256':sha(D/'build.py'),
        'runner_sha256':sha(D/'run_build.py'),
        'sources':{str(path):sha(path) for path in sources},
        'worker_count':1,'wall_cap_s':120,'rss_cap_bytes':4*1024**3}
(D/'protocol.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps({'protocol_sha256':sha(D/'protocol.json')}))
