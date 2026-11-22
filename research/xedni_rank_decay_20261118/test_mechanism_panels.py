#!/usr/bin/env python3
"""Mutation, leakage, selector, and certificate controls for M1--M6."""

from __future__ import annotations

import copy
from decimal import Decimal, ROUND_DOWN, localcontext
import hashlib
import json
import unittest

import invariants_pari
import mechanism_panels as panels


def digest(index: int) -> str:
    return f"{index:064x}"


def work(scale: int = 1) -> dict[str, int]:
    return {
        "attempts": scale,
        "rejections": scale + 1,
        "public_group_operations": scale + 2,
        "cpu_ns": scale + 3,
        "retained_bytes": scale + 4,
    }


def candidate(
    identifier: str,
    iso_class: str,
    features: dict,
    scale: int = 1,
) -> dict:
    return {
        "candidate_id": identifier,
        "q_isomorphism_class": iso_class,
        "public_features": features,
        "construction_work": work(scale),
    }


def frozen_bank(panel: str, candidates: list[dict], p: int = 65521):
    manifest = panels.freeze_candidate_bank(
        panel, p, f"{panel.lower()}-bank-{p}", candidates, len(candidates)
    )
    return manifest, panels.prepare_candidate_bank(manifest, len(candidates))


def invariant_record(
    index: int,
    raw_delta: int,
    delta_min: int,
    max_height: str,
    stable_rho: str,
) -> dict:
    value = Decimal(stable_rho)
    significand = "".join(str(digit) for digit in value.as_tuple().digits)
    candidate_hash = digest(100 + index)
    record = {
        "adapter": "pari-minimal-height-invariants-v1",
        "status": "OK",
        "reason": "computed",
        "row_id": f"invariant-{index}",
        "construction_discriminant": str(raw_delta),
        "minimal_model": {"discriminant": str(delta_min)},
        "max_canonical_height": max_height,
        "rho": stable_rho,
        "candidate_sha256": candidate_hash,
        "stable_selection_key": [
            value.adjusted(),
            significand,
            candidate_hash,
            f"invariant-{index}",
        ],
        "rho_stability": {
            "stable_40_significant_digit_key": stable_rho,
            "low_precision_max_height": max_height,
            "low_precision_rho": stable_rho,
        },
    }
    evidence = invariants_pari.selection_evidence(record)
    encoded = json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()
    record["selection_evidence_sha256"] = hashlib.sha256(encoded).hexdigest()
    return record


def m1_candidates(*, panel="M1") -> list[dict]:
    records = [
        invariant_record(
            0,
            -100,
            -20,
            "2.000000000000000000000000000000000000000",
            "1.500000000000000000000000000000000000000E+0",
        ),
        invariant_record(
            1,
            10,
            100,
            "100.0000000000000000000000000000000000000",
            "4.600000000000000000000000000000000000000E-2",
        ),
        invariant_record(
            2,
            -30,
            -5,
            "1.000000000000000000000000000000000000000",
            "1.600000000000000000000000000000000000000E+0",
        ),
    ]
    return [
        candidate(
            f"c{index}", f"iso-{index}",
            panels.m1_features_from_invariants(
                record, is_balanced=(index == 0) if panel == "M1" else None
            ),
            index + 1,
        )
        for index, record in enumerate(records)
    ]


def m4_point(point_id: str, certificate_index: int) -> dict:
    return {
        "point_id": point_id,
        "cubic_coordinates": [point_id, "1", "1"],
        "jacobian_coordinates": [point_id, "2"],
        "image_verified": True,
        "source_replay_verified": True,
        "certificate_hash": digest(certificate_index),
    }


def m4_certificate() -> dict:
    return {
        "cubic_model": {"equation": "F(X,Y,Z)=0", "model_hash": digest(1)},
        "jacobian_model": {"equation": "y^2=x^3+Ax+B", "model_hash": digest(2)},
        "cubic_to_jacobian_map": {"formula": "phi(X:Y:Z)", "map_hash": digest(3)},
        "good_reduction_certified": True,
        "origin_certificate": m4_point("origin", 4),
        "selected_point_certificates": [m4_point("p0", 5), m4_point("p1", 6)],
    }


