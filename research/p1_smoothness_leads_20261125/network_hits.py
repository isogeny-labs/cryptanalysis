"""Exact two-summand hit census under NETWORK_PROTOCOL.md.

Run: sage -python research/p1_smoothness_leads_20261125/network_hits.py
"""

import json
from fractions import Fraction
from itertools import combinations

from sage.all import EllipticCurve, GF


PRIME = 10007
ORDER = 10193
BOUND = 20
DEGREES = (2, 3, 5, 7, 11, 13, 17, 19)


def bounded_points(curve, field):
    return {
        point
        for x_integer in range(BOUND)
        for point in curve.lift_x(field(x_integer), all=True)
    }


def hit_set(points):
    return {p + q for p in points for q in points}


def census(sets, order):
    hit_sets = [hit_set(base) for base in sets]
    base_union = set().union(*sets)
    hit_union = set().union(*hit_sets)
    largest = max(map(len, hit_sets))
    survival = Fraction(1, 1)
    for hits in hit_sets:
        survival *= Fraction(order - len(hits), order)
    independent = 1 - survival
    return {
        "factor_base_sizes": [len(s) for s in sets],
        "factor_base_sum": sum(map(len, sets)),
        "factor_base_union": len(base_union),
        "factor_base_pairwise_overlaps": [
            len(sets[i] & sets[j]) for i, j in combinations(range(len(sets)), 2)
        ],
        "hit_sizes": [len(s) for s in hit_sets],
        "hit_union": len(hit_union),
        "hit_pairwise_overlaps": [
            len(hit_sets[i] & hit_sets[j])
            for i, j in combinations(range(len(hit_sets)), 2)
        ],
        "union_to_largest_hit_ratio": round(len(hit_union) / largest, 9),
        "independent_hit_probability": round(float(independent), 9),
        "actual_hit_probability": round(len(hit_union) / order, 9),
    }


def main():
    field = GF(PRIME)
    curve = EllipticCurve(field, [-3, 7])
    assert int(curve.order()) == ORDER and curve.order().is_prime()
    network = [
        (degree, phi)
        for degree in DEGREES
        for phi in curve.isogenies_prime_degree(degree)
    ]
    assert [degree for degree, _ in network] == [7, 11, 11, 19, 19]

    reference = bounded_points(curve, field)
    pulled_bases = []
    for degree, phi in network:
        points = bounded_points(phi.codomain(), field)
        inv_degree = pow(degree, -1, ORDER)
        pulled = {inv_degree * phi.dual()(q) for q in points}
        assert len(pulled) == len(points)
        assert all(phi(p) in points for p in pulled)
        pulled_bases.append(pulled)

    # Independently verify the exact shared-base construction's null gain.
    reference_hits = hit_set(reference)
    for _, phi in network:
        mapped = {phi(p) for p in reference}
        assert len(mapped) == len(reference)
        assert {phi(p) for p in reference_hits} == hit_set(mapped)

    result = {
        "field_prime": PRIME,
        "curve_a4_a6": [-3, 7],
        "curve_order": ORDER,
        "coordinate_bound": BOUND,
        "summands": 2,
        "network_degrees": [degree for degree, _ in network],
        "reference_base_size": len(reference),
        "reference_hit_size": len(reference_hits),
        "network_only": census(pulled_bases, ORDER),
        "base_plus_network": census([reference, *pulled_bases], ORDER),
        "shared_base_identical_hits": True,
    }
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
