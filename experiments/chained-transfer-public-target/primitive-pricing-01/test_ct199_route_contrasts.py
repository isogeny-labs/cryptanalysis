#!/usr/bin/env python3
"""CT199 analytic source-only controls, not native route measurements/PCC."""
import math
import unittest
from unittest import mock
from fractions import Fraction

import ct188_physical_crossover_design as design
import ct190_block_fixed_effect_diagnostic as diagnostic
from test_ct190_block_fixed_effect_diagnostic import synthetic_records


class CT199CarryoverContrastTest(unittest.TestCase):
    def test_registered_48_packet_roster_has_exact_previous_B_share(self):
        self.assertTrue(diagnostic.assert_design())
        self.assertEqual(design.roster_sha256(),
                         diagnostic.EXPECTED_ROSTER_SHA256)
        for packet in range(design.PACKETS):
            self.assertEqual(diagnostic.previous_b_roster_share(packet),
                             Fraction(3, 8))
        self.assertEqual(sum(design.model_row(s, pos)[5]
                             for s in design.SEQUENCES
                             for pos in range(4)), 12)

    def test_null_is_null_under_all_estimands(self):
        result = diagnostic.analyze_untrusted_times(synthetic_records())
        self.assertEqual(result["roster_standardization_previous_B_fraction"],
                         "3/8")
        for name in ("median_direct_over_retained_ratio_block_fixed",
                     "median_direct_over_retained_ratio_previous_A",
                     "median_direct_over_retained_ratio_previous_B",
                     "median_direct_over_retained_ratio_roster_standardized"):
            self.assertAlmostEqual(result[name], 1.0, places=7)
        self.assertEqual(len(result["per_packet_direct_over_retained_log_ratios"]),
                         48)
        self.assertFalse(result["signed_independent_pcc"])

    def test_interaction_requires_distinct_conditional_and_marginal_ratios(self):
        # Independent analytic oracle: direct is 25% more costly with prev=A.
        # With prev=B, B route has a further 8% latency modifier.
        # A common previous_B 15% latency factor cancels from route contrast.
        result = diagnostic.analyze_untrusted_times(
            synthetic_records(block_shock=True, direct_cost=1.25,
                              previous_b_cost=1.15, interaction_cost=1.08))
        self.assertAlmostEqual(
            result["median_direct_over_retained_ratio_previous_A"],
            1.25, places=6)
        self.assertAlmostEqual(
            result["median_direct_over_retained_ratio_previous_B"],
            1.25 / 1.08, places=6)
        self.assertAlmostEqual(
            result["median_direct_over_retained_ratio_roster_standardized"],
            1.25 / 1.08 ** (3 / 8), places=6)
        self.assertAlmostEqual(
            result["median_direct_over_retained_ratio_block_fixed"],
            result["median_direct_over_retained_ratio_previous_A"], places=12)
        self.assertIn("previous_B=0", result["legacy_ratio_condition"])
        self.assertFalse(result["complete_single_target_ecdlp_advantage_established"])

    def test_misleading_previous_A_ratio_can_reverse_direction(self):
        # A 1.05 previous-A gain coexists with an overall roster-standardized
        # model loss when a physical B-after-B interaction is expensive.
        result = diagnostic.analyze_untrusted_times(
            synthetic_records(direct_cost=1.05, interaction_cost=1.7))
        self.assertGreater(result["median_direct_over_retained_ratio_previous_A"], 1)
        self.assertLess(result["median_direct_over_retained_ratio_previous_B"], 1)
        self.assertLess(result["median_direct_over_retained_ratio_roster_standardized"], 1)
        self.assertAlmostEqual(
            result["median_direct_over_retained_ratio_roster_standardized"],
            1.05 / 1.7 ** (3 / 8), places=6)

    def test_nuisance_only_carryover_does_not_change_contrast(self):
        result = diagnostic.analyze_untrusted_times(
            synthetic_records(previous_b_cost=1.5, direct_cost=1.13))
        for name in ("median_direct_over_retained_ratio_previous_A",
                     "median_direct_over_retained_ratio_previous_B",
                     "median_direct_over_retained_ratio_roster_standardized"):
            self.assertAlmostEqual(result[name], 1.13, places=6)

    def test_corrupted_previous_B_cohort_refused_before_scoring(self):
        original = design.order

        def tampered_order(block, packet):
            seq = original(block, packet)
            if block == 0 and packet == 0:
                return "AAAAAA"
            return seq

        with mock.patch.object(design, "order", side_effect=tampered_order):
            with self.assertRaises(ValueError):
                diagnostic.previous_b_roster_share(0)
            with self.assertRaises(ValueError):
                diagnostic.assert_design()


if __name__ == "__main__":
    unittest.main()
