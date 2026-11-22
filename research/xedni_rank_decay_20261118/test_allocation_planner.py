#!/usr/bin/env python3

from fractions import Fraction
import copy
import contextlib
import io
import json
import unittest

import allocation_planner as planner


class ExactArithmeticTests(unittest.TestCase):
    def test_ceil_nth_root_is_minimal(self):
        for degree in range(1, 8):
            for value in range(0, 500):
                root = planner.ceil_nth_root(value, degree)
                self.assertGreaterEqual(root**degree, value)
                if root:
                    self.assertLess((root - 1) ** degree, value)

    def test_top_bit_matches_frozen_power_arithmetic(self):
        self.assertEqual(
            planner.reference_top_bit_rows(Fraction(-1, 1)), 128_849_018_880
        )
        self.assertEqual(
            planner.reference_top_bit_rows(Fraction(-3, 4)), 503_316_480
        )
        self.assertEqual(
            planner.reference_top_bit_rows(Fraction(-1, 2)), 1_966_080
        )

    def test_invalid_inputs_fail_closed(self):
        with self.assertRaises(planner.AllocationError):
            planner.ceil_nth_root(4, 0)
        with self.assertRaises(planner.AllocationError):
            planner.trials_for_expected_events(20, Fraction(1, 2), 5)
        with self.assertRaises(planner.AllocationError):
            planner.two_phase_scenario(10, Fraction(0, 1), Fraction(1, 2))

    def test_integer_slot_split_is_exact_and_deterministic(self):
        self.assertEqual(planner.split_integer_across_slots(8), [3, 3, 2])
        self.assertEqual(planner.split_integer_across_slots(9), [3, 3, 3])
        with self.assertRaises(planner.AllocationError):
            planner.split_integer_across_slots(1, 0)

    def test_zero_event_reference_matches_frozen_check(self):
        result = planner.zero_event_exposure()
        self.assertEqual(result["trials"], 50_260_046)
        self.assertEqual(result["bits"], 32)
        self.assertEqual(result["beta"], "-3/4")
        self.assertIn("not a multi-profile power calculation", result["scope"])
        self.assertFalse(result["multiplicity_cluster_censoring_included"])


class FrozenDesignTests(unittest.TestCase):
    def test_frozen_counts_and_bootstrap_are_preserved(self):
        manifest = planner.build_manifest()
        frozen = manifest["frozen_requirements"]
        self.assertEqual(frozen["simultaneous_profiles"], 4320)
        self.assertEqual(frozen["bootstrap_replicates"], 172800)
        self.assertEqual(frozen["bootstrap_minimum_recomputed"], 172800)
        self.assertEqual(frozen["factor_cells"], 90)
        self.assertEqual(frozen["required_useful_event_sizes_per_stage"], [20, 22, 24])
        self.assertEqual(
            frozen["minimum_observed_high_bit_useful_events_combined_stages"], 30
        )

    def test_optional_scale_has_complete_matrix_and_stronger_scope(self):
        allocations = planner.build_manifest()["optional_stronger_full_factorial_scale"]
        for allocation in allocations:
            self.assertEqual(allocation["matrix_bits"], [16, 18, 20, 22, 24])
            self.assertEqual(
                allocation["optional_expected_high_bit_events_per_factor_cell_combined_stages"],
                30,
            )
            self.assertEqual(
                allocation["optional_expected_events_per_factor_cell_all_bits_combined_stages"],
                50,
            )
            self.assertEqual(
                allocation[
                    "total_rows_all_factor_cells_both_stages_if_executed"
                ],
                allocation["rows_per_factor_cell_both_stages"] * 90,
            )
            self.assertEqual(allocation["status"], "SCALE_ONLY")
        matrix = planner.build_manifest()["optional_execution_matrix"]
        self.assertEqual(matrix["bits"], [16, 18, 20, 22, 24])
        self.assertEqual(matrix["slot_order_for_all_arrays"], [0, 1, 2])
        self.assertEqual(matrix["source_sharing"]["rows_per_unique_source"], 45)
        self.assertFalse(matrix["prime_identity_reuse_between_stages_permitted"])
        stages = {item["stage"]: item for item in matrix["stage_matrices"]}
        self.assertEqual(set(stages), {"discovery", "replication"})
        self.assertEqual(stages["discovery"]["status"], "SCALE_ONLY_UNALLOCATED")
        self.assertEqual(stages["replication"]["status"], "UNALLOCATED")
        self.assertIsNone(stages["replication"]["prime_binding"]["path"])
        frozen_slots = planner.prime_slots()
        shared = matrix["shared_exposure_matrix_by_bit"]
        self.assertEqual([row["bits"] for row in shared], [16, 18, 20, 22, 24])
        for row in shared:
            self.assertEqual(len(row["scenarios"]), 3)
            self.assertEqual(
                {scenario["beta"] for scenario in row["scenarios"]},
                {"-1/1", "-3/4", "-1/2"},
            )
            for scenario in row["scenarios"]:
                split = scenario["trials_per_factor_cell_stage_by_slot"]
                self.assertEqual(len(split), 3)
                self.assertEqual(sum(split), scenario["rows_per_factor_cell_stage"])
                self.assertEqual(
                    scenario["unique_sources_per_curve_family_by_slot"], split
                )
                self.assertEqual(
                    scenario[
                        "source_index_stop_exclusive_per_curve_family_by_slot"
                    ],
                    split,
                )
                self.assertEqual(
                    scenario["unique_sources_all_curve_families_by_slot"],
                    [trials * 2 for trials in split],
                )
                self.assertEqual(
                    scenario["factor_rows_all_cells_by_slot"],
                    [trials * 90 for trials in split],
                )
        discovery_rows = {
            row["bits"]: row["slot_primes"]
            for row in stages["discovery"]["prime_binding"]["rows"]
        }
        replication_rows = {
            row["bits"]: row["slot_primes"]
            for row in stages["replication"]["prime_binding"]["rows"]
        }
        for bits in [16, 18, 20, 22, 24]:
            self.assertEqual(
                discovery_rows[bits], [row["prime"] for row in frozen_slots[bits]]
            )
            self.assertEqual(replication_rows[bits], [None, None, None])
        self.assertEqual(
            stages["replication"]["prime_binding"]["status"],
            "UNALLOCATED_MISSING_FRESH_PRIME_MANIFEST",
        )

    def test_protocol_rule_is_not_mislabeled_as_per_cell_power(self):
        manifest = planner.build_manifest()
        frozen = manifest["frozen_requirements"]
        self.assertEqual(
            frozen["minimum_observed_high_bit_useful_events_combined_stages"], 30
        )
        self.assertIn("global protocol rule", frozen["observation_rule_scope"])
        self.assertIn("one factor cell", frozen["analyzer_note"])
        top_bit = manifest["top_bit_expected_count_check"]
        self.assertIn("distinct", top_bit["scope"])
        self.assertEqual(top_bit["status"], "REFERENCE_SCALE_ONLY_NOT_POWERED")

    def test_calibration_timeout_ceiling(self):
        calibration = planner.calibration_budget()
        self.assertEqual(calibration["rows"], 1080)
        self.assertEqual(calibration["rank_timeout_seconds_per_row"], 2460)
        self.assertEqual(
            calibration["rank_timeout_ceiling"]["worker_seconds"], 2_656_800
        )
        self.assertEqual(
            calibration["rows"],
            len(calibration["bit_sizes"])
            * calibration["prime_slots_per_bit"]
            * calibration["factor_cells"]
            * calibration["rows_per_factor_cell_prime"],
        )
        self.assertEqual(calibration["feasibility"], "NOT_ESTABLISHED")


