"""Check the explicit constant-coefficient obstruction in Sage's GF(2^131)."""
import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing

here = Path(__file__).resolve().parent
certificate = json.loads((here / 'linear_certificate.json').read_text())
P = PolynomialRing(GF(2), 'u')
u = P.gen()
K = GF(2**131, name='u', modulus=u**131 + u**13 + u**2 + u + 1)


def field(word):
    return K(P([(int(word) >> i) & 1 for i in range(131)]))


def constant(value):
    return int(value.polynomial()[0])


PB = [field(word) for word in certificate['product_basis']]
seed = field(certificate['source_seed'])
assert all(a*a + seed*a == p for a, p in
           zip(map(field, certificate['source_basis']), PB))
C = field(certificate['C'])
H = field(certificate['H'])
CH = field(certificate['CH'])
assert C+H == K.one()
assert C*H == CH == seed*seed
squares = [b*b for b in PB]
pair_products = [PB[i]*PB[j] for i in range(28) for j in range(i, 28)]
scaled_squares = [CH*square for square in squares]
assert certificate['parity_mask'] == 1
assert all(constant(value) == 0 for value in
           squares + pair_products + scaled_squares)
assert constant(K.one()) == 1
receipt = {
    'status': 'PASS_SAGE_GF2_131_CONSTANT_COEFFICIENT_CERTIFICATE',
    'curve_id': certificate['curve_id'],
    'generator_counts': [len(squares), len(pair_products), len(scaled_squares)],
    'constant_coefficient_of_all_generators': 0,
    'constant_coefficient_of_one': 1,
    'certificate_sha256': hashlib.sha256((here / 'linear_certificate.json').read_bytes()).hexdigest(),
}
(here / 'linear_certificate_sage_replay.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
print(json.dumps(receipt, sort_keys=True))
