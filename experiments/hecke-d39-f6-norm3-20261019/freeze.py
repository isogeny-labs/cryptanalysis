#!/usr/bin/env python3
"""Freeze the prospective holdout before running its producer."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
sha = lambda name: hashlib.sha256((P / name).read_bytes()).hexdigest()
names = ['PROTOCOL.md', 'tools/exp11_class_walk.py', 'tools/hecke11.py', 'sage_runtime.json']
assert json.loads((P / 'sage_runtime.json').read_text())['status'] == 'verified'
assert sha('tools/exp11_class_walk.py') == '17a2a87c86206644e4d9f6e64735f97f5e56c2526fe20a3b54807c193685ba09'
assert sha('tools/hecke11.py') == '17457e16894d8899fbf51f031837b497895b670b45a7100351a17f6b2aa04d85'
protocol = {
    'status': 'FROZEN_BEFORE_D39_F6_PRODUCER',
    'DK': -39, 'f': 6, 'p_predicted': 367, 'u_predicted': 8,
    'hecke_primes': [2, 3], 'class_columns_predicted': 64,
    'conductor_strata_predicted': {'1': 8, '2': 8, '3': 24, '6': 24},
    'rows_by_degree_predicted': {'2': 32, '3': 16},
    'rank_predicted': 40,
    'subset_rank_predicted': {'2': [32, 30], '3': [16, 12], '2+3': [40, 36]},
    'norm2_cycle_rows_predicted': [12, 12],
    'norm3_floor_pair_differences_predicted': 4,
    'environment': {'PFS_WALK_DK': '-39', 'PFS_WALK_F': '6',
                    'PFS_WALK_L': '2,3', 'PFS_WALK_PMIN': '0'},
    'timeout_seconds': 600, 'candidate_id': None, 'timing_claim': None,
    'input_sha256': {name: sha(name) for name in names},
    'runner_sha256': sha('run.py'),
}
path = P / 'protocol.json'
assert not path.exists()
path.write_text(json.dumps(protocol, sort_keys=True, indent=2) + '\n')
print(json.dumps({'status': protocol['status'], 'protocol_sha256': sha('protocol.json')}))
