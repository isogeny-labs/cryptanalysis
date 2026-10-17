#!/usr/bin/env sage -python
"""Independently replay an optional W23 SAT model in the binary curve group."""
import hashlib
import itertools
import json
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

BASE = Path(__file__).resolve().parent
SOURCE = BASE.parent / 'n131_w23_sixpair_shared_circuit_20261017'
R = 680564733841876926932320129493409985129
SEED = 898618
ROTATIONS = (0, 18, 36, 54, 72, 90)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(mode):
    assert mode in ('control', 'model')
    start = time.monotonic_ns()
    protocol = json.loads((BASE / 'protocol.json').read_text())
    if mode == 'control':
        fixture = json.loads((SOURCE / 'fixture.json').read_text())
        codes = [row['masks'][0] for row in fixture['pairs']]
        outputs = [row['output_reciprocal'] for row in fixture['pairs']]
        raw_coordinates = fixture['target_raw_point']
        subgroup_coordinates = fixture['subgroup_point']
    else:
        result = json.loads((BASE / 'result.json').read_text())
        model = json.loads((BASE / 'decoded_model.json').read_text())
        assert result['status'] == 'SAT_PENDING_GROUP_REPLAY'
        codes = model['mask_codes']
        outputs = model['unrotated_pair_standard_reciprocals']
        raw_coordinates = protocol['raw_point']
        subgroup_coordinates = protocol['public_target']
    poly = PolynomialRing(GF(2), 't')
    t = poly.gen()
    field = GF(2**131, name='t', modulus=t**131 + t**13 + t**2 + t + 1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def dec(value):
        return field(poly([int(value >> i & 1) for i in range(131)]))

    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

    def halftrace(value):
        output = field.zero()
        term = value
        for _ in range(66):
            output += term
            term = term**4
        assert output**2 + output == value
        return output

    def canonical(mask):
        value = dec(mask << 1)
        answer = mask
        for _ in range(131):
            encoded = enc(value)
            if encoded and not (encoded & 1) and encoded < (1 << 24):
                answer = min(answer, encoded >> 1)
            value = value**2
        assert value == dec(mask << 1)
        return answer

    def endpoint_points(mask):
        w = dec(mask << 1)
        assert w and w.trace() == 0 and (1/w).trace() == 0
        u = halftrace(w)
        x = 1 + 1/u
        points = curve.lift_x(x, all=True)
        assert len(points) == 2
        assert all(R*(4*point) == curve(0) for point in points)
        return points

    def frob_point(point, exponent):
        if point == curve(0):
            return point
        power = 1 << exponent
        return curve(point[0]**power, point[1]**power)

    assert len(codes) == len(outputs) == 6
    pair_options = []
    columns = []
    rows = []
    for slot, (a, output, rotation) in enumerate(zip(codes, outputs, ROTATIONS)):
        b = a ^ SEED
        assert 0 < a < 1 << 23 and 0 < b < 1 << 23
        ca, cb = canonical(a), canonical(b)
        columns.extend((ca, cb))
        left, right = endpoint_points(a), endpoint_points(b)
        all_sums = [p+q for p, q in itertools.product(left, right)]
        matches = [point for point in all_sums if point != curve(0)
                   and point[0] and enc(1/point[0]) == output]
        pair_options.append([frob_point(point, rotation) for point in matches])
        rows.append({'slot': slot, 'masks': [a, b], 'columns': [ca, cb],
                     'standard_reciprocal': output,
                     'matching_signed_pair_sums': len(matches)})
    raw = curve(dec(raw_coordinates[0]), dec(raw_coordinates[1]))
    public = curve(dec(subgroup_coordinates[0]), dec(subgroup_coordinates[1]))
    assert 4*raw == public
    hits = []
    if all(pair_options):
        for selection in itertools.product(*(range(len(options)) for options in pair_options)):
            points = [options[index] for options, index in zip(pair_options, selection)]
            total = sum(points, curve(0))
            if total == raw:
                hits.append({'choice_indices': list(selection),
                             'pair_points': [[enc(point[0]), enc(point[1])]
                                             for point in points]})
    distinct = len(set(columns)) == 12
    status = ('PASS_INDEPENDENT_W23_CONSTRUCTED_MODEL_CONTROL' if
              mode == 'control' and hits and distinct else
              'PASS_INDEPENDENT_W23_ORDINARY_RELATION' if hits and distinct else
              'MODEL_COLUMN_COLLISION' if hits else
              'MODEL_GROUP_REPLAY_MISS')
    output = {'status': status, 'curve_id': protocol['curve_id'],
              'public_target': subgroup_coordinates,
              'raw_point': raw_coordinates,
              'source_rows': rows, 'distinct_columns': len(set(columns)),
              'group_hits': hits, 'enumerated_signed_combinations':
              __import__('math').prod(map(len, pair_options)),
              'elapsed_ns': time.monotonic_ns()-start,
              'source_sha256': {'script': sha(Path(__file__)),
                                'protocol': sha(BASE / 'protocol.json'),
                                'input': sha(SOURCE / 'fixture.json') if mode == 'control'
                                else sha(BASE / 'decoded_model.json'),
                                'runtime': sha(BASE / 'sage_runtime_info.json')}}
    with (BASE / ('model_control_result.json' if mode == 'control'
                  else 'model_audit_result.json')).open('x') as out:
        json.dump(output, out, sort_keys=True, indent=2)
        out.write('\n')
    print(status, len(hits), distinct)


if __name__ == '__main__':
    assert len(sys.argv) == 2
    main(sys.argv[1])
