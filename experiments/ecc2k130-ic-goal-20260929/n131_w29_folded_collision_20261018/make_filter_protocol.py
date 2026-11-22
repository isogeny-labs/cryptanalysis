"""Freeze valid-source collision filtering before its first execution."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
out = HERE / 'filter_protocol.json'
assert not out.exists()
paths = [HERE / 'filter_valid.py', HERE / 'audit_result.json',
         HERE / 'sage_runtime_info.json',
         ROOT / 'n41_n131_fivepair_w9_w29_20261017' / 'circuit_n131_3p2.py',
         ROOT / 'n131_w23_sixpair_shared_circuit_20261017' / 'circuit.py',
         ROOT / 'n41_n131_w29_rotation_alignment_20261017' / 'n131_aligned_control.json']
record = {
    'status': 'FROZEN_BEFORE_N131_W29_VALID_COLLISION_FILTER',
    'candidate_id': None,
    'curve_id': 'EC1N131Ckb1heb5f1998f20b',
    'input_law': 'all nontrivial full-domain affine Frobenius collision spaces, exact source-validity filter',
    'wall_cap_seconds': 120,
    'rss_cap_bytes': 4294967296,
    'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths},
}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
