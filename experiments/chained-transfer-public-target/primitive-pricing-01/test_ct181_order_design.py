#!/usr/bin/env python3
"""CT181 source-only tests; no real Jacobian runtime or measurement."""
from collections import Counter
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct179_panel_adjudicator as legacy
import ct181_order_design as design

FIXTURE = (Path(__file__).resolve().parent.parent /
           "evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json")


class CT181OrderDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, _ = legacy.frozen_fixture(FIXTURE)

    def test_actual_ct179_scorer_reports_false_one_point_five_ratio(self):
        # Precisely the legacy synthetic fixture: no arm dependence whatsoever.
        matrix = {(block, packet): [3_000_000, 2_000_000, 2_000_000,
                                    3_000_000, 3_000_000, 3_000_000]
                  for block in range(design.BLOCKS)
                  for packet in range(design.PACKETS)}
        result = legacy.paired_statistics(matrix, self.rows)
        self.assertEqual(len(result), 16)
        for stratum in result:
            self.assertAlmostEqual(
                stratum["direct_over_retained_transfer_wall_ratio"], 1.5)
            self.assertAlmostEqual(stratum["aa_abs_log_ratio_p95"], 0)
            if stratum["class"] == "generic":
                lower, upper = stratum["cluster_bootstrap_ratio_ci95"]
                self.assertAlmostEqual(lower, 1.5)
                self.assertAlmostEqual(upper, 1.5)
            else:
                self.assertIsNone(stratum["cluster_bootstrap_ratio_ci95"])

    def test_balanced_roster_is_exactly_four_of_each_per_packet(self):
        counts = Counter()
        by_block = Counter()
        all_records = list(design.roster())
        self.assertEqual(len(all_records), 2304)
        self.assertEqual(len(set(all_records)), 2304)
        for block, packet, position, arm in all_records:
            self.assertEqual(arm, design.order(block, packet)[position])
            counts[(packet, design.order(block, packet))] += (position == 0)
            by_block[(block, design.order(block, packet))] += (position == 0)
        for i in range(48):
            self.assertEqual(counts[(i, design.ABBA)], 4)
            self.assertEqual(counts[(i, design.BAAB)], 4)
        for b in range(8):
            self.assertEqual(by_block[(b, design.ABBA)], 24)
            self.assertEqual(by_block[(b, design.BAAB)], 24)

    def test_no_arm_effect_gives_one_with_counterbalancing(self):
        for packet in range(48):
            self.assertAlmostEqual(design.packet_ratio(packet, 200, 200, True),
                                   1, places=12)
            self.assertAlmostEqual(design.packet_ratio(packet, 200, 200, False),
                                   1.5, places=12)
            for block in range(8):
                _, drift = design.one_block_log_ratio(
                    design.order(block, packet), 200, 200)
                self.assertEqual(drift, 0)

    def test_separable_true_effect_survives_balancing(self):
        # A genuinely slower A has intrinsic A/B ratio 5/4. Fixed ABBA
        # reports 15/8, while alternating ABBA/BAAB recovers 5/4.
        for packet in range(48):
            self.assertAlmostEqual(design.packet_ratio(packet, 125, 100, True),
                                   1.25, places=12)
            self.assertAlmostEqual(design.packet_ratio(packet, 125, 100, False),
                                   1.875, places=12)

    def test_refuse_bad_design_inputs(self):
        for pair in [(-1, 0), (8, 0), (0, -1), (0, 48),
                     (True, 0), (0, False)]:
            with self.subTest(pair=pair), self.assertRaises(ValueError):
                design.order(*pair)
        for bad in (0, -1, True, 2.2):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                design.one_block_log_ratio(design.ABBA, bad, 100)
        with self.assertRaisesRegex(ValueError, "two A and two B"):
            design.one_block_log_ratio(("A",) * 6, 100, 100)

    def test_no_scientific_advance_claim_in_diagnostic(self):
        report = design.null_diagnostic()
        self.assertEqual(report["total_roster_entries"], 2304)
        self.assertFalse(report["complete_single_target_ecdlp_advantage_established"])
        self.assertEqual(report["standing"], "[pcc:unverified]")
        self.assertAlmostEqual(report["legacy_null_direct_over_retained"], 1.5)
        self.assertAlmostEqual(report["balanced_null_direct_over_retained"], 1)


if __name__ == "__main__":
    unittest.main()
