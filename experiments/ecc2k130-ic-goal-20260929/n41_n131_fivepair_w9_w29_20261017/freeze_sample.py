"""Freeze the N131 W29 source-density sample before running it."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parent.parent / 'koblitz-s5-invariant-20260924/lowpoly_w23_geometry.cpp'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = {'status': 'FROZEN_BEFORE_W29_SAMPLE',
            'field_modulus': 't^131+t^13+t^2+t+1',
            'source_width': 29, 'seed_mask': 898618,
            'canonical_mask_sample_count': 65536,
            'prng': 'splitmix64', 'prng_seed': 20261017,
            'worker_count': 1, 'wall_cap_seconds': 120,
            'source_sha256': {'sample_w29.cpp': sha(HERE / 'sample_w29.cpp'),
                              'sample_w29': sha(HERE / 'sample_w29'),
                              'lowpoly_w23_geometry.cpp': sha(KERNEL),
                              'sage_runtime_info.json': sha(HERE / 'sage_runtime_info.json')}}
with (HERE / 'sample_protocol.json').open('x') as out:
    json.dump(protocol, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': protocol['status'], 'source_sha256': protocol['source_sha256']}))
