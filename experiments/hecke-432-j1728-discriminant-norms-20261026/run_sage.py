"""Exact norms of the quartic and octic factor discriminants."""
import json
from hashlib import sha256
from math import gcd
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ, ZZ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'bridge_gate': ROOT / 'experiments/hecke-432-j1728-sqrt2-resultants-20261026/bridge_gate.json',
    'power_certificate': ROOT / 'experiments/hecke-432-j1728-norm-power-20261026/power_certificate.json',
    'multiplicity_result': ROOT / 'experiments/hecke-432-j1728-fiber-overlap-20261026/multiplicity_result.json',
    'projection_exact_audit': ROOT / 'experiments/hecke-432-j1728-resultant-projection-20261026/exact_audit_result.json',
}


def at_alpha(vector, alpha, K):
    return sum((K(QQ(v)) * alpha ** i for i, v in enumerate(vector)), K(0))


def valuation(n, p):
    count = 0
    while n and n % p == 0:
        n //= p
        count += 1
    return count


def main():
    path = HERE / 'protocol.json'
    protocol = json.loads(path.read_text())
    for name, source in INPUTS.items():
        assert sha256(source.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    certificate = json.loads(INPUTS['factor_certificate'].read_text())
    bridge = json.loads(INPUTS['bridge_gate'].read_text())
    pair_norms = {row['name']: row for row in bridge['norms']}
    Rx = PolynomialRing(QQ, 'x')
    f = Rx([QQ(v) for v in certificate['field_polynomial_coefficients_low_to_high']])
    assert f.degree() == 18 and f.is_irreducible()
    K = NumberField(f, 'alpha')
    alpha = K.gen()
    Rz = PolynomialRing(K, 'z')
    rows = []
    for record in certificate['factors']:
        q = Rz([at_alpha(vector, alpha, K)
                for vector in record['coefficients_low_to_high']])
        degree = int(q.degree())
        assert degree in (4, 8) and q.is_irreducible()
        disc = q.discriminant()
        assert disc != 0
        resultant = q.resultant(q.derivative())
        assert disc == ((-1) ** (degree * (degree - 1) // 2)
                        * resultant / q.leading_coefficient())
        norm = QQ(disc.norm())
        assert norm != 0
        pair = pair_norms[f'pair_resultant_{degree}']
        pair_numerator = abs(int(pair['numerator']))
        numerator = abs(int(norm.numerator()))
        denominator = int(norm.denominator())
        prime_rows = []
        for p in protocol['known_primes']:
            prime_rows.append({'prime': str(p),
                               'discriminant_numerator_valuation': valuation(numerator, p),
                               'discriminant_denominator_valuation': valuation(denominator, p),
                               'pair_resultant_numerator_valuation': valuation(pair_numerator, p)})
        rows.append({'factor_degree': degree,
                     'discriminant_coefficients_low_to_high':
                         [str(v) for v in disc.polynomial().list()],
                     'discriminant_norm_numerator': str(norm.numerator()),
                     'discriminant_norm_denominator': str(norm.denominator()),
                     'discriminant_norm_numerator_digits': len(str(numerator)),
                     'discriminant_norm_denominator_digits': len(str(denominator)),
                     'pair_resultant_norm_numerator_digits': len(str(pair_numerator)),
                     'gcd_with_pair_resultant_numerator':
                         str(gcd(numerator, pair_numerator)),
                     'known_prime_valuations': prime_rows})
        print(json.dumps({'degree': degree,
                          'disc_norm_numerator_digits': len(str(numerator)),
                          'disc_norm_denominator_digits': len(str(denominator))},
                         sort_keys=True), flush=True)
    out = {'status': 'EXACT_QUARTIC_OCTIC_DISCRIMINANT_NORMS',
           'protocol_sha256': sha256(path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'source_field_degree': 18, 'rows': rows}
    (HERE / 'result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'],
                      'summary': [{k: row[k] for k in ('factor_degree',
                                  'discriminant_norm_numerator_digits',
                                  'discriminant_norm_denominator_digits')}
                                  for row in rows]}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
