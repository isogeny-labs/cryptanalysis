#!/usr/bin/env python3
"""Freeze the D183 holdout before calling the producer."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
def sha(name):
    return hashlib.sha256((P / name).read_bytes()).hexdigest()

files = ['PROTOCOL_D183.md', 'PROTOCOL.md', 'protocol.json',
         'scan_candidates.py', 'scan_candidates.json',
         'check_modular_gate.py', 'modular_gate_scan.json',
         'compare_signed_incidence.py', 'comparison.json', 'sage_runtime.json',
         'tools/exp11_class_walk.py', 'tools/hecke11.py',
         'data/exp11_class_walk_D15_f6.json', 'launch.json']
out = {
    'status': 'FROZEN_BEFORE_D183_F6_PRODUCER',
    'DK': -183, 'f': 6, 'hecke_primes': [2, 3],
    'environment': {'PFS_WALK_DK': '-183', 'PFS_WALK_F': '6',
                    'PFS_WALK_L': '2,3', 'PFS_WALK_PMIN': '0'},
    'p_predicted': 1663, 'u_predicted': 8,
    'conductor_strata_predicted': {'1': 16, '2': 16, '3': 48, '6': 48},
    'class_columns_predicted': 128,
    'rows_by_degree_predicted': {'2': 64, '3': 32},
    'rank_predicted': 80,
    'subset_rank_predicted': {'2': [64, 62], '3': [32, 24], '2+3': [80, 70]},
    'norm2_cycle_rows_predicted': [24, 24],
    'norm3_floor_pair_differences_predicted': 8,
    'cycle_pair_ratio_predicted': 'nonuniform_on_at_least_one_block_per_cycle',
    'timeout_seconds': 600, 'candidate_id': None, 'timing_claim': None,
    'input_sha256': {name: sha(name) for name in files},
}
path = P / 'protocol_D183.json'
assert not path.exists()
path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
print(sha('protocol_D183.json'))
