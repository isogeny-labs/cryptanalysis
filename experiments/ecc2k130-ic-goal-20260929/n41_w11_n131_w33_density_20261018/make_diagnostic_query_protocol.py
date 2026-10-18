"""Freeze known-code diagnostic arms before any solver process starts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ref = json.loads((HERE / 'n41_query_protocol.json').read_text())
solver = Path(ref['solver'])
out = HERE / 'diagnostic_query_protocol.json'
assert not out.exists()
paths = [HERE / 'run_diagnostic.py', HERE / 'diagnostic_build_result.json',
         HERE / 'all5_formula.xcnf', HERE / 'first3_formula.xcnf',
         HERE / 'n41_query_result.json', HERE / 'sage_runtime_info.json',
         solver]
record = {'status': 'FROZEN_BEFORE_N41_W11_KNOWN_CODE_DIAGNOSTIC_QUERIES',
          'candidate_id': None,
          'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'input_law': 'same frozen N41 public point; independently verified relation codes fixed in all five or first three slots, all root branches free',
          'arm_order': ['all5', 'first3'],
          'solver': str(solver), 'worker_count': 1,
          'solver_cap_seconds': 110,
          'parent_wall_cap_seconds': 120,
          'rss_cap_bytes': 4294967296,
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
