#!/usr/bin/env python3
"""Search structured split abscissae for low signed-Hankel tensor width."""

from collections import Counter
from itertools import product
import json
from random import Random

import binary_split_norm_control as split_control
from conjugate_hankel_quotient import (
    cofactor_kernel,
    independent_row_indices,
    matrix_add,
    matrix_multiply,
    matrix_vector,
    multilinear_profile,
    nullspace_basis,
)
from signed_hankel_minrank import evaluate, lagrange_weights, rank_mod
from structured_abscissa_search import FixedChoiceRandom, progression_candidates
from toy_jacobian import GenusTwo


PRIME = 101
GENUS = 2
SEED = 9_220_271


def hankel(values, xs, weights, rows, columns, prime):
    moments = [
        sum(
            value * weight * pow(x, exponent, prime)
            for value, x, weight in zip(values, xs, weights, strict=True)
        ) % prime
        for exponent in range(rows + columns - 1)
    ]
    return [
        [moments[row + column] for column in range(columns)]
        for row in range(rows)
    ]


def geometric_candidates(curve, length):
    split = {
        x: (x, curve.roots(x))
        for x in range(1, curve.p)
        if len(curve.roots(x)) == 2
    }
    seen = set()
    out = []
    for scale in range(1, curve.p):
        for ratio in range(2, curve.p):
            xs = tuple(
                scale * pow(ratio, index, curve.p) % curve.p
                for index in range(length)
            )
            key = tuple(sorted(xs))
            if (
                len(set(xs)) != length
                or not all(x in split for x in xs)
                or key in seen
            ):
                continue
            seen.add(key)
            out.append({
                "scale": scale,
                "ratio": ratio,
                "abscissae": xs,
                "fibers": tuple(split[x] for x in xs),
            })
    return out


def analyze_panel(panel, curve):
    prime = curve.p
    r = panel["projective_section_dimension"]
    b_degree = (r - 1) // 2
    c_degree = r // 2
    columns = b_degree + 1
    rows = panel["tail_slots"] - c_degree - 1
    xs = panel["split_abscissae"]
    weights = lagrange_weights(xs, prime)
    u = panel["target_u"]
    v = panel["target_v"]
    centers = []
    signed_parts = []
    for x, y in panel["selected_signed_points"]:
        inverse_u = pow(evaluate(u, x, prime), -1, prime)
        centers.append(-evaluate(v, x, prime) * inverse_u % prime)
        signed_parts.append(y * inverse_u % prime)

    center = hankel(centers, xs, weights, rows, columns, prime)
    center_rank = rank_mod(center, prime)
    quotient = nullspace_basis(
        list(map(list, zip(*center, strict=True))), prime
    )
    applicable = center_rank == GENUS and columns > GENUS
    if not applicable:
        return {
            "center_rank": center_rank,
            "quotient_reduction_applies": False,
        }

    assert len(quotient) == columns - 1
    pivot_rows = independent_row_indices(center, GENUS, prime)
    residual_tables = [[] for _ in pivot_rows]
    rank_histogram = Counter()
    zero_signings = 0
    for bits in product((0, 1), repeat=len(xs)):
        values = [
            (1 if bit == 0 else -1) * value % prime
            for bit, value in zip(bits, signed_parts, strict=True)
        ]
        signed = hankel(values, xs, weights, rows, columns, prime)
        projected = matrix_multiply(quotient, signed, prime)
        projected_rank = rank_mod(projected, prime)
        rank_histogram[projected_rank] += 1
        if projected_rank != columns - 1:
            continue
        kernel = cofactor_kernel(projected, prime)
        total = matrix_add(center, signed, prime)
        residual = matrix_vector(total, kernel, prime)
        for table, row_index in zip(residual_tables, pivot_rows, strict=True):
            table.append(residual[row_index])
        zero_signings += not any(residual)

    full_rank_signings = rank_histogram[columns - 1]
    if full_rank_signings != 2 ** len(xs):
        return {
            "center_rank": center_rank,
            "quotient_reduction_applies": True,
            "projected_rank_histogram": {
                str(key): value for key, value in sorted(rank_histogram.items())
            },
            "all_projected_signings_full_rank": False,
        }

    profiles = [
        multilinear_profile(table, len(xs), prime)
        for table in residual_tables
    ]
    return {
        "center_rank": center_rank,
        "quotient_reduction_applies": True,
        "projected_rank_histogram": {
            str(key): value for key, value in sorted(rank_histogram.items())
        },
        "all_projected_signings_full_rank": True,
        "residual_zero_signings": zero_signings,
        "minimum_balanced_cut_rank": min(
            profile["minimum_balanced_cut_rank"] for profile in profiles
        ),
        "maximum_balanced_cut_rank": max(
            profile["maximum_balanced_cut_rank"] for profile in profiles
        ),
        "residual_balanced_cut_rank_histograms": [
            profile["balanced_cut_rank_histogram"] for profile in profiles
        ],
    }


def make_panel(curve, variables, fibers, label):
    rng = FixedChoiceRandom(f"{SEED}/{label}", fibers)
    return split_control.build_panel(curve, variables, rng)


def compact(panel, family, parameters, curve):
    result = {
        "family": family,
        "projective_section_dimension": panel["projective_section_dimension"],
        "tail_slots": panel["tail_slots"],
        "split_abscissae": panel["split_abscissae"],
        "parameters": parameters,
    }
    result.update(analyze_panel(panel, curve))
    return result


def summarize(records):
    applicable = [
        record for record in records
        if record.get("all_projected_signings_full_rank")
    ]
    minimum_histogram = Counter(
        record["minimum_balanced_cut_rank"] for record in applicable
    )
    return {
        "panels": len(records),
        "full_rank_quotient_panels": len(applicable),
        "minimum_balanced_cut_rank_histogram": {
            str(key): value for key, value in sorted(minimum_histogram.items())
        },
        "lowest_rank_panels": sorted(
            applicable,
            key=lambda record: record["minimum_balanced_cut_rank"],
        )[:5],
    }


def main():
    curve = GenusTwo(PRIME)
    records = []
    structured_count = 0
    for length in (7, 8, 9):
        variables = length - GENUS
        for index, candidate in enumerate(progression_candidates(curve, length)):
            panel = make_panel(
                curve, variables, candidate["fibers"],
                f"ap/{length}/{index}",
            )
            records.append(compact(
                panel,
                "arithmetic_progression",
                {"offset": candidate["offset"], "step": candidate["step"]},
                curve,
            ))
            structured_count += 1
        for index, candidate in enumerate(geometric_candidates(curve, length)):
            panel = make_panel(
                curve, variables, candidate["fibers"],
                f"gp/{length}/{index}",
            )
            records.append(compact(
                panel,
                "geometric_progression",
                {"scale": candidate["scale"], "ratio": candidate["ratio"]},
                curve,
            ))
            structured_count += 1

    random_records = []
    for index, structured in enumerate(records):
        variables = structured["projective_section_dimension"]
        rng = Random(f"{SEED}/random/{variables}/{index}")
        panel = split_control.build_panel(curve, variables, rng)
        random_records.append(compact(panel, "random", {"index": index}, curve))

    result = {
        "prime": PRIME,
        "genus": GENUS,
        "seed": SEED,
        "curve_coefficients": curve.coefficients,
        "structured": summarize(records),
        "random_controls": summarize(random_records),
        "structured_records": records,
        "random_records": random_records,
        "structured_panels": structured_count,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
