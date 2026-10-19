import math
import unittest

from audit_panels_v2 import interval_qualifies, recompute_pair_ratio


class PairRatioTests(unittest.TestCase):
    def test_recomputes_reference_over_candidate(self):
        self.assertEqual(recompute_pair_ratio(120.0, 100.0, 1.2), 1.2)

    def test_rejects_forged_pair_speedup(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            recompute_pair_ratio(120.0, 100.0, 0.8)

    def test_rejects_nonpositive_raw_times_even_when_ratio_is_positive(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            recompute_pair_ratio(-120.0, -100.0, 1.2)

    def test_rejects_nonfinite_values(self):
        with self.assertRaisesRegex(ValueError, "finite"):
            recompute_pair_ratio(math.inf, 100.0, math.inf)


class DirectionalGateTests(unittest.TestCase):
    def test_a_a_failure_blocks_interval_above_one(self):
        self.assertFalse(interval_qualifies([1.01, 1.20], aa_passed=False))

    def test_a_a_failure_blocks_interval_below_one(self):
        self.assertFalse(interval_qualifies([0.80, 0.99], aa_passed=False))

    def test_both_directions_remain_available_after_a_a_pass(self):
        self.assertTrue(interval_qualifies([1.01, 1.20], aa_passed=True))
        self.assertTrue(interval_qualifies([0.80, 0.99], aa_passed=True))

    def test_malformed_interval_fails_closed(self):
        self.assertFalse(interval_qualifies([0.99, 1.01], aa_passed=True))
        self.assertFalse(interval_qualifies([1.2, 1.1], aa_passed=True))
        self.assertFalse(interval_qualifies([0.8, math.nan], aa_passed=True))


if __name__ == "__main__":
    unittest.main()
