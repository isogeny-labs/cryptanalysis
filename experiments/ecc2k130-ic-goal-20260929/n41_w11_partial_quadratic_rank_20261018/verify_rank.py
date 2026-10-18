"""Independently replay Sage partials and feature rank in integer GF(2)[u]."""
import hashlib
import json
import time
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'verify_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
source = json.loads((HERE / 'result.json').read_text())
MOD = (1 << 41) | (1 << 3) | 1
MASK = (1 << 41) - 1


def mul(a, b):
    out = 0
    while b:
        if b & 1:
            out ^= a
        b >>= 1
        a <<= 1
        if a >> 41:
            a ^= MOD
    return out


def sq(a):
    return mul(a, a)


def inv(a):
    assert a
    u, v, g1, g2 = a, MOD, 1, 0
    while u != 1:
        assert u
        shift = u.bit_length() - v.bit_length()
        if shift < 0:
            u, v = v, u
            g1, g2 = g2, g1
            shift = -shift
        u ^= v << shift
        g1 ^= g2 << shift
    while g1.bit_length() > 41:
        g1 ^= MOD << (g1.bit_length() - 42)
    assert mul(a, g1) == 1
    return g1


def trace(a):
    out = 0
    for _ in range(41):
        out ^= a
        a = sq(a)
    assert out in (0, 1)
    return out


def halftrace(a):
    assert trace(a) == 0
    out, power = 0, a
    for _ in range(21):
        out ^= power
        power = sq(sq(power))
    assert sq(out) ^ out == a
    return out


def on_curve(point):
    if point is None:
        return True
    x, y = point
    return (sq(y) ^ mul(x, y)) == (mul(sq(x), x) ^ 1)


def add(p, q):
    if p is None:
        return q
    if q is None:
        return p
    x1, y1 = p
    x2, y2 = q
    if x1 == x2:
        if y1 != y2 or x1 == 0:
            return None
        slope = x1 ^ mul(y1, inv(x1))
        x3 = sq(slope) ^ slope
        y3 = sq(x1) ^ mul(slope ^ 1, x3)
    else:
        slope = mul(y1 ^ y2, inv(x1 ^ x2))
        x3 = sq(slope) ^ slope ^ x1 ^ x2
        y3 = mul(slope, x1 ^ x3) ^ x3 ^ y1
    result = (x3, y3)
    assert on_curve(result)
    return result


def frob(point, steps):
    x, y = point
    for _ in range(steps):
        x, y = sq(x), sq(y)
    return x, y


def source_points(a):
    h = halftrace(a)
    assert h
    x = 1 ^ inv(h)
    q = x ^ sq(inv(x))
    z = halftrace(q)
    y = mul(x, z)
    points = [(x, y), (x, y ^ x)]
    assert all(on_curve(point) for point in points)
    return points


BITS = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]
cache = {}


def pair_outputs(code):
    if code not in cache:
        a = 0
        for index, bit in enumerate(BITS):
            if code >> index & 1:
                a ^= 1 << (bit + 1)
        b = a ^ 112
        assert a and b and not trace(a) and not trace(inv(a)) and not trace(inv(b))
        left, right = source_points(a), source_points(b)
        options = {add(p, q) for p in left for q in right}
        assert len(options) == 4 and all(p is not None and p[0] for p in options)
        cache[code] = options
    return cache[code]


PAIRS = list(combinations(range(41), 2))
assert len(PAIRS) == 820


def feature_row(x):
    active = {i for i in range(41) if x >> i & 1}
    row = 1
    for i in active:
        row |= 1 << (1 + i)
    for index, (i, j) in enumerate(PAIRS):
        if i in active and j in active:
            row |= 1 << (42 + index)
    return row


started = time.monotonic()
pivots = {}
for witness in source['basis_witnesses']:
    left, right = tuple(witness['left_point']), tuple(witness['right_point'])
    assert left in pair_outputs(witness['left_code'])
    assert right in pair_outputs(witness['right_code'])
    assert witness['left_code'] != witness['right_code']
    assert all(0 <= coordinate <= MASK for coordinate in left + right)
    partial = add(frob(left, 12), frob(right, 24))
    assert partial is not None and partial[0]
    x = inv(partial[0])
    assert x == witness['partial_reciprocal_x']
    row = feature_row(x)
    while row:
        pivot = row.bit_length() - 1
        if pivot not in pivots:
            assert pivot == witness['pivot']
            pivots[pivot] = row
            break
        row ^= pivots[pivot]
    else:
        raise AssertionError('dependent claimed basis row')
assert len(pivots) == source['rank'] == len(source['basis_witnesses'])
assert source['feature_dimension'] == 862
result = {'status': 'PASS_INDEPENDENT_N41_W11_PARTIAL_QUADRATIC_RANK',
          'candidate_id': None, 'curve_id': source['curve_id'],
          'replayed_basis_rows': len(pivots), 'reconstructed_source_codes': len(cache),
          'full_rank': len(pivots) == 862,
          'wall_seconds': time.monotonic() - started,
          'protocol_sha256': sha(HERE / 'verify_protocol.json')}
out = HERE / 'verify_result.json'
assert not out.exists()
out.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
