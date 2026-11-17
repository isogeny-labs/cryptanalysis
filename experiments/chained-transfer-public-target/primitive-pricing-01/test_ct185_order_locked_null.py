#!/usr/bin/env python3
"""CT185: independently programmed, SYNTHETIC crossover nuisance falsification.

This test directly calls the exact pinned CT182 v2 statistical scorer. No native
child is executed; it neither times hardware nor solves an ECDLP. [pcc:unverified]
"""
import math
import os
from pathlib import Path
import sys
import unittest

LOCAL = Path(__file__).resolve().parent
PINNED = os.environ.get("CT182_SOURCE_ROOT")
if not PINN:
    raise RuntimeError("CT182_SOURCE_ROOT must point to pinned commit 92d0c646")
READER = Path(PINNED).resolve(strict=True)
if not (READER / "ct182_v2_panel_adjudicator.py").is_file():
    raise RuntimeError("pinned CT182 reader missing")
sys.path.insert(0, str(READER))

import ct179_panel_adjudicator as legacy
import ct181_order_design as design
import ct182_v2_panel_adjudicator as scorer

FIXTURE = (LOCAL.parent / "evidence" /
           "fixed-chain-norm-point-native-01" / "literal-selected-vectors.json")


def synthetic_matrix(sequence_locked, physical_a=1, physical_b=1):
    """Two identical-cost routes under an order-correlated period nuisance."""
    if (type(physical_a) is not int or type(physical_b) is not int
            or physical_a <= 0 or physical_b <= 0):
        raise ValueError("positive integer intrinsic times required")
    out = {}
    for block in range(design.BLOCKS):
        for packet in range(design.PACKETS):
            assignment = design.order(block, packet)
            is_abba = tuple(assignment[:4]) == ("A", "B", "B", "A")
            # Nuisance depends ONLY on the known sequence, not physical route.
            # Physical A and B have the same cost under the falsifying null.
            if sequence_locked and not is_abba:
                factors = (2, 3, 3, 2)
            else:
                factors = (3, 2, 2, 3)
            times = [
                factors[position] * (
                    physical_a if assignment[position] == "A" else physical_b
                )
                for position in range(4)
            ]
            # The original trailing A/A control cannot see slots 0..3.
            times.extend((3 * physical_a, 3 * physical_a))
            out[(block, packet)] = times
    return out


class CT185OrderLockedNull(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.fixture_sha = legacy.frozen_fixture(FIXTURE)
        assert len(cls.rows) == 48
        assert scorer.roster_sha256() == (
            "1dddb4839321ad6560fd429330778aa083ff3a13625393250e964c05f9fc5ee4"
        )

    def score(self, locked, a=1, b=1):
        output = scorer.paired_statistics_v2(
            synthetic_matrix(locked, a, b), self.rows
        )
        self.assertEqual(len(output), 16)
        return output

    def test_stationary_position_only_null_cancels(self):
        for stratum in self.score(False):
            self.assertAlmostEqual(
                stratum["direct_over_retained_transfer_wall_ratio"], 1.0
            )
            self.assertAlmostEqual(
                stratum["abba_log_ratio_median_diagnostic"], math.log(3 / 2)
            )
            self.assertAlmostEqual(
                stratum["baab_log_ratio_median_diagnostic"], math.log(2 / 3)
            )
            self.assertEqual(stratum["aa_abs_log_ratio_p95"], 0)
            self.assertEqual(
                stratum["balanced_abba_blocks"],
                stratum["balanced_baab_blocks"],
            )

    def test_order_correlated_period_null_looks_like_1point5_speedup(self):
        for stratum in self.score(True, 1, 1):
            self.assertAlmostEqual(
                stratum["direct_over_retained_transfer_wall_ratio"], 1.5
            )
            self.assertAlmostEqual(
                stratum["abba_log_ratio_median_diagnostic"], math.log(1.5)
            )
            self.assertAlmostEqual(
                stratum["baab_log_ratio_median_diagnostic"], math.log(1.5)
            )
            self.assertEqual(stratum["aa_abs_log_ratio_p95"], 0)
            ci = stratum["cluster_bootstrap_ratio_ci95"]
            if stratum["unique_packets"] == 1:
                self.assertIsNone(ci)
            else:
                self.assertIsNotNone(ci)
                self.assertAlmostEqual(ci[0], 1.5)
                self.assertAlmostEqual(ci[1], 1.5)

    def test_stationary_true_five_to_four_is_preserved(self):
        for stratum in self.score(False, a=5, b=4):
            self.assertAlmostEqual(
                stratum["direct_over_retained_transfer_wall_ratio"], 1.25
            )
            self.assertEqual(stratum["aa_abs_log_ratio_p95"], 0)

    def test_falsifier_is_a_treatment_null_not_altered_geometry(self):
        matrix = synthetic_matrix(True, 1, 1)
        self.assertEqual(len(matrix), 48 * 8)
        self.assertEqual(sum(len(x) for x in matrix.values()), 2304)
        for (block, packet), durations in matrix.items():
            order = design.order(block, packet)
            self.assertEqual(len(durations), 6)
            self.assertEqual(durations[4:], [3, 3])
            # The only difference is sequence/period nuisance.
            self.assertEqual(
                sorted(durations[:4]), [2, 2, 3, 3]
            )
            self.assertEqual(
                sum(durations[j] for j in range(4) if order[j] == "A"), 6
            )
            self.assertEqual(
                sum(durations[j] for j in range(4) if order[j] == "B"), 4
            )


if __name__ == "__main__":
    unittest.main()