def m5_point(point_id: str, certificate_index: int) -> dict:
    return {
        "point_id": point_id,
        "source_coordinates": [point_id, "source"],
        "phi_image": [point_id, "neighbor"],
        "psi_phi_image": [point_id, "three-times"],
        "ell_multiple": [point_id, "three-times"],
        "composition_verified": True,
        "certificate_hash": digest(certificate_index),
    }


def m5_certificate() -> dict:
    return {
        "degree": 3,
        "subgroup_order": 7,
        "source_model": {"equation": "E", "model_hash": digest(11)},
        "neighbor_model": {"equation": "Eprime", "model_hash": digest(12)},
        "phi": {"formula": "phi(P)", "map_hash": digest(13), "degree": 3},
        "dual_psi": {"formula": "psi(Q)", "map_hash": digest(14), "degree": 3},
        "kernel_certificate": {
            "kernel_order": 3,
            "intersection_order": 1,
            "verified": True,
            "certificate_hash": digest(15),
        },
        "subgroup_certificate": {
            "source_order": 7,
            "image_order": 7,
            "verified": True,
            "certificate_hash": digest(16),
        },
        "point_certificates": [m5_point("p0", 17), m5_point("p1", 18)],
        "target_recovery_verified": True,
    }


class CandidateBankTests(unittest.TestCase):
    def test_constant_k_hash_and_q_isomorphism_work_retention(self):
        rows = [
            candidate("c0", "iso-a", {"proxy": 1}, 1),
            candidate("c1", "iso-a", {"proxy": 2}, 10),
            candidate("c2", "iso-b", {"proxy": 3}, 100),
        ]
        manifest, prepared = frozen_bank("M5", rows)
        self.assertEqual(prepared.constant_k, 3)
        self.assertEqual(prepared.representative_ids, ("c0", "c2"))
        self.assertEqual(prepared.duplicate_q_isomorphism_candidates, 1)
        self.assertEqual(
            prepared.construction_work()["attempts"],
            sum(row["construction_work"]["attempts"] for row in rows),
        )
        second = panels.freeze_candidate_bank(
            "M5", 131071, "m5-bank-131071", rows, 3
        )
        banks = panels.prepare_panel_banks([manifest, second], 3)
        self.assertEqual(len(banks), 2)

    def test_mutation_reorder_and_k_change_fail_closed(self):
        manifest = panels.freeze_candidate_bank("M1", 65521, "bank", m1_candidates(), 3)
        mutated = copy.deepcopy(manifest)
        mutated["candidates"][0]["public_features"]["raw_delta"] = "-99"
        with self.assertRaisesRegex(panels.MechanismError, "hash mismatch"):
            panels.prepare_candidate_bank(mutated, 3)
        reordered = copy.deepcopy(manifest)
        reordered["candidates"].reverse()
        with self.assertRaisesRegex(panels.MechanismError, "hash mismatch"):
            panels.prepare_candidate_bank(reordered, 3)
        with self.assertRaisesRegex(panels.MechanismError, "K changed"):
            panels.prepare_candidate_bank(manifest, 4)

    def test_duplicate_ids_nan_and_outcome_leakage_are_rejected(self):
        duplicate = m1_candidates()
        duplicate[1]["candidate_id"] = duplicate[0]["candidate_id"]
        with self.assertRaisesRegex(panels.MechanismError, "duplicate candidate"):
            panels.freeze_candidate_bank("M1", 65521, "bank", duplicate, 3)
        bad_nan = m1_candidates()
        bad_nan[0]["public_features"]["max_height"] = "NaN"
        with self.assertRaises(panels.MechanismError):
            _, bad_bank = frozen_bank("M1", bad_nan)
            panels.select_m1(bad_bank, "nan-control")
        for leaked_name in ("rank_upper", "relation_vector", "useful_recovery"):
            leaked = m1_candidates()
            leaked[0]["public_features"][leaked_name] = 0
            with self.assertRaisesRegex(panels.MechanismError, "forbidden"):
                panels.freeze_candidate_bank("M1", 65521, "bank", leaked, 3)


