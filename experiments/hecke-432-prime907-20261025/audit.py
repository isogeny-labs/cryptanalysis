"""Independently audit the F907 level-432 source and image census."""
import json
from collections import Counter
from math import gcd
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = 907


def read(name):
    return json.loads((HERE / name).read_text())


def phi(n):
    return sum(gcd(k, n) == 1 for k in range(1, n + 1))


def main():
    census = read('census.json')
    image = read('image.json')
    intermediate = read('intermediate_j.json')
    assert census['prime'] == image['prime'] == P
    assert census['j_values_scanned'] == P
    assert image['status'] == 'COMPLETE_F907_KERNEL_IMAGE'
    assert all(intermediate[f'j{k}']['training_nullity'] == 1
               and intermediate[f'j{k}']['holdout_zero'] for k in (3, 9))

    expected = [(tuple(row['curve_ainvs']), (i, j))
                for row in census['rows']
                for i in range(len(row['two_paths']))
                for j in range(len(row['three_paths']))]
    actual = [(tuple(row['source_ainvs']), tuple(row['pair']))
              for row in image['rows']]
    assert actual == expected and len(set(actual)) == len(actual)
    assert len(actual) == census['paired_chain_count'] == image['row_count']
    assert census['generic_twist_parity_checks'] == census['rows_with_chains']

    cusps = sum(phi(gcd(d, 432 // d)) for d in range(1, 433)
                if 432 % d == 0 and (P - 1) % gcd(d, 432 // d) == 0)
    assert census['X0_point_count_from_Hecke'] - cusps == len(actual)

    assert all(row['intermediate_filtered_counts'] == [1, 1]
               and row['frobenius_pair_count'] == 1
               and len(row['B_candidates']) == 1 for row in image['rows'])
    fibers = Counter(tuple(row['B_candidates'][0]) if row['B_candidates'][0] is not None
                     else None for row in image['rows'])
    assert all(point is None or (point[1]**2 - point[0]**3 + 16) % P == 0
               for point in fibers)
    histogram = Counter(fibers.values())
    assert sum(size * count for size, count in histogram.items()) == len(actual)

    squares = Counter(y * y % P for y in range(P))
    b_order = 1 + sum(squares[(x*x*x - 16) % P] for x in range(P))
    assert b_order == 889
    full_image = set(fibers) | {None}
    out = {
        'status': 'PASS_F907_IMAGE_AUDIT',
        'prime': P,
        'X0_rational_points': census['X0_point_count_from_Hecke'],
        'rational_cusps': cusps,
        'noncuspidal_source_points': len(actual),
        'B_group_order': b_order,
        'noncuspidal_B_images': len(fibers),
        'identity_in_noncuspidal_image': None in fibers,
        'whole_curve_B_images': len(full_image),
        'B_points_outside_whole_curve_image': b_order - len(full_image),
        'fiber_size_distribution': {str(k): v for k, v in sorted(histogram.items())},
        'coordinate_candidate_count_distribution': {
            str(key): value for key, value in Counter(
                tuple(row['coordinate_counts']) for row in image['rows']).items()},
    }
    (HERE / 'audit.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
