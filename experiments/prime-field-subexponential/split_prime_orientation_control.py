#!/usr/bin/env python3
"""Verify the Jacobian orientation equation for split prime factors."""

from itertools import product
import json
from pathlib import Path

from toy_jacobian import GenusTwo


PRIME = 101


def subtract(curve, left, right):
    return curve.add(left, curve.neg(right))


def analyze(curve, panel):
    xs = panel["split_abscissae"]
    pairs = [
        tuple(curve.point_divisor(x, y) for y in curve.roots(x)) for x in xs
    ]
    for plus, minus in pairs:
        assert minus == curve.neg(plus)

    base = curve.identity
    for plus, _ in pairs:
        base = curve.add(base, plus)
    increments = [subtract(curve, minus, plus) for plus, minus in pairs]
    for (plus, _), increment in zip(pairs, increments, strict=True):
        assert increment == curve.add(curve.neg(plus), curve.neg(plus))

    target_inverse = curve.neg((tuple(panel["target_u"]), tuple(panel["target_v"])))
    matches = 0
    affine_orientation_identity = True
    for bits in product((0, 1), repeat=len(xs)):
        direct = curve.identity
        affine = base
        for bit, pair, increment in zip(bits, pairs, increments, strict=True):
            direct = curve.add(direct, pair[bit])
            if bit:
                affine = curve.add(affine, increment)
        affine_orientation_identity &= direct == affine
        matches += direct == target_inverse
    assert affine_orientation_identity
    return {
        "projective_section_dimension": panel["projective_section_dimension"],
        "split_prime_factors": len(xs),
        "orientations": 1 << len(xs),
        "target_orientations": matches,
        "every_conjugate_class_is_the_negative": True,
        "every_flip_increment_is_minus_twice_the_base_class": True,
        "all_orientation_sums_match_the_affine_subset_sum_formula": True,
        "all_orientations_have_the_same_image_modulo_2J": True,
    }


def main():
    source = json.loads(
        Path(__file__).with_name("binary_split_norm_control.json").read_text()
    )
    curve = GenusTwo(PRIME)
    result = {
        "prime": PRIME,
        "genus": 2,
        "panels": [analyze(curve, panel) for panel in source["panels"]],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
