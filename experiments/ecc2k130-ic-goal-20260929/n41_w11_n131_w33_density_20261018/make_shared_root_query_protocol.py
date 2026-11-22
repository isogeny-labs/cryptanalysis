"""Pin the shared-root known-code query against the original control."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ref = json.loads((HERE / 'diagnostic_query_protocol.json').read_text())
solver = Path(ref['solver'])
out = HERE / 'shared_root_query_protocol.json'
assert not out.exists()
paths = [HERE / 'run_shared_root_query.py',
         HERE / 'shared_root_diagnostic_build_result.json',
         HERE / 'shared_root_all5_formula.xcnf',
         HERE / 'diagnostic_query_result.json',
         HERE / 'sage_runtime_info.json', solver]
record = {'status': 'FROZEN_BEFORE_N41_W11_SHARED_ROOT_KNOWN_CODE_QUERY',
          'candidate_id': None, 'curve_id': ref['curve_id'],
          'input_law': 'same frozen N41 public point; five verified relation codes fixed; pair branches free',
          'solver': str(solver), 'worker_count': 1,
          'solver_cap_seconds': 110,
          'parent_wall_cap_seconds': 120,
          'rss_cap_bytes': 4294967296,
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
