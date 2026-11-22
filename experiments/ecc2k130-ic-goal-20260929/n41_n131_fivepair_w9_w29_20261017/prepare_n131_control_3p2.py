"""Three-plus-two W29 correctness fixture from source-valid W23 edges."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n131_w23_sixpair_shared_circuit_20261017/fixture.json'
source = json.loads(SOURCE.read_text())
R = PolynomialRing(GF(2), 't')
t = R.gen()
F = GF(2**131, name='t', modulus=t**131 + t**13 + t**2 + t + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(131)]))


def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def halftrace(value):
    result = F.zero()
    current = value
    for _ in range(66):
        result += current
        current = current**4
    assert result**2 + result == value
    return result


def point(mask):
    w = dec(mask << 1)
    assert w.trace() == 0 and (1 / w).trace() == 0
    return E.lift_x(1 + 1 / halftrace(w), all=True)[0]


def xy(value):
    return [enc(value[0]), enc(value[1])]


rows = source['pairs'][:5]
nodes = []
for row, rotation in zip(rows, [0, 18, 36, 54, 72]):
    a, b = row['masks']
    assert a ^ b == 898618 and a < b and a < (1 << 29)
    summed = point(a) + point(b)
    assert summed != E(0) and enc(1 / summed[0]) == row['output_reciprocal']
    nodes.append(E(summed[0]**(1 << rotation), summed[1]**(1 << rotation)))
assert len({c for row in rows for c in row['columns']}) == 10
middle = []
for i, j, k in ((0, 1, 5), (5, 2, 6), (3, 4, 7), (6, 7, 8)):
    q = nodes[i] + nodes[j]
    assert q != E(0) and q[0]
    nodes.append(q)
    if k != 8:
        middle.append(enc(1 / q[0]))
target = nodes[-1]
data = {'status': 'COMPLETE_CONSTRUCTED_CONTROL', 'curve_id': source['curve_id'],
        'seed_mask': 898618, 'width': 29, 'rotations': [0, 18, 36, 54, 72],
        'pairs': rows, 'middle_reciprocals': middle,
        'target_raw_point': xy(target), 'target_reciprocal': enc(1 / target[0]),
        'subgroup_point': xy(4 * target), 'distinct_folded_columns': 10,
        'source_fixture_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with (HERE / 'n131_control_3p2.json').open('x') as out:
    json.dump(data, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({key: data[key] for key in ('status', 'target_raw_point',
                                            'subgroup_point', 'distinct_folded_columns')}))
