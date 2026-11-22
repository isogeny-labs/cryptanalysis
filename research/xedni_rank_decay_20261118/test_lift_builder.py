#!/usr/bin/env python3
"""Control-only tests for the exact short-Weierstrass lift builder."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parent))
import lift_builder as lift
import local_conditions as local
import rank_pari


def tiny_source() -> dict:
    """A hand-certified F_17 fixture; no point-count scan occurs in tests."""
    points = [[2, 8], [12, 3], [16, 16], [8, 8], [7, 9], [6, 15]]
    return {
        "schema": "xedni-rank-decay-source/v1",
        "master_seed": "tiny-control-only",
        "source_id": "tiny-f17-control",
        "source_index": 0,
        "p": 17,
        "bits": 5,
        "family": "generic",
        "curve": {"a": 1, "b": 3, "generation_attempts": 1},
        "cardinality": 17,
        "cardinality_factors": [[17, 1]],
        "cardinality_backend": "hand-certified-control",
        "source_subgroup_order": 17,
        "source_cofactor": 1,
        "base_point": [2, 8],
        "base_point_order": 17,
        "point_sampling_attempts": 1,
        "scalar_sampling_attempts": 6,
        "max_r": 6,
        "ordered_scalars": [1, 2, 3, 4, 5, 6],
        "ordered_points": points,
        "prefix_permutation": list(range(6)),
        "prefixes": {
            str(r): {"indices": list(range(r)), "target_index": r - 1}
            for r in range(2, 7)
        },
    }


class RecordingOptimizer:
    """Mock the ca-icx envelope while returning its feasible input unchanged."""

    def __init__(self):
        self.calls = []

    def __call__(self, payload, *, radius, max_candidates):
        self.calls.append(
            {
                "payload": copy.deepcopy(payload),
                "radius": radius,
                "max_candidates": max_candidates,
            }
        )
        return {
            "schema_version": 1,
            "operation": "xedni-lift",
            "status": "complete",
            "model": "weierstrass",
            "search": {"radius": radius, "max_candidates": max_candidates},
            "result": {
                "optimized_coefficients": list(payload["particular"]),
                "optimized_score": {"nonsingular": True},
                "candidates_evaluated": 1,
                "exact_constraints_preserved": True,
                "congruence_preserved": True,
            },
        }


class LiftBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # These are deterministic, tiny local-control fixtures (primes <=19).
        cls.locals = {}
        for r in range(2, 7):
            prime = 7 if r == 2 else 11 if r <= 5 else 19
            cls.locals[r] = local.build_local_conditions(
                "P_neutral_crt", r, [prime], seed="tiny"
            )

    def setUp(self):
        self.source = tiny_source()

    def test_balanced_all_executable_r_without_local_conditions(self):
        for r in range(2, 7):
            with self.subTest(r=r):
                result = lift.build_lift(self.source, r, "balanced")
                self.assertEqual(result["incidence_coset"]["rank"], r)
                self.assertEqual(result["incidence_coset"]["kernel_dimension"], 7 - r)
                self.assertEqual(result["crt_modulus"], 17)
                self.assertEqual(result["rank_outcome"], None)
                self.assertEqual(result["status"], lift.STATUS)
                self.assertNotIn("classification", result)
                self.assertNotIn("rank_bounds", result)
                self.assertEqual(lift.verify_lift(result, self.source), [])

    def test_crt_local_points_and_coefficients_all_r(self):
        for r in range(2, 7):
            with self.subTest(r=r):
                conditions = self.locals[r]
                result = lift.build_lift(
                    self.source, r, "balanced", conditions
                )
                self.assertEqual(
                    result["crt_modulus"], 17 * conditions["M"]
                )
                self.assertEqual(
                    result["moduli"], [17] + conditions["accepted_primes"]
                )
                self.assertEqual(
                    lift.verify_lift(result, self.source, conditions), []
                )

    def test_wide_is_deterministic_public_and_residue_preserving(self):
        conditions = self.locals[5]
        balanced = lift.build_lift(self.source, 5, "balanced", conditions)
        first = lift.build_lift(self.source, 5, "wide", conditions)
        second = lift.build_lift(self.source, 5, "wide", conditions)
        self.assertEqual(first, second)
        modulus = first["crt_modulus"]
        for base, wide, shifts in zip(
            balanced["coordinate_representatives"],
            first["coordinate_representatives"],
            first["coordinate_shifts"],
        ):
            self.assertTrue(all(shift in {-1, 0, 1} for shift in shifts))
            self.assertEqual([wide[i] - base[i] for i in range(2)], [modulus * x for x in shifts])
        public_input = first["public_selector"]["input"]
        self.assertNotIn("ordered_scalars", public_input)
        self.assertNotIn("scalars", public_input)
        self.assertFalse(first["public_selector"]["uses_source_scalars"])
        self.assertEqual(lift.verify_lift(first, self.source, conditions), [])

    def test_optimized_all_r_uses_balanced_coset_and_frozen_budget(self):
        for r in range(2, 7):
            with self.subTest(r=r):
                mock = RecordingOptimizer()
                optimized = lift.build_lift(
                    self.source,
                    r,
                    "optimized",
                    self.locals[r],
                    optimizer=mock,
                )
                balanced = lift.build_lift(
                    self.source, r, "balanced", self.locals[r]
                )
                self.assertEqual(len(mock.calls), 1)
                self.assertEqual(mock.calls[0]["radius"], 1)
                self.assertEqual(mock.calls[0]["max_candidates"], 3 ** (7 - r))
                self.assertEqual(
                    optimized["coordinate_representatives"],
                    balanced["coordinate_representatives"],
                )
                self.assertEqual(
                    mock.calls[0]["payload"]["particular"],
                    [str(value) for value in balanced["incidence_coset"]["particular"]],
                )
                self.assertEqual(
                    lift.verify_lift(optimized, self.source, self.locals[r]), []
                )

    def test_generalized_conversion_matches_frozen_formula(self):
        result = lift.build_lift(self.source, 4, "balanced", self.locals[4])
        u = result["signed_coefficients"]
        a0, a1, a3 = u[:3]
        a00, a2, a4, a6 = (-u[3], -u[4], -u[5], -u[6])
        c3 = a0 * a00
        expected_ainvs = [
            a1,
            a0 * a2,
            a3 * c3,
            a0 * a4 * c3,
            a0 * a6 * c3 * c3,
        ]
        expected_points = [
            [c3 * x, c3 * a0 * y]
            for x, y in result["coordinate_representatives"]
        ]
        self.assertEqual(result["ainvs"], expected_ainvs)
        self.assertEqual(result["points"], expected_points)

    def test_output_is_direct_rank_adapter_input_but_remains_unranked(self):
        result = lift.build_lift(self.source, 3, "balanced", self.locals[3])
        row_id, r, ainvs = rank_pari.validate_row(result)
        self.assertEqual(row_id, result["row_id"])
        self.assertEqual(r, 3)
        self.assertEqual(list(ainvs), result["ainvs"])
        self.assertIsNone(result["rank_outcome"])

    def test_output_mutations_fail_independent_replay(self):
        conditions = self.locals[4]
        result = lift.build_lift(self.source, 4, "balanced", conditions)
        mutations = []
        changed = copy.deepcopy(result)
        changed["ainvs"][4] += 1
        mutations.append(changed)
        changed = copy.deepcopy(result)
        changed["points"][0][0] += 1
        mutations.append(changed)
        changed = copy.deepcopy(result)
        changed["signed_coefficients"][0] += result["crt_modulus"]
        mutations.append(changed)
        changed = copy.deepcopy(result)
        changed["hashes"]["model_sha256"] = "0" * 64
        mutations.append(changed)
        changed = copy.deepcopy(result)
        changed["certificate"]["source_replay"] = False
        mutations.append(changed)
        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=index):
                self.assertTrue(lift.verify_lift(mutation, self.source, conditions))

    def test_source_and_local_mutations_fail_closed(self):
        source = copy.deepcopy(self.source)
        source["ordered_points"][2][0] += 1
        with self.assertRaises(lift.LiftBuildError):
            lift.build_lift(source, 4, "balanced", self.locals[4])

        conditions = copy.deepcopy(self.locals[4])
        conditions["local"][0]["selected_points"][0][0] += 1
        with self.assertRaises(lift.LiftBuildError):
            lift.build_lift(self.source, 4, "balanced", conditions)

        conditions = copy.deepcopy(self.locals[4])
        conditions["local"][0]["weierstrass_coefficient_vector"][6] += 1
        with self.assertRaises(lift.LiftBuildError):
            lift.build_lift(self.source, 4, "balanced", conditions)

    def test_optimizer_mutations_fail_closed(self):
        def mutate_residue(payload, *, radius, max_candidates):
            report = RecordingOptimizer()(payload, radius=radius, max_candidates=max_candidates)
            report["result"]["optimized_coefficients"][0] = str(
                int(report["result"]["optimized_coefficients"][0]) + 1
            )
            return report

        def false_certificate(payload, *, radius, max_candidates):
            report = RecordingOptimizer()(payload, radius=radius, max_candidates=max_candidates)
            report["result"]["exact_constraints_preserved"] = False
            return report

        def malformed(payload, *, radius, max_candidates):
            return {"operation": "wrong"}

        for optimizer in (mutate_residue, false_certificate, malformed):
            with self.subTest(optimizer=optimizer.__name__):
                with self.assertRaises(lift.LiftBuildError):
                    lift.build_lift(
                        self.source,
                        4,
                        "optimized",
                        self.locals[4],
                        optimizer=optimizer,
                    )

    def test_noncoprime_source_local_moduli_are_rejected(self):
        same_prime = local.build_local_conditions(
            "P_neutral_crt", 2, [17], seed="noncoprime-control"
        )
        with self.assertRaises(lift.LiftBuildError) as caught:
            lift.build_lift(self.source, 2, "balanced", same_prime)
        self.assertEqual(caught.exception.code, "noncoprime_moduli")

    def test_r7_and_all_unimplemented_mechanism_panels_are_blocked(self):
        with self.assertRaises(lift.LiftBuildError) as caught:
            lift.build_lift(self.source, 7, "balanced")
        self.assertEqual(caught.exception.code, "unsupported_r")
        for panel in ("M1", "M2", "M3", "M4", "M5", "M6"):
            with self.subTest(panel=panel):
                with self.assertRaises(lift.LiftBuildError) as caught:
                    lift.build_lift(
                        self.source, 4, "balanced", mechanism_panel=panel
                    )
                self.assertEqual(caught.exception.code, "unsupported_panel")

        incompatible = local.build_local_conditions(
            "I_incompatible", 2, [7, 11], seed="incompatible-control"
        )
        with self.assertRaises(lift.LiftBuildError) as caught:
            lift.build_lift(self.source, 2, "balanced", incompatible)
        self.assertEqual(caught.exception.code, "unsupported_panel")

    def test_crt_and_balanced_representation_controls(self):
        self.assertEqual(lift.crt_combine([2, 3], [5, 7]), 17)
        self.assertEqual(lift.balanced_residue(17, 35), 17)
        self.assertEqual(lift.balanced_residue(18, 35), -17)
        with self.assertRaises(ValueError):
            lift.crt_combine([1, 1], [5, 10])


if __name__ == "__main__":
    unittest.main()
