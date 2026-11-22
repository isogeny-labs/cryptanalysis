import importlib.util
import sys
import unittest
from pathlib import Path


MODULE = Path(__file__).parents[1] / "src" / "smith_screen.py"
SPEC = importlib.util.spec_from_file_location("smith_screen", MODULE)
smith = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["smith_screen"] = smith
SPEC.loader.exec_module(smith)


REFERENCE = {
    (8,): 1,
    (6, 2): 1,
    (6, 1, 1): 1,
    (4, 2, 1, 1): 1,
    (4, 2, 2): 3,
    (4, 1, 1, 1, 1): 3,
    (3, 3, 2): 3,
    (3, 3, 1, 1): 3,
    (4, 4): 5,
    (2, 2, 2, 1, 1): 7,
    (2, 2, 1, 1, 1, 1): 9,
    (2, 1, 1, 1, 1, 1, 1): 15,
    (2, 2, 2, 2): 25,
    (1, 1, 1, 1, 1, 1, 1, 1): 105,
}


class SmithScreenTests(unittest.TestCase):
    def test_all_105_perfect_matchings_are_enumerated(self):
        self.assertEqual(len(smith.MATCHINGS_8), 105)
        self.assertEqual(len(set(smith.MATCHINGS_8)), 105)

    def test_reproduces_smith_factorization_table(self):
        for pattern in smith.integer_partitions(8):
            expected = REFERENCE.get(pattern, 0)
            self.assertEqual(smith.tractable_count(pattern), expected, pattern)

    def test_cycle_type_weights_sum_to_one(self):
        self.assertEqual(
            sum((smith.cycle_type_weight(p) for p in smith.integer_partitions(8)), smith.Fraction()),
            1,
        )

    def test_asymptotic_success_reproduces_18_57_percent(self):
        value = float(smith.asymptotic_success())
        self.assertGreater(value, 0.185)
        self.assertLess(value, 0.186)

    def test_exponent_change(self):
        cost = smith.cost_model(85)
        self.assertAlmostEqual(cost["hyperelliptic_to_plane_quartic_exponent_saving_bits"], 85 / 3)
        self.assertAlmostEqual(cost["pollard_to_plane_quartic_exponent_saving_bits"], 42.5)

    def test_smith_f37_positive_control(self):
        coefficients = [1, 28, 15, 20, 33, 12, 29, 2]
        pattern = smith.factorization_pattern(37, coefficients)
        self.assertEqual(pattern, (6, 1, 1))
        self.assertEqual(smith.tractable_count(pattern), 1)

    def test_rejects_characteristics_outside_smith_scope(self):
        with self.assertRaisesRegex(ValueError, "greater than three"):
            smith.factorization_pattern(3, [1, 0, 0, 0, 0, 0, 0, 1])


if __name__ == "__main__":
    unittest.main()
