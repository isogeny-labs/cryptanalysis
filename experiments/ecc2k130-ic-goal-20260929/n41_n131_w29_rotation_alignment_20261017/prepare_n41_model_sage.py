"""Recover exact reciprocal S3 model wires from the N41 aligned relation."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


source = json.loads((HERE / 'aligned_states.json').read_text())
audit = json.loads((HERE / 'n41_audit_result.json').read_text())
assert audit['status'] == 'PASS_INDEPENDENT_N41_ALIGNED_PUBLIC_RELATION'
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(coefficient) << index
               for index, coefficient in enumerate(value.polynomial().list()))


def halftrace(value):
    return sum((value**(1 << (2 * i)) for i in range(21)), F.zero())


points = []
pairs = []
for slot, sid in enumerate(audit['state_ids']):
    row = source['states'][slot][sid]
    leaves = []
    for mask, sign in zip(row['masks'], row['signs']):
        h = halftrace(dec(mask << 1))
        point = E.lift_x(1 + 1 / h, all=True)[0]
        leaves.append(-point if sign else point)
    pair = leaves[0] + leaves[1]
    assert pair != E(0) and pair[0]
    rotated = E(pair[0]**(1 << source['rotations'][slot]),
                pair[1]**(1 << source['rotations'][slot]))
    assert [enc(rotated[0]), enc(rotated[1])] == row['point']
    points.append(rotated)
    w0, w1 = [dec(mask << 1) for mask in row['masks']]
    product = w0 * w1
    assert product
    pairs.append({'state_id': sid, 'masks': row['masks'], 'signs': row['signs'],
                  'output_reciprocal': enc(1 / pair[0]),
                  'source_inverse_product': enc(1 / product)})

middle = [points[0] + points[1], points[0] + points[1] + points[2],
          points[3] + points[4]]
assert all(point != E(0) and point[0] for point in middle)
target = sum(points, E(0))
assert [enc(target[0]), enc(target[1])] == audit['raw_oriented_point']
assert middle[1] + middle[2] == target
fixture = {'status': 'PASS_ALIGNED_N41_EXACT_S3_MODEL',
           'curve_id': source['curve_id'], 'rotations': source['rotations'],
           'orientation': audit['orientation'], 'raw_oriented_point': audit['raw_oriented_point'],
           'target_reciprocal': enc(1 / target[0]),
           'pairs': pairs,
           'middle_reciprocals': [enc(1 / point[0]) for point in middle],
           'source_sha256': {name: sha(path) for name, path in
                             {'script': Path(__file__), 'audit': HERE / 'n41_audit_result.json',
                              'states': HERE / 'aligned_states.json',
                              'runtime': HERE / 'sage_runtime_info.json'}.items()}}
with (HERE / 'n41_model_fixture.json').open('x') as out:
    json.dump(fixture, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': fixture['status'],
                  'target_reciprocal': fixture['target_reciprocal'],
                  'middle_reciprocals': fixture['middle_reciprocals']}))
