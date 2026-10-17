"""Freeze the unpinned N41 residual panel for normalized recurrence replay."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
ROOT=D.parent
OLD=ROOT/'n41_n131_linearized_quadratic_algebra_20261014'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


paths=[OLD/'n41_gate.py',OLD/'result.json',OLD/'audit_result.json',
       ROOT/'n41_w8_fixed_sum_table_20261009'/'geometry.json',
       ROOT/'n41_w8_two_code_affine_span_20261013'/'target_result_v2.json']
record={'schema':1,'producer_sha256':sha(D/'n41_control.py'),
        'sources':{str(path):sha(path) for path in paths},
        'panel_count':65,'left_roots_per_panel':80,
        'worker_count':1,'wall_cap_s':120,'rss_cap_bytes':4*1024**3}
(D/'n41_protocol.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps({'protocol_sha256':sha(D/'n41_protocol.json')}))
