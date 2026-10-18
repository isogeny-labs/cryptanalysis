"""Independent integer-field audit of every tested block-norm zero set."""
import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


cfg = json.loads((HERE / 'audit_protocol.json').read_text())
for name, expected in cfg['source_sha256'].items():
    path = Path(name)
    if not path.is_absolute():
        path = ROOT / path
    assert sha(path) == expected, name
source = json.loads((BASE / 'n41_n131_fivepair_w9_w29_20261017' /
                     'n41_states.json').read_text())
panel = [line.split() for line in (BASE / 'n41_w9_implicit_pair_oracle_20261018' /
                                    'panel.tsv').read_text().splitlines()]
sweep = json.loads((HERE / 'sweep_result.json').read_text())
assert sweep['status'] == 'PASS_WIDTH_SWEEP_CONTROLS'

N = 41
MOD = (1 << 41) | (1 << 3) | 1


def mul(a, b):
    result = 0
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & (1 << N):
            a ^= MOD
    return result


def square(a):
    return mul(a, a)


def power(a, exponent):
    result = 1
    while exponent:
        if exponent & 1:
            result = mul(result, a)
        a = square(a)
        exponent >>= 1
    return result


def inverse(a):
    assert a
    result = power(a, (1 << N) - 2)
    assert mul(a, result) == 1
    return result


def frob(a, count):
    for _ in range(count):
        a = square(a)
    return a


def halftrace(a):
    result = 0
    for _ in range(21):
        result ^= a
        a = square(square(a))
    return result


def on_curve(point):
    if point is None:
        return True
    x, y = point
    return square(y) ^ mul(x, y) == mul(square(x), x) ^ 1


def negate(point):
    return None if point is None else (point[0], point[1] ^ point[0])


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
        slope = x1 ^ mul(y1, inverse(x1))
        x3 = square(slope) ^ slope
        y3 = square(x1) ^ mul(slope ^ 1, x3)
    else:
        slope = mul(y1 ^ y2, inverse(x1 ^ x2))
        x3 = square(slope) ^ slope ^ x1 ^ x2
        y3 = mul(slope, x1 ^ x3) ^ x3 ^ y1
    result = (x3, y3)
    assert on_curve(result)
    return result


seed = 56 << 1
H = square(halftrace(seed))
C = 1 ^ H
basis = [1 << (i + 1) for i in range(9) if i != 5]
products = [square(a) ^ mul(seed, a) for a in basis]
coeff = [1]
for value in products:
    evaluation = 0
    power_value = value
    for c in coeff:
        evaluation ^= mul(c, power_value)
        power_value = square(power_value)
    updated = [0] * (len(coeff) + 1)
    for i, c in enumerate(coeff):
        updated[i] ^= mul(evaluation, c)
        updated[i + 1] ^= square(c)
    coeff = updated
assert len(coeff) == 9
rotated_coeff = [frob(c, 6) for c in coeff]
Crot, Hrot = frob(C, 6), frob(H, 6)


def linearized(value):
    result = 0
    for c in rotated_coeff:
        result ^= mul(c, value)
        value = square(value)
    return result


states = [tuple(row['point']) for row in source['states'][0]]
by_x = {}
for sid, point in enumerate(states):
    assert on_curve(point)
    by_x.setdefault(point[0], []).append(sid)
assert len(by_x) == 142 and all(len(ids) == 2 for ids in by_x.values())

started = time.monotonic()
summary = []
for row in sweep['results']:
    panel_row = panel[row['panel_index']]
    key = (int(panel_row[5]), int(panel_row[6]))
    assert on_curve(key)
    root_count = 0
    direct_candidates = []
    for x in row['block_x']:
        ids = by_x[x]
        assert states[ids[0]][1] ^ states[ids[1]][1] == x
        factors = []
        for sid in ids:
            residual = add(key, negate(states[sid]))
            assert residual is not None and residual[0]
            xres = residual[0]
            prot = mul(Crot, inverse(xres)) ^ mul(Hrot, xres)
            image = linearized(prot)
            factors.append(image)
            if image == 0:
                direct_candidates.append({'state_id': sid,
                                          'product': frob(prot, 35)})
        if mul(factors[0], factors[1]) == 0:
            root_count += 1
    assert root_count == row['gcd_degree']
    assert sorted(direct_candidates, key=lambda item: item['state_id']) == sorted(
        row['direct_candidates'], key=lambda item: item['state_id'])
    assert (root_count > 0) == (row['status'] == 'RETAIN')
    summary.append({'width': row['width'], 'panel_index': row['panel_index'],
                    'norm_zero_roots': root_count,
                    'direct_source_states': len(direct_candidates)})

result = {'status': 'PASS_INTEGER_FIELD_BLOCK_NORM_ZERO_SETS',
          'candidate_id': None, 'curve_id': source['curve_id'],
          'tested_blocks': len(summary), 'summary': summary,
          'wall_seconds': time.monotonic()-started,
          'source_sha256': sha(BASE / 'n41_n131_fivepair_w9_w29_20261017' /
                               'n41_states.json'),
          'sweep_result_sha256': sha(HERE / 'sweep_result.json'),
          'protocol_sha256': sha(HERE / 'audit_protocol.json'),
          'auditor_sha256': sha(Path(__file__))}
assert not (HERE / 'audit_result.json').exists()
(HERE / 'audit_result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps({'status': result['status'],
                  'tested_blocks': result['tested_blocks'],
                  'wall_seconds': result['wall_seconds']}, sort_keys=True))
