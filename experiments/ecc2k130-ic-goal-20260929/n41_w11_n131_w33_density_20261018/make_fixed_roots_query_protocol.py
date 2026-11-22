"""Freeze the fixed-pair-output control before solver launch."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ref = json.loads((HERE / 'shared_root_query_protocol.json').read_text())
out = HERE / 'fixed_roots_query_protocol.json'
assert not out.exists()
paths = [HERE / 'run_fixed_roots_query.py',
         HERE / 'fixed_roots_build_result.json',
         HERE / 'shared_root_fixed_outputs_formula.xcnf',
         HERE / 'shared_root_query_result.json',
         HERE / 'sage_runtime_info.json', Path(ref['solver'])]
record = {'status': 'FROZEN_BEFORE_N41_W11_FIXED_PAIR_OUTPUT_QUERY',
          'candidate_id': None, 'curve_id': ref['curve_id'],
          'input_law': 'same frozen public N41 point; verified source codes and pair outputs fixed; S3 middles free',
          'solver': ref['solver'], 'worker_count': 1,
          'solver_cap_seconds': 55,
          'parent_wall_cap_seconds': 60,
          'rss_cap_bytes': 4294967296,
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
