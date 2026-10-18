"""Freeze one worker on the widened N41 public-point circuit."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
reference = json.loads((ROOT / 'n131_w29_staged_target_20261018' /
                        'query_protocol.json').read_text())
solver = Path(reference['solver'])
out = HERE / 'n41_query_protocol.json'
assert not out.exists()
paths = [HERE / 'query_n41.py', HERE / 'n41_build_result.json',
         HERE / 'n41_formula.xcnf', HERE / 'n41_input_wires.json',
         HERE / 'sage_runtime_info.json', solver]
record = {'status': 'FROZEN_BEFORE_N41_W11_ORDINARY_PUBLIC_QUERY',
          'candidate_id': None,
          'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'input_law': 'one frozen N41 public point; five full W11 fixed-seed pair codes and free root branches; aligned rotations 0,0,12,12,24',
          'worker_count': 1, 'solver': str(solver),
          'solver_cap_seconds': 590,
          'parent_wall_cap_seconds': 600,
          'rss_cap_bytes': 4294967296,
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
