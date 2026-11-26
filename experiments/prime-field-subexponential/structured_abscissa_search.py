#!/usr/bin/env python3
"""Search arithmetic-progression split fibers for certificate-degree drops."""

import json
from collections import Counter
from itertools import product
from math import comb
from random import Random

import binary_split_norm_control as split_control
import binary_graeffe_macaulay as macaulay
from toy_jacobian import GenusTwo


PRIME = 101
SEED = 6_440_117


CERTIFICATE_LIMIT = 8


def truncated_diagnostics(equations, planted, variables, prime, degree):
    pivots = {}
    for equation in equations:
        coefficients = macaulay.polynomial_dict(equation, prime)
        input_degree = equation.total_degree()
        if input_degree > degree:
            continue
        for multiplier in macaulay.monomials(
            len(variables), degree - input_degree
        ):
            row = {
                tuple(
                    left + right
                    for left, right in zip(monomial, multiplier, strict=True)
                ): coefficient
                for monomial, coefficient in coefficients.items()
            }
            macaulay.add_echelon_row(pivots, row, prime)
    recovered = []
    for index in range(len(variables)):
        exponent = [0] * len(variables)
        exponent[index] = 1
        target = {tuple(exponent): 1}
        constant = -planted[index] % prime
        if constant:
            target[(0,) * len(variables)] = constant
        recovered.append(macaulay.reduces_to_zero(pivots, target, prime))
    columns = comb(len(variables) + degree, len(variables))
    return {
        "macaulay_columns_at_limit": columns,
        "macaulay_rank_at_limit": len(pivots),
        "truncated_quotient_dimension_at_limit": columns - len(pivots),
        "linear_form_recovery_at_limit": recovered,
    }


def modular_rank(matrix, prime):
    rows = [[value % prime for value in row] for row in matrix]
    rank = 0
    for column in range(len(rows[0])):
        pivot = next(
            (index for index in range(rank, len(rows)) if rows[index][column]),
            None,
        )
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        inverse = pow(rows[rank][column], -1, prime)
        rows[rank] = [value * inverse % prime for value in rows[rank]]
        for index in range(len(rows)):
            if index == rank or not rows[index][column]:
                continue
            scale = rows[index][column]
            rows[index] = [
                (left - scale * right) % prime
                for left, right in zip(rows[index], rows[rank], strict=True)
            ]
        rank += 1
    return rank


def planted_jacobian_rank(equations, planted, variables, prime):
    substitution = dict(zip(variables, planted, strict=True))
    matrix = [
        [int(equation.diff(variable).eval(substitution)) for variable in variables]
        for equation in equations
    ]
    return modular_rank(matrix, prime)


def bounded_certificate_panel(equations, planted, variables, prime, limit=12):
    try:
        return macaulay.certificate_panel(
            equations, planted, variables, prime, limit=min(limit, CERTIFICATE_LIMIT)
        )
    except AssertionError:
        diagnostics = truncated_diagnostics(
            equations, planted, variables, prime, CERTIFICATE_LIMIT
        )
        result = {
            "minimum_static_certificate_degree": None,
            "all_parameter_linear_forms_recovered": False,
            "planted_jacobian_rank": planted_jacobian_rank(
                equations, planted, variables, prime
            ),
        }
        result.update(diagnostics)
        return result


split_control.certificate_panel = bounded_certificate_panel


class FixedChoiceRandom(Random):
    def __init__(self, seed, chosen):
        super().__init__(seed)
        self.chosen = list(chosen)

    def sample(self, population, count):
        assert count == len(self.chosen)
        return list(self.chosen)


def progression_candidates(curve, length):
    split = {
        x: (x, curve.roots(x))
        for x in range(curve.p)
        if len(curve.roots(x)) == 2
    }
    seen = set()
    out = []
    for offset in range(curve.p):
        for step in range(1, curve.p):
            xs = tuple((offset + step * index) % curve.p for index in range(length))
            if len(set(xs)) != length or not all(x in split for x in xs):
                continue
            key = tuple(sorted(xs))
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "offset": offset,
                    "step": step,
                    "abscissae": xs,
                    "fibers": tuple(split[x] for x in xs),
                }
            )
    return out


def cyclic_span(values, prime):
    values = sorted(set(values))
    gaps = [
        (values[(index + 1) % len(values)] - values[index]) % prime
        for index in range(len(values))
    ]
    return prime - max(gaps) + 1