class M1Tests(unittest.TestCase):
    def test_all_selectors_are_deterministic_and_use_named_public_scores(self):
        _, bank = frozen_bank("M1", m1_candidates())
        first = panels.select_m1(bank, "m1-selector-seed")
        second = panels.select_m1(bank, "m1-selector-seed")
        self.assertEqual(first, second)
        self.assertEqual(
            first["mandatory_direct_source_baseline"],
            "DIRECT_SOURCE_RELATION_TEST",
        )
        selected = first["selections"]
        self.assertEqual(selected["balanced"], "c0")
        self.assertEqual(selected["min_raw_delta"], "c1")
        self.assertEqual(selected["min_delta_min"], "c2")
        self.assertEqual(
            selected["min_log_abs_delta_min_over_max_height"], "c1"
        )
        self.assertEqual(
            set(selected),
            {
                "balanced",
                "deterministic_random",
                "min_raw_delta",
                "min_delta_min",
                "min_log_abs_delta_min_over_max_height",
                "permuted_score_null",
            },
        )

    def test_positive_height_and_exact_feature_allowlist(self):
        rows = m1_candidates()
        rows[0]["public_features"]["max_height"] = "0"
        _, bank = frozen_bank("M1", rows)
        with self.assertRaisesRegex(panels.MechanismError, "strictly positive"):
            panels.select_m1(bank, "seed")
        rows = m1_candidates()
        rows[0]["public_features"]["unused_public_score"] = 4
        _, bank = frozen_bank("M1", rows)
        with self.assertRaisesRegex(panels.MechanismError, "feature mismatch"):
            panels.select_m1(bank, "seed")

    def test_invariant_adapter_is_hash_bound_and_uses_no_float_score(self):
        record = invariant_record(
            9,
            -100,
            -20,
            "2.000000000000000000000000000000000000000",
            "1.500000000000000000000000000000000000000E+0",
        )
        features = panels.m1_features_from_invariants(record)
        self.assertIsInstance(features["raw_delta"], str)
        self.assertIsInstance(features["delta_min"], str)
        self.assertIsInstance(features["max_height"], str)
        self.assertRegex(features["invariants_sha256"], r"^[0-9a-f]{64}$")
        changed = copy.deepcopy(record)
        changed["stable_selection_key"][1] = "9" * 40
        with self.assertRaisesRegex(panels.MechanismError, "does not replay"):
            panels.m1_features_from_invariants(changed)
        for field, value, reason in (
            ("rho", "1.6", "does not replay"),
            ("row_id", "another-row", "does not replay"),
            ("max_canonical_height", 2.0, "decimal strings"),
            ("construction_discriminant", "-99", "hash mismatch"),
        ):
            with self.subTest(field=field), self.assertRaisesRegex(panels.MechanismError, reason):
                panels.m1_features_from_invariants({**record, field: value})

    def test_selection_values_ignore_rounding_context_and_observation_noise(self):
        record = invariant_record(
            9, 100, 100, "2", "1.500000000000000000000000000000000000000E+0"
        )
        features = panels.m1_features_from_invariants(record, is_balanced=True)
        with localcontext() as context:
            context.prec = 8
            context.rounding = ROUND_DOWN
            repeated = panels.m1_features_from_invariants(
                {**record, "execution": {"wall_ns": 23}, "max_canonical_height": "2.0000"},
                is_balanced=True,
            )
        self.assertEqual(repeated, features)

        rows = m1_candidates()
        _, bank = frozen_bank("M1", rows)
        rows[0]["construction_work"]["cpu_ns"] += 1000
        _, repeated_bank = frozen_bank("M1", rows)
        first = panels.select_m1(bank, "seed")
        second = panels.select_m1(repeated_bank, "seed")
        self.assertNotEqual(first["candidate_bank_hash"], second["candidate_bank_hash"])
        self.assertEqual(first["selection_input_sha256"], second["selection_input_sha256"])
        self.assertEqual(first["selections"], second["selections"])
        self.assertEqual(first["permuted_score_assignment_hash"], second["permuted_score_assignment_hash"])

    def test_balanced_comparator_requires_one_strict_boolean_representative(self):
        for index, flag, reason in (
            (0, False, "exactly one balanced representative"),
            (1, True, "exactly one balanced representative"),
            (0, 1, "expected a boolean"),
        ):
            rows = m1_candidates()
            rows[index]["public_features"]["is_balanced"] = flag
            _, bank = frozen_bank("M1", rows)
            with self.subTest(index=index, flag=flag), self.assertRaisesRegex(panels.MechanismError, reason):
                panels.select_m1(bank, "seed")
        rows = m1_candidates()
        rows[0]["public_features"]["is_balanced"] = False
        rows[1]["public_features"]["is_balanced"] = True
        rows[1]["q_isomorphism_class"] = rows[0]["q_isomorphism_class"]
        _, bank = frozen_bank("M1", rows)
        with self.assertRaisesRegex(panels.MechanismError, "exactly one balanced representative"):
            panels.select_m1(bank, "seed")
        manifest, _ = frozen_bank("M1", m1_candidates())
        manifest["candidates"][0]["public_features"]["is_balanced"] = False
        with self.assertRaisesRegex(panels.MechanismError, "hash mismatch"):
            panels.prepare_candidate_bank(manifest, 3)

    def test_distinct_decimal_scores_that_round_to_same_float_keep_their_order(self):
        records = [
            invariant_record(0, 37, 37, "4", "1.000000000000000000000000000000000000002E+0"),
            invariant_record(1, 37, 37, "4", "1.000000000000000000000000000000000000001E+0"),
        ]
        self.assertEqual(float(records[0]["rho"]), float(records[1]["rho"]))
        rows = [
            candidate(
                f"c{index}", f"iso-{index}",
                panels.m1_features_from_invariants(record, is_balanced=index == 0),
            )
            for index, record in enumerate(records)
        ]
        _, bank = frozen_bank("M1", rows)
        result = panels.select_m1(bank, "seed")
        self.assertEqual(result["selections"]["min_log_abs_delta_min_over_max_height"], "c1")

    def test_refreezing_mutated_score_does_not_match_adapter_evidence(self):
        rows = m1_candidates()
        rows[0]["public_features"]["stable_selection_key"][0] += 1
        _, bank = frozen_bank("M1", rows)
        with self.assertRaisesRegex(panels.MechanismError, "selection evidence hash mismatch"):
            panels.select_m1(bank, "seed")

    def test_m4_bank_uses_same_preoutcome_selectors(self):
        _, bank = frozen_bank("M4", m1_candidates(panel="M4"))
        selection = panels.select_m4_candidates(bank, "m4-seed")
        self.assertEqual(selection["panel"], "M4")
        self.assertEqual(selection["selections"]["min_raw_delta"], "c1")


