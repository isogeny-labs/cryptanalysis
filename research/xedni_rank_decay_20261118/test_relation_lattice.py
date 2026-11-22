#!/usr/bin/env python3
"""Controls for the conditional complete relation-lattice verifier."""

from __future__ import annotations

import copy
from fractions import Fraction
import unittest
from unittest import mock

import relation_certificate as ec
import relation_lattice as lattice


TRUSTED_VERIFIER = "a" * 64
PROOF_HASH = "b" * 64


def jfraction(value: Fraction | int) -> int | str:
    value = Fraction(value)
    return value.numerator if value.denominator == 1 else str(value)


def jpoint(point: ec.PointQ):
    if point is None:
        return None
    return [jfraction(point[0]), jfraction(point[1])]


def attach_receipt(value: dict) -> dict:
    result = copy.deepcopy(value)
    subject = {
        "curve": result["curve"],
        "free_basis": result["free_basis"],
        "torsion": result["torsion"],
    }
    result["full_basis_receipt"] = {
        "schema": lattice.RECEIPT_SCHEMA,
        "status": "CERTIFIED_FULL_SATURATED",
        "subject_sha256": lattice.object_sha256(subject),
        "method": "signed-control-full-basis",
        "proof_artifact_sha256": PROOF_HASH,
    }
    return result


def signed_control_verifier(receipt: dict, request: dict) -> dict:
    return {
        "schema": lattice.VERIFIER_SCHEMA,
        "status": "PASS",
        "subject_sha256": request["subject_sha256"],
        "receipt_sha256": lattice.object_sha256(receipt),
        "verifier_identity_sha256": TRUSTED_VERIFIER,
        "signature_verified": True,
        "independent": True,
    }


def rank_one_fixture() -> dict:
    curve = {"ainvs": [0, 0, 0, 0, -2]}
    ainvs = tuple(Fraction(value) for value in curve["ainvs"])
    point = (Fraction(3), Fraction(5))
    twice = ec.point_mul(2, point, ainvs)
    return attach_receipt(
        {
            "schema": lattice.INPUT_SCHEMA,
            "curve": curve,
            "free_basis": [jpoint(point)],
            "torsion": {"invariants": [], "generators": []},
            "selected_points": [jpoint(point), jpoint(twice)],
            "coordinates": {"free": [[1], [2]], "torsion": [[], []]},
            "relation_basis": [[2, -1]],
            "target_index": 1,
            "source_subgroup_order": 23,
            "full_basis_receipt": None,
        }
    )


def independent_fixture() -> dict:
    # The signed control receipt supplies the full-basis assertion.  This module
    # verifies only the exact consequences of that assertion.
    point = [3, 2]
    other = [4, 6]
    return attach_receipt(
        {
            "schema": lattice.INPUT_SCHEMA,
            "curve": {"ainvs": [0, 0, 0, -5, -8]},
            "free_basis": [point, other],
            "torsion": {"invariants": [], "generators": []},
            "selected_points": [point, other],
            "coordinates": {"free": [[1, 0], [0, 1]], "torsion": [[], []]},
            "relation_basis": [],
            "target_index": 1,
            "source_subgroup_order": 23,
            "full_basis_receipt": None,
        }
    )


def opposite_fixture() -> dict:
    return attach_receipt(
        {
            "schema": lattice.INPUT_SCHEMA,
            "curve": {"ainvs": [0, 0, 0, 0, -2]},
            "free_basis": [[3, 5]],
            "torsion": {"invariants": [], "generators": []},
            "selected_points": [[3, 5], [3, -5]],
            "coordinates": {"free": [[1], [-1]], "torsion": [[], []]},
            "relation_basis": [[1, 1]],
            "target_index": 1,
            "source_subgroup_order": 23,
            "full_basis_receipt": None,
        }
    )


