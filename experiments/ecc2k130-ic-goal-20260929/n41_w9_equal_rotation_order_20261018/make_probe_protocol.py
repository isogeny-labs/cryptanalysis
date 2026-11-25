"""Freeze the paired solver test for the equal-rotation ordering rule."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
base = here.parent/'n41_w9_final_pair_quadratics_20261018'
old = json.loads((base/'probe_protocol.json').read_text())
out = here/'probe_protocol.json'
assert not out.exists()
formulas = {'quadratic': base/'formula.xcnf', 'ordered': here/'formula.xcnf'}
paths = [here/'probe.py', here/'build_result.json', base/'build_result.json',
         here/'sage_runtime_info.json', *formulas.values(), Path(old['solver'])]
record = {'status': 'FROZEN_BEFORE_EQUAL_ROTATION_ORDER_PROBE',
          'candidate_id': None, 'curve_id': old['curve_id'],
          'public_point': old['public_point'],
          'arms': ['quadratic', 'ordered', 'ordered', 'quadratic'],
          'formulas': {key: str(path) for key,path in formulas.items()},
          'solver': old['solver'], 'worker_count': 1,
          'max_conflicts': 20000, 'solver_wall_cap_seconds': 170,
          'parent_wall_cap_seconds': 180, 'rss_cap_bytes': 4294967296,
          'promotion_gate': 'All arms reach the conflict cap with monitors passing; both ordered arms have at most 90 percent of their adjacent quadratic arm decisions and at most 125 percent of adjacent wall.',
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2)+'\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
