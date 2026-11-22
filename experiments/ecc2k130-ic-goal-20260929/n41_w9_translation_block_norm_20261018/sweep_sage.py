"""Check a target-translated, sign-closed source block in a quotient algebra."""
import hashlib
import json
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[2]
started_total = time.monotonic()
protocol = json.loads((HERE / 'sweep_protocol.json').read_text())
for name, expected in protocol['source_sha256'].items():
    path = Path(name)
    if not path.is_absolute():
        path = ROOT / path
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
source = json.loads((BASE / 'n41_n131_fivepair_w9_w29_20261017' /
                     'n41_states.json').read_text())
panel = [line.split() for line in (BASE / 'n41_w9_implicit_pair_oracle_20261018' /
                                    'panel.tsv').read_text().splitlines()]
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41+u**3+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])
P = PolynomialRing(F, 'X')
X = P.gen()


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def halftrace(value):
    result = F.zero()
    for _ in range(21):
        result += value
        value = value**4
    return result


seed = dec(56 << 1)
H = halftrace(seed)**2
C = 1 + H
bits = [i for i in range(9) if i != 5]
basis = [dec(1 << (i + 1)) for i in bits]
products = [a*a + seed*a for a in basis]
coeff = [F.one()]
for value in products:
    evaluation = sum((c*value**(2**i) for i, c in enumerate(coeff)), F.zero())
    updated = [F.zero()] * (len(coeff) + 1)
    for i, c in enumerate(coeff):
        updated[i] += evaluation*c
        updated[i + 1] += c*c
    coeff = updated
assert len(coeff) == 9
span = {sum((products[i] for i in range(8) if mask >> i & 1), F.zero())
        for mask in range(256)}
assert len(span) == 256
assert all(sum((c*v**(2**i) for i, c in enumerate(coeff)), F.zero()) == 0
           for v in span)
rotated_coeff = [c**(2**6) for c in coeff]

states = [E(*(dec(v) for v in row['point'])) for row in source['states'][0]]
by_x = {}
for sid, point in enumerate(states):
    by_x.setdefault(enc(point[0]), []).append(sid)
assert len(by_x) == 142 and all(len(ids) == 2 for ids in by_x.values())
ordered_x = sorted(by_x)


class Pair:
    def __init__(self, a, b, ring, xbar, x3plus1):
        self.a, self.b = ring(a), ring(b)
        self.ring, self.xbar, self.x3plus1 = ring, xbar, x3plus1

    def __add__(self, other):
        return Pair(self.a + other.a, self.b + other.b,
                    self.ring, self.xbar, self.x3plus1)

    def __mul__(self, other):
        return Pair(self.a*other.a + self.b*other.b*self.x3plus1,
                    self.a*other.b + self.b*other.a +
                    self.b*other.b*self.xbar,
                    self.ring, self.xbar, self.x3plus1)

    def square(self):
        return Pair(self.a*self.a + self.b*self.b*self.x3plus1,
                    self.b*self.b*self.xbar,
                    self.ring, self.xbar, self.x3plus1)

    def norm(self):
        return (self.a*self.a + self.a*self.b*self.xbar +
                self.b*self.b*self.x3plus1)

    def inverse(self):
        n = self.norm()
        inv = self.ring(n.lift().inverse_mod(self.ring.modulus()))
        return Pair((self.a + self.b*self.xbar)*inv, self.b*inv,
                    self.ring, self.xbar, self.x3plus1)


def block_test(key, block):
    started = time.monotonic()
    f = P.one()
    for xint in block:
        f *= X + dec(xint)
    A = P.quotient(f, 'xbar')
    xb = A.gen()
    x3plus1 = xb**3 + 1

    def pair(a, b=0):
        return Pair(a, b, A, xb, x3plus1)

    d = A(key[0]) + xb
    if P(d.lift()).gcd(f).degree() > 0:
        return {'status': 'EXCEPTIONAL_SLOPE', 'elapsed': time.monotonic()-started}
    d_inv = A(d.lift().inverse_mod(f))
    lam = pair((A(key[1]) + xb)*d_inv, d_inv)
    qx = lam.square() + lam + pair(A(key[0]) + xb)
    if P(qx.norm().lift()).gcd(f).degree() > 0:
        return {'status': 'EXCEPTIONAL_OUTPUT_X', 'elapsed': time.monotonic()-started}
    inferred = pair(C**(2**6)) * qx.inverse() + pair(H**(2**6)) * qx
    power = inferred
    image = pair(0)
    for coefficient in rotated_coeff:
        image = image + pair(coefficient) * power
        power = power.square()
    norm = P(image.norm().lift())
    gcd = norm.gcd(f)
    elapsed = time.monotonic()-started
    direct_started = time.monotonic()
    direct = []
    for xint in block:
        for sid in by_x[xint]:
            V = key - states[sid]
            if V == E(0) or not V[0]:
                direct.append({'state_id': sid, 'exceptional': True})
                continue
            rawx = V[0]**(2**35)
            p = C/rawx + H*rawx
            if p in span:
                direct.append({'state_id': sid, 'product': enc(p)})
    return {'status': 'RETAIN' if gcd.degree() > 0 else 'REJECT',
            'gcd_degree': int(gcd.degree()), 'direct_candidates': direct,
            'elapsed': elapsed,
            'direct_elapsed': time.monotonic()-direct_started,
            'block_x': block}


results = []
for width in (1, 2, 4, 8, 16, 32):
    blocks = [ordered_x[i:i + width] for i in range(0, len(ordered_x), width)]
    positive_block = next(i for i, block in enumerate(blocks)
                          if enc(states[0][0]) in block)
    for index in (0, 1, 2):
        row = panel[index]
        key = E(dec(row[5]), dec(row[6]))
        outcome = block_test(key, blocks[positive_block])
        assert outcome['status'] not in ('EXCEPTIONAL_SLOPE', 'EXCEPTIONAL_OUTPUT_X')
        assert (outcome['status'] == 'RETAIN') == bool(outcome['direct_candidates'])
        results.append({'width': width, 'panel_index': index,
                        'block_index': positive_block, **outcome})
        if index == 0:
            assert outcome['status'] == 'RETAIN'
            assert any(item['state_id'] == 0 for item in outcome['direct_candidates'])
record = {'status': 'PASS_WIDTH_SWEEP_CONTROLS', 'candidate_id': None,
          'curve_id': source['curve_id'], 'widths': [1, 2, 4, 8, 16, 32],
          'tested_panel_indices': [0, 1, 2], 'results': results,
          'wall_seconds': time.monotonic()-started_total,
          'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'prototype_result_sha256': hashlib.sha256((HERE / 'prototype_result.json').read_bytes()).hexdigest()}
assert not (HERE / 'sweep_result.json').exists()
(HERE / 'sweep_result.json').write_text(json.dumps(record, indent=2, sort_keys=True)+'\n')
print(json.dumps({'status': record['status'],
                  'results': [(row['width'], row['panel_index'], row['status'],
                               row['gcd_degree'], len(row['direct_candidates']),
                               row['elapsed'], row['direct_elapsed'])
                              for row in results]}, sort_keys=True))