class M2Tests(unittest.TestCase):
    def records(self):
        rows = []
        for index, arm in enumerate(panels.M2_LOCAL_ARMS, 1):
            if arm in ("A_none", "C_size_matched"):
                primes = []
            else:
                primes = [7, 11]
            rows.append(
                {
                    "arm": arm,
                    "auxiliary_primes": primes,
                    "crt_modulus": 1 if not primes else 77,
                    "quotient_compatible": arm != "I_incompatible",
                    "construction_work": work(index),
                }
            )
        return rows

    def test_all_arms_are_identified_and_incompatible_is_excluded(self):
        result = panels.validate_m2_arms(self.records())
        by_arm = {row["arm"]: row for row in result["arms"]}
        self.assertTrue(by_arm["B_reverse_mestre"]["primary_eligible"])
        self.assertFalse(by_arm["I_incompatible"]["primary_eligible"])
        self.assertFalse(by_arm["C_size_matched"]["primary_eligible"])
        self.assertEqual(result["disposition"], "MECHANISM_ONLY")
        self.assertEqual(
            result["mandatory_direct_source_baseline"],
            "DIRECT_SOURCE_RELATION_TEST",
        )

    def test_missing_mismatched_and_false_compatibility_controls_reject(self):
        with self.assertRaisesRegex(panels.MechanismError, "missing arms"):
            panels.validate_m2_arms(self.records()[:-1])
        mismatched = self.records()
        by_arm = {row["arm"]: row for row in mismatched}
        by_arm["P_neutral_crt"]["auxiliary_primes"] = [7]
        by_arm["P_neutral_crt"]["crt_modulus"] = 7
        with self.assertRaisesRegex(panels.MechanismError, "identical"):
            panels.validate_m2_arms(mismatched)
        composite = self.records()
        plus_one = next(
            row for row in composite if row["arm"] == "B_reverse_mestre_plus1"
        )
        plus_one["auxiliary_primes"] = [9]
        plus_one["crt_modulus"] = 9
        with self.assertRaisesRegex(panels.MechanismError, "composite"):
            panels.validate_m2_arms(composite)
        compatible = self.records()
        next(row for row in compatible if row["arm"] == "I_incompatible")[
            "quotient_compatible"
        ] = True
        with self.assertRaisesRegex(panels.MechanismError, "must be incompatible"):
            panels.validate_m2_arms(compatible)


