"""Check a factored two-quadratic S3 elimination against the frozen resultant."""
import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'factor_protocol.json').read_text())
for path, digest in protocol['sources'].items():
    assert sha(path) == digest, path
assert not (HERE / 'factor_result.json').exists()
source = json.loads(Path(protocol['resultant']).read_text())
S = PolynomialRing(GF(2), 'u')
u = S.gen()
F = GF(2**41, name='u', modulus=u**41+u**3+1)


def dec(word):
    return F(S([(int(word) >> i) & 1 for i in range(41)]))


R = PolynomialRing(F, names=('p','q','t'))
p,q,t = R.gens()
C,H = map(dec, source['first_pair_constants'])
D,J = map(dec, source['second_pair_constants_rotated'])
assert C and D
alpha, beta = p/C, H/C
t2 = t**2
q2 = q**2
U0, U2 = J+D*t2, D+J*t2
K0 = U0**2+q2*t2
K1 = q*t*U0
K2 = q2*(1+t**4)+D*J*t2
K3 = q*t*U2
K4 = U2**2+q2*t2
L = K1+K2*alpha+K3*(alpha**2+beta)+K4*alpha**3
M = K0+K2*beta+K3*alpha*beta+K4*(alpha**2*beta+beta**2)
factored = C*M**2+p*L*M+H*L**2
expanded = sum((dec(row['coefficient'])*p**row['exponents'][0]
                *q**row['exponents'][1]*t**row['exponents'][2]
                for row in source['terms']),R.zero())
assert factored == expanded
assert len(expanded.monomials()) == 37
result = {'status':'PASS_FACTORED_RESULTANT_IDENTITY',
          'candidate_id':None,'curve_id':protocol['curve_id'],
          'term_count':len(expanded.monomials()),
          'degree_p_q_t':[int(expanded.degree(v)) for v in (p,q,t)],
          'factorization':'K0..K4, L, M, C*M^2+p*L*M+H*L^2',
          'protocol_sha256':sha(HERE/'factor_protocol.json')}
(HERE/'factor_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
