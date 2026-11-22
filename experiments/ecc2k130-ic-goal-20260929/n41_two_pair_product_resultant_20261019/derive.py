"""Eliminate the two reciprocal pair outputs into one product resultant."""
import hashlib
import json
import sys
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929')
sys.path.insert(0, str(ROOT / 'n41_w9_lazy_source_20261017'))
import circuit as design


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'derive_protocol.json').read_text())
for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'resultant.json').exists()
S = PolynomialRing(GF(2), 'u')
u = S.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)


def dec(word):
    return F(S([(int(word) >> bit) & 1 for bit in range(41)]))


def enc(value):
    return sum(int(coefficient) << bit
               for bit, coefficient in enumerate(value.polynomial().list()))


C, H = dec(design.C), dec(design.H)
Crot, Hrot = C**64, H**64
R = PolynomialRing(F, names=('p', 'q', 't'))
p, q, t = R.gens()
R1 = PolynomialRing(R, 'z1')
z1 = R1.gen()
R2 = PolynomialRing(R1, 'z2')
z2 = R2.gen()
first_pair = C*z1**2 + p*z1 + H
second_pair = Crot*z2**2 + q*z2 + Hrot
s3 = (z1*z2*t)**2 + z1*z2*t + (z1+z2)**2 + t**2
started = time.monotonic()
second_eliminated = s3.resultant(second_pair)
resultant = second_eliminated.resultant(first_pair)
elapsed = time.monotonic() - started
assert resultant and len(resultant.monomials()) == 37
assert [resultant.degree(x) for x in (p, q, t)] == [4, 4, 8]
terms = []
for monomial in resultant.monomials():
    exponents = tuple(map(int, monomial.exponents()[0]))
    terms.append({'exponents': list(exponents),
                  'coefficient': enc(resultant.monomial_coefficient(monomial))})
terms.sort(key=lambda row: row['exponents'])
result = {'status': 'PASS_N41_TWO_PAIR_PRODUCT_RESULTANT_DERIVATION',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'first_pair_constants': [enc(C), enc(H)],
          'second_pair_constants_rotated': [enc(Crot), enc(Hrot)],
          'term_count': len(terms), 'degree_p_q_t': [4, 4, 8],
          'terms': terms, 'derivation_wall_seconds': elapsed,
          'protocol_sha256': sha(HERE / 'derive_protocol.json')}
(HERE / 'resultant.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'terms':len(terms),
                  'degree_p_q_t':result['degree_p_q_t'],
                  'wall_seconds':elapsed}))
