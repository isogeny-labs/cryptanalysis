"""Freeze exact model-replay inputs after a SAT terminal result."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
base = here.parent/'n41_w9_final_pair_quadratics_20261018'
old = json.loads((base/'build_protocol.json').read_text())
query = json.loads((here/'query_result.json').read_text())
assert query['status'] == 'SAT_MODEL_UNVERIFIED'
out = here/'replay_protocol.json'
assert not out.exists()
paths = [here/'replay_model_sage.py', here/'query_result.json',
         here/'solver.stdout', base/'input_wires.json',
         Path(old['states']), Path(old['fixture']), here/'sage_runtime_info.json']
record = {'status': 'FROZEN_BEFORE_INDEPENDENT_ORDERED_MODEL_REPLAY',
          'curve_id': query['curve_id'], 'candidate_id': None,
          'states': old['states'], 'fixture': old['fixture'],
          'input_wires': str(base/'input_wires.json'),
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2)+'\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
