"""Freeze the exact full-orbit collision-space audit before execution."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
out = HERE / 'protocol.json'
assert not out.exists()
paths = [HERE / 'audit.py', HERE / 'sage_runtime_info.json',
         ROOT / 'n41_n131_fivepair_w9_w29_20261017' / 'circuit_n131_3p2.py',
         ROOT / 'n131_w23_sixpair_shared_circuit_20261017' / 'circuit.py',
         ROOT / 'n131_w18_allseed_fourpair_20261012' / 'fourpair_v2.py']
record = {
    'status': 'FROZEN_BEFORE_COLLISION_SPACE_AUDIT',
    'candidate_id': None,
    'curve_id': 'EC1N131Ckb1heb5f1998f20b',
    'input_law': 'all 28-bit canonical W29 source codes, both seed-pair endpoints, every Frobenius power 0..130',
    'wall_cap_seconds': 120,
    'rss_cap_bytes': 4294967296,
    'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths},
}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
