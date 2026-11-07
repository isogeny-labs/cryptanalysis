"""Independent finite-field support audit for the saved ideal valuations."""
import json
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

from sympy import Poly, Symbol

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
protocol = json.loads((HERE / 'protocol.json').read_text())
result = json.loads((HERE / 'result.json').read_text())
assert result['status'] == 'PASS_RELATIVE_IDEAL_VALUATION_OVERLAP'
cert_path = ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json'
assert sha256(cert_path.read_bytes()).hexdigest() == protocol['input_sha256']['factor_certificate']
cert = json.loads(cert_path.read_text())
x = Symbol('x')
f_coeff = [int(c) for c in cert['field_polynomial_coefficients_low_to_high']]


def mod_coeff(value, p):
    value = Fraction(value)
    assert value.denominator % p
    return value.numerator * pow(value.denominator, -1, p) % p


def poly_from_low(coefficients, p):
    return Poly.from_list(list(reversed([mod_coeff(c, p) for c in coefficients])), x, modulus=p)


rows = []
for row in result['rows']:
    degree = row['base_degree']
    primes = []
    for entry in row['primes']:
        p = entry['prime']
        f = poly_from_low(f_coeff, p)
        e = poly_from_low(row['relative_discriminant_in_K_coefficients_low_to_high'], p)
        r = poly_from_low(row['pair_resultant_in_K_coefficients_low_to_high'], p)
        factors = f.factor_list()[1]
        assert all(exponent == 1 for _, exponent in factors)
        e_degrees = sorted(int(q.degree()) for q, _ in factors if e.rem(q).is_zero)
        r_degrees = sorted(int(q.degree()) for q, _ in factors if r.rem(q).is_zero)
        both_degrees = sorted(int(q.degree()) for q, _ in factors
                              if e.rem(q).is_zero and r.rem(q).is_zero)
        saved = entry['places']
        assert e_degrees == sorted(v['residue_degree'] for v in saved
                                   if v['relative_discriminant_valuation'] > 0)
        assert r_degrees == sorted(v['residue_degree'] for v in saved
                                   if v['pair_resultant_valuation'] > 0)
        assert both_degrees == sorted(v['residue_degree'] for v in saved
                                      if v['same_place_overlap'])
        assert len(both_degrees) == entry['overlap_place_count']
        assert sum(both_degrees) == f.gcd(e).gcd(r).degree()
        primes.append({'prime': p, 'relative_support_degrees': e_degrees,
                       'pair_support_degrees': r_degrees,
                       'common_support_degrees': both_degrees})
    rows.append({'base_degree': degree, 'primes': primes})
audit = {'status': 'PASS_INDEPENDENT_MODULAR_IDEAL_SUPPORT',
         'result_sha256': sha256((HERE / 'result.json').read_bytes()).hexdigest(),
         'rows': rows}
(HERE / 'audit.json').write_text(json.dumps(audit, sort_keys=True, indent=2) + '\n')
print(json.dumps({'status': audit['status'],
                  'overlap': {str(r['base_degree']): [[p['prime'], p['common_support_degrees']]
                                                    for p in r['primes']] for r in rows}},
                 sort_keys=True))
