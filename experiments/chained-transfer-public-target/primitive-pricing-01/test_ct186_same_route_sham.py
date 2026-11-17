#!/usr/bin/env python3
"""CT186 source-only same-route synthetic falsification tests. [pcc:unverified]"""
import copy
import math
import statistics
import unittest

import ct186_same_route_sham as sham

ROSTER_SHA = "7cf758b05c82adf2d1e9edc675d10dc5a0bb603a004d51a42f9375a077d75228"


def synthetic_records(model="stationary"):
    out = []
    for block, packet, pos, label, arm in sham.roster():
        labels = sham.label_order(packet, block)
        if model == "stationary":
            factors = (3, 2, 2, 3)
        elif model == "sequence_locked":
            factors = (3, 2, 2, 3) if labels == sham.ABBA else (2, 3, 3, 2)
        elif model == "all_equal":
            factors = (1, 1, 1, 1)
        else:
            raise ValueError("unknown synthetic nuisance")
        out.append({
            "block": block, "packet_index": packet, "position": pos,
            "label": label, "physical_arm": arm, "wall_ns": factors[pos],
        })
    return out


class CT186ShamControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = synthetic_records("all_equal")

    def test_exact_roster_sha_and_balance(self):
        self.assertEqual(sham.roster_sha256(), ROSTER_SHA)
        self.assertEqual(sum(1 for _ in sham.roster()), 1536)
        self.assertEqual(sham.plan()["processes_if_later_admitted"], 1536)
        for packet in range(48):
            orders = [sham.label_order(packet, b) for b in range(8)]
            self.assertEqual(orders.count(sham.ABBA), 4)
            self.assertEqual(orders.count(sham.BAAB), 4)
        # The new schedule must not silently inherit CT183 parity assignment.
        self.assertTrue(any(sham.label_order(i, b) !=
                            (sham.ABBA if (b + i) % 2 == 0 else sham.BAAB)
                            for b in range(8) for i in range(48)))

    def test_all_same_route_null(self):
        out = sham.adjudicate(self.records)
        self.assertEqual(out["complete_records"], 1536)
        self.assertEqual(out["median_sham_ratio"], 1.0)
        self.assertFalse(out["complete_single_target_ecdlp_advantage_established"])
        self.assertFalse(out["signed_independent_pcc"])
        self.assertEqual(len(out["per_packet_log_ratios"]), 48)

    def test_stationary_slot_bias_cancels(self):
        out = sham.adjudicate(synthetic_records("stationary"))
        self.assertAlmostEqual(out["median_sham_ratio"], 1.0)
        for x in out["per_packet_log_ratios"]:
            self.assertAlmostEqual(x, 0)
        self.assertAlmostEqual(out["abba_log_median"], math.log(1.5))
        self.assertAlmostEqual(out["baab_log_median"], math.log(2/3))

    def test_assignment_conditioned_null_detected(self):
        out = sham.adjudicate(synthetic_records("sequence_locked"))
        self.assertAlmostEqual(out["median_sham_ratio"], 1.5)
        self.assertAlmostEqual(out["abba_log_median"], math.log(1.5))
        self.assertAlmostEqual(out["baab_log_median"], math.log(1.5))
        for x in out["per_packet_log_ratios"]:
            self.assertAlmostEqual(x, math.log(1.5))
        # Every row still executed only direct_composite despite placebo labels.
        self.assertEqual({r["physical_arm"] for r in synthetic_records("sequence_locked")},
                         {sham.PHYSICAL_ARM})

    def test_wrong_physical_arm_rejected_not_a_real_5_4_experiment(self):
        records = copy.deepcopy(self.records)
        records[1]["physical_arm"] = "strongest_retained_lift_chain"
        with self.assertRaisesRegex(ValueError, "physical-arm"):
            sham.adjudicate(records)

    def test_bad_custody_and_durations_fail_closed(self):
        mutations = []
        for field, value in (
            ("wall_ns", 0), ("wall_ns", True),
            ("wall_ns", 1.5), ("wall_ns", -1),
            ("label", "B" if self.records[0]["label"] == "A" else "A"), ("position", True),
            ("packet_index", 99), ("block", -1),
        ):
            records = copy.deepcopy(self.records)
            records[0][field] = value
            mutations.append(records)
        records = copy.deepcopy(self.records)
        records[0]["surplus"] = "x"
        mutations.append(records)
        mutations.append(self.records[:-1])
        mutations.append(self.records + [self.records[0]])
        records = copy.deepcopy(self.records)
        records[0], records[1] = records[1], records[0]
        mutations.append(records)
        for records in mutations:
            with self.subTest(records=len(records)):
                with self.assertRaises(ValueError):
                    sham.adjudicate(records)

    def test_schema_separation_and_type_strictness(self):
        with self.assertRaisesRegex(ValueError, "schema"):
            sham.adjudicate(self.records, schema="ct182-counterbalanced-cold-public-process-panel/v2")
        with self.assertRaisesRegex(ValueError, "schema"):
            sham.adjudicate(tuple(self.records))
        for invalid in (True, 48.0, -1, 48):
            with self.assertRaises(ValueError):
                sham.label_order(invalid, 0)
        with self.assertRaises(ValueError):
            sham.label_order(0, 8)


if __name__ == "__main__":
    unittest.main()
