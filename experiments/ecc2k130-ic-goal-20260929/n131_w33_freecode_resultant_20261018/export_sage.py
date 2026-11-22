"""N131 W33 two-pair resultant coefficients for control and public point."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
cfg = json.loads((HERE / 'export_protocol.json').read_text())
for name, digest in cfg['sources'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
assert not (HERE / 'coefficients.json').exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('N131 resultant export cap')))
signal.alarm(cfg['wall_cap_seconds'])
started = time.monotonic()
P = PolynomialRing(GF(2), 'u')
u = P.gen()
K = GF(2**131, name='u', modulus=u**131+u**13+u**2+u+1)
E = EllipticCurve(K, [1, 0, 0, 0, 1])
B = PolynomialRing(K, names=('p', 'q'))
p, q = B.gens()
W = PolynomialRing(B, 'w')
w = W.gen()


def dec(n):
    return K(P([(n >> i) & 1 for i in range(131)]))


def enc(x):
    return sum(int(v) << i for i, v in enumerate(x.polynomial().list()))


seed_mask = 898618
seed = dec(seed_mask << 1)
h = K.zero()
power = seed
for _ in range(66):
    h += power
    power = power**4
assert h*h + h == seed
H = h*h
C = K.one()+H
rotations = [0, 18]
H1, H2 = [H**(1 << rotation) for rotation in rotations]
C1, C2 = [C**(1 << rotation) for rotation in rotations]
assert all((H1, H2, C1, C2))
bits = [bit for bit in range(33) if bit != seed_mask.bit_length()-1]
assert len(bits) == 32
base = [dec(1 << (bit+1)) for bit in bits]
pb = [(a*a+seed*a) for a in base]


def rank(words):
    pivots = {}
    for word in words:
        v = enc(word)
        while v:
            bit = v.bit_length()-1
            if bit not in pivots:
                pivots[bit] = v
                break
            v ^= pivots[bit]
    return len(pivots)


assert rank(pb) == 32


def source(code):
    a = sum((base[j] for j in range(32) if code >> j & 1), K.zero())
    product = a*(a+seed)
    return a, product


audit = json.loads((ROOT / cfg['positive_audit']).read_text())
public = json.loads((ROOT / cfg['public_protocol']).read_text())
assert audit['status'] == 'PASS_INDEPENDENT_SAGE_W20_IMPLICIT_PAIR_HIT'
assert audit['selected_codes'] == [3, 16722]
assert public['curve_id'] == cfg['curve_id']
positive_point = audit['positive_group_sum']
public_point = public['raw_point']
assert E(*(dec(v) for v in positive_point)) != E(0)
assert E(*(dec(v) for v in public_point)) != E(0)
source_checks = []
for code in audit['selected_codes']:
    a, product = source(code)
    assert product and a and a+seed
    assert not a.trace() and not (~a).trace() and not (~(a+seed)).trace()
    source_checks.append({'code': code, 'parameter': enc(a),
                          'unrotated_product': enc(product),
                          'inverse_product': enc(~product)})
assert source_checks[0]['code'] == 3 and source_checks[1]['code'] == 16722
p1 = source(3)[1]**(1 << rotations[0])
p2 = source(16722)[1]**(1 << rotations[1])

rows = []
for name, coords in [('constructed_w20_subset_positive', positive_point),
                     ('frozen_public_raw_point', public_point)]:
    row_started = time.monotonic()
    t = ~dec(coords[0])
    tw = t*w
    A = 1+tw*tw
    D = t*t+w*w
    M = A*H2+C2*D
    quartic = A*D*q*q+tw*M*q+M*M+C2*H2*tw*tw
    coeff = quartic.list()
    assert quartic.degree() == 4
    alpha, beta = p/C1, H1/C1
    powers = [(B.one(),B.zero()),(B.zero(),B.one())]
    for _ in range(2,5):
        r0,r1 = powers[-1]
        powers.append((r1*beta,r0+r1*alpha))
    r0 = sum((c*powers[j][0] for j,c in enumerate(coeff)), B.zero())
    r1 = sum((c*powers[j][1] for j,c in enumerate(coeff)), B.zero())
    f = C1*w*w+p*w+H1
    assert quartic % f == W(r0+r1*w)
    resultant = C1*r0*r0+p*r0*r1+H1*r1*r1
    terms = sorted([[int(i),int(j),enc(v)] for (i,j),v in resultant.dict().items()])
    assert len(terms)==13 and resultant.degrees()==(4,4)
    if name == 'constructed_w20_subset_positive':
        assert resultant(p1,p2)==0
    rows.append({'name': name, 'point': coords, 'reciprocal': enc(t),
                 'terms': terms, 'bidegree': [4,4],
                 'symbolic_remainder_verified': True,
                 'positive_pair_products': [enc(p1),enc(p2)] if name.startswith('constructed') else None,
                 'elapsed_seconds': time.monotonic()-row_started})

signal.alarm(0)
result = {'status': 'PASS_N131_W33_FREECODE_RESULTANT_EXPORT',
          'candidate_id': None, 'curve_id': cfg['curve_id'],
          'field_degree': 131, 'seed_mask': seed_mask,
          'source_width': 33, 'free_code_bits': 32,
          'source_product_rank': rank(pb), 'rotations': rotations,
          'positive_source_checks': source_checks,
          'rows': rows, 'wall_seconds': time.monotonic()-started,
          'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'protocol_sha256': hashlib.sha256((HERE / 'export_protocol.json').read_bytes()).hexdigest()}
(HERE / 'coefficients.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps({'status': result['status'], 'rows': len(rows),
                  'terms': [len(row['terms']) for row in rows],
                  'wall_seconds': result['wall_seconds']}, sort_keys=True))
