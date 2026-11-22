"""Independently replay an N41 W11 SAT model as ten signed source points."""
import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
query = json.loads((HERE / 'n41_query_result.json').read_text())
assert query['status'] == 'SAT_MODEL_UNVERIFIED'
wires = json.loads((HERE / 'n41_input_wires.json').read_text())
P = PolynomialRing(GF(2), 'u')
u = P.gen()
K = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(K, [1, 0, 0, 0, 1])


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def field(word):
    return K(P([(int(word) >> i) & 1 for i in range(41)]))


def packed(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def xy(point):
    return [packed(point[0]), packed(point[1])]


def halftrace(value):
    out, current = K.zero(), value
    for _ in range(21):
        out += current
        current = current**4
    assert out*out + out == value
    return out


def mask_for(code):
    return sum(((code >> i) & 1) << bit
               for i, bit in enumerate(wires['source_bits']))


def source_points(mask):
    w = field(mask << 1)
    assert w and w.trace() == 0 and (~w).trace() == 0
    h = halftrace(w)
    assert h
    x = K.one() + ~h
    points = E.lift_x(x, all=True)
    assert len(points) == 2
    return points


def orbit_id(mask):
    w = field(mask << 1)
    values = []
    for _ in range(41):
        values.append(packed(w))
        w *= w
    return min(values)


assignment = {}
for line in (HERE / 'n41_solver.stdout').read_text().splitlines():
    if line.startswith('v '):
        for literal in map(int, line.split()[1:]):
            if literal:
                assignment[abs(literal)] = int(literal > 0)
needed = [wire for group in wires['mask'] + wires['out'] for wire in group]
assert all(wire in assignment for wire in needed)


def decode(group):
    return sum(assignment[wire] << i for i, wire in enumerate(group))


codes = [decode(row) for row in wires['mask']]
outroots = [decode(row) for row in wires['out']]
masks = [mask_for(code) for code in codes]
endpoints = [(mask, mask ^ 56) for mask in masks]
orbit_ids = [orbit_id(mask) for pair in endpoints for mask in pair]
options = []
for slot, ((a_mask, b_mask), root) in enumerate(zip(endpoints, outroots)):
    pair_options = []
    for left, right in itertools.product(source_points(a_mask),
                                         source_points(b_mask)):
        pair = left + right
        if pair != E(0) and pair[0] and packed(1 / pair[0]) == root:
            rotation = wires['rotations'][slot]
            pair_options.append((left, right,
                                 E(pair[0]**(1 << rotation),
                                   pair[1]**(1 << rotation))))
    options.append(pair_options)
target = E(*map(field, wires['raw_oriented_point']))
matches = []
if all(options):
    for choice in itertools.product(*options):
        total = sum((row[2] for row in choice), E(0))
        if total == target:
            matches.append((choice, 1))
        elif total == -target:
            matches.append((choice, -1))
status = ('PASS_N41_W11_INDEPENDENT_PUBLIC_RELATION'
          if matches and len(set(orbit_ids)) == 10 else
          'SAT_MODEL_REJECTED_BY_INDEPENDENT_GROUP_REPLAY')
selected = None
if matches:
    selected, orientation = matches[0]
    if orientation == -1:
        selected = tuple((-a, -b, -pair) for a, b, pair in selected)
    assert sum((row[2] for row in selected), E(0)) == target
result = {'status': status, 'candidate_id': None,
          'curve_id': query['curve_id'],
          'codes': codes, 'masks': masks,
          'endpoint_masks': [list(pair) for pair in endpoints],
          'folded_orbit_ids': orbit_ids,
          'distinct_folded_columns': len(set(orbit_ids)),
          'outroot_words': outroots,
          'pair_sign_options': [len(row) for row in options],
          'matching_group_sign_choices': len(matches),
          'selected_source_points':
              [[xy(a), xy(b)] for a, b, _ in selected] if selected else None,
          'selected_pair_points': [xy(pair) for _, _, pair in selected] if selected else None,
          'raw_target': xy(target),
          'subgroup_target': xy(4*target),
          'query_result_sha256': sha(HERE / 'n41_query_result.json'),
          'solver_stdout_sha256': sha(HERE / 'n41_solver.stdout'),
          'source_sha256': sha(Path(__file__))}
out = HERE / 'n41_group_replay.json'
assert not out.exists()
out.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: result[key] for key in
                  ('status', 'distinct_folded_columns',
                   'matching_group_sign_choices', 'raw_target')}, sort_keys=True))
