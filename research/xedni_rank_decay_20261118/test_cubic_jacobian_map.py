#!/usr/bin/env python3
"""Adversarial controls for the explicit cubic/Jacobian transfer verifier."""

from __future__ import annotations

import copy
import unittest
from unittest import mock

import cubic_jacobian_map as target


def reseal(value: dict, field: str) -> None:
    value[field] = target.object_sha256({key: item for key, item in value.items() if key != field})


def reseal_certificate(certificate: dict) -> None:
    reseal(certificate, "certificate_sha256")


class CubicJacobianControlTests(unittest.TestCase):
    def test_identity_controls_r7_through_r9(self):
        for r in (7, 8, 9):
            certificate = target.build_identity_control(r)
            result = target.verify_certificate(certificate)
            self.assertEqual(result["status"], "VERIFIED_PROJECTIVE_LINEAR_TRANSFER")
            self.assertEqual(result["selected_point_count"], r)
            self.assertEqual(result["relation_count"], 1)
            self.assertFalse(result["production_eligible"])

    def test_characteristic_two_rejected_before_curve_work(self):
        certificate = target.build_identity_control()
        certificate["prime"] = 2
        reseal_certificate(certificate)
        with mock.patch.object(
            target, "_model", side_effect=AssertionError("curve work reached")
        ):
            with self.assertRaisesRegex(target.CubicMapError, "odd prime"):
                target.verify_certificate(certificate)

    def test_certificate_shape_limits_fail_before_hash_or_algebra(self):
        certificate = target.build_identity_control()
        certificate["relations"] = [None] * (target.MAX_CONTAINER_ITEMS + 1)
        with mock.patch.object(
            target, "object_sha256", side_effect=AssertionError("hashing reached")
        ):
            with self.assertRaisesRegex(target.CubicMapError, "container limit"):
                target.verify_certificate(certificate)

        certificate = target.build_identity_control()
        certificate["prime"] = 1 << target.MAX_JSON_INTEGER_BITS
        with mock.patch.object(
            target, "object_sha256", side_effect=AssertionError("hashing reached")
        ):
            with self.assertRaisesRegex(target.CubicMapError, "integer-bit limit"):
                target.verify_certificate(certificate)

    def test_polynomial_complexity_limits_fail_before_sympy_construction(self):
        mutations = {
            "terms": lambda equation: equation["terms"].extend(
                copy.deepcopy(equation["terms"][0])
                for _ in range(target.MAX_POLYNOMIAL_TERMS)
            ),
            "exponent": lambda equation: equation["terms"][0]["exponents"].__setitem__(
                0, target.MAX_POLYNOMIAL_EXPONENT + 1
            ),
            "coefficient": lambda equation: equation["terms"][0].__setitem__(
                "numerator", 1 << target.MAX_POLYNOMIAL_COEFFICIENT_BITS
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                certificate = target.build_identity_control()
                mutate(certificate["cubic"]["equation"])
                reseal(certificate["cubic"], "model_sha256")
                reseal_certificate(certificate)
                with mock.patch.object(
                    target.sp,
                    "Poly",
                    side_effect=AssertionError("SymPy construction reached"),
                ):
                    with self.assertRaises(target.CubicMapError):
                        target.verify_certificate(certificate)

    def test_symbolic_composition_expansion_has_explicit_ceiling(self):
        dense = target.sp.Poly(
            (target.x + target.y + target.z) ** target.MAX_MAP_COMPONENT_DEGREE,
            target.x,
            target.y,
            target.z,
            domain=target.sp.QQ,
        )
        with self.assertRaisesRegex(target.CubicMapError, "expansion limit"):
            target._require_bounded_composition(dense, [dense, dense, dense], "control")

    def test_group_replay_scalars_fail_before_curve_or_group_work(self):
        certificate = target.build_identity_control()
        certificate["selected_points"][0]["source_multiplier"] = (
            1 << target.MAX_SOURCE_MULTIPLIER_BITS
        )
        with mock.patch.object(
            target, "_model", side_effect=AssertionError("curve work reached")
        ):
            with self.assertRaisesRegex(target.CubicMapError, "source multiplier"):
                target.verify_certificate(certificate)

        certificate = target.build_identity_control()
        certificate["relations"][0]["coefficients"][0] = (
            target.MAX_RELATION_COEFFICIENT_ABS + 1
        )
        with mock.patch.object(
            target, "_model", side_effect=AssertionError("curve work reached")
        ):
            with self.assertRaisesRegex(target.CubicMapError, "relation coefficient"):
                target.verify_certificate(certificate)

        certificate = target.build_identity_control()
        certificate["relations"] = certificate["relations"] * (
            target.MAX_RELATIONS + 1
        )
        with mock.patch.object(
            target, "_model", side_effect=AssertionError("curve work reached")
        ):
            with self.assertRaisesRegex(target.CubicMapError, "relation count"):
                target.verify_certificate(certificate)

    def test_certificate_hash_mutation_rejected(self):
        certificate = target.build_identity_control()
        certificate["prime"] = 103
        with self.assertRaisesRegex(target.CubicMapError, "self hash mismatch"):
            target.verify_certificate(certificate)

    def test_forward_polynomial_semantic_mutation_rejected_after_reseal(self):
        certificate = target.build_identity_control()
        certificate["map"]["forward"][0]["terms"][0]["numerator"] = 2
        reseal(certificate["map"], "map_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "polynomial identity failed"):
            target.verify_certificate(certificate)

    def test_nonhomogeneous_map_component_rejected(self):
        certificate = target.build_identity_control()
        certificate["map"]["forward"][0]["terms"].append(
            {"exponents": [0, 0, 0], "numerator": 1, "denominator": 1}
        )
        reseal(certificate["map"], "map_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "must be homogeneous"):
            target.verify_certificate(certificate)

    def test_map_components_require_one_common_degree(self):
        certificate = target.build_identity_control()
        certificate["map"]["forward"][0]["terms"][0]["exponents"] = [2, 0, 0]
        reseal(certificate["map"], "map_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "one common degree"):
            target.verify_certificate(certificate)

    def test_multiplier_homogeneous_degree_is_bound(self):
        certificate = target.build_identity_control()
        certificate["map"]["forward_multiplier"] = {
            "variables": ["X", "Y", "Z"],
            "terms": [
                {"exponents": [1, 0, 0], "numerator": 1, "denominator": 1}
            ],
        }
        reseal(certificate["map"], "map_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "wrong homogeneous degree"):
            target.verify_certificate(certificate)

    def test_inverse_multiplier_homogeneous_degree_is_bound(self):
        certificate = target.build_identity_control()
        certificate["map"]["inverse_multiplier"] = {
            "variables": ["x", "y", "z"],
            "terms": [
                {"exponents": [1, 0, 0], "numerator": 1, "denominator": 1}
            ],
        }
        reseal(certificate["map"], "map_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "wrong homogeneous degree"):
            target.verify_certificate(certificate)

    def test_forward_point_mutation_rejected_after_reseal(self):
        certificate = target.build_identity_control()
        point = certificate["selected_points"][3]
        point["forward_coordinates"] = certificate["selected_points"][2]["forward_coordinates"]
        reseal(point, "point_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "forward image mismatch"):
            target.verify_certificate(certificate)

    def test_origin_translation_mutation_rejected(self):
        certificate = target.build_identity_control()
        origin = certificate["origin"]
        origin["translated_coordinates"] = ["0", "1", "1"]
        reseal(origin, "point_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "origin translation mismatch"):
            target.verify_certificate(certificate)

    def test_source_multiplier_mutation_rejected_after_full_reseal(self):
        certificate = target.build_identity_control()
        certificate["selected_points"][0]["source_multiplier"] += 10
        certificate["source_subgroup"]["selected_multipliers"][0] += 10
        reseal(certificate["selected_points"][0], "point_sha256")
        reseal(certificate["source_subgroup"], "source_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "forward source replay failed"):
            target.verify_certificate(certificate)

    def test_nonexact_source_order_rejected(self):
        certificate = target.build_identity_control()
        certificate["source_subgroup"]["generator_order"] *= 2
        reseal(certificate["source_subgroup"], "source_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "not exact"):
            target.verify_certificate(certificate)

    def test_source_order_above_hasse_bound_fails_before_factoring(self):
        certificate = target.build_identity_control()
        certificate["source_subgroup"]["generator_order"] = 10**30
        reseal(certificate["source_subgroup"], "source_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "exceeds Hasse bound"):
            target.verify_certificate(certificate)

    def test_relation_mutation_rejected_after_reseal(self):
        certificate = target.build_identity_control()
        certificate["relations"][0]["coefficients"][0] = 3
        reseal(certificate["relations"][0], "relation_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "relation.*replay failed"):
            target.verify_certificate(certificate)

    def test_bad_reduction_rejected_before_source_claim(self):
        certificate = target.build_identity_control()
        certificate["prime"] = 23
        certificate["source_subgroup"]["prime"] = 23
        reseal(certificate["source_subgroup"], "source_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "bad reduction"):
            target.verify_certificate(certificate)

    def test_selected_exceptional_point_rejected(self):
        certificate = target.build_identity_control()
        certificate["map"]["map_class"] = "birational_selected_points_only"
        certificate["map"]["exceptional_cubic_points"] = [
            certificate["selected_points"][0]["cubic_coordinates"]
        ]
        reseal(certificate["map"], "map_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "not in the base locus"):
            target.verify_certificate(certificate)

    def test_inverse_exceptional_forward_image_rejected(self):
        certificate = target.build_identity_control()
        certificate["map"]["map_class"] = "birational_selected_points_only"
        certificate["map"]["exceptional_jacobian_points"] = [
            certificate["selected_points"][0]["forward_coordinates"]
        ]
        reseal(certificate["map"], "map_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "not in the base locus"):
            target.verify_certificate(certificate)

    def test_exceptional_entry_must_lie_on_named_curve(self):
        certificate = target.build_identity_control()
        certificate["map"]["map_class"] = "birational_selected_points_only"
        certificate["map"]["exceptional_cubic_points"] = [["1", "0", "1"]]
        reseal(certificate["map"], "map_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "off the named curve"):
            target.verify_certificate(certificate)

    def test_offcurve_cubic_point_rejected_after_reseal(self):
        certificate = target.build_identity_control()
        point = certificate["selected_points"][0]
        point["cubic_coordinates"] = ["1", "0", "1"]
        reseal(point, "point_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "cubic point is off curve"):
            target.verify_certificate(certificate)

    def test_duplicate_point_ids_rejected(self):
        certificate = target.build_identity_control()
        point = certificate["selected_points"][1]
        point["point_id"] = certificate["selected_points"][0]["point_id"]
        reseal(point, "point_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "duplicate id"):
            target.verify_certificate(certificate)

    def test_duplicate_point_coordinates_rejected(self):
        certificate = target.build_identity_control()
        point = certificate["selected_points"][1]
        other = certificate["selected_points"][0]
        for key in (
            "cubic_coordinates",
            "forward_coordinates",
            "translated_coordinates",
            "source_multiplier",
        ):
            point[key] = copy.deepcopy(other[key])
        certificate["source_subgroup"]["selected_multipliers"][1] = other[
            "source_multiplier"
        ]
        reseal(point, "point_sha256")
        reseal(certificate["source_subgroup"], "source_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "must be distinct"):
            target.verify_certificate(certificate)

    def test_construction_unavailable_rejected(self):
        certificate = target.build_identity_control()
        certificate["construction"]["available"] = False
        certificate["construction"]["status"] = "BLOCKED"
        reseal(certificate["construction"], "construction_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "explicit map is unavailable"):
            target.verify_certificate(certificate)

    def test_construction_identity_is_nonempty_and_hash_bound(self):
        certificate = target.build_identity_control()
        construction = certificate["construction"]
        construction["identity"] = ""
        construction["backend_sha256"] = target.object_sha256(
            {
                "backend": construction["backend"],
                "version": construction["version"],
                "identity": construction["identity"],
            }
        )
        reseal(construction, "construction_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "nonempty string required"):
            target.verify_certificate(certificate)

        certificate = target.build_identity_control()
        construction = certificate["construction"]
        construction["version"] = "2"
        reseal(construction, "construction_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "identity mismatch"):
            target.verify_certificate(certificate)

    def test_construction_backend_hash_is_strict(self):
        certificate = target.build_identity_control()
        certificate["construction"]["backend_sha256"] = ""
        reseal(certificate["construction"], "construction_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "expected lowercase SHA-256"):
            target.verify_certificate(certificate)

    def test_strict_extra_keys_and_noncanonical_rationals(self):
        certificate = target.build_identity_control()
        certificate["map"]["extra"] = True
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "key mismatch"):
            target.verify_certificate(certificate)
        certificate = target.build_identity_control()
        point = certificate["selected_points"][0]
        point["cubic_coordinates"][0] = "2/2"
        reseal(point, "point_sha256")
        reseal_certificate(certificate)
        with self.assertRaisesRegex(target.CubicMapError, "not canonical"):
            target.verify_certificate(certificate)

    def test_map_inverse_composition_replayed(self):
        certificate = target.build_identity_control()
        inverse_component = certificate["map"]["inverse"][1]
        inverse_component["terms"][0]["exponents"] = [1, 0, 0]
        reseal(certificate["map"], "map_sha256")
        reseal_certificate(certificate)
        with self.assertRaises(target.CubicMapError):
            target.verify_certificate(certificate)

    def test_general_birational_class_remains_selected_points_only(self):
        certificate = target.build_identity_control()
        certificate["map"]["map_class"] = "birational_selected_points_only"
        reseal(certificate["map"], "map_sha256")
        reseal_certificate(certificate)
        result = target.verify_certificate(certificate)
        self.assertEqual(result["status"], "SELECTED_POINTS_ONLY")
        self.assertFalse(result["production_eligible"])

    def test_probe_does_not_promote_pari_coefficients_to_map(self):
        probe = target.construction_probe()
        self.assertEqual(
            probe["pari"]["ellfromeqn_scope"],
            "Jacobian coefficients only; no selected-point map",
        )
        if not probe["sage"]["available"] and not probe["magma"]["available"]:
            self.assertEqual(probe["status"], "BLOCKED_NO_EXPLICIT_CONSTRUCTOR")

    def test_deterministic_certificate_and_verification_hash(self):
        left = target.build_identity_control()
        right = target.build_identity_control()
        self.assertEqual(left, right)
        self.assertEqual(target.verify_certificate(left), target.verify_certificate(right))

    def test_input_is_not_mutated(self):
        certificate = target.build_identity_control()
        retained = copy.deepcopy(certificate)
        target.verify_certificate(certificate)
        self.assertEqual(certificate, retained)


if __name__ == "__main__":
    unittest.main()
