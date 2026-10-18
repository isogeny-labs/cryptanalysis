"""Freeze a one-worker bounded search for the equivalent sparse equation."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
base = json.loads((here / 'query_protocol.json').read_text())
out = here / 'sparse_query_protocol.json'
assert not out.exists()
paths = [here / 'sparse_query.py', here / 'sparse_build_result.json',
         here / 'sparse_formula.xcnf', here / 'sage_runtime_info.json',
         Path(base['solver'])]
record = {
    'status': 'FROZEN_BEFORE_N131_W29_SPARSE_EXCEPTION_QUERY',
    'candidate_id': None,
    'curve_id': base['curve_id'],
    'input_law': 'all p,s in the 28-dimensional W29 product subspace with p,s,p+s nonzero; equation p^2+p*s+C*H*s^2=1',
    'solver': base['solver'],
    'worker_count': 1,
    'solver_cap_seconds': base['solver_cap_seconds'],
    'parent_wall_cap_seconds': base['parent_wall_cap_seconds'],
    'rss_cap_bytes': base['rss_cap_bytes'],
    'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths},
}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
