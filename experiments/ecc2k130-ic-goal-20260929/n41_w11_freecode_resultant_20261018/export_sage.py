"""Export a free-code bivariate two-pair resultant for frozen N41 targets."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
cfg = json.loads((HERE / 'protocol.json').read_text())
for name, digest in cfg['sources'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
assert not (HERE / 'resultant_input.tsv').exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('bivariate export cap')))
signal.alarm(cfg['wall_cap_seconds'])
started = time.monotonic()
P = PolynomialRing(GF(2), 'u')
u = P.gen()
K = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
B = PolynomialRing(K, names=('p', 'q'))
p, q = B.gens()
W = PolynomialRing(B, 'w')
w = W.gen()


def dec(n):
    return K(P([(n >> i) & 1 for i in range(41)]))


def enc(x):
    return sum(int(v) << i for i, v in enumerate(x.polynomial().list()))


seed = dec(112)
h = K.zero()
power = seed
for _ in range(21):
    h += power
    power = power**4
assert h*h + h == seed
H = h*h
C = K.one()+H
H1, C1 = H**(1 << 12), C**(1 << 12)
H2, C2 = H**(1 << 24), C**(1 << 24)
assert C1 and H1 and C2 and H2
bits = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]


def product(code, rotation):
    a = sum((dec(1 << (bit+1)) for j, bit in enumerate(bits)
             if code >> j & 1), K.zero())
    return (a*(a+seed))**(1 << rotation)


valid = sorted(json.loads((ROOT / cfg['source_count']).read_text())['valid_codes'])
assert len(valid) == 281
products = {code: (product(code, 12), product(code, 24)) for code in valid}
targets = json.loads((ROOT / cfg['target_rows']).read_text())['rows']
assert len(targets) == cfg['target_count'] == 25
lines = [f'FREECODE {len(targets)} {len(valid)} 13']
lines.extend(f'P {code} {enc(v1)} {enc(v2)}'
             for code, (v1, v2) in products.items())
rows = []
for index, target in enumerate(targets):
    row_start = time.monotonic()
    t = ~dec(target['target_point'][0])
    tw = t*w
    A = 1 + tw*tw
    D = t*t + w*w
    M = A*H2 + C2*D
    quartic = A*D*q*q + tw*M*q + M*M + C2*H2*tw*tw
    coeff = quartic.list()
    assert quartic.degree() == 4
    alpha, beta = p/C1, H1/C1
    powers = [(B.one(), B.zero()), (B.zero(), B.one())]
    for _ in range(2, 5):
        r0, r1 = powers[-1]
        powers.append((r1*beta, r0+r1*alpha))
    r0 = sum((c*powers[j][0] for j, c in enumerate(coeff)), B.zero())
    r1 = sum((c*powers[j][1] for j, c in enumerate(coeff)), B.zero())
    f = C1*w*w + p*w + H1
    assert quartic % f == W(r0+r1*w)
    resultant = C1*r0*r0 + p*r0*r1 + H1*r1*r1
    terms = sorted(((tuple(map(int, exponent)), enc(value))
                    for exponent, value in resultant.dict().items()),
                   key=lambda x: x[0])
    assert len(terms) == 13 and resultant.degrees() == (4, 4)
    if index == 0:
        assert resultant(products[253][0], products[63][1]) == 0
    lines.append(f'T {index} {target["target_point"][0]} {target["target_point"][1]}')
    lines.extend(f'C {index} {i} {j} {value}' for (i, j), value in terms)
    rows.append({'name': target['name'], 'target_point': target['target_point'],
                 'reciprocal': enc(t), 'monomial_count': len(terms),
                 'bidegree': [4, 4], 'coefficient_sha256': hashlib.sha256(
                     json.dumps(terms, sort_keys=True).encode()).hexdigest(),
                 'symbolic_remainder_verified': True,
                 'elapsed_seconds': time.monotonic()-row_start})

path = HERE / 'resultant_input.tsv'
path.write_text('\n'.join(lines)+'\n')
signal.alarm(0)
result = {'status': 'PASS_N41_W11_FREECODE_RESULTANT_EXPORT',
          'candidate_id': None, 'curve_id': cfg['curve_id'],
          'source_codes': len(valid), 'target_count': len(targets),
          'terms_per_target': 13, 'bidegree': [4, 4],
          'rows': rows, 'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
          'input_bytes': path.stat().st_size,
          'wall_seconds': time.monotonic()-started,
          'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'protocol_sha256': hashlib.sha256((HERE / 'protocol.json').read_bytes()).hexdigest()}
(HERE / 'export_result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps({'status': result['status'], 'targets': len(rows),
                  'seconds': result['wall_seconds']}, sort_keys=True))
