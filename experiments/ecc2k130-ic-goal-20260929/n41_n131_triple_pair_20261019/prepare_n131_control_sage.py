"""Construct an N131 triple-plus-pair control from audited W29 pair points."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'n41_n131_all_aligned_20261019/n131_all_aligned_control.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'n131_control_protocol.json').read_text())
assert protocol['status'] == 'FROZEN_BEFORE_TRIPLE_PAIR_N131_CONTROL'
assert protocol['script_sha256'] == sha(Path(__file__))
assert protocol['source_sha256'] == sha(SOURCE)
old = json.loads(SOURCE.read_text())
assert old['aligned_rotations'] == [0] * 5
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**131, name='u', modulus=u**131 + u**13 + u**2 + u + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(131)]))


def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def xy(point):
    return [enc(point[0]), enc(point[1])]


def frob(point, count):
    return E(point[0]**(1 << count), point[1]**(1 << count))


rotations = [0, 0, 0, 36, 36]
base = [E(*map(dec, coords)) for coords in old['pair_points']]
for slot, point in enumerate(base):
    assert enc(1 / point[0]) == old['pairs'][slot]['output_reciprocal']
points = [frob(point, rotation) for point, rotation in zip(base, rotations)]
middle = [points[0] + points[1], points[0] + points[1] + points[2],
          points[3] + points[4]]
assert all(point != E(0) and point[0] for point in middle)
target = sum(points, E(0))
assert target != E(0) and target[0] and middle[1] + middle[2] == target
codes = old['codes']
assert codes[:3] == sorted(codes[:3]) and codes[3:] == sorted(codes[3:])
control = {
    'status': 'PASS_N131_TRIPLE_PAIR_CONSTRUCTED_GROUP_CONTROL',
    'curve_id': old['curve_id'], 'original_rotations': old['original_rotations'],
    'aligned_rotations': rotations, 'pair_points': [xy(point) for point in points],
    'raw_target': xy(target), 'target_reciprocal': enc(1 / target[0]),
    'middle_reciprocals': [enc(1 / point[0]) for point in middle],
    'pairs': old['pairs'], 'codes': codes, 'distinct_folded_columns': 10,
    'source_sha256': sha(SOURCE),
    'runtime_sha256': sha(HERE / 'sage_runtime_info.json'),
    'protocol_sha256': sha(HERE / 'n131_control_protocol.json'),
}
(HERE / 'n131_triple_pair_control.json').write_text(json.dumps(control, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: control[key] for key in ('status', 'raw_target', 'target_reciprocal')}))
