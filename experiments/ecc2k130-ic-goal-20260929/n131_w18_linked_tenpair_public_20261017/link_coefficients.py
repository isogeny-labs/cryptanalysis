#!/usr/bin/env python3
"""Check both folded-log coefficients allowed by linked x roots."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPSTREAM = HERE.parent / 'n41_n131_linked_frobenius_pair_20261012/projection_result.json'
record = json.loads(UPSTREAM.read_text())
assert record['status'] == 'PASS_CONSERVATIVE_LABELED_SOURCE_PROJECTION'
r = int(record['subgroup_order'])
rows = []
fixed_field_roots = 0
for encoded in record['frobenius_eigenvalue_roots_mod_r']:
    lam = int(encoded)
    assert (lam*lam + lam + 2) % r == 0
    fixed_field = pow(lam, 131, r) == 1
    fixed_field_roots += fixed_field
    power = pow(lam, 16, r)
    plus, minus = (1+power) % r, (1-power) % r
    assert plus and minus
    assert str(plus) in record['one_plus_lambda_pow_16_for_each_root_mod_r']
    rows.append({'lambda': str(lam), 'frobenius_131_identity': fixed_field,
                 'lambda_pow_16': str(power),
                 'same_sign_coefficient': str(plus),
                 'opposite_sign_coefficient': str(minus)})
assert fixed_field_roots == 1
out = {'status': 'PASS_LINKED_PLUS_MINUS_NONZERO', 'subgroup_order': str(r),
       'rotation_gap': 16, 'rows': rows,
       'source_sha256': hashlib.sha256(UPSTREAM.read_bytes()).hexdigest(),
       'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with (HERE / 'link_coefficients.json').open('x') as file:
    json.dump(out, file, sort_keys=True, indent=2)
    file.write('\n')
print(out['status'])
