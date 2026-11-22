"""Freeze exact public/control inputs before the batch residual measurement."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD = ROOT/'n131_w18_two_terminal_bilinear_20261015'
ARITH = ROOT/'n131_fixed_seed_halftrace_cubic_20261011/verify.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    paths = {'batch.py': HERE/'batch.py', 'run.py': HERE/'run.py',
             'freeze.py': HERE/'freeze.py', 'arithmetic.py': ARITH,
             'pool.json': OLD/'pool.json', 'query_result.json': OLD/'query_result.json',
             'control_result.json': OLD/'control_result.json',
             'old_terminal.py': OLD/'terminal.py', 'old_protocol.json': OLD/'protocol.json'}
    old_protocol = json.loads(paths['old_protocol.json'].read_text())
    assert old_protocol['status'] == 'FROZEN_BILINEAR_TWO_TERMINAL_BEFORE_QUERY'
    assert old_protocol['target_dependent_cap_seconds'] == 600
    data = {'status': 'FROZEN_BATCH_RESIDUAL_COMPARISON', 'candidate_id': None,
            'curve_id': old_protocol['curve_id'], 'workload_id': old_protocol['workload_id'],
            'public_target': old_protocol['public_target'], 'worker_count': 1,
            'resource_envelope': {'wall_cap_seconds': 300, 'rss_cap_bytes': 4294967296},
            'input_sha256': {name: sha(path) for name, path in paths.items()}}
    with (HERE/'protocol.json').open('x') as stream:
        json.dump(data,stream,sort_keys=True,indent=2);stream.write('\n')
    print(data['status'])


if __name__=='__main__':
    main()
