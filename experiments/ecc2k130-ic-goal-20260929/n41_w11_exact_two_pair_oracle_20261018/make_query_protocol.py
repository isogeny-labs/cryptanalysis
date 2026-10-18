"""Freeze the exact two-pair positive solver control."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ref = json.loads((ROOT / 'n41_w11_n131_w33_density_20261018' /
                  'n41_query_protocol.json').read_text())
solver = Path(ref['solver'])
out = HERE / 'query_protocol.json'
assert not out.exists()
paths = [HERE / 'run.py', HERE / 'build_result.json',
         HERE / 'formula.xcnf', HERE / 'fixture.json',
         HERE / 'sage_runtime_info.json', solver]
record = {'status': 'FROZEN_BEFORE_N41_W11_EXACT_TWO_PAIR_POSITIVE_QUERY',
          'candidate_id': None, 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'input_law': 'positive residual from independently replayed unpinned N41 public relation; both W11 source codes and pair roots free',
          'solver': str(solver), 'worker_count': 1,
          'solver_cap_seconds': 110, 'parent_wall_cap_seconds': 120,
          'rss_cap_bytes': 4294967296,
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