class TwoPhaseTests(unittest.TestCase):
    def test_full_census_is_the_only_generic_equivalent_option(self):
        full = planner.two_phase_scenario(1000, Fraction(1, 10), Fraction(1, 1))
        sampled = planner.two_phase_scenario(
            1000, Fraction(1, 10), Fraction(1, 10)
        )
        self.assertTrue(full["equivalent_exposure_established"])
        self.assertEqual(full["status"], "FULL_CENSUS")
        self.assertFalse(sampled["equivalent_exposure_established"])
        self.assertEqual(sampled["status"], "SCENARIO_ONLY_NOT_POWER_EQUIVALENT")
        self.assertLess(
            sampled["kish_effective_fraction_proxy"]["numerator"],
            sampled["kish_effective_fraction_proxy"]["denominator"],
        )

    def test_no_resource_claim_is_promoted(self):
        self.assertEqual(
            planner.validate_resource_commitment(None)["status"], "UNALLOCATED"
        )
        fake = {
            "workers": 5,
            "wall_seconds": 1,
            "storage_bytes": 1,
            "checkpoint_transport_verified": True,
            "licensed_magma_verified": True,
            "signed_commitment_sha256": "0" * 64,
        }
        self.assertEqual(
            planner.validate_resource_commitment(fake)["status"], "UNALLOCATED"
        )


class ManifestTests(unittest.TestCase):
    def test_imported_main_retains_argument_aware_cli(self):
        output = io.StringIO()
        path = planner.HERE / "POWER_ALLOCATION_20261119.json"
        with contextlib.redirect_stdout(output):
            self.assertEqual(planner.main(["--check", str(path)]), 0)
        self.assertEqual(
            json.loads(output.getvalue())["status"],
            "PASS_PROSPECTIVE_UNALLOCATED",
        )

    def test_manifest_is_exactly_recomputable_and_unallocated(self):
        manifest = planner.build_manifest()
        result = planner.validate_manifest(manifest)
        self.assertEqual(result["status"], "PASS_PROSPECTIVE_UNALLOCATED")
        self.assertEqual(manifest["status"], "UNALLOCATED")
        self.assertFalse(manifest["natural_rows_included"])
        self.assertTrue(manifest["allocation_decision"]["no_downscaling"])

    def test_manifest_mutation_and_rehash_do_not_change_frozen_recomputation(self):
        manifest = planner.build_manifest()
        mutated = copy.deepcopy(manifest)
        mutated["frozen_requirements"]["simultaneous_profiles"] = 1
        body = dict(mutated)
        body.pop("manifest_sha256")
        mutated["manifest_sha256"] = planner.object_sha256(body)
        with self.assertRaisesRegex(planner.AllocationError, "recomputation"):
            planner.validate_manifest(mutated)

    def test_checked_in_manifest_matches_generator(self):
        path = planner.HERE / "POWER_ALLOCATION_20261119.json"
        self.assertEqual(json.loads(path.read_text()), planner.build_manifest())


if __name__ == "__main__":
    unittest.main()
