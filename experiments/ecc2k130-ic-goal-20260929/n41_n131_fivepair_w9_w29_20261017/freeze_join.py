"""Freeze the exact N41 five-pair public join inputs and resource envelope."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


sources = {path.name: sha(path) for path in
           (HERE / 'prepare_n41.py', HERE / 'n41_states.json',
            HERE / 'prepare_input.py', HERE / 'join_input.tsv',
            HERE / 'join_five.cpp', HERE / 'join_five',
            HERE / 'sage_runtime_info.json')}
state = json.loads((HERE / 'n41_states.json').read_text())
protocol = {'status': 'FROZEN_BEFORE_JOIN',
            'curve_id': state['curve_id'], 'width': state['width'],
            'seed': state['seed'], 'rotations': state['rotations'],
            'target_raw_point': state['target_raw_point'],
            'states_per_slot': state['states_per_slot'],
            'source_sha256': sources,
            'worker_count': 1, 'parent_wall_cap_seconds': 600,
            'combined_rss_cap_bytes': 4 * 1024**3,
            'join_policy': 'three-left versus two-right exact group lookup, all five leaf ids free'}
with (HERE / 'join_protocol.json').open('x') as out:
    json.dump(protocol, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': protocol['status'], 'source_sha256': sources}))
