"""Transport the audited W29 constructed pair points to aligned rotations."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_n131_fivepair_w9_w29_20261017/n131_control_3p2.json'
AUDIT = ROOT / 'n41_n131_trace_parity_20261017/n131_trace_model_control_result.json'
ORIGINAL = [0, 18, 36, 54, 72]
ALIGNED = [0, 0, 36, 36, 72]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


source = json.loads(PRIOR.read_text())
audit = json.loads(AUDIT.read_text())
assert source['rotations'] == ORIGINAL
assert audit['status'] == 'PASS_INDEPENDENT_W29_FIVEPAIR_CONSTRUCTED_CONTROL'
assert audit['group_hits'][0]['choice_indices'] == [0] * 5
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**131, name='u', modulus=u**131 + u**13 + u**2 + u + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(131)]))


def enc(value):
    return sum(int(coefficient) << index
               for index, coefficient in enumerate(value.polynomial().list()))


def xy(point):
    return [enc(point[0]), enc(point[1])]


def frob(point, count):
    return E(point[0]**(1 << count), point[1]**(1 << count))


original = [E(*map(dec, coords)) for coords in audit['group_hits'][0]['pair_points']]
assert xy(sum(original, E(0))) == source['target_raw_point']
aligned = []
for slot, (point, old_rotation, new_rotation) in enumerate(zip(original, ORIGINAL, ALIGNED)):
    raw = frob(point, (131 - old_rotation) % 131)
    assert enc(1 / raw[0]) == source['pairs'][slot]['output_reciprocal']
    aligned.append(frob(raw, new_rotation))
    assert aligned[-1][0]
middle = [aligned[0] + aligned[1],
          aligned[0] + aligned[1] + aligned[2],
          aligned[3] + aligned[4]]
assert all(point != E(0) and point[0] for point in middle)
target = sum(aligned, E(0))
assert target != E(0) and target[0] and middle[1] + middle[2] == target
control = {'status': 'PASS_N131_ALIGNED_CONSTRUCTED_GROUP_CONTROL',
           'curve_id': source['curve_id'],
           'original_rotations': ORIGINAL, 'aligned_rotations': ALIGNED,
           'raw_target': xy(target), 'target_reciprocal': enc(1 / target[0]),
           'rotated_pair_points': [xy(point) for point in aligned],
           'middle_reciprocals': [enc(1 / point[0]) for point in middle],
           'pairs': source['pairs'],
           'distinct_folded_columns': audit['distinct_columns'],
           'source_sha256': {name: sha(path) for name, path in
                             {'script': Path(__file__), 'source_control': PRIOR,
                              'audited_pair_points': AUDIT,
                              'runtime': HERE / 'sage_runtime_info.json'}.items()}}
with (HERE / 'n131_aligned_control.json').open('x') as out:
    json.dump(control, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({key: control[key] for key in
                  ('status', 'raw_target', 'target_reciprocal', 'middle_reciprocals')}))
