"""Seal the exact N41 second-lift input and bounded native search."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'n41_n131_fivepair_w9_w29_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


paths = {'input': HERE / 'n41_raw1_join_input.tsv',
         'lift_targets': HERE / 'lift_targets.json',
         'native_binary': SOURCE / 'join_orbit',
         'native_source': SOURCE / 'join_orbit.cpp',
         'states': SOURCE / 'n41_states.json',
         'runtime': HERE / 'sage_runtime_info.json'}
lift = json.loads(paths['lift_targets'].read_text())
assert lift['status'] == 'PASS_TWO_TRACE_COMPATIBLE_RAW_LIFTS'
assert sha(paths['input']) == lift['n41_raw1_join_input_sha256']
raw1 = lift['rows'][0]['raw1']
assert paths['input'].read_text().splitlines()[0] == 'ECC2K41 5 284 ' + ' '.join(map(str, raw1))
protocol = {'status': 'FROZEN_BEFORE_N41_RAW1_QUERY',
            'curve_id': lift['rows'][0]['curve_id'],
            'target_raw_point': raw1,
            'target_rule': '41 successive Frobenius squares of both raw point coordinates',
            'source_rule': 'same five W9 rotated signed-pair state tables as raw0',
            'worker_count': 1, 'worker_rss_cap_bytes': 4 * 1024**3,
            'parent_wall_cap_seconds': 600,
            'source_sha256': {name: sha(path) for name, path in paths.items()}}
with (HERE / 'n41_raw1_protocol.json').open('x') as out:
    json.dump(protocol, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps(protocol, sort_keys=True))
