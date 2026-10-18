"""Freeze exact/deferred N41 formulas and check the archived relation assignment."""
import hashlib
import json
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'n131_w20_selector_elimination_v2_20261013'))
import selector
import circuit_n41 as design


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE.parent / 'n41_n131_fivepair_w9_w29_20261017' / name).read_text())


cfg = json.loads((HERE / 'build_protocol.json').read_text())
for name, expected in cfg['sources'].items():
    assert sha(ROOT / name) == expected, name
relation = load('orbit_audit_result.json')
source = load('n41_states.json')
assert relation['status'] == 'PASS_INDEPENDENT_N41_W9_FIVEPAIR_PUBLIC_RELATION'
assert relation['orientation'] == 3 and source['rotations'] == design.ROTATIONS
assert relation['raw_public_point'] == source['target_raw_point']
assert cfg['oriented_point'] == relation['raw_oriented_point']
assert len(relation['pair_rows']) == 5
R = PolynomialRing(GF(2), 't')
t = R.gen()
K = GF(2**41, name='t', modulus=t**41+t**3+1)
E = EllipticCurve(K, [1, 0, 0, 0, 1])


def dec(value):
    return K(R([(value >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


points = []
for slot, row in enumerate(relation['pair_rows']):
    state = source['states'][slot][row['state_id']]
    assert state['masks'] == row['masks']
    assert state['point'] == row['rotated_point']
    assert design.source_valid(state['masks'][0])
    points.append(E(*(dec(value) for value in state['point'])))
target = E(*(dec(value) for value in cfg['oriented_point']))
assert sum(points, E(0)) == target
assert target[0] and enc(1 / target[0]) == design.F.inverse(cfg['oriented_point'][0])
middle_points = [points[0]+points[1],
                 points[0]+points[1]+points[2], points[3]+points[4]]
assert all(point != E(0) and point[0] for point in middle_points)
middle_reciprocals = [enc(1 / point[0]) for point in middle_points]
target_reciprocal = design.F.inverse(cfg['oriented_point'][0])

for variant in ('exact', 'deferred'):
    started = time.monotonic()
    circ, wires, counts = design.build(target_reciprocal,
                                      deferred=(variant == 'deferred'))
    build_seconds = time.monotonic() - started
    assignment = {}

    def bind(bits, value):
        assignment.update({wire: (value >> j) & 1 for j, wire in enumerate(bits)})

    codes = []
    for slot, row in enumerate(relation['pair_rows']):
        mask = row['masks'][0]
        code = sum(((mask >> bit) & 1) << j for j, bit in enumerate(design.BITS))
        codes.append(code)
        bind(wires['mask'][slot], code)
        x = design.F.frob(row['rotated_point'][0],
                          design.N-design.ROTATIONS[slot])
        bind(wires['out'][slot], design.F.inverse(x))
        witness = wires['source_inverse'][slot]
        if witness is not None:
            p = design.F.mul(mask << 1, row['masks'][1] << 1)
            bind(witness, design.F.inverse(p))
    for bits, reciprocal in zip(wires['middle'], middle_reciprocals):
        bind(bits, reciprocal)
    full = selector.old.complete_assignment(circ, assignment)
    checked = selector.old.check_assignment(circ, full)
    assert checked == {'clauses': counts['clauses'],
                       'native_xor_rows': counts['xor_rows']}
    formula = HERE / f'{variant}.xcnf'
    assert not formula.exists()
    circ.write(formula)
    row = {'status': 'PASS_N41_PUBLIC_RELATION_ASSIGNMENT',
           'candidate_id': None, 'curve_id': cfg['curve_id'],
           'variant': variant, 'orientation': relation['orientation'],
           'oriented_point': cfg['oriented_point'],
           'target_reciprocal': target_reciprocal,
           'mask_codes': codes, 'middle_reciprocals': middle_reciprocals,
           'assignment_check': checked, 'counts': counts,
           'formula_bytes': formula.stat().st_size,
           'formula_sha256': sha(formula), 'build_seconds': build_seconds,
           'wall_seconds': time.monotonic()-started,
           'protocol_sha256': sha(HERE / 'build_protocol.json')}
    (HERE / f'build_{variant}_result.json').write_text(
        json.dumps(row, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'variant': variant, 'status': row['status'],
                      'counts': counts, 'wall_seconds': row['wall_seconds']},
                     sort_keys=True))
