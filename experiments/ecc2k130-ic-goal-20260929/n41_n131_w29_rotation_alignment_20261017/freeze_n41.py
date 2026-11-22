"""Seal the N41 paired-aligned orbit query before native execution."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'n41_n131_fivepair_w9_w29_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


prepared = json.loads((HERE / 'prepare_result.json').read_text())
assert prepared['status'] == 'PASS_PAIRED_ALIGNED_N41_INPUT'
assert prepared['aligned_rotations'] == [0, 0, 12, 12, 24]
paths = {'preparer': HERE / 'prepare_n41.py',
         'prepared': HERE / 'prepare_result.json',
         'states': HERE / 'aligned_states.json',
         'input': HERE / 'aligned_input.tsv',
         'runner': HERE / 'run_n41.py',
         'native_source': SOURCE / 'join_orbit.cpp',
         'native_binary': SOURCE / 'join_orbit',
         'sage_runtime': HERE / 'sage_runtime_info.json'}
for name in ('preparer', 'states', 'input'):
    assert sha(paths[name]) == prepared['source_sha256'][
        {'preparer': 'script', 'states': 'aligned_states', 'input': 'aligned_input'}[name]]
protocol = {'status': 'FROZEN_BEFORE_PAIRED_ALIGNED_N41_QUERY',
            'curve_id': prepared['curve_id'],
            'target_raw_point': prepared['target_raw_point'],
            'target_rule': '41 successive Frobenius squares of both raw point coordinates',
            'rotations': prepared['aligned_rotations'],
            'worker_count': 1, 'worker_rss_cap_bytes': 4 * 1024**3,
            'parent_wall_cap_seconds': 600,
            'source_sha256': {name: sha(path) for name, path in paths.items()}}
with (HERE / 'n41_protocol.json').open('x') as out:
    json.dump(protocol, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps(protocol, sort_keys=True))
