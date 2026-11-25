"""Freeze inputs for the source-only functional-root N41 Boolean build."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parent
base = json.loads((root/'n41_w9_final_pair_quadratics_20261018/build_protocol.json').read_text())
out = here/'source_build_protocol.json'
assert not out.exists()
paths = [here/'source_build.py', here/'n41_result.json', here/'sage_runtime_info.json',
         Path(base['states']), Path(base['fixture']), Path(base['panel'])]
record = {'status': 'FROZEN_BEFORE_SOURCE_FUNCTIONAL_ROOT_BUILD',
          'curve_id': base['curve_id'], 'candidate_id': None,
          'states': base['states'], 'fixture': base['fixture'], 'panel': base['panel'],
          'wall_cap_seconds': 240, 'rss_envelope_bytes': 4294967296,
          'sources': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2)+'\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
