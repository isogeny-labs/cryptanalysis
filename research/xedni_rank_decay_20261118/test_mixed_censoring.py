#!/usr/bin/env python3
"""Exact-box and fail-closed controls for mixed unresolved allocations."""

from __future__ import annotations

import itertools
import math
import unittest

import analyze
import mixed_censoring as mixed
import sensitivity


DIGEST = "1" * 64


def cell(p: int, exposure: int, certified: int, unresolved: int) -> dict[str, int]:
    return {
        "p": p,
        "exposure": exposure,
        "certified_successes": certified,
        "unresolved": unresolved,
    }


def objective_number(value):
    if value == "-inf" or value is None:
        return -math.inf
    if value == "+inf":
        return math.inf
    return float(value)


class MixedCensoringTests(unittest.TestCase):
    def test_normalize_aggregates_duplicate_primes(self):
        self.assertEqual(
            mixed.normalize_cells(
                [cell(5, 7, 1, 2), cell(3, 4, 0, 1), cell(5, 9, 2, 3)]
            ),
            [cell(3, 4, 0, 1), cell(5, 16, 3, 5)],
        )

    def test_schema_and_integer_validation(self):
        bad = cell(3, 4, 1, 1)
        bad["extra"] = 0
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.normalize_cells([bad])
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.normalize_cells([cell(3, 1, True, 0)])
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.normalize_cells([cell(3, 2, 1, 2)])

    def test_exact_enumeration_finds_interior_not_uniform_corner(self):
        cells = [cell(3, 3, 0, 2), cell(5, 2, 0, 1)]

        def evaluator(successes):
            return (successes[0] - 1) ** 2 + (successes[1] - 1) ** 2

        result = mixed.exact_box_optimize(
            cells,
            evaluator,
            method="synthetic",
            objective="interior quadratic",
            evaluator_sha256=DIGEST,
            max_states=6,
        )
        self.assertEqual(result["status"], "COMPLETE")
        self.assertTrue(result["exact_integer_box"])
        self.assertEqual(result["state_count"], 6)
        self.assertEqual(result["evaluated_states"], 6)
        self.assertEqual(result["minimum"]["value"], 0.0)
        self.assertEqual(
            [row["successes"] for row in result["minimum"]["allocation"]],
            [1, 1],
        )
        self.assertTrue(mixed.verify_certificate_digest(result))
        result["minimum"]["value"] = 1.0
        self.assertFalse(mixed.verify_certificate_digest(result))

    def test_state_limit_fails_before_evaluation(self):
        calls = 0

        def evaluator(_successes):
            nonlocal calls
            calls += 1
            return 0.0

        result = mixed.exact_box_optimize(
            [cell(3, 10, 0, 9), cell(5, 10, 0, 9)],
            evaluator,
            method="synthetic",
            objective="zero",
            evaluator_sha256=DIGEST,
            max_states=99,
        )
        self.assertEqual(result["status"], "BLOCKED_STATE_LIMIT")
        self.assertEqual(result["state_count"], 100)
        self.assertEqual(result["evaluated_states"], 0)
        self.assertEqual(calls, 0)
        self.assertTrue(mixed.verify_certificate_digest(result))

    def test_binomial_matches_independent_full_product(self):
        cells = [
            cell(101, 80, 3, 2),
            cell(211, 90, 2, 2),
            cell(431, 100, 1, 2),
        ]
        alpha = 0.5
        hypotheses = 1
        result = mixed.optimize_binomial_cloglog(
            cells,
            familywise_alpha=alpha,
            simultaneous_hypotheses=hypotheses,
            max_states=27,
        )
        brute = []
        normalized = mixed.normalize_cells(cells)
        for extras in itertools.product(range(3), repeat=3):
            successes = tuple(
                row["certified_successes"] + extra
                for row, extra in zip(normalized, extras, strict=True)
            )
            fit = sensitivity.fit_binomial_cloglog(
                [
                    (row["p"], row["exposure"], count)
                    for row, count in zip(normalized, successes, strict=True)
                ],
                familywise_alpha=alpha,
                simultaneous_hypotheses=hypotheses,
            )
            brute.append((objective_number(fit["signed_beta_lower"]), successes))
        expected = min(brute)
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["evaluated_states"], 27)
        self.assertEqual(
            objective_number(result["minimum"]["value"]), expected[0]
        )
        self.assertEqual(
            tuple(row["successes"] for row in result["minimum"]["allocation"]),
            expected[1],
        )
        self.assertTrue(mixed.verify_certificate_digest(result))

    def test_poisson_structural_optimizer_matches_full_product(self):
        cases = [
            [
                cell(101, 500, 80, 3),
                cell(211, 500, 50, 4),
                cell(431, 500, 30, 2),
            ],
            [
                cell(1009, 1000, 20, 2),
                cell(2003, 1000, 25, 3),
                cell(4001, 1000, 35, 2),
                cell(8009, 1000, 45, 1),
            ],
        ]
        alpha = 0.5
        hypotheses = 1
        for cells in cases:
            with self.subTest(cells=cells):
                normalized = mixed.normalize_cells(cells)
                result = mixed.optimize_poisson_hoeffding(
                    normalized,
                    familywise_alpha=alpha,
                    simultaneous_hypotheses=hypotheses,
                )
                brute = []
                ranges = [range(row["unresolved"] + 1) for row in normalized]
                for extras in itertools.product(*ranges):
                    successes = tuple(
                        row["certified_successes"] + extra
                        for row, extra in zip(normalized, extras, strict=True)
                    )
                    fit = analyze.poisson_profile(
                        [
                            (row["p"], row["exposure"], count)
                            for row, count in zip(normalized, successes, strict=True)
                        ],
                        familywise_alpha=alpha,
                        simultaneous_hypotheses=hypotheses,
                    )
                    brute.append(
                        (
                            objective_number(fit["confidence_interval"]["lower"]),
                            successes,
                        )
                    )
                expected_value = min(item[0] for item in brute)
                self.assertEqual(result["status"], "COMPLETE")
                self.assertTrue(result["exact_integer_box"])
                self.assertAlmostEqual(
                    objective_number(result["minimum"]["value"]),
                    expected_value,
                    places=11,
                )
                self.assertTrue(mixed.verify_certificate_digest(result))

    def test_zero_certified_events_has_global_negative_infinity(self):
        result = mixed.optimize_poisson_hoeffding(
            [cell(101, 10, 0, 4), cell(211, 10, 0, 4)],
            familywise_alpha=0.05,
            simultaneous_hypotheses=4320,
        )
        self.assertEqual(result["minimum"]["value"], "-inf")
        self.assertEqual(result["minimum"]["extra_successes"], 0)

    def test_cluster_bootstrap_fails_closed_on_aggregate_box(self):
        result = mixed.cluster_bootstrap_fail_closed(
            [cell(101, 10, 1, 2), cell(211, 10, 1, 2)],
            evaluator_sha256=DIGEST,
        )
        self.assertEqual(
            result["status"], "BLOCKED_NEEDS_ROW_LEVEL_CLUSTER_ALLOCATION"
        )
        self.assertFalse(result["exact_integer_box"])
        self.assertEqual(result["evaluated_states"], 0)
        self.assertTrue(mixed.verify_certificate_digest(result))

    def test_single_prime_poisson_fails_closed(self):
        result = mixed.optimize_poisson_hoeffding(
            [cell(101, 10, 1, 2)],
            familywise_alpha=0.05,
            simultaneous_hypotheses=1,
        )
        self.assertEqual(result["status"], "BLOCKED_UNIDENTIFIABLE_DESIGN")
        self.assertTrue(mixed.verify_certificate_digest(result))


if __name__ == "__main__":
    unittest.main()