def compatible_sign_assignment_count(panel):
    curve = GenusTwo(PRIME)
    fibers = [curve.roots(x) for x in panel["split_abscissae"]]
    target = (tuple(panel["target_u"]), tuple(panel["target_v"]))
    count = 0
    for choices in product((0, 1), repeat=len(fibers)):
        total = curve.identity
        for x, roots, choice in zip(
            panel["split_abscissae"], fibers, choices, strict=True
        ):
            total = curve.add(total, curve.point_divisor(x, roots[choice]))
        count += curve.neg(total) == target
    return count


def summarize(rows):
    degrees = Counter(row["minimum_static_certificate_degree"] for row in rows)
    resolved = [degree for degree in degrees if degree is not None]
    minimum = min(resolved) if resolved else None
    return {
        "panels": len(rows),
        "certificate_degree_histogram": {
            (
                f"unresolved_through_{CERTIFICATE_LIMIT}"
                if degree is None
                else str(degree)
            ): count
            for degree, count in sorted(
                degrees.items(), key=lambda item: (item[0] is None, item[0] or 0)
            )
        },
        "minimum_certificate_degree": minimum,
        "unresolved_through_certificate_limit": degrees.get(None, 0),
        "unresolved_panels": [
            row
            for row in rows
            if row["minimum_static_certificate_degree"] is None
        ],
        "minimum_cyclic_span": min(row["cyclic_span"] for row in rows),
        "minimum_degree_panels": [
            row
            for row in rows
            if row["minimum_static_certificate_degree"] == minimum
        ][:3],
    }


def compact(panel, arm, progression=None):
    xs = panel["split_abscissae"]
    row = {
        "arm": arm,
        "split_abscissae": xs,
        "cyclic_span": cyclic_span(xs, PRIME),
        "minimum_static_certificate_degree": panel[
            "minimum_static_certificate_degree"
        ],
        "macaulay_columns_at_certificate": panel.get(
            "macaulay_columns_at_certificate"
        ),
        "construction_attempts": panel["construction_attempts"],
    }
    if progression is not None:
        row["progression_offset"] = progression["offset"]
        row["progression_step"] = progression["step"]
    if panel["minimum_static_certificate_degree"] is None:
        row["planted_jacobian_rank"] = panel["planted_jacobian_rank"]
        row["truncated_quotient_dimension_at_limit"] = panel[
            "truncated_quotient_dimension_at_limit"
        ]
        row["macaulay_columns_at_limit"] = panel[
            "macaulay_columns_at_limit"
        ]
        row["macaulay_rank_at_limit"] = panel["macaulay_rank_at_limit"]
        row["linear_form_recovery_at_limit"] = panel[
            "linear_form_recovery_at_limit"
        ]
        row["compatible_sign_assignments"] = compatible_sign_assignment_count(
            panel
        )
        row["selected_signed_points"] = panel["selected_signed_points"]
        row["target_u"] = panel["target_u"]
        row["target_v"] = panel["target_v"]
    return row


def main():
    curve = GenusTwo(PRIME)
    coordinator = Random(SEED)
    results = []
    for variables in (4, 5):
        length = variables + 2
        candidates = progression_candidates(curve, length)
        coordinator.shuffle(candidates)
        progression_rows = []
        for index, candidate in enumerate(candidates):
            rng = FixedChoiceRandom(
                f"{SEED}/ap/{variables}/{index}", candidate["fibers"]
            )
            progression_rows.append(
                compact(
                    split_control.build_panel(curve, variables, rng),
                    "progression",
                    candidate,
                )
            )

        random_rows = []
        for index in range(len(candidates)):
            rng = Random(f"{SEED}/random/{variables}/{index}")
            random_rows.append(
                compact(split_control.build_panel(curve, variables, rng), "random")
            )

        results.append(
            {
                "variables": variables,
                "tail_slots": length,
                "available_split_progressions": len(candidates),
                "progression": summarize(progression_rows),
                "random": summarize(random_rows),
            }
        )
    print(
        json.dumps(
            {
                "prime": PRIME,
                "genus": 2,
                "seed": SEED,
                "sampling": (
                    "Complete census of distinct split-fiber arithmetic-"
                    "progression abscissa sets, paired with the same number "
                    "of deterministic random controls."
                ),
                "scope": (
                    "Exact finite search. Progression panels fix split "
                    "abscissae x_i=a+bi; signs and valid targets are sampled "
                    "by the same norm producer used for random controls."
                ),
                "algorithm_claimed": False,
                "results": results,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
