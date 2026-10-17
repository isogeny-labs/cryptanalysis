"""Reconstruct the N41 five-pair orbit hit as a circuit correctness fixture."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_n131_fivepair_w9_w29_20261017'
states_path = SOURCE / 'n41_states.json'
audit_path = SOURCE / 'orbit_audit_result.json'
states = json.loads(states_path.read_text())
audit = json.loads(audit_path.read_text())
assert audit['status'] == 'PASS_INDEPENDENT_N41_W9_FIVEPAIR_PUBLIC_RELATION'
assert audit['orientation'] == 3
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> bit) & 1 for bit in range(41)]))


def enc(value):
    return sum(int(bit) << bit_index
               for bit_index, bit in enumerate(value.polynomial().list()))


def xy(point):
    return [enc(point[0]), enc(point[1])]


def halftrace(value):
    return sum((value**(1 << (2 * bit)) for bit in range(21)), F.zero())


def endpoint(mask, sign):
    w = dec(mask << 1)
    assert w.trace() == 0 and (1 / w).trace() == 0
    h = halftrace(w)
    assert h**2 + h == w and h
    point = E.lift_x(1 + 1 / h, all=True)[0]
    return -point if sign else point


pairs = []
nodes = []
for slot, state_id in enumerate(audit['state_ids']):
    row = states['states'][slot][state_id]
    a, b = row['masks']
    sa, sb = row['signs']
    unrotated = endpoint(a, sa) + endpoint(b, sb)
    assert unrotated != E(0) and unrotated[0]
    rotation = states['rotations'][slot]
    rotated = E(unrotated[0]**(1 << rotation),
                unrotated[1]**(1 << rotation))
    assert xy(rotated) == row['point']
    nodes.append(rotated)
    product = dec(a << 1) * dec(b << 1)
    assert product
    pairs.append({'masks': [a, b], 'signs': [sa, sb],
                  'columns': row['columns'], 'source_product': enc(product),
                  'source_inverse_product': enc(1 / product),
                  'output_reciprocal': enc(1 / unrotated[0])})
assert len({c for row in pairs for c in row['columns']}) == 10
middle = []
for i, j, k in ((0, 1, 5), (5, 2, 6), (3, 4, 7), (6, 7, 8)):
    q = nodes[i] + nodes[j]
    assert q != E(0) and q[0]
    nodes.append(q)
    if k != 8:
        middle.append(enc(1 / q[0]))
target = E(*map(dec, states['target_raw_point']))
oriented = E(target[0]**8, target[1]**8)
assert nodes[-1] == oriented
fixture = {'status': 'COMPLETE_CONSTRUCTED_ORBIT_CONTROL',
           'curve_id': states['curve_id'], 'source_width': 9,
           'seed_mask': states['seed'], 'rotations': states['rotations'],
           'orientation': audit['orientation'], 'pairs': pairs,
           'middle_reciprocals': middle,
           'oriented_raw_point': xy(oriented),
           'oriented_target_reciprocal': enc(1 / oriented[0]),
           'oriented_subgroup_point': xy(4 * oriented),
           'original_raw_point': states['target_raw_point'],
           'original_subgroup_point': audit['subgroup_public_point'],
           'source_sha256': {'states': hashlib.sha256(states_path.read_bytes()).hexdigest(),
                             'orbit_audit': hashlib.sha256(audit_path.read_bytes()).hexdigest(),
                             'script': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}}
with (HERE / 'fixture.json').open('x') as out:
    json.dump(fixture, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': fixture['status'], 'oriented_raw_point': fixture['oriented_raw_point'],
                  'oriented_subgroup_point': fixture['oriented_subgroup_point']}))
