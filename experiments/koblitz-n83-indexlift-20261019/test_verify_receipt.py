import unittest

from verify_receipt import decide


class DecideTests(unittest.TestCase):
    def checks(self, q0=True):
        return {
            "all_executed_rows_valid": True,
            "q0_matches_archived_feistel_identity": q0,
            "every_scheduled_row_present": True,
            "all_points_complete": True,
            "all_rank_blocks_complete": True,
        }

    def stats(self):
        return {
            "aa_e2e_shared_cP_over_cPaa": {"estimate": 1.0},
            "aa_cold_cP_over_cPaa": {"estimate": 1.0},
            "sharing_rank_attempt_kPI_over_kP": {"estimate": 1.0},
            "planted_cold_cPIX_over_cPI": {"ci95": [1.01, 1.1]},
            "primary_e2e_shared_cP_over_cPI": {"ci95": [1.01, 1.1]},
        }

    def test_missing_q0_identity_is_invalid(self):
        decision, _ = decide(self.checks(q0=None), self.stats())
        self.assertEqual(decision, "invalid")

    def test_all_true_gates_can_pass_controls(self):
        decision, _ = decide(self.checks(), self.stats())
        self.assertEqual(decision, "improvement")


if __name__ == "__main__":
    unittest.main()
