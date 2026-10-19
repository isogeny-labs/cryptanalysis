"""Check exact S3 quadratic branches on every archived W11 four-pair hit."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'n131_w18_allseed_fourpair_20261012'))
from fourpair_v2 import Field

FIELD = Field(41, [0, 3])
SOURCE = ROOT / 'n41_w11_fourpair_public_20261019' / 'join4_input.tsv'
HITS = ROOT / 'n41_w11_fourpair_orbit_sat_20261019' / 'census' / 'census.stdout'
OUT = HERE / 'chart_result.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add(left, right):
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2:
        if y1 != y2 or x1 == 0:
            return None
        slope = x1 ^ FIELD.mul(y1, FIELD.inverse(x1))
        x3 = FIELD.square(slope) ^ slope
        y3 = FIELD.square(x1) ^ FIELD.mul(slope ^ 1, x3)
    else:
        slope = FIELD.mul(y1 ^ y2, FIELD.inverse(x1 ^ x2))
        x3 = FIELD.square(slope) ^ slope ^ x1 ^ x2
        y3 = FIELD.mul(slope, x1 ^ x3) ^ x3 ^ y1
    return x3, y3


def halftrace(value):
    result = 0
    current = value
    for _ in range(21):
        result ^= current
        current = FIELD.square(FIELD.square(current))
    return result


def quadratic(a, b, z):
    ab = FIELD.mul(a, b)
    A = FIELD.square(ab) ^ 1
    B = ab
    D = FIELD.square(a ^ b)
    assert FIELD.mul(A, FIELD.square(z)) ^ FIELD.mul(B, z) ^ D == 0
    assert B != 0
    if A == 0:
        assert z == FIELD.mul(D, FIELD.inverse(B))
        return 'linear', None
    inv_a = FIELD.inverse(A)
    q = FIELD.mul(FIELD.mul(A, D), FIELD.square(FIELD.inverse(B)))
    h = halftrace(q)
    assert FIELD.square(h) ^ h == q
    unit = FIELD.mul(B, inv_a)
    root0 = FIELD.mul(unit, h)
    roots = [root0, root0 ^ unit]
    assert z in roots
    return 'quadratic', roots.index(z)


def main():
    states = {}
    target = None
    for line in SOURCE.read_text().splitlines():
        row = line.split()
        if row and row[0] == 'T':
            target = int(row[2]), int(row[3])
        if row and row[0] == 'S':
            states[int(row[1]), int(row[2])] = int(row[9]), int(row[10])
    assert target and len(states) == 4 * 1124
    witnesses = []
    for line in HITS.read_text().splitlines():
        row = line.split()
        if not row or row[0] != 'HIT':
            continue
        orientation = int(row[1])
        state_ids = [int(v) for v in row[2:6]]
        pair_points = [states[slot, state_id] for slot, state_id in enumerate(state_ids)]
        left = add(pair_points[0], pair_points[1])
        right = add(pair_points[2], pair_points[3])
        total = add(left, right)
        oriented_target = FIELD.frob(target[0], orientation), FIELD.frob(target[1], orientation)
        assert total == oriented_target
        assert all(p is not None and p[0] for p in pair_points + [left, right, total])
        reciprocals = [FIELD.inverse(p[0]) for p in pair_points + [left, right, total]]
        charts = [quadratic(reciprocals[i], reciprocals[j], reciprocals[k])
                  for i, j, k in [(0, 1, 4), (2, 3, 5), (4, 5, 6)]]
        witnesses.append({'orientation': orientation, 'state_ids': state_ids,
                          'charts': [kind for kind, _ in charts],
                          'branches': [branch for _, branch in charts]})
    assert len(witnesses) == 32
    out = {'status': 'PASS_N41_W11_S3_CHART_AUDIT', 'candidate_id': None,
           'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
           'source_sha256': digest(SOURCE), 'hits_sha256': digest(HITS),
           'witness_count': len(witnesses),
           'quadratic_charts': sum(v == 'quadratic' for row in witnesses for v in row['charts']),
           'linear_charts': sum(v == 'linear' for row in witnesses for v in row['charts']),
           'witnesses': witnesses}
    OUT.write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({k: out[k] for k in ['status', 'witness_count', 'quadratic_charts', 'linear_charts']}, sort_keys=True))


if __name__ == '__main__':
    main()