class M3Tests(unittest.TestCase):
    def rows(self):
        return [
            candidate("c0", "iso-a", {"proxy_curvature": 3.0, "is_balanced": True}),
            candidate("c1", "iso-b", {"proxy_curvature": 1.0, "is_balanced": False}),
            candidate("c2", "iso-c", {"proxy_curvature": 2.0, "is_balanced": False}),
        ]

    def test_frozen_proxy_random_permuted_and_balanced(self):
        _, bank = frozen_bank("M3", self.rows())
        spec = panels.freeze_m3_selector("proxy_curvature", "min", "m3-seed")
        result = panels.select_m3(bank, spec, spec["selector_hash"])
        self.assertEqual(result["selections"]["nonlinear_proxy"], "c1")
        self.assertEqual(result["selections"]["balanced"], "c0")
        self.assertEqual(result, panels.select_m3(bank, spec, spec["selector_hash"]))

    def test_proxy_hash_mutation_and_leakage_reject(self):
        _, bank = frozen_bank("M3", self.rows())
        spec = panels.freeze_m3_selector("proxy_curvature", "min", "m3-seed")
        mutated = copy.deepcopy(spec)
        mutated["direction"] = "max"
        with self.assertRaisesRegex(panels.MechanismError, "mutated"):
            panels.select_m3(bank, mutated, spec["selector_hash"])
        with self.assertRaisesRegex(panels.MechanismError, "forbidden"):
            panels.freeze_m3_selector("rank_proxy", "min", "m3-seed")
        rows = self.rows()
        rows[0]["public_features"]["relation_hint"] = 1
        with self.assertRaisesRegex(panels.MechanismError, "forbidden"):
            panels.freeze_candidate_bank("M3", 65521, "bank", rows, 3)


class M4AdmissionTests(unittest.TestCase):
    def test_complete_map_origin_and_every_point_admit_mechanism_only(self):
        result = panels.admit_m4(m4_certificate(), ["p0", "p1"])
        self.assertTrue(result["certificate_gate_passed"])
        self.assertEqual(result["disposition"], "MECHANISM_ONLY")

    def test_missing_duplicate_or_false_replay_blocks(self):
        self.assertEqual(
            panels.admit_m4(None, ["p0", "p1"])["disposition"], "BLOCKED"
        )
        missing = m4_certificate()
        missing["selected_point_certificates"].pop()
        self.assertEqual(
            panels.admit_m4(missing, ["p0", "p1"])["disposition"], "BLOCKED"
        )
        duplicate = m4_certificate()
        duplicate["selected_point_certificates"][1]["point_id"] = "p0"
        self.assertEqual(
            panels.admit_m4(duplicate, ["p0", "p1"])["disposition"], "BLOCKED"
        )
        replay = m4_certificate()
        replay["origin_certificate"]["source_replay_verified"] = False
        self.assertEqual(
            panels.admit_m4(replay, ["p0", "p1"])["disposition"], "BLOCKED"
        )


class M5AdmissionTests(unittest.TestCase):
    def test_complete_isogeny_certificate_admits_mechanism_only(self):
        result = panels.admit_m5(m5_certificate(), 7, ["p0", "p1"], [2, 3, 5])
        self.assertTrue(result["certificate_gate_passed"])
        self.assertEqual(result["disposition"], "MECHANISM_ONLY")

    def test_degree_subgroup_dual_composition_and_recovery_fail_closed(self):
        wrong_source_order = m5_certificate()
        self.assertEqual(
            panels.admit_m5(wrong_source_order, 11, ["p0", "p1"], [3])[
                "disposition"
            ],
            "BLOCKED",
        )
        bad_gcd = m5_certificate()
        bad_gcd["subgroup_order"] = 3
        self.assertEqual(
            panels.admit_m5(bad_gcd, 3, ["p0", "p1"], [3])["disposition"],
            "BLOCKED",
        )
        missing_dual = m5_certificate()
        del missing_dual["dual_psi"]
        self.assertEqual(
            panels.admit_m5(missing_dual, 7, ["p0", "p1"], [3])["disposition"],
            "BLOCKED",
        )
        composition = m5_certificate()
        composition["point_certificates"][0]["ell_multiple"] = ["different"]
        self.assertEqual(
            panels.admit_m5(composition, 7, ["p0", "p1"], [3])["disposition"],
            "BLOCKED",
        )
        recovery = m5_certificate()
        recovery["target_recovery_verified"] = False
        self.assertEqual(
            panels.admit_m5(recovery, 7, ["p0", "p1"], [3])["disposition"],
            "BLOCKED",
        )


