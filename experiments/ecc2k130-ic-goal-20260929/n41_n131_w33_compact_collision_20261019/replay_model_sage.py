"""Independently replay an all-aligned W33 five-pair witness in Sage's curve group."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
parser = argparse.ArgumentParser()
parser.add_argument('--control', action='store_true')
args = parser.parse_args()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


P = PolynomialRing(GF(2), 'u')
u = P.gen()
K = GF(2**131, name='u', modulus=u**131 + u**13 + u**2 + u + 1)
E = EllipticCurve(K, [1, 0, 0, 0, 1])
BITS = [bit for bit in range(33) if bit != (898618).bit_length() - 1]
ROTATIONS = [0, 0, 0, 0, 0]


def field(word):
    return K(P([(int(word) >> i) & 1 for i in range(131)]))


def packed(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def xy(point):
    return [packed(point[0]), packed(point[1])]


def halftrace(value):
    out = K.zero()
    power = value
    for _ in range(66):
        out += power
        power = power**4
    assert out*out + out == value
    return out


def mask_for(code):
    return sum(((code >> i) & 1) << bit for i, bit in enumerate(BITS))


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
    for _ in range(131):
        values.append(packed(w))
        w *= w
    return min(values)


def rotated(point, power):
    return E(point[0]**(1 << power), point[1]**(1 << power))


def replay(codes, outroots, raw_target):
    assert len(codes) == len(outroots) == 5
    masks = [mask_for(code) for code in codes]
    assert all(a < b for a, b in zip(codes, codes[1:]))
    endpoints = [(mask, mask ^ 898618) for mask in masks]
    orbit_ids = [orbit_id(mask) for pair in endpoints for mask in pair]
    assert len(set(orbit_ids)) == 10
    options = []
    for slot, ((a_mask, b_mask), root) in enumerate(zip(endpoints, outroots)):
        candidates = []
        for left, right in itertools.product(source_points(a_mask),
                                             source_points(b_mask)):
            pair = left + right
            if pair != E(0) and pair[0] and packed(1 / pair[0]) == root:
                candidates.append((left, right, rotated(pair, ROTATIONS[slot])))
        assert candidates, (slot, a_mask, b_mask, root)
        options.append(candidates)
    target = E(*map(field, raw_target))
    assert target and target[0]
    matches = []
    for choice in itertools.product(*options):
        total = sum((row[2] for row in choice), E(0))
        if total == target:
            matches.append((choice, 1))
        elif total == -target:
            matches.append((choice, -1))
    assert matches
    selected, orientation = matches[0]
    if orientation == -1:
        selected = tuple((-a, -b, -(pair)) for a, b, pair in selected)
    assert sum((row[2] for row in selected), E(0)) == target
    return {
        'codes': codes,
        'masks': masks,
        'endpoint_masks': [list(pair) for pair in endpoints],
        'folded_orbit_ids': orbit_ids,
        'outroot_words': outroots,
        'pair_sign_options': [len(row) for row in options],
        'matching_group_sign_choices': len(matches),
        'selected_pair_points': [xy(row[2]) for row in selected],
        'selected_source_points': [[xy(row[0]), xy(row[1])] for row in selected],
        'raw_target': xy(target),
        'subgroup_target': xy(4*target),
    }


if args.control:
    protocol = json.loads((HERE / 'control_protocol.json').read_text())
    assert protocol['script_sha256'] == sha(__file__)
    for path,digest in protocol['sources'].items():
        assert sha(path) == digest,path
    control = json.loads(Path(protocol['constructed_control']).read_text())
    codes = [sum(((row['masks'][0] >> bit) & 1) << index
                 for index, bit in enumerate(BITS)) for row in control['pairs']]
    outroots = [row['output_reciprocal'] for row in control['pairs']]
    data = replay(codes, outroots, control['raw_target'])
    assert data['subgroup_target'] == xy(4*E(*map(field, control['raw_target'])))
    data.update({'status': 'PASS_W33_CONSTRUCTED_INDEPENDENT_GROUP_REPLAY',
                 'source_sha256': sha(Path(__file__)),
                 'control_sha256': sha(protocol['constructed_control']),
                 'protocol_sha256':sha(HERE/'control_protocol.json')})
    out = HERE / 'control_replay.json'
else:
    query = json.loads((HERE / 'query_result.json').read_text())
    assert query['status'] == 'SAT_MODEL_UNVERIFIED'
    wires = json.loads((HERE / 'input_wires.json').read_text())
    assigned = {}
    for line in (HERE / 'solver.stdout').read_text().splitlines():
        if line.startswith('v '):
            for literal in map(int, line.split()[1:]):
                if literal:
                    assigned[abs(literal)] = int(literal > 0)
    needed = [wire for group in wires['mask'] + wires['out'] for wire in group]
    assert all(wire in assigned for wire in needed)
    def decode(group):
        return sum(assigned[wire] << i for i, wire in enumerate(group))
    codes = [decode(row) for row in wires['mask']]
    outroots = [decode(row) for row in wires['out']]
    data = replay(codes, outroots, wires['public_raw_point'])
    public = json.loads((ROOT / 'n131_w23_sixpair_public_sat_20261017' /
                         'protocol.json').read_text())
    assert data['subgroup_target'] == public['public_target']
    data.update({'status': 'PASS_PUBLIC_INDEPENDENT_GROUP_RELATION',
                 'query_result_sha256': sha(HERE / 'query_result.json'),
                 'solver_stdout_sha256': sha(HERE / 'solver.stdout'),
                 'source_sha256': sha(Path(__file__))})
    out = HERE / 'public_group_replay.json'
assert not out.exists()
out.write_text(json.dumps(data, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: data[key] for key in
                  ('status', 'matching_group_sign_choices', 'subgroup_target')},
                 sort_keys=True))
