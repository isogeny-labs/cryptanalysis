"""Independent integer replay of the saved norm and power identities."""
import json
import sys
from hashlib import sha256
from pathlib import Path

sys.set_int_max_str_digits(10000)
HERE = Path(__file__).resolve().parent
base = json.loads((HERE / 'result.json').read_text())
relative = json.loads((HERE / 'relative_result.json').read_text())
pairs = json.loads((HERE.parent / 'hecke-432-j1728-sqrt2-resultants-20261026/resultant_norms.json').read_text())
assert base['status'] == 'EXACT_QUARTIC_OCTIC_DISCRIMINANT_NORMS'
assert relative['status'] == 'PASS_RELATIVE_DISCRIMINANT_PRODUCT_AND_SIXTH_POWER'
pair_rows = {r['base_degree']: r for r in pairs['rows']}
base_rows = {r['factor_degree']: r for r in base['rows']}
rows = []
for r in relative['rows']:
    d = r['base_degree']
    b = base_rows[d]
    pair = pair_rows[d]
    D = int(b['discriminant_norm_numerator'])
    R = int(pair['norm_numerator'])
    E = int(r['relative_discriminant_norm_numerator'])
    e = int(r['relative_discriminant_sixth_root'])
    p = int(r['pair_resultant_norm_cube_root'])
    a = int(r['base_discriminant_norm_sixth_root'])
    assert D == E * R * R == a ** 6
    assert E == e ** 6 and R == p ** 3 and a == e * p
    assert int(b['discriminant_norm_denominator']) == 1
    assert int(pair['norm_denominator']) == 1
    assert int(r['relative_discriminant_norm_denominator']) == 1
    vals = []
    for v in b['known_prime_valuations']:
        prime = int(v['prime'])
        count = 0
        work = D
        while work % prime == 0:
            count += 1
            work //= prime
        assert count == v['discriminant_numerator_valuation']
        if count:
            vals.append({'prime': str(prime), 'valuation': count})
    rows.append({'degree': d, 'base_norm_digits': len(str(D)),
                 'relative_norm_digits': len(str(E)),
                 'base_sixth_root_digits': len(str(a)),
                 'known_prime_valuations': vals,
                 'integer_product_and_power_checks': True})
out = {'status': 'PASS_INDEPENDENT_INTEGER_REPLAY',
       'input_sha256': {name: sha256((HERE / name).read_bytes()).hexdigest()
                        for name in ('result.json', 'relative_result.json')},
       'rows': rows}
(HERE / 'audit.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
print(json.dumps(out, sort_keys=True))
