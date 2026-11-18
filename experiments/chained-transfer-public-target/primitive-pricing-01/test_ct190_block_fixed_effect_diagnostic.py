#!/usr/bin/env python3
"""CT190 source-only counterexamples. No native hardware or solver runs."""
import copy
import math
import unittest

import ct188_physical_crossover_design as old
import ct190_block_fixed_effect_diagnostic as new

# Independently derived from the exact seven-column CT188 least-squares model:
# coefficient of an arbitrary BLOCK CONSTANT in physical_B, by sequence.
# Sequence multiplicities: ABBA and BAAB occur twice in each eight-block set.
# Sum(weights)=0 and sum(weights^2)=793/10082.
BLOCK_PROJECTION = {
    "AABB": -53 / 284, "ABAB": 11 / 284, "ABBA": -11 / 284,
    "BAAB": 11 / 284, "BABA": 53 / 284, "BBAA": -11 / 284,
}
SQUARED_PROJECTION_NORM = 793 / 10082
BASE_NS = 10**12


def synthetic_records(block_shock=False, direct_cost=1.0,
                      previous_b_cost=1.0, interaction_cost=1.0):
    """Each block's speed factor affects A and B identically.

    True treatment/carryover effects, when requested, are separately explicit.
    These invented durations are not native observations.
    """
    records = []
    for block, packet, position, arm in old.roster():
        sequence = old.order(block, packet)[:4]
        latency = 1.0
        if block_shock:
            # Engineering a counterexample is intentional: this is not a
            # claim about physically observed host load.
            latency = math.exp(-math.log(1.5) * BLOCK_PROJECTION[sequence] /
                               SQUARED_PROJECTION_NORM)
        if arm == old.ARMS["A"]:
            latency *= direct_cost
        if position < 4 and position > 0 and sequence[position - 1] == "B":
            latency *= previous_b_cost
            if arm == old.ARMS["B"]:
                latency *= interaction_cost
        records.append({
            "block": block, "packet_index": packet,
            "position": position, "arm": arm,
            "wall_ns": round(BASE_NS * latency),
        })
    return records


class CT190BlockEffectSourceTest(unittest.TestCase):
    def test_exact_rational_design_and_frozen_roster(self):
        self.assertEqual(old.roster_sha256(), new.EXPECTED_ROSTER_SHA256)
        self.assertTrue(new.assert_design())
        self.assertEqual(new.N_BLOCK_COLUMNS, 14)
        self.assertEqual(sum(x * x for k, x in BLOCK_PROJECTION.items()
                             for _ in range(2 if k in ("ABBA", "BAAB") else 1)),
                         SQUARED_PROJECTION_NORM)

    def test_uniform_equal_cost_null(self):
        result = new.analyze_untrusted_times(synthetic_records())
        self.assertAlmostEqual(result["median_direct_over_retained_ratio_block_fixed"],
                               1.0, places=7)
        self.assertAlmostEqual(
            result["original_seven_column_diagnostic"]
            ["median_direct_over_retained_ratio_conditional_model"],
            1.0, places=7)
        self.assertEqual(result["supplied_processes"], 2304)
        self.assertFalse(result["signed_independent_pcc"])

    def test_block_common_shocks_falsify_original_but_not_fixed(self):
        result = new.analyze_untrusted_times(
            synthetic_records(block_shock=True))
        legacy = result["original_seven_column_diagnostic"]
        self.assertAlmostEqual(
            legacy["median_direct_over_retained_ratio_conditional_model"],
            1.5, places=6)
        self.assertAlmostEqual(
            result["median_direct_over_retained_ratio_block_fixed"],
            1.0, places=6)
        self.assertLess(legacy["maximum_aa_abs_log_drift"], 1e-12)

    def test_true_effect_not_erased_and_carryover_separated(self):
        result = new.analyze_untrusted_times(
            synthetic_records(block_shock=True, direct_cost=1.25,
                              previous_b_cost=1.15, interaction_cost=1.08))
        self.assertAlmostEqual(
            result["median_direct_over_retained_ratio_block_fixed"],
            1.25, places=6)
        self.assertAlmostEqual(
            result["median_previous_B_coefficient_block_fixed"],
            math.log(1.15), places=6)
        self.assertAlmostEqual(
            result["median_interaction_coefficient_block_fixed"],
            math.log(1.08), places=6)
        self.assertFalse(result["complete_single_target_ecdlp_advantage_established"])

    def test_full_population_wrong_arm_and_invalid_time_refused(self):
        base = synthetic_records()
        mutations = [
            base[:-1],
            base + [dict(base[-1])],
            copy.deepcopy(base),
            copy.deepcopy(base),
            copy.deepcopy(base),
        ]
        mutations[2][0]["arm"] = "forged"
        mutations[3][0]["wall_ns"] = 0
        mutations[4][0]["wall_ns"] = True
        for i, bad in enumerate(mutations):
            with self.subTest(mutation=i), self.assertRaises(ValueError):
                new.analyze_untrusted_times(bad)


if __name__ == "__main__":
    unittest.main()
