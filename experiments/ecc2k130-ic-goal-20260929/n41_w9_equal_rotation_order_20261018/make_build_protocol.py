"""Freeze the symmetry-breaker builder and reference circuit before execution."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
base = here.parent/'n41_w9_final_pair_quadratics_20261018'
old = json.loads((base/'build_protocol.json').read_text())
out = here/'build_protocol.json'
assert not out.exists()
paths = [here/'build.py', base/'formula.xcnf', base/'input_wires.json',
         base/'build_result.json', Path(old['panel']), Path(old['states'])]
record = {'status': 'FROZEN_BEFORE_N41_EQUAL_ROTATION_ORDER_BUILD',
          'candidate_id': None, 'curve_id': old['curve_id'],
          'baseline_formula': str(base/'formula.xcnf'),
          'input_wires': str(base/'input_wires.json'),
          'panel': old['panel'], 'states': old['states'],
          'symmetry': 'exchange the first two equal-rotation pair slots and require code0 < code1',
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2)+'\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
