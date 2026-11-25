#!/usr/bin/env python3
"""CT188 source-only tests: physical-arm permutation and first-order carryover.

All durations below are programmed synthetic numbers, not native measurements.
"""
import math
import unittest

import ct188_physical_crossover_design as ct


def make_synthetic(direct_over_retained=1.0, previous_b=0.0, interaction=0.0):
    # Log-time regression truth; use large integer ns to avoid quantization noise.
    truth = (math.log(1_000_000_000), 0.013, -0.025, 0.019,
             -math.log(direct_over_retained), previous_b, interaction)
    records = []
    for block, packet, position, arm in ct.roster():
        if position < 4:
            row = ct.model_row(ct.order(block, packet)[:4], position)
            wall_ns = max(1, round(math.exp(sum(a * b for a, b in zip(row, truth)))))
        else:
            wall_ns = 1_000_000_000
        records.append({"block": block, "packet_index": packet,
                        "position": position, "arm": arm, "wall_ns": wall_ns})
    return records


class CT188SourceTests(unittest.TestCase):
    def test_design_is_pinned_balanced_and_full_rank(self):
        self.assertTrue(ct.assert_design())
        plan = ct.plan()
        self.assertEqual(plan["planned_processes"], 2304)
        self.assertEqual(plan["packets"], 48)
        self.assertEqual(plan["design_rank_every_packet"], 7)
        self.assertEqual(len(plan["roster_sha256"]), 64)
        self.assertEqual(plan["fixture_git_blob"],
                         "9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3")
        self.assertEqual(ct.roster_sha256(), ct.roster_sha256())
        self.assertNotEqual(ct.roster_sha256(),
                            "1dddb4839321ad6560fd429330778aa083ff3a13625393250e964c05f9fc5ee4")
        self.assertEqual(sorted(ct.SEQUENCES),
                         sorted(("AABB", "ABAB", "ABBA", "BAAB",
                                 "BABA", "BBAA", "ABBA", "BAAB")))
        for packet in range(48):
            seq = ct.packet_sequences(packet)
            self.assertEqual(sorted(seq), sorted(ct.SEQUENCES))
            self.assertEqual([sum(s[i] == "B" for s in seq) for i in range(4)],
                             [4, 4, 4, 4])
            self.assertTrue(all(ct.order(b, packet)[-2:] == "AA"
                                for b in range(8)))

    def test_equal_intrinsic_routes_with_period_and_carryover(self):
        result = ct.adjudicate_untrusted_times(make_synthetic(
            direct_over_retained=1, previous_b=0.13, interaction=-0.07))
        self.assertAlmostEqual(
            result["median_direct_over_retained_ratio_conditional_model"],
            1.0, places=7)
        self.assertAlmostEqual(result["median_previous_B_coefficient"],
                               0.13, places=7)
        self.assertAlmostEqual(result["median_B_x_previous_B_coefficient"],
                               -0.07, places=7)
        self.assertEqual(result["supplied_records"], 2304)
        self.assertEqual(result["treatment_positions"], 1536)
        self.assertEqual(result["aa_control_positions"], 768)
        self.assertFalse(result["signed_independent_pcc"])
        self.assertFalse(result["complete_single_target_ecdlp_advantage_established"])

    def test_programmed_true_route_effect_is_separated_from_carryover(self):
        result = ct.adjudicate_untrusted_times(make_synthetic(
            direct_over_retained=1.25, previous_b=0.20, interaction=0.12))
        self.assertAlmostEqual(
            result["median_direct_over_retained_ratio_conditional_model"],
            1.25, places=7)
        self.assertAlmostEqual(result["median_previous_B_coefficient"],
                               0.20, places=7)
        self.assertAlmostEqual(result["median_B_x_previous_B_coefficient"],
                               0.12, places=7)

    def test_source_input_refuses_tampering_and_censoring(self):
        full = make_synthetic()
        with self.assertRaises(ValueError):
            ct.adjudicate_untrusted_times(full[:-1])
        cases = [
            ("arm", "strongest_retained_lift_chain"
             if full[0]["arm"] == "direct_composite" else "direct_composite"),
            ("position", 100), ("wall_ns", True), ("wall_ns", 0),
            ("wall_ns", -1), ("wall_ns", float("nan")),
        ]
        for field, bad in cases:
            rows = list(full)
            rows[0] = dict(rows[0])
            rows[0][field] = bad
            with self.subTest(field=field, bad=bad):
                with self.assertRaises(ValueError):
                    ct.adjudicate_untrusted_times(rows)
        rows = list(full)
        rows[1] = dict(rows[1])
        rows[1]["additional_cost"] = 0
        with self.assertRaises(ValueError):
            ct.adjudicate_untrusted_times(rows)

    def test_bad_packet_block_and_model_row_are_rejected(self):
        for packet in (-1, 48, True):
            with self.assertRaises(ValueError):
                ct.packet_sequences(packet)
        for block in (-1, 8, True):
            with self.assertRaises(ValueError):
                ct.order(block, 0)
        for seq, position in (("BBBB", 0), ("ABBA", 4), ("ABBA", True)):
            with self.assertRaises(ValueError):
                ct.model_row(seq, position)


if __name__ == "__main__":
    unittest.main()
