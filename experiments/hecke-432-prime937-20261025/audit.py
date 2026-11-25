"""Audit the zero noncuspidal source count at p=937."""
import json
from collections import Counter
from hashlib import sha256
from math import gcd
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = 937


def read(name):
    return json.loads((HERE / name).read_text())


def phi(n):
    return sum(gcd(k, n) == 1 for k in range(1, n + 1))


def curve_order(b):
    squares = Counter(y*y % P for y in range(P))
    return 1 + sum(squares[(x*x*x + b) % P] for x in range(P))


def main():
    protocol = read('protocol.json')
    census = read('census.json')
    projection = read('image.json')
    assert protocol['status'] == 'FROZEN_BEFORE_SOURCE_AND_PROJECTION_EVALUATION'
    assert protocol['prime'] == census['prime'] == projection['prime'] == P
    assert sha256((HERE / 'intermediate_j.json').read_bytes()).hexdigest() == \
        protocol['intermediate_map_sha256']
    assert census['j_values_scanned'] == P
    assert census['rows_with_chains'] == len(census['rows']) == 0
    assert census['paired_chain_count'] == 0
    assert projection['status'] == 'COMPLETE_F937_E_PROJECTION'
    assert projection['row_count'] == len(projection['rows']) == 0

    cusps = sum(phi(gcd(d, 432 // d)) for d in range(1, 433)
                if 432 % d == 0 and (P - 1) % gcd(d, 432 // d) == 0)
    assert cusps == 36
    assert census['X0_point_count_from_Hecke'] == P + 1 - census['Hecke_trace'] == 36
    assert census['X0_point_count_from_Hecke'] - cusps == 0
    b_order = curve_order(-16)
    e_order = curve_order(432)
    assert b_order == e_order == 999
    rational_dual_kernel_size = 1 + sum(y*y % P == (-16) % P for y in range(P))
    assert rational_dual_kernel_size == 3

    out = {
        'status': 'PASS_F937_ZERO_SOURCE_AUDIT',
        'prime': P,
        'X0_rational_points': 36,
        'rational_cusps': cusps,
        'noncuspidal_source_points': 0,
        'E_projection_rows': 0,
        'B_group_order': b_order,
        'E_group_order': e_order,
        'rational_dual_kernel_size': rational_dual_kernel_size,
        'whole_curve_B_images': 1,
        'B_points_outside_whole_curve_image': b_order - 1,
    }
    (HERE / 'audit.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
