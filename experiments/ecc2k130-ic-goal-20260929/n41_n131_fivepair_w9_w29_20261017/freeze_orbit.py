"""Freeze a new 41-orientation query after the completed raw miss."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


single = json.loads((HERE / 'single_result.json').read_text())
assert single['status'] == 'COMPLETE_MISS'
source = json.loads((HERE / 'n41_states.json').read_text())
paths = [HERE / name for name in ('n41_states.json', 'join_input.tsv',
                                  'join_orbit.cpp', 'join_orbit',
                                  'single_result.json', 'sage_runtime_info.json')]
protocol = {'status': 'FROZEN_BEFORE_ORBIT_QUERY',
            'curve_id': source['curve_id'], 'target_raw_point': source['target_raw_point'],
            'target_rule': '41 successive Frobenius squares of both raw point coordinates',
            'source_rule': 'same five W9 rotated signed-pair state tables',
            'worker_count': 1, 'parent_wall_cap_seconds': 600,
            'worker_rss_cap_bytes': 4 * 1024**3,
            'source_sha256': {path.name: sha(path) for path in paths}}
with (HERE / 'orbit_protocol.json').open('x') as out:
    json.dump(protocol, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': protocol['status'], 'source_sha256': protocol['source_sha256']}))
