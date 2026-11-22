#!/usr/bin/env python3
"""Freeze the D15 holdout before calling the producer."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
def sha(name):
    return hashlib.sha256((P / name).read_bytes()).hexdigest()

files = ['PROTOCOL.md', 'scan_candidates.py', 'scan_candidates.json',
         'compare_signed_incidence.py', 'comparison.json', 'sage_runtime.json',
         'tools/exp11_class_walk.py', 'tools/hecke11.py']
out = {
    'status': 'FROZEN_BEFORE_D15_F6_PRODUCER',
    'DK': -15, 'f': 6, 'hecke_primes': [2, 3],
    'environment': {'PFS_WALK_DK': '-15', 'PFS_WALK_F': '6',
                    'PFS_WALK_L': '2,3', 'PFS_WALK_PMIN': '0'},
    'p_predicted': 139, 'u_predicted': 4,
    'conductor_strata_predicted': {'1': 4, '2': 4, '3': 12, '6': 12},
    'class_columns_predicted': 32,
    'rows_by_degree_predicted': {'2': 16, '3': 8},
    'rank_predicted': 20,
    'subset_rank_predicted': {'2': [16, 14], '3': [8, 6], '2+3': [20, 18]},
    'norm2_cycle_rows_predicted': [6, 6],
    'norm3_floor_pair_differences_predicted': 2,
    'cycle_pair_ratio_predicted': 'uniform_on_each_six_column_pair_support',
    'timeout_seconds': 600, 'candidate_id': None, 'timing_claim': None,
    'input_sha256': {name: sha(name) for name in files},
}
path = P / 'protocol.json'
assert not path.exists()
path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
print(sha('protocol.json'))
