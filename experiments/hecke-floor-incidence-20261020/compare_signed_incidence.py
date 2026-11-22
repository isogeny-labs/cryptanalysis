#!/usr/bin/env python3
"""Read-only local ratio comparison of the independently sealed D39/D87 receipts."""
import hashlib
import json
from pathlib import Path

ROOT = Path('/Volumes/SSD990/cryptanalysis/experiments')
P = Path(__file__).resolve().parent
paths = {
    'D39': ROOT / 'hecke-d39-f6-norm3-20261019/floor.json',
    'D87': ROOT / 'ecdlp-hecke-cross-discriminant-20261012/prospective_D87_f6/floor_intersection.json',
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def integer_vector(d):
    return {int(k): int(v) for k, v in d.items()}

cases = {}
for label, path in paths.items():
    data = json.loads(path.read_text())
    if label == 'D39':
        pairs = [integer_vector(x['signed_columns']) for x in data['degree3_pair_records']]
        cycles = [integer_vector(x['signed_floor_columns']) for x in data['degree2_certificates']]
    else:
        pairs = [integer_vector(x['floor_vector']) for x in data['pairs']]
        cycles = [integer_vector(x['floor_vector']) for x in data['cross_degree_identities']]
    assert len(cycles) == 2
    pair_supports = [set(v) for v in pairs]
    assert all(not pair_supports[i] & pair_supports[j]
               for i in range(len(pairs)) for j in range(i + 1, len(pairs)))
    rows = []
    for ci, cycle in enumerate(cycles):
        for pi, pair in enumerate(pairs):
            overlap = sorted(set(cycle) & set(pair))
            if overlap:
                assert set(pair) <= set(cycle)
                ratios = sorted({cycle[j] // pair[j] for j in overlap})
                assert all(cycle[j] % pair[j] == 0 for j in overlap)
                rows.append({'cycle': ci, 'pair': pi, 'columns': overlap,
                             'ratios': ratios, 'uniform': len(ratios) == 1})
    cases[label] = {'floor_receipt_sha256': sha(path), 'pair_count': len(pairs),
                    'cycle_count': len(cycles), 'overlaps': rows,
                    'all_uniform': all(row['uniform'] for row in rows)}
output = {'status': 'EXACT_LOCAL_RATIO_COMPARISON', 'cases': cases}
(P / 'comparison.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: {'all_uniform': v['all_uniform'], 'overlap_count': len(v['overlaps'])}
                  for k, v in cases.items()}, sort_keys=True))
