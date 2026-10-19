"""Independently replay the one-root norm over N41 and the N131 control."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'audit_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


assert protocol['script_sha256'] == sha(__file__)
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
    q = z*w*t
    return q**2+q+(z+w+t)**2


def norm(a, g, b, z, t, one):
    t2 = t**2
    k = one+t2*b
    A = t2*a*g+t
    B = a*k
    D = g*k
    E = t2*(b**2+one)
    M = A*z+D
    N = B*z+E
    return N**2+g*N*M+b*M**2


K, dec, enc = field(41, [0, 3])
curve = EllipticCurve(K, [1, 0, 0, 0, 1])
halftrace = lambda value: sum((value**(4**j) for j in range(21)), K.zero())
H = halftrace(dec(112))**2
C = K.one()+H
beta = H/C
producer = json.loads(Path(protocol['n41_result']).read_text())
residual = curve(dec(producer['residual_point'][0]), dec(producer['residual_point'][1]))
t = 1/residual[0]
by_code = {}
for line in Path(protocol['join_input']).read_text().splitlines():
    row = line.split()
    if not row or row[0] != 'S' or row[1] != '0':
        continue
    code = int(row[3])
    entry = by_code.setdefault(code, {'masks': list(map(int, row[5:7])),
                                      'columns': list(map(int, row[7:9])),
                                      'roots': set()})
    point = curve(dec(row[-2]), dec(row[-1]))
    entry['roots'].add(1/point[0])
assert len(by_code) == 281
for row in by_code.values():
    assert len(row['roots']) == 2
    row['alpha'] = dec(row['masks'][0])*dec(row['masks'][1])/C

digest = hashlib.sha256()
checked = 0
zero_cases = []
codes = sorted(by_code)
for i, left in enumerate(codes):
    for right in codes[i+1:]:
        a, g = by_code[left], by_code[right]
        if len(set(a['columns']+g['columns'])) != 4:
            continue
        for z in sorted(a['roots'], key=enc):
            w = min(g['roots'], key=enc)
            expected = f3(z,w,t)*f3(z,w+g['alpha'],t)
            computed = norm(a['alpha'],g['alpha'],beta,z,t,K.one())
            assert computed == expected, (left,right,enc(z))
            digest.update(enc(computed).to_bytes(6,'little'))
            if computed == 0:
                zero_cases.append([left,right,enc(z)])
            checked += 1
assert checked == 78670
assert sorted({tuple(row[:2]) for row in zero_cases}) == [(425,527)]

K131, dec131, enc131 = field(131, [0, 1, 2, 13])
curve131 = EllipticCurve(K131, [1, 0, 0, 0, 1])
control = json.loads(Path(protocol['n131_control']).read_text())
assert control['status'] == 'PASS_N131_TRIPLE_PAIR_CONSTRUCTED_GROUP_CONTROL'
points = [curve131(dec131(x),dec131(y)) for x,y in control['pair_points']]
target = curve131(*map(dec131,control['raw_target']))
residual131 = target-sum(points[:3],curve131(0))
assert residual131 == points[3]+points[4]
t131 = 1/residual131[0]
half131 = lambda value: sum((value**(4**j) for j in range(66)),K131.zero())
H0 = half131(dec131(898618<<1))**2
C0 = K131.one()+H0
Hr = H0**(1<<36)
Cr = C0**(1<<36)
params = []
for slot in (3,4):
    masks = control['pairs'][slot]['masks']
    product = dec131(masks[0]<<1)*dec131(masks[1]<<1)
    z = 1/points[slot][0]
    alpha = product**(1<<36)/Cr
    assert Cr*z**2+product**(1<<36)*z+Hr == 0
    params.append((alpha,z))
value = norm(params[0][0],params[1][0],Hr/Cr,params[0][1],t131,K131.one())
product = f3(params[0][1],params[1][1],t131)*f3(params[0][1],params[1][1]+params[1][0],t131)
assert value == product == 0
result = {'status':'PASS_INDEPENDENT_ONE_ROOT_NORM_AUDIT',
          'n41_root_cases_checked':checked,
          'n41_full_value_digest_sha256':digest.hexdigest(),
          'n41_zero_cases':zero_cases,
          'n131_constructed_norm_zero':True,
          'n131_residual_point':[enc131(residual131[0]),enc131(residual131[1])],
          'protocol_sha256':sha(HERE/'audit_protocol.json')}
(HERE/'audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
