"""Audit F997 source, E projection, rational B cosets, and degree bounds."""
import json
from collections import Counter
from hashlib import sha256
from math import gcd
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = 997


def read(name):
    return json.loads((HERE / name).read_text())


def phi(n):
    return sum(gcd(k, n) == 1 for k in range(1, n + 1))


def curve_order(b):
    squares = Counter(y*y % P for y in range(P))
    return 1 + sum(squares[(x*x*x + b) % P] for x in range(P))


def dual_image(point):
    if point is None or point[0] == 0:
        return None
    x, y = point
    inv_x = pow(x, -1, P)
    return (((x**3 - 64) * inv_x**2) % P,
            (y * (x**3 + 128) * inv_x**3) % P)


def main():
    protocol = read('protocol.json')
    census = read('census.json')
    projection = read('image.json')
    screen = read('../hecke-432-prime937-20261025/screen_result.json')
    assert protocol['status'] == 'FROZEN_BEFORE_SOURCE_AND_PROJECTION_EVALUATION'
    assert protocol['prime'] == census['prime'] == projection['prime'] == P
    assert screen['selected_prime'] == P
    assert sha256((HERE / 'intermediate_j.json').read_bytes()).hexdigest() == \
        protocol['intermediate_map_sha256']
    assert census['j_values_scanned'] == P
    assert projection['status'] == 'COMPLETE_F997_E_PROJECTION'
    expected = [(tuple(row['curve_ainvs']), (i, j))
                for row in census['rows']
                for i in range(len(row['two_paths']))
                for j in range(len(row['three_paths']))]
    actual = [(tuple(row['source_ainvs']), tuple(row['pair']))
              for row in projection['rows']]
    assert actual == expected and len(set(actual)) == len(actual)
    assert len(actual) == census['paired_chain_count'] == projection['row_count']
    assert census['generic_twist_parity_checks'] == census['rows_with_chains']

    cusps = sum(phi(gcd(d, 432 // d)) for d in range(1, 433)
                if 432 % d == 0 and (P - 1) % gcd(d, 432 // d) == 0)
    assert census['X0_point_count_from_Hecke'] - cusps == len(actual)
    assert [census['X0_point_count_from_Hecke'], cusps, len(actual)] == [
        screen['screened'][-1][key] for key in
        ('X0_points', 'rational_cusps', 'noncuspidal_points')]
    b_order, e_order = curve_order(-16), curve_order(432)
    assert b_order == e_order == 1008
    assert 1 + sum(y*y % P == (-16) % P for y in range(P)) == 3

    fibers = Counter()
    cosets = {}
    for row in projection['rows']:
        assert row['intermediate_filtered_counts'] == [1, 1]
        assert row['frobenius_pair_count'] == 1
        assert len(row['projections']) == 1
        value = row['projections'][0]
        h = None if value['E_point'] is None else tuple(value['E_point'])
        if h is not None:
            assert (h[1]**2 - h[0]**3 - 432) % P == 0
        bpoints = tuple(None if q is None else tuple(q)
                        for q in value['B_preimages'])
        assert len(bpoints) == len(set(bpoints)) == 3
        for q in bpoints:
            if q is not None:
                assert (q[1]**2 - q[0]**3 + 16) % P == 0
            assert dual_image(q) == h
        if h in cosets:
            assert cosets[h] == bpoints
        else:
            cosets[h] = bpoints
        fibers[h] += 1

    histogram = Counter(fibers.values())
    assert sum(size * count for size, count in histogram.items()) == len(actual)
    assert all(size <= 72 for size in fibers.values())
    lower_b_images = sum((size + 23) // 24 for size in fibers.values())
    upper_b_images = sum(min(3, size) for size in fibers.values())
    all_saturated = all(size == 72 for size in fibers.values())
    if all_saturated:
        assert lower_b_images == upper_b_images == 3 * len(fibers)
        full_b_images = lower_b_images + (0 if None in fibers else 1)
    else:
        full_b_images = None
    assert any(size == 12 for size in fibers.values())
    assert None not in fibers
    full_b_lower, full_b_upper = lower_b_images + 1, upper_b_images + 1

    out = {
        'status': 'PASS_F997_E_PROJECTION_AUDIT',
        'prime': P,
        'X0_rational_points': census['X0_point_count_from_Hecke'],
        'rational_cusps': cusps,
        'noncuspidal_source_points': len(actual),
        'B_group_order': b_order,
        'E_group_order': e_order,
        'rational_dual_kernel_size': 3,
        'E_projection_images': len(fibers),
        'E_projection_fiber_size_distribution': {
            str(k): v for k, v in sorted(histogram.items())},
        'identity_in_noncuspidal_E_image': None in fibers,
        'noncuspidal_B_image_lower_bound': lower_b_images,
        'noncuspidal_B_image_upper_bound': upper_b_images,
        'full_B_image_lower_bound': full_b_lower,
        'full_B_image_upper_bound': full_b_upper,
        'B_points_outside_full_image_lower_bound': b_order - full_b_upper,
        'B_points_outside_full_image_upper_bound': b_order - full_b_lower,
        'uniform_24_point_B_fibers_ruled_out': True,
        'all_projected_fibers_saturate_degree_bound': all_saturated,
        'full_B_image_if_forced': full_b_images,
        'B_points_outside_full_image_if_forced':
            None if full_b_images is None else b_order - full_b_images,
    }
    (HERE / 'audit.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
