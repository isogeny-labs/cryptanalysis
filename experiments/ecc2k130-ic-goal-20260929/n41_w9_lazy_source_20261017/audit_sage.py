"""Independent checked-Sage group replay of a W9 five-pair SAT model."""
import hashlib
import itertools
import json
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
SEED = 56
ROTATIONS = (0, 6, 12, 18, 24)
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def halftrace(value):
    return sum((value**(1 << (2 * i)) for i in range(21)), F.zero())


def endpoint(mask):
    w = dec(mask << 1)
    assert w and w.trace() == 0 and (1 / w).trace() == 0
    h = halftrace(w)
    assert h and h**2 + h == w
    points = E.lift_x(1 + 1 / h, all=True)
    assert len(points) == 2
    return points


def folded_column(point):
    return min(enc(point[0]**(1 << k)) for k in range(41))


def rotate(point, exponent):
    return E(point[0]**(1 << exponent), point[1]**(1 << exponent))


def main(variant):
    assert variant in ('control', 'exact5', 'exact3', 'table5')
    start = time.monotonic_ns()
    fixture_path = HERE / 'fixture.json'
    fixture = json.loads(fixture_path.read_text())
    if variant == 'control':
        codes = [row['masks'][0] for row in fixture['pairs']]
        outputs = [row['output_reciprocal'] for row in fixture['pairs']]
        input_path = fixture_path
    else:
        input_path = HERE / (variant + '_result.json')
        result = json.loads(input_path.read_text())
        assert result['status'] == 'SAT_MEMBERSHIP_PASS_GROUP_AUDIT_PENDING'
        codes = result['last_model']['mask_values']
        outputs = result['last_model']['output_reciprocals']
    options, columns, rows = [], [], []
    for slot, (a, output, rotation) in enumerate(zip(codes, outputs, ROTATIONS)):
        b = a ^ SEED
        assert 0 < a < b < 1 << 9
        left, right = endpoint(a), endpoint(b)
        ca, cb = folded_column(left[0]), folded_column(right[0])
        columns.extend((ca, cb))
        sums = [p + q for p, q in itertools.product(left, right)]
        matches = [point for point in sums
                   if point != E(0) and point[0] and enc(1 / point[0]) == output]
        options.append([rotate(point, rotation) for point in matches])
        rows.append({'slot': slot, 'masks': [a, b],
                     'folded_columns': [ca, cb],
                     'matching_signed_pair_sums': len(matches)})
    raw = E(*map(dec, fixture['oriented_raw_point']))
    subgroup = E(*map(dec, fixture['oriented_subgroup_point']))
    assert 4 * raw == subgroup
    hits = []
    for choices in itertools.product(*(range(len(slot)) for slot in options)):
        points = [slot[choice] for slot, choice in zip(options, choices)]
        if sum(points, E(0)) == raw:
            hits.append({'choice_indices': choices,
                         'pair_points': [[enc(p[0]), enc(p[1])] for p in points]})
    distinct = len(set(columns)) == 10
    status = ('PASS_INDEPENDENT_W9_CONSTRUCTED_CONTROL'
              if variant == 'control' and hits and distinct else
              'PASS_INDEPENDENT_W9_PUBLIC_RELATION'
              if variant != 'control' and hits and distinct else
              'MODEL_COLUMN_COLLISION' if hits else 'MODEL_GROUP_REPLAY_MISS')
    evidence = {'status': status, 'curve_id': fixture['curve_id'],
                'oriented_raw_target': fixture['oriented_raw_point'],
                'oriented_subgroup_target': fixture['oriented_subgroup_point'],
                'source_rows': rows, 'distinct_columns': len(set(columns)),
                'group_hits': hits,
                'enumerated_signed_combinations': __import__('math').prod(map(len, options)),
                'elapsed_ns': time.monotonic_ns() - start,
                'source_sha256': {'auditor': sha(Path(__file__)),
                                  'input': sha(input_path),
                                  'fixture': sha(fixture_path),
                                  'runtime': sha(HERE / 'sage_runtime_info.json')}}
    path = HERE / (variant + '_audit_result.json')
    with path.open('x') as out:
        json.dump(evidence, out, sort_keys=True, indent=2)
        out.write('\n')
    print(json.dumps({'variant': variant, 'status': status,
                      'group_hits': len(hits),
                      'distinct_columns': len(set(columns))}))


if __name__ == '__main__':
    assert len(sys.argv) == 2
    main(sys.argv[1])
