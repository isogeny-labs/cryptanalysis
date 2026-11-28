#!/usr/bin/env python3
"""Control known-log Abel-curve sourcing and doubling chains."""

from collections import Counter
import json

from toy_jacobian import GenusTwo


PRIME = 101


def jacobian_classes(curve):
    classes = set()
    key_count = 1 + curve.p + curve.p * curve.p
    for serial in range(key_count):
        u = curve.monic_key(serial)
        for v in curve.v_choices(u):
            classes.add((u, v))
    return classes


def abel_curve_classes(curve):
    classes = {curve.identity}
    for x in range(curve.p):
        for y in curve.roots(x):
            classes.add(curve.point_divisor(x, y))
    return classes


def doubling_control(curve, abel_classes):
    hits = []
    chain_histogram = Counter()
    maximum_distinct_chain = 0
    for divisor in sorted(abel_classes):
        doubled = curve.add(divisor, divisor)
        if doubled in abel_classes:
            hits.append({"source": divisor, "double": doubled})
        seen = set()
        current = divisor
        length = 0
        while current in abel_classes and current not in seen:
            seen.add(current)
            length += 1
            current = curve.add(current, current)
        chain_histogram[length] += 1
        maximum_distinct_chain = max(maximum_distinct_chain, length)
    return {
        "classes_doubling_back_to_abel_curve": len(hits),
        "doubling_hits": hits,
        "distinct_chain_length_histogram": [
            {"length": length, "count": count}
            for length, count in sorted(chain_histogram.items())
        ],
        "maximum_distinct_doubling_chain_length": maximum_distinct_chain,
    }


def main():
    curve = GenusTwo(PRIME)
    abel_classes = abel_curve_classes(curve)
    all_classes = jacobian_classes(curve)
    result = {
        "prime": PRIME,
        "genus": 2,
        "curve_coefficients": curve.coefficients,
        "jacobian_classes": len(all_classes),
        "abel_curve_classes_including_infinity": len(abel_classes),
        "abel_density_in_jacobian": len(abel_classes) / len(all_classes),
        **doubling_control(curve, abel_classes),
        "fixed_genus_bezout_ledger": [
            {
                "genus": genus,
                "three_theta_degree_of_abel_curve": 3 * genus,
                "three_theta_degree_of_doubling_preimage": (
                    3 * genus * 2 ** (2 * genus - 2)
                ),
                "bezout_intersection_upper_bound": (
                    9 * genus * genus * 2 ** (2 * genus - 2)
                ),
                "random_known_scalar_sourcing_exponent": genus - 1,
            }
            for genus in range(2, 8)
        ],
        "algorithm_claimed": False,
        "scope": (
            "Exact genus-two doubling intersections plus fixed-genus "
            "geometric and density bounds for known-log curve-point fibers."
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
