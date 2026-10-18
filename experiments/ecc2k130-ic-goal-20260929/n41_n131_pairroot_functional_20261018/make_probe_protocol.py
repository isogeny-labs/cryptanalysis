"""Freeze a paired fixed-conflict N41 functional-root probe."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parent
baseline = root/'n41_w9_final_pair_quadratics_20261018'
old = json.loads((baseline/'probe_protocol.json').read_text())
out = here/'probe_protocol.json'
assert not out.exists()
formulas = {'quadratic': baseline/'formula.xcnf',
            'functional': here/'formula.xcnf'}
paths = [here/'probe.py', here/'build_result.json', here/'n41_result.json',
         baseline/'build_result.json', *formulas.values(), Path(old['solver'])]
record = {'status': 'FROZEN_BEFORE_ABBA_FUNCTIONAL_ROOT_PROBE',
          'candidate_id': None, 'curve_id': old['curve_id'],
          'public_point': old['public_point'],
          'arms': ['quadratic', 'functional', 'functional', 'quadratic'],
          'formulas': {k:str(v) for k,v in formulas.items()},
          'solver': old['solver'], 'worker_count': 1,
          'max_conflicts': 20000, 'solver_wall_cap_seconds': 170,
          'parent_wall_cap_seconds': 180, 'rss_cap_bytes': 4294967296,
          'promotion_gate': 'All arms reach the conflict cap with monitors passing; each functional arm has at most 80 percent of its adjacent quadratic arm decisions and no more than 125 percent of its adjacent quadratic arm wall.',
          'sources': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2)+'\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