class M6Tests(unittest.TestCase):
    def rows(self):
        return [
            candidate("c0", "iso-a", {"trace_proxy": 1.0, "height_proxy": 0.0}),
            candidate("c1", "iso-b", {"trace_proxy": 0.0, "height_proxy": 10.0}),
            candidate("c2", "iso-c", {"trace_proxy": 3.0, "height_proxy": 1.0}),
        ]

    def test_disjoint_holdout_frozen_predictor_and_all_baselines(self):
        _, bank = frozen_bank("M6", self.rows())
        predictor = panels.freeze_m6_linear_predictor(
            ["development-a", "development-b"],
            ["trace_proxy", "height_proxy"],
            [2.0, -1.0],
            0.0,
        )
        permuted = panels.freeze_m6_linear_predictor(
            ["development-a", "development-b"],
            ["trace_proxy", "height_proxy"],
            [-1.0, 1.0],
            0.0,
            training_labels="permuted",
            label_permutation_hash=digest(30),
        )
        result = panels.select_m6(
            bank,
            predictor,
            predictor["predictor_hash"],
            permuted,
            permuted["predictor_hash"],
            ["holdout-a", "holdout-b"],
        )
        self.assertEqual(result["selections"]["frozen_predictor"], "c2")
        self.assertEqual(
            set(result["selections"]),
            {
                "frozen_predictor",
                "deterministic_random",
                "permuted_predictor",
                "direct_source_baseline",
            },
        )
        self.assertEqual(
            result["selections"]["direct_source_baseline"],
            "DIRECT_SOURCE_RELATION_TEST",
        )

    def test_seed_overlap_predictor_mutation_and_feature_leakage_reject(self):
        _, bank = frozen_bank("M6", self.rows())
        predictor = panels.freeze_m6_linear_predictor(
            ["development-a"],
            ["trace_proxy", "height_proxy"],
            [2.0, -1.0],
            0.0,
        )
        permuted = panels.freeze_m6_linear_predictor(
            ["development-a"],
            ["trace_proxy", "height_proxy"],
            [-1.0, 1.0],
            0.0,
            training_labels="permuted",
            label_permutation_hash=digest(31),
        )
        with self.assertRaisesRegex(panels.MechanismError, "disjoint"):
            panels.select_m6(
                bank,
                predictor,
                predictor["predictor_hash"],
                permuted,
                permuted["predictor_hash"],
                ["development-a"],
            )
        mutated = copy.deepcopy(predictor)
        mutated["weights"][0] = 99
        with self.assertRaisesRegex(panels.MechanismError, "mutated"):
            panels.select_m6(
                bank,
                mutated,
                predictor["predictor_hash"],
                permuted,
                permuted["predictor_hash"],
                ["holdout"],
            )
        with self.assertRaisesRegex(panels.MechanismError, "forbidden"):
            panels.freeze_m6_linear_predictor(
                ["development"], ["rank_hint"], [1.0], 0.0
            )
        rows = self.rows()
        rows[0]["public_features"]["relation_found"] = False
        with self.assertRaisesRegex(panels.MechanismError, "forbidden"):
            panels.freeze_candidate_bank("M6", 65521, "bank", rows, 3)


class DispositionTests(unittest.TestCase):
    def test_only_four_mechanism_dispositions_exist(self):
        self.assertEqual(
            panels.panel_disposition(blocked_reasons=["missing certificate"]),
            "BLOCKED",
        )
        self.assertEqual(panels.panel_disposition(), "NULL_IN_SCOPE")
        self.assertEqual(
            panels.panel_disposition(mechanism_signal=True), "MECHANISM_ONLY"
        )
        self.assertEqual(
            panels.panel_disposition(replicated_useful_signal=True),
            "REPLICATED_USEFUL_SIGNAL",
        )
        for value in panels.DISPOSITIONS:
            self.assertEqual(panels.validate_disposition(value), value)
        with self.assertRaisesRegex(panels.MechanismError, "never emit"):
            panels.validate_disposition("DEFEATED_IN_SCOPE")


if __name__ == "__main__":
    unittest.main()
