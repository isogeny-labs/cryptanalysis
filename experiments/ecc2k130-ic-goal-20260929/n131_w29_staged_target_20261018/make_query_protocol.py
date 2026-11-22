"""Freeze one public-point search with the exact collision-aware source."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
reference = json.loads((ROOT / 'n131_w29_pair_exception_20261018' /
                        'query_protocol.json').read_text())
solver = Path(reference['solver'])
out = HERE / 'query_protocol.json'
assert not out.exists()
paths = [HERE / 'query.py', HERE / 'build_result.json',
         HERE / 'formula.xcnf', HERE / 'input_wires.json',
         HERE / 'sage_runtime_info.json',
         ROOT / 'n131_w29_folded_collision_20261018' / 'verification_result.json',
         solver]
record = {
    'status': 'FROZEN_BEFORE_N131_COLLISION_EXACT_PUBLIC_QUERY',
    'candidate_id': None,
    'curve_id': 'EC1N131Ckb1heb5f1998f20b',
    'input_law': 'one frozen public N131 subgroup point; five valid W29 pair codes, ten distinct folded columns, aligned rotations 0,0,36,36,72',
    'solver': str(solver),
    'worker_count': 1,
    'solver_cap_seconds': 590,
    'parent_wall_cap_seconds': 600,
    'rss_cap_bytes': 4294967296,
    'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths},
}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
