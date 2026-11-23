"""Exact affine left-block norm with modular right-subspace test on N131."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'n131_transfer_protocol.json').read_text())
for path, digest in protocol['sources'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
assert not (HERE / 'n131_transfer_result.json').exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('N131 transfer wall cap')))
signal.alarm(protocol['wall_cap_seconds'])
started = time.monotonic()
source = json.loads(Path(protocol['coefficients']).read_text())
S = PolynomialRing(GF(2), 'u')
u = S.gen()
F = GF(2**131, name='u', modulus=u**131+u**13+u**2+u+1)


def dec(word):
    return F(S([(int(word) >> i) & 1 for i in range(131)]))


R = PolynomialRing(F, names=('p', 'q'))
p, q = R.gens()
U = PolynomialRing(F, 'X')
X = U.gen()
Q = PolynomialRing(F, 'x')
x = Q.gen()
seed = dec(source['seed_mask'] << 1)
bits = [bit for bit in range(33) if bit != source['seed_mask'].bit_length()-1]
basis = []
for bit in bits:
    a = dec(1 << (bit+1))
    basis.append(a*a + seed*a)
right_basis = [b**(1 << 18) for b in basis]


def product(code, rotation=0):
    return sum((basis[i] for i in range(32) if (code >> i) & 1), F.zero())**(1 << rotation)


LB = X
for b in basis[:4]:
    LB = LB**2 + LB(b)*LB
assert LB.degree() == 16
LB_R = sum((coefficient*p**i for i, coefficient in LB.dict().items()), R.zero())


def qpoly(expr, pvalue):
    out = Q.zero()
    for (i, j), value in expr.dict().items():
        out += value*pvalue**i*x**j
    return out


def right_subspace_gcd_degree(f):
    # The linearized recurrence is reduced modulo f at each step, so its
    # 2^32-degree polynomial is never materialized.
    remainder = x % f
    coefficients = [F.one()]
    for b in right_basis:
        value = sum((c*b**(1 << i) for i, c in enumerate(coefficients)), F.zero())
        remainder = (remainder**2 + value*remainder) % f
        updated = [F.zero()] * (len(coefficients)+1)
        for i, c in enumerate(coefficients):
            updated[i] += value*c
            updated[i+1] += c*c
        coefficients = updated
    return int(f.gcd(remainder).degree())


rows = []
for source_row in source['rows']:
    name = source_row['name']
    H = sum((dec(coef)*p**i*q**j for i, j, coef in source_row['terms']), R.zero())
    build_start = time.monotonic()
    N = H
    for b in basis[:4]:
        N *= N(p+b, q)
    build_seconds = time.monotonic()-build_start
    assert N.degree(p) == 64 and N.degree(q) == 64
    residual = N
    coeffs = {}
    for power in range(4, -1, -1):
        assert not residual or residual.degree(p) <= 16*power
        coeff = sum((v*q**j for (i,j), v in residual.dict().items()
                     if i == 16*power), R.zero())
        coeffs[power] = coeff
        residual -= coeff*LB_R**power
    assert residual == 0
    qcoeffs = {power: qpoly(expr, F.one()) for power, expr in coeffs.items()}
    for prefix in protocol['sampled_prefixes']:
        base_code = prefix << 4
        base_p = product(base_code)
        invariant = LB(base_p)
        compact = sum((invariant**power*expr for power, expr in qcoeffs.items()), Q.zero())
        explicit = Q.one()
        for offset in range(16):
            explicit *= qpoly(H, product(base_code | offset))
        assert compact == explicit
        test_start = time.monotonic()
        degree = right_subspace_gcd_degree(compact)
        test_seconds = time.monotonic()-test_start
        if name == 'constructed_w20_subset_positive' and prefix == 0:
            assert compact(product(16722, 18)) == 0 and degree >= 1
        rows.append({'target': name, 'prefix': prefix, 'gcd_degree': degree,
                     'block_code_count': 16, 'right_source_code_count': 1 << 32,
                     'gcd_seconds': test_seconds, 'norm_build_seconds': build_seconds,
                     'norm_monomials': len(N.dict()),
                     'compact_monomials': sum(len(v.dict()) for v in coeffs.values())})
        print(json.dumps({'target':name,'prefix':prefix,'gcd_degree':degree,
                          'elapsed_seconds':time.monotonic()-started}),flush=True)
signal.alarm(0)
result = {'status':'PASS_N131_SAMPLED_BLOCK_TRANSFER','candidate_id':None,
          'curve_id':protocol['curve_id'],'rows':rows,
          'protocol_sha256':hashlib.sha256((HERE/'n131_transfer_protocol.json').read_bytes()).hexdigest(),
          'total_wall_seconds':time.monotonic()-started,
          'self_maxrss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(HERE/'n131_transfer_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'total_wall_seconds':result['total_wall_seconds']}))
