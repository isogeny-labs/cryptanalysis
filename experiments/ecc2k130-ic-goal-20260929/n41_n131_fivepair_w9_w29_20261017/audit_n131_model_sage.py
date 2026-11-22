"""Independent checked-Sage replay for a W29 five-pair SAT model or control."""
import hashlib
import itertools
import json
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
SEED = 898618
ROTATIONS = (0, 18, 36, 54, 72)
ORDER = 680564733841876926932320129493409985129


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(mode):
    assert mode in ('control', 'model')
    start = time.monotonic_ns()
    protocol = json.loads((HERE / 'n131_query_protocol.json').read_text())
    if mode == 'control':
        source = json.loads((HERE / 'n131_control.json').read_text())
        codes = [row['masks'][0] for row in source['pairs']]
        outputs = [row['output_reciprocal'] for row in source['pairs']]
        raw_xy, subgroup_xy = source['target_raw_point'], source['subgroup_point']
        input_path = HERE / 'n131_control.json'
    else:
        result = json.loads((HERE / 'n131_query_result.json').read_text())
        assert result['status'] == 'SAT_PENDING_GROUP_REPLAY'
        source = json.loads((HERE / 'n131_decoded_model.json').read_text())
        codes = source['mask_codes']
        outputs = source['unrotated_pair_standard_reciprocals']
        raw_xy, subgroup_xy = protocol['raw_point'], protocol['public_target']
        input_path = HERE / 'n131_decoded_model.json'
    R = PolynomialRing(GF(2), 'u')
    u = R.gen()
    F = GF(2**131, name='u', modulus=u**131 + u**13 + u**2 + u + 1)
    E = EllipticCurve(F, [1, 0, 0, 0, 1])

    def dec(word):
        return F(R([(int(word) >> i) & 1 for i in range(131)]))

    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

    def halftrace(value):
        result = F.zero()
        current = value
        for _ in range(66):
            result += current
            current = current**4
        assert result**2 + result == value
        return result

    def endpoint(mask):
        w = dec(mask << 1)
        assert w and w.trace() == 0 and (1 / w).trace() == 0
        x = 1 + 1 / halftrace(w)
        points = E.lift_x(x, all=True)
        assert len(points) == 2
        assert all(ORDER * (4 * point) == E(0) for point in points)
        return points

    def folded_column(point):
        return min(enc(point[0]**(1 << k)) for k in range(131))

    def rotate(point, exponent):
        return E(point[0]**(1 << exponent), point[1]**(1 << exponent))

    assert len(codes) == len(outputs) == 5
    options, columns, rows = [], [], []
    for slot, (a, output, rotation) in enumerate(zip(codes, outputs, ROTATIONS)):
        b = a ^ SEED
        assert 0 < a < b < (1 << 29)
        left, right = endpoint(a), endpoint(b)
        ca, cb = folded_column(left[0]), folded_column(right[0])
        columns.extend((ca, cb))
        sums = [p + q for p, q in itertools.product(left, right)]
        matches = [p for p in sums if p != E(0) and p[0]
                   and enc(1 / p[0]) == output]
        options.append([rotate(p, rotation) for p in matches])
        rows.append({'slot': slot, 'masks': [a, b], 'folded_columns': [ca, cb],
                     'standard_reciprocal': output,
                     'matching_signed_pair_sums': len(matches)})
    raw = E(*map(dec, raw_xy))
    subgroup = E(*map(dec, subgroup_xy))
    assert 4 * raw == subgroup
    hits = []
    if all(options):
        for choices in itertools.product(*(range(len(slot)) for slot in options)):
            points = [slot[choice] for slot, choice in zip(options, choices)]
            if sum(points, E(0)) == raw:
                hits.append({'choice_indices': choices,
                             'pair_points': [[enc(p[0]), enc(p[1])] for p in points]})
    distinct = len(set(columns)) == 10
    status = ('PASS_INDEPENDENT_W29_FIVEPAIR_CONSTRUCTED_CONTROL'
              if mode == 'control' and hits and distinct else
              'PASS_INDEPENDENT_W29_FIVEPAIR_ORDINARY_RELATION'
              if mode == 'model' and hits and distinct else
              'MODEL_COLUMN_COLLISION' if hits else 'MODEL_GROUP_REPLAY_MISS')
    result = {'status': status, 'curve_id': protocol['curve_id'],
              'raw_target': raw_xy, 'subgroup_target': subgroup_xy,
              'source_rows': rows, 'distinct_columns': len(set(columns)),
              'group_hits': hits,
              'enumerated_signed_combinations': __import__('math').prod(map(len, options)),
              'elapsed_ns': time.monotonic_ns() - start,
              'source_sha256': {'auditor': sha(Path(__file__)),
                                'protocol': sha(HERE / 'n131_query_protocol.json'),
                                'input': sha(input_path),
                                'runtime': sha(HERE / 'sage_runtime_info.json')}}
    path = HERE / ('n131_model_control_result.json' if mode == 'control'
                   else 'n131_model_audit_result.json')
    with path.open('x') as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write('\n')
    print(json.dumps({'status': status, 'group_hits': len(hits),
                      'distinct_columns': result['distinct_columns']}))


if __name__ == '__main__':
    assert len(sys.argv) == 2
    main(sys.argv[1])