def torsion_fixture() -> dict:
    return attach_receipt(
        {
            "schema": lattice.INPUT_SCHEMA,
            "curve": {"ainvs": [0, 0, 0, -1, 0]},
            "free_basis": [],
            "torsion": {"invariants": [2, 2], "generators": [[0, 0], [1, 0]]},
            "selected_points": [[0, 0], [1, 0], [-1, 0]],
            "coordinates": {
                "free": [[], [], []],
                "torsion": [[1, 0], [0, 1], [1, 1]],
            },
            "relation_basis": [[2, 0, 0], [0, 2, 0], [1, 1, 1]],
            "target_index": 2,
            "source_subgroup_order": 5,
            "full_basis_receipt": None,
        }
    )


def build(value: dict) -> dict:
    return lattice.build_relation_lattice_certificate(
        value,
        basis_verifier=signed_control_verifier,
        trusted_verifier_sha256=TRUSTED_VERIFIER,
    )


class RelationLatticeTests(unittest.TestCase):
    def test_rank_one_planted_relation_is_conditionally_complete(self):
        certificate = build(rank_one_fixture())
        self.assertEqual(certificate["status"], "CONDITIONAL_STRUCTURE_ONLY")
        self.assertEqual(certificate["matrix_certificate"]["kernel_rank"], 1)
        self.assertEqual(certificate["matrix_certificate"]["maximal_minor_gcd"], 1)
        self.assertEqual(certificate["outcome"]["selected_dependence"], "UNKNOWN")
        self.assertEqual(
            certificate["outcome"]["conditional_selected_dependence"], "CERT_YES"
        )
        self.assertEqual(certificate["outcome"]["target_coefficient_gcd"], 1)
        self.assertIsNone(
            certificate["outcome"]["conditional_invertible_target_relation_exists"]
        )
        self.assertEqual(certificate["source_binding"]["status"], "UNBOUND")
        self.assertTrue(
            certificate["source_binding"]["conditional_invertibility_suppressed"]
        )
        self.assertFalse(certificate["production_eligible"])
        self.assertEqual(
            lattice.verify_relation_lattice_certificate(
                certificate,
                basis_verifier=signed_control_verifier,
                trusted_verifier_sha256=TRUSTED_VERIFIER,
            ),
            [],
        )

    def test_semantic_complexity_limits_fail_before_curve_arithmetic(self):
        cases = []

        oversized_basis = rank_one_fixture()
        oversized_basis["free_basis"] = [[3, 5]] * (
            lattice.MAX_FREE_BASIS_RANK + 1
        )
        cases.append(oversized_basis)

        oversized_torsion = rank_one_fixture()
        oversized_torsion["torsion"] = {
            "invariants": [2] * (lattice.MAX_TORSION_FACTORS + 1),
            "generators": [[3, 5]] * (lattice.MAX_TORSION_FACTORS + 1),
        }
        cases.append(oversized_torsion)

        oversized_scalar = rank_one_fixture()
        oversized_scalar["coordinates"]["free"][0][0] = (
            lattice.MAX_GROUP_SCALAR_ABS + 1
        )
        cases.append(oversized_scalar)

        oversized_order = rank_one_fixture()
        oversized_order["source_subgroup_order"] = 1 << lattice.MAX_SUBGROUP_ORDER_BITS
        cases.append(oversized_order)

        for fixture in cases:
            with self.subTest(keys=sorted(fixture)):
                with mock.patch.object(
                    lattice.ec,
                    "on_curve",
                    side_effect=AssertionError("curve arithmetic reached"),
                ):
                    with self.assertRaises(lattice.RelationLatticeError) as caught:
                        build(fixture)
                self.assertEqual(caught.exception.code, "complexity")

    def test_json_and_matrix_budgets_fail_before_hashing(self):
        oversized_integer = rank_one_fixture()
        oversized_integer["target_index"] = 1 << lattice.MAX_JSON_INTEGER_BITS
        with mock.patch.object(
            lattice, "object_sha256", side_effect=AssertionError("hashing reached")
        ):
            with self.assertRaises(lattice.RelationLatticeError) as caught:
                build(oversized_integer)
        self.assertEqual(caught.exception.code, "complexity")

    def test_certificate_verification_preflights_before_hashing(self):
        certificate = build(rank_one_fixture())
        certificate["oversized"] = [None] * (lattice.MAX_CONTAINER_ITEMS + 1)
        with mock.patch.object(
            lattice, "object_sha256", side_effect=AssertionError("hashing reached")
        ):
            errors = lattice.verify_relation_lattice_certificate(
                certificate,
                basis_verifier=signed_control_verifier,
                trusted_verifier_sha256=TRUSTED_VERIFIER,
            )
        self.assertEqual(errors, ["certificate_preflight:complexity"])

        cyclic: dict = {}
        cyclic["self"] = cyclic
        with mock.patch.object(
            lattice, "object_sha256", side_effect=AssertionError("hashing reached")
        ):
            errors = lattice.verify_relation_lattice_certificate(
                cyclic,
                basis_verifier=signed_control_verifier,
                trusted_verifier_sha256=TRUSTED_VERIFIER,
            )
        self.assertEqual(errors, ["certificate_preflight:json"])

        oversized_matrix = rank_one_fixture()
        row_width = lattice.MAX_CONTAINER_ITEMS
        row_count = lattice.MAX_MATRIX_ENTRIES // row_width + 1
        oversized_matrix["relation_basis"] = [
            [0] * row_width for _ in range(row_count)
        ]
        with mock.patch.object(
            lattice, "object_sha256", side_effect=AssertionError("hashing reached")
        ):
            with self.assertRaises(lattice.RelationLatticeError) as caught:
                build(oversized_matrix)
        self.assertEqual(caught.exception.code, "complexity")

    def test_rational_coordinate_bit_limit(self):
        fixture = rank_one_fixture()
        fixture["curve"]["ainvs"][0] = str(1 << lattice.MAX_RATIONAL_BITS)
        fixture = attach_receipt(fixture)
        with self.assertRaises(lattice.RelationLatticeError) as caught:
            build(fixture)
        self.assertEqual(caught.exception.code, "complexity")

    def test_independent_row_selection_is_linear_scan(self):
        matrix = [[1, 0]] * (lattice.MAX_FREE_BASIS_RANK - 2)
        matrix.extend([[0, 1], [1, 1]])
        self.assertEqual(
            lattice.independent_row_indices(matrix, 2),
            [0, lattice.MAX_FREE_BASIS_RANK - 2],
        )

    def test_derived_bezout_scalars_cannot_bypass_replay_limit(self):
        # Every supplied coefficient is within the input ceiling, including a
        # negative target value, but iterative Bezout coefficients for these
        # four values are much larger.  Reject before they can reach _sum_points.
        relation_basis = [[-80], [116], [126], [117]]
        with mock.patch.object(
            lattice,
            "_sum_points",
            side_effect=AssertionError("exact group replay reached"),
        ):
            with self.assertRaises(lattice.RelationLatticeError) as caught:
                lattice._bounded_target_witness(relation_basis, 0, 1)
        self.assertEqual(caught.exception.code, "complexity")

    def test_independence_uses_exact_nonzero_free_minor(self):
        certificate = build(independent_fixture())
        self.assertEqual(certificate["matrix_certificate"]["kernel_rank"], 0)
        self.assertEqual(certificate["outcome"]["selected_dependence"], "UNKNOWN")
        self.assertEqual(
            certificate["outcome"]["conditional_selected_dependence"], "CERT_NO"
        )
        self.assertTrue(certificate["outcome"]["conditional_selected_independent"])
        self.assertEqual(certificate["outcome"]["independence_minor"]["determinant"], 1)
        self.assertIsNone(
            certificate["outcome"]["conditional_invertible_target_relation_exists"]
        )

    def test_torsion_congruence_kernel_is_conditionally_complete(self):
        certificate = build(torsion_fixture())
        matrix = certificate["matrix_certificate"]
        self.assertEqual(matrix["kernel_rank"], 3)
        self.assertEqual(matrix["extended_kernel_rank"], 3)
        self.assertEqual(matrix["maximal_minor_gcd"], 1)
        self.assertEqual(certificate["outcome"]["target_coefficient_gcd"], 1)
        self.assertEqual(certificate["outcome"]["target_gcd_relation"], [1, 1, 1])

    def test_nonprimitive_sublattice_is_rejected(self):
        fixture = rank_one_fixture()
        fixture["relation_basis"] = [[4, -2]]
        with self.assertRaisesRegex(lattice.RelationLatticeError, "finite-index") as caught:
            build(fixture)
        self.assertEqual(caught.exception.code, "kernel_not_primitive")

    def test_missing_relation_basis_vector_is_rejected(self):
        fixture = torsion_fixture()
        fixture["relation_basis"].pop()
        with self.assertRaises(lattice.RelationLatticeError) as caught:
            build(fixture)
        self.assertEqual(caught.exception.code, "kernel_rank")

    def test_false_relation_and_wrong_decomposition_are_rejected(self):
        fixture = rank_one_fixture()
        fixture["relation_basis"] = [[1, -1]]
        with self.assertRaises(lattice.RelationLatticeError) as caught:
            build(fixture)
        self.assertEqual(caught.exception.code, "kernel")
        fixture = rank_one_fixture()
        fixture["coordinates"]["free"][1] = [3]
        with self.assertRaises(lattice.RelationLatticeError) as caught:
            build(fixture)
        self.assertEqual(caught.exception.code, "decomposition")

    def test_exact_torsion_order_is_replayed(self):
        fixture = torsion_fixture()
        fixture["torsion"]["invariants"] = [2, 4]
        fixture = attach_receipt(fixture)
        with self.assertRaises(lattice.RelationLatticeError) as caught:
            build(fixture)
        self.assertEqual(caught.exception.code, "torsion")

    def test_non_mazur_torsion_is_rejected_before_factoring(self):
        fixture = torsion_fixture()
        fixture["torsion"]["invariants"] = [2, 2**4096]
        with mock.patch.object(
            lattice,
            "_prime_divisors",
            side_effect=AssertionError("factorization must not be reached"),
        ):
            with self.assertRaises(lattice.RelationLatticeError) as caught:
                build(fixture)
        self.assertEqual(caught.exception.code, "torsion_structure")

    def test_unbound_source_suppresses_target_invertibility(self):
        fixture = rank_one_fixture()
        fixture["target_index"] = 0
        fixture["source_subgroup_order"] = 2
        certificate = build(fixture)
        self.assertEqual(certificate["outcome"]["target_coefficient_gcd"], 2)
        self.assertIsNone(
            certificate["outcome"]["conditional_invertible_target_relation_exists"]
        )
        self.assertIsNone(
            certificate["outcome"]["conditional_target_gcd_coprime_to_subgroup_order"]
        )
        self.assertEqual(
            certificate["outcome"]["conditional_invertibility_scope"],
            "UNBOUND_SUPPRESSED",
        )
        self.assertEqual(certificate["outcome"]["source_subgroup_order"], "UNBOUND")
        self.assertEqual(certificate["outcome"]["claimed_source_subgroup_order"], 2)

    def test_arbitrary_callback_cannot_promote_p_plus_negative_p(self):
        # The relation is algebraically real: P + (-P) = O.  The exploit is
        # trusting a producer callback to assert that P is a full saturated MW
        # basis.  Structural replay may retain the conditional relation, but it
        # must never turn that callback into an independent certificate.
        fixture = opposite_fixture()
        ainvs = tuple(Fraction(value) for value in fixture["curve"]["ainvs"])
        points = [
            (Fraction(point[0]), Fraction(point[1]))
            for point in fixture["selected_points"]
        ]
        self.assertIsNone(ec.relation_sum([1, 1], points, ainvs))
        certificate = build(fixture)
        self.assertEqual(certificate["matrix_certificate"]["relation_basis"], [[1, 1]])
        self.assertEqual(
            certificate["outcome"]["conditional_selected_dependence"], "CERT_YES"
        )
        self.assertEqual(certificate["outcome"]["selected_dependence"], "UNKNOWN")
        self.assertFalse(certificate["outcome"]["complete_relation_lattice"])
        self.assertFalse(certificate["production_eligible"])
        self.assertEqual(
            certificate["basis_verifier"]["standing"],
            "CALLER_SUPPLIED_NOT_INDEPENDENT",
        )
        self.assertFalse(certificate["basis_verifier"]["production_eligible"])
        self.assertFalse(certificate["repository_trust"]["production_ready"])
        self.assertFalse(lattice.PRODUCTION_READY)

    def test_basis_receipt_and_trusted_verifier_are_mandatory(self):
        fixture = rank_one_fixture()
        with self.assertRaises(lattice.RelationLatticeError) as caught:
            lattice.build_relation_lattice_certificate(
                fixture, basis_verifier=None, trusted_verifier_sha256=TRUSTED_VERIFIER
            )
        self.assertEqual(caught.exception.code, "basis_verifier_unavailable")
        bad = copy.deepcopy(fixture)
        bad["full_basis_receipt"]["status"] = "PARI_RANK_BOUNDS_ONLY"
        with self.assertRaises(lattice.RelationLatticeError) as caught:
            build(bad)
        self.assertEqual(caught.exception.code, "basis_receipt")

    def test_wrong_verifier_identity_signature_or_subject_rejected(self):
        fixture = rank_one_fixture()

        def wrong_identity(receipt, request):
            result = signed_control_verifier(receipt, request)
            result["verifier_identity_sha256"] = "c" * 64
            return result

        with self.assertRaises(lattice.RelationLatticeError) as caught:
            lattice.build_relation_lattice_certificate(
                fixture,
                basis_verifier=wrong_identity,
                trusted_verifier_sha256=TRUSTED_VERIFIER,
            )
        self.assertEqual(caught.exception.code, "basis_verifier")

        def unsigned(receipt, request):
            result = signed_control_verifier(receipt, request)
            result["signature_verified"] = False
            return result

        with self.assertRaises(lattice.RelationLatticeError):
            lattice.build_relation_lattice_certificate(
                fixture,
                basis_verifier=unsigned,
                trusted_verifier_sha256=TRUSTED_VERIFIER,
            )

    def test_receipt_extra_pari_bounds_and_arbitrary_proof_rejected(self):
        fixture = rank_one_fixture()
        fixture["full_basis_receipt"]["pari_rank_bounds"] = [1, 1]
        with self.assertRaises(lattice.RelationLatticeError) as caught:
            build(fixture)
        self.assertEqual(caught.exception.code, "schema")
        fixture = rank_one_fixture()
        fixture["full_basis_receipt"]["subject_sha256"] = "0" * 64
        with self.assertRaises(lattice.RelationLatticeError) as caught:
            build(fixture)
        self.assertEqual(caught.exception.code, "basis_receipt")

    def test_certificate_mutation_and_arbitrary_certificate_fail_replay(self):
        certificate = build(rank_one_fixture())
        certificate["outcome"]["selected_dependence"] = "CERT_NO"
        without_hash = dict(certificate)
        without_hash.pop("certificate_sha256")
        certificate["certificate_sha256"] = lattice.object_sha256(without_hash)
        errors = lattice.verify_relation_lattice_certificate(
            certificate,
            basis_verifier=signed_control_verifier,
            trusted_verifier_sha256=TRUSTED_VERIFIER,
        )
        self.assertIn("certificate_mismatch", errors)
        self.assertTrue(
            lattice.verify_relation_lattice_certificate(
                {"certificate_sha256": "0" * 64},
                basis_verifier=signed_control_verifier,
                trusted_verifier_sha256=TRUSTED_VERIFIER,
            )
        )


if __name__ == "__main__":
    unittest.main()
