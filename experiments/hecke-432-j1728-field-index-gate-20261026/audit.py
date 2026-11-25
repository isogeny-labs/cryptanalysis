"""Independent polynomial-discriminant and integer-index replay."""
import json
from hashlib import sha256
from math import isqrt, prod
from pathlib import Path

from sympy import Poly, Symbol, factorint

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
protocol = json.loads((HERE / 'protocol.json').read_text())
source = ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json'
assert sha256(source.read_bytes()).hexdigest() == protocol['input_sha256']['factor_certificate']
record = json.loads((HERE / 'result.json').read_text())
assert record['status'] == 'PASS_FIELD_INDEX_DISCRIMINANT_IDENTITY'
cert = json.loads(source.read_text())
x = Symbol('x')
f = Poly.from_list(list(reversed([int(c) for c in cert['field_polynomial_coefficients_low_to_high']])), x)
polynomial_disc = int(f.discriminant())
field_disc = int(record['field_discriminant'])
index = int(record['order_index'])
assert polynomial_disc == int(record['polynomial_discriminant']) == field_disc * index * index
assert field_disc == 2 ** 18 * 3 ** 45


def valuation(n, p):
    v = 0
    while n % p == 0:
        n //= p
        v += 1
    return v


def trial_prime(p):
    return p >= 2 and all(p % d for d in range(2, isqrt(p) + 1))


index_factors = sorted((int(p), int(e)) for p, e in factorint(index).items())
assert prod(p ** e for p, e in index_factors) == index
assert all(trial_prime(p) for p, _ in index_factors)
local = []
for row in record['local']:
    p = int(row['prime'])
    fac = Poly(f.as_expr(), x, modulus=p).factor_list()[1]
    degrees = sorted((int(q.degree()), int(e)) for q, e in fac)
    assert degrees == sorted(tuple(v) for v in row['mod_p_factor_degrees'])
    vp = valuation(polynomial_disc, p)
    vf = valuation(field_disc, p)
    vi = valuation(index, p)
    assert vp == row['polynomial_discriminant_valuation'] == vf + 2 * vi
    assert vf == row['field_discriminant_valuation']
    assert vi == row['order_index_valuation']
    assert (all(e == 1 for _, e in degrees)) == row['mod_p_squarefree']
    local.append({'prime': p, 'polynomial_valuation': vp,
                  'field_valuation': vf, 'index_valuation': vi,
                  'mod_p_factor_degrees': degrees})
audit = {'status': 'PASS_INDEPENDENT_DISCRIMINANT_INDEX_AUDIT',
         'input_sha256': {name: sha256((HERE / name).read_bytes()).hexdigest()
                          for name in ('result.json', 'protocol.json')},
         'field_discriminant_factorization': [[2, 18], [3, 45]],
         'complete_index_factorization': index_factors,
         'local': local}
(HERE / 'audit.json').write_text(json.dumps(audit, sort_keys=True, indent=2) + '\n')
print(json.dumps({'status': audit['status'],
                  'field_discriminant_factorization': audit['field_discriminant_factorization'],
                  'index_factor_count': len(index_factors)}, sort_keys=True))
