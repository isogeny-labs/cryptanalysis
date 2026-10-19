"""Independently replay the norm identity on N41 catalog and N131 control."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'audit_protocol.json').read_text())
assert protocol['status'] == 'FROZEN_BEFORE_PAIR_RESULTANT_INDEPENDENT_AUDIT'
assert protocol['script_sha256'] == sha(Path(__file__))
for path, digest in protocol['sources'].items():
    assert sha(path) == digest, path


def field(n, taps):
    P = PolynomialRing(GF(2), 'u')
    u = P.gen()
    K = GF(2**n, name='u', modulus=u**n + sum(u**bit for bit in taps))
    def dec(word):
        return K(P([(int(word) >> i) & 1 for i in range(n)]))
    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
    return K, dec, enc


def f3(z, w, t):
    q = z * w * t
    return q**2 + q + (z + w + t)**2


def closed_norm(a, g, b, t, one):
    t2 = t**2
    k = one + t2*b
    A = t2*a*g+t
    B = a*k
    D = g*k
    E = t2*(b**2+one)
    U = B**2+g*B*A+b*A**2
    V = g*(B*D+E*A)
    W = E**2+g*E*D+b*D**2
    L1 = U*a+V
    L0 = U*b+W
    return L0**2+a*L0*L1+b*L1**2


K, dec, enc = field(41, [0, 3])
Ecurve = EllipticCurve(K, [1, 0, 0, 0, 1])
halftrace = lambda value: sum((value**(4**j) for j in range(21)), K.zero())
H = halftrace(dec(112))**2
C = K.one() + H
beta = H / C
producer = json.loads((HERE / 'result.json').read_text())
residual = Ecurve(dec(producer['residual_point'][0]),
                  dec(producer['residual_point'][1]))
t = 1 / residual[0]
by_code = {}
for line in Path(protocol['join_input']).read_text().splitlines():
    row = line.split()
    if not row or row[0] != 'S' or row[1] != '0':
        continue
    code = int(row[3])
    entry = by_code.setdefault(code, {'masks': list(map(int, row[5:7])),
                                      'columns': list(map(int, row[7:9])),
                                      'roots': set()})
    point = Ecurve(dec(row[-2]), dec(row[-1]))
    entry['roots'].add(1 / point[0])
assert len(by_code) == 281
for row in by_code.values():
    assert len(row['roots']) == 2
    row['alpha'] = dec(row['masks'][0])*dec(row['masks'][1])/C

digest = hashlib.sha256()
zero_pairs = []
checked = 0
codes = sorted(by_code)
for i, left in enumerate(codes):
    for right in codes[i+1:]:
        a, g = by_code[left], by_code[right]
        if len(set(a['columns']+g['columns'])) != 4:
            continue
        product = K.one()
        for z in a['roots']:
            for w in g['roots']:
                product *= f3(z, w, t)
        computed = closed_norm(a['alpha'], g['alpha'], beta, t, K.one())
        assert computed == product, (left, right)
        digest.update(enc(product).to_bytes(6, 'little'))
        if product == 0:
            zero_pairs.append([left, right])
        checked += 1
assert checked == producer['code_pairs'] == 39335
assert zero_pairs == producer['filter_hits'] == [[425, 527]]

K131, dec131, enc131 = field(131, [0, 1, 2, 13])
E131 = EllipticCurve(K131, [1, 0, 0, 0, 1])
control = json.loads(Path(protocol['n131_control']).read_text())
assert control['status'] == 'PASS_N131_TRIPLE_PAIR_CONSTRUCTED_GROUP_CONTROL'
points = [E131(dec131(x), dec131(y)) for x, y in control['pair_points']]
target = E131(*map(dec131, control['raw_target']))
residual131 = target - sum(points[:3], E131(0))
assert residual131 == points[3] + points[4]
assert residual131 != E131(0) and residual131[0]
t131 = 1 / residual131[0]
half131 = lambda value: sum((value**(4**j) for j in range(66)), K131.zero())
H0 = half131(dec131(898618 << 1))**2
C0 = K131.one() + H0
rotation = 36
Hr = H0**(1 << rotation)
Cr = C0**(1 << rotation)
beta131 = Hr / Cr
params = []
for slot in (3, 4):
    masks = control['pairs'][slot]['masks']
    p0 = dec131(masks[0] << 1) * dec131(masks[1] << 1)
    pr = p0**(1 << rotation)
    z = 1 / points[slot][0]
    assert Cr*z**2 + pr*z + Hr == 0
    params.append((pr/Cr, z))
assert f3(params[0][1], params[1][1], t131) == 0
assert closed_norm(params[0][0], params[1][0], beta131,
                   t131, K131.one()) == 0

result = {'status': 'PASS_INDEPENDENT_PAIR_RESULTANT_AUDIT',
          'candidate_id': None, 'n41_code_pairs_checked': checked,
          'n41_exact_value_product_sha256': digest.hexdigest(),
          'n41_zero_pairs': zero_pairs,
          'n131_constructed_residual': [enc131(residual131[0]),
                                       enc131(residual131[1])],
          'n131_rotated_quadratics_verified': 2,
          'n131_constructed_resultant_zero': True,
          'protocol_sha256': sha(HERE / 'audit_protocol.json')}
(HERE / 'audit_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
