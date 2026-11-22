"""Freeze the public N41 ordered-slot query before search."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
base = here.parent/'n41_w9_final_pair_quadratics_20261018'
old = json.loads((base/'query_protocol.json').read_text())
base_build = json.loads((base/'build_result.json').read_text())
ordered_build = json.loads((here/'build_result.json').read_text())
probe = json.loads((here/'probe_result.json').read_text())
assert probe['status'] == 'COMPLETED_FROZEN_ABBA_PROBE'
arms = probe['arm_results']
assert all(row['status'] == 'INDETERMINATE_CONFLICT_CAP' and
           row['monitor_error'] is None for row in arms)
for i,j in ((1,0),(2,3)):
    assert arms[i]['reported_decisions'] <= .9*arms[j]['reported_decisions']
    assert arms[i]['wall_seconds'] <= 1.25*arms[j]['wall_seconds']
out = here/'query_protocol.json'
assert not out.exists()
paths = [here/'query.py', here/'build_result.json', here/'formula.xcnf',
         here/'probe_result.json', here/'sage_runtime_info.json',
         base/'build_result.json', Path(old['solver'])]
record = {'status': 'FROZEN_BEFORE_ORDERED_N41_PUBLIC_QUERY',
          'candidate_id': None, 'curve_id': old['curve_id'],
          'public_point': old['public_point'],
          'solver': old['solver'], 'worker_count': 1,
          'solver_cap_seconds': 590, 'parent_wall_cap_seconds': 600,
          'rss_cap_bytes': 4294967296,
          'charged_build_seconds': base_build['wall_seconds']+ordered_build['wall_seconds'],
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2)+'\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
