"""Construct an all-aligned N131 group control from audited W29 pair states."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_n131_w29_rotation_alignment_20261017/n131_aligned_control.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'n131_control_protocol.json').read_text())
assert protocol['status'] == 'FROZEN_BEFORE_ALL_ALIGNED_N131_CONTROL'
assert sha(Path(__file__)) == protocol['script_sha256']
assert sha(SOURCE) == protocol['source_sha256']
old = json.loads(SOURCE.read_text())
assert old['aligned_rotations'] == [0, 0, 36, 36, 72]
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


raw = []
for slot, (coords, rotation) in enumerate(zip(old['rotated_pair_points'], old['aligned_rotations'])):
    point = E(*map(dec, coords))
    base = frob(point, (131 - rotation) % 131)
    assert enc(1 / base[0]) == old['pairs'][slot]['output_reciprocal']
    raw.append(base)
codes = [row['masks'][0] for row in old['pairs']]
assert codes == sorted(codes) and len(set(codes)) == 5
assert len({col for row in old['pairs'] for col in row['columns']}) == 10
middle = [raw[0] + raw[1], raw[0] + raw[1] + raw[2], raw[3] + raw[4]]
assert all(point != E(0) and point[0] for point in middle)
target = sum(raw, E(0))
assert target != E(0) and target[0] and middle[1] + middle[2] == target
control = {
    'status': 'PASS_N131_ALL_ALIGNED_CONSTRUCTED_GROUP_CONTROL',
    'curve_id': old['curve_id'], 'original_rotations': old['original_rotations'],
    'aligned_rotations': [0] * 5, 'pair_points': [xy(point) for point in raw],
    'raw_target': xy(target), 'target_reciprocal': enc(1 / target[0]),
    'middle_reciprocals': [enc(1 / point[0]) for point in middle],
    'pairs': old['pairs'], 'distinct_folded_columns': 10,
    'codes': codes, 'source_sha256': sha(SOURCE),
    'runtime_sha256': sha(HERE / 'sage_runtime_info.json'),
    'protocol_sha256': sha(HERE / 'n131_control_protocol.json'),
}
(HERE / 'n131_all_aligned_control.json').write_text(json.dumps(control, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: control[key] for key in ('status', 'raw_target', 'target_reciprocal')}))
