"""Freeze the exact collision-aware public circuit build."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
out = HERE / 'build_protocol.json'
assert not out.exists()
control = ROOT / 'n41_n131_w29_rotation_alignment_20261017' / 'n131_aligned_control.json'
public = ROOT / 'n131_w23_sixpair_public_sat_20261017' / 'protocol.json'
collision = ROOT / 'n131_w29_folded_collision_20261018' / 'filter_result.json'
paths = [HERE / 'build.py', HERE / 'sage_runtime_info.json', control, public,
         collision,
         ROOT / 'n41_n131_fivepair_w9_w29_20261017' / 'circuit_n131_3p2.py',
         ROOT / 'n131_w23_sixpair_shared_circuit_20261017' / 'circuit.py',
         ROOT / 'n131_w18_allseed_fourpair_20261012' / 'fourpair_v2.py',
         ROOT / 'n131_w20_selector_elimination_v2_20261013' / 'selector.py']
record = {
    'status': 'FROZEN_BEFORE_N131_W29_COLLISION_EXACT_PUBLIC_BUILD',
    'candidate_id': None,
    'curve_id': 'EC1N131Ckb1heb5f1998f20b',
    'constructed_control': str(control),
    'public_point': str(public),
    'collision_table': str(collision),
    'wall_cap_seconds': 240,
    'rss_cap_bytes': 4294967296,
    'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths},
}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
