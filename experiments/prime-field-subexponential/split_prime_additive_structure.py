#!/usr/bin/env python3
"""Compare split-prime orientation instances with matched subset-sum controls."""

from collections import Counter, defaultdict
from fractions import Fraction
from itertools import combinations
import json
from pathlib import Path
import random

from toy_jacobian import GenusTwo


PRIME = 101
GENUS = 2
CONTROL_TRIALS = 256


def factor_distinct(number):
    factors = []
    candidate = 2
    while candidate * candidate <= number:
        if number % candidate == 0:
            factors.append(candidate)
            while number % candidate == 0:
                number //= candidate
        candidate += 1
    if number > 1:
        factors.append(number)
    return factors


def enumerate_classes(curve):
    classes = []
    key_count = 1 + curve.p + curve.p * curve.p
    for serial in range(key_count):
        u = curve.monic_key(serial)
        classes.extend((u, v) for v in curve.v_choices(u))
    assert len(classes) == len(set(classes))
    return classes


def cyclic_coordinates(curve, classes):
    order = len(classes)
    prime_divisors = factor_distinct(order)
    generator = next(
        divisor
        for divisor in classes
        if divisor != curve.identity
        and all(
            curve.mul(order // prime, divisor) != curve.identity
            for prime in prime_divisors
        )
    )
    coordinates = {}
    value = curve.identity
    for scalar in range(order):
        assert value not in coordinates
        coordinates[value] = scalar
        value = curve.add(value, generator)
    assert value == curve.identity
    assert len(coordinates) == order
    return generator, coordinates


def all_subset_sums(values, modulus):
    sums = [0]
    for value in values:
        sums += [(old + value) % modulus for old in sums]
    return sums


def weight_layer_is_injective(values, modulus, weight):
    sums = {
        sum(values[index] for index in chosen) % modulus
        for chosen in combinations(range(len(values)), weight)
    }
    return len(sums) == sum(1 for _ in combinations(range(len(values)), weight))


def collision_metrics(values, modulus):
    sums = all_subset_sums(values, modulus)
    buckets = defaultdict(list)
    for mask, value in enumerate(sums):
        buckets[value].append(mask)

    collision_pairs = sum(len(masks) * (len(masks) - 1) // 2 for masks in buckets.values())
    minimum_distance = None
    for masks in buckets.values():
        for left_index, left in enumerate(masks):
            for right in masks[left_index + 1:]:
                distance = (left ^ right).bit_count()
                if minimum_distance is None or distance < minimum_distance:
                    minimum_distance = distance

    weight = len(values) // 2
    balanced_masks = [
        sum(1 << index for index in chosen)
        for chosen in combinations(range(len(values)), weight)
    ]
    balanced_counts = Counter(sums[mask] for mask in balanced_masks)
    balanced_collisions = sum(
        count * (count - 1) // 2 for count in balanced_counts.values()
    )
    zero_masks = buckets.get(0, ())
    nonempty_zero_weights = [mask.bit_count() for mask in zero_masks if mask]
    return {
        "subset_count": len(sums),
        "distinct_subset_sums": len(buckets),
        "collision_pairs": collision_pairs,
        "maximum_bucket_size": max(map(len, buckets.values())),
        "minimum_signed_relation_support": minimum_distance,
        "nonempty_zero_sum_subsets": len(nonempty_zero_weights),
        "minimum_zero_sum_weight": min(nonempty_zero_weights, default=None),
        "balanced_weight": weight,
        "balanced_subset_count": len(balanced_masks),
        "balanced_distinct_sums": len(balanced_counts),
        "balanced_collision_pairs": balanced_collisions,
        "balanced_maximum_bucket_size": max(balanced_counts.values()),
    }


def median(values):
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def summarize_controls(records, actual):
    keys = (
        "distinct_subset_sums",
        "collision_pairs",
        "maximum_bucket_size",
        "balanced_distinct_sums",
        "balanced_collision_pairs",
        "balanced_maximum_bucket_size",
    )
    summary = {}
    for key in keys:
        values = [record[key] for record in records]
        summary[key] = {
            "minimum": min(values),
            "median": median(values),
            "maximum": max(values),
            "controls_at_most_actual": sum(value <= actual[key] for value in values),
        }

    relation_values = [
        record["minimum_signed_relation_support"]
        for record in records
        if record["minimum_signed_relation_support"] is not None
    ]
    summary["minimum_signed_relation_support"] = {
        "controls_with_a_relation": len(relation_values),
        "minimum": min(relation_values, default=None),
        "median": median(relation_values) if relation_values else None,
        "maximum": max(relation_values, default=None),
        "controls_at_most_actual": (
            None
            if actual["minimum_signed_relation_support"] is None
            else sum(
                value <= actual["minimum_signed_relation_support"]
                for value in relation_values
            )
        ),
    }
    return summary


def split_point_coordinates(curve, coordinates):
    pool = []
    for x in range(curve.p):
        roots = curve.roots(x)
        if len(roots) == 2:
            point = curve.point_divisor(x, roots[0])
            pool.append(coordinates[point])
    return pool


def pair_layer_census(point_pool, group_order):
    undoubled = defaultdict(list)
    doubled = defaultdict(list)
    for pair in combinations(range(len(point_pool)), 2):
        value = sum(point_pool[index] for index in pair) % group_order
        undoubled[value].append(pair)
        doubled[-2 * value % group_order].append(pair)

    doubled_collisions = [pairs for pairs in doubled.values() if len(pairs) > 1]
    torsion_coordinate = group_order // 2
    torsion_explains_all = True
    collisions_are_disjoint = True
    for pairs in doubled_collisions:
        if len(pairs) != 2:
            torsion_explains_all = False
            continue
        left, right = pairs
        difference = (
            sum(point_pool[index] for index in left)
            - sum(point_pool[index] for index in right)
        ) % group_order
        torsion_explains_all &= difference == torsion_coordinate
        collisions_are_disjoint &= set(left).isdisjoint(right)

    sample_expectations = {}
    cofactor_bound_expectations = {}
    pool_size = len(point_pool)
    collision_pairs = sum(
        len(pairs) * (len(pairs) - 1) // 2 for pairs in doubled.values()
    )
    kernel_size = 2
    theoretical_collision_bound = (
        (kernel_size - 1) * len(point_pool) * (len(point_pool) - 1) // 4
    )
    for sample_size in range(3, 10):
        if sample_size < 4 or not collisions_are_disjoint:
            expectation = Fraction(0)
        else:
            numerator = 1
            denominator = 1
            for offset in range(4):
                numerator *= sample_size - offset
                denominator *= pool_size - offset
            expectation = collision_pairs * Fraction(numerator, denominator)
        sample_expectations[str(sample_size)] = (
            f"{expectation.numerator}/{expectation.denominator}"
        )
        bound_probability = Fraction(1)
        for offset in range(3):
            bound_probability *= Fraction(
                sample_size - offset, pool_size - offset
            )
        bound_expectation = theoretical_collision_bound * bound_probability
        cofactor_bound_expectations[str(sample_size)] = (
            f"{bound_expectation.numerator}/{bound_expectation.denominator}"
        )

    return {
        "point_count": len(point_pool),
        "pair_subsets": sum(len(pairs) for pairs in undoubled.values()),
        "undoubled_distinct_pair_sums": len(undoubled),
        "undoubled_collision_pairs": sum(
            len(pairs) * (len(pairs) - 1) // 2 for pairs in undoubled.values()
        ),
        "doubled_distinct_pair_sums": len(doubled),
        "doubled_collision_pairs": collision_pairs,
        "doubled_maximum_bucket_size": max(map(len, doubled.values())),
        "doubling_kernel_size": kernel_size,
        "theoretical_cofactor_collision_pair_bound": (
            theoretical_collision_bound
        ),
        "nonzero_two_torsion_coordinate": torsion_coordinate,
        "every_doubled_collision_is_translation_by_two_torsion": (
            torsion_explains_all
        ),
        "every_doubled_collision_uses_four_distinct_points": (
            collisions_are_disjoint
        ),
        "expected_retained_pair_collisions_in_uniform_slot_sample": (
            sample_expectations
        ),
        "cofactor_bound_on_expected_retained_pair_collisions": (
            cofactor_bound_expectations
        ),
    }


def analyze_panel(curve, coordinates, group_order, doubled_pool, panel, panel_index):
    values = []
    point_values = []
    planted_mask = 0
    for index, (x, selected) in enumerate(
        zip(panel["split_abscissae"], panel["selected_signed_points"], strict=True)
    ):
        roots = curve.roots(x)
        assert len(roots) == 2
        plus = curve.point_divisor(x, roots[0])
        point_value = coordinates[plus]
        point_values.append(point_value)
        values.append((-2 * point_value) % group_order)
        assert selected[0] == x
        if selected[1] == roots[1]:
            planted_mask |= 1 << index
        else:
            assert selected[1] == roots[0]

    actual = collision_metrics(values, group_order)
    target = sum(
        value for index, value in enumerate(values) if planted_mask >> index & 1
    ) % group_order
    sums = all_subset_sums(values, group_order)
    assert sum(value == target for value in sums) == 1

    rng = random.Random(0xA66171E + panel_index)
    subgroup_order = group_order // 2
    uniform_controls = []
    doubled_point_controls = []
    for _ in range(CONTROL_TRIALS):
        uniform = [2 * rng.randrange(subgroup_order) for _ in values]
        point_sample = rng.sample(doubled_pool, len(values))
        uniform_controls.append(collision_metrics(uniform, group_order))
        doubled_point_controls.append(collision_metrics(point_sample, group_order))

    return {
        "projective_section_dimension": panel["projective_section_dimension"],
        "split_prime_factors": len(values),
        "increment_coordinates_modulo_group_order": values,
        "undoubled_layers_through_genus_are_injective": all(
            weight_layer_is_injective(point_values, group_order, weight)
            for weight in range(1, min(GENUS, len(values)) + 1)
        ),
        "doubled_layers_through_genus_are_injective": all(
            weight_layer_is_injective(values, group_order, weight)
            for weight in range(1, min(GENUS, len(values)) + 1)
        ),
        "planted_orientation_mask": planted_mask,
        "planted_target_has_one_orientation": True,
        "actual": actual,
        "uniform_2J_controls": summarize_controls(uniform_controls, actual),
        "random_doubled_curve_point_controls": summarize_controls(
            doubled_point_controls, actual
        ),
    }


def main():
    source = json.loads(
        Path(__file__).with_name("binary_split_norm_control.json").read_text()
    )
    curve = GenusTwo(PRIME)
    classes = enumerate_classes(curve)
    generator, coordinates = cyclic_coordinates(curve, classes)
    group_order = len(classes)
    point_pool = split_point_coordinates(curve, coordinates)
    doubled_pool = [(-2 * value) % group_order for value in point_pool]
    result = {
        "prime": PRIME,
        "genus": GENUS,
        "jacobian_order": group_order,
        "jacobian_is_cyclic": True,
        "cyclic_generator": [list(part) for part in generator],
        "orientation_increment_subgroup_order": group_order // 2,
        "rational_split_abscissae": len(doubled_pool),
        "full_split_point_pool_pair_census": pair_layer_census(
            point_pool, group_order
        ),
        "control_trials_per_ensemble": CONTROL_TRIALS,
        "panels": [
            analyze_panel(
                curve, coordinates, group_order, doubled_pool, panel, panel_index
            )
            for panel_index, panel in enumerate(source["panels"])
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
