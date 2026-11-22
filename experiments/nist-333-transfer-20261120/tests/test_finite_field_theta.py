import importlib.util
import sys
import unittest
from pathlib import Path


MODULE = Path(__file__).parents[1] / "src" / "finite_field_theta.py"
SPEC = importlib.util.spec_from_file_location("finite_field_theta", MODULE)
theta = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["finite_field_theta"] = theta
SPEC.loader.exec_module(theta)


class FiniteFieldThetaTests(unittest.TestCase):
    def test_cubic_extension_inverse(self):
        base = theta.nist.FFContext(7, [0, 1])
        field = theta.CubicContext(base, [3, 0, 0, 1])  # z^3+3, irreducible over F_7
        value = field.e([1, 2, 4])
        self.assertEqual(value * value.inverse(), field.one)

    def test_p256_two_division_splits_in_existing_cubic_subfield(self):
        data = theta.p256_setup()
        self.assertEqual(data["field"].order, data["curve"]["p"] ** 6)
        self.assertEqual(len(set(data["two_torsion"])), 3)
        for diagonal in data["two_torsion"]:
            for point in diagonal:
                self.assertIsNone(theta.nist.ec_mul(2, point, data["a"][0]))

    def test_p224_normal_weil_set(self):
        engine = theta.P224ThetaEngine()
        self.assertEqual(len(engine.kernel), 27)
        self.assertEqual(len(engine.alpha), 27)
        self.assertTrue(engine.theta(engine.generic))
        quotient = engine.quotient_theta_data()
        self.assertEqual(quotient["odd_zero_count"], 28)
        self.assertEqual(quotient["even_nonzero_count"], 36)
        self.assertEqual(quotient["violations"], [])
        reconstruction = engine.reconstruct_quartic(quotient)
        product = lambda *indices: engine.theta_product(indices, quotient)
        g = product(7, 16, 42, 61)
        h = product(12, 27, 33, 54)
        i = product(2, 21, 47, 56)
        self.assertEqual(
            reconstruction["alphas"][2][1],
            (g - h - i) / (2 * product(12, 27, 47, 56)),
        )
        self.assertEqual(
            reconstruction["alphas"][2][2],
            (h + g - i) / (2 * product(12, 27, 42, 61)),
        )
        self.assertGreaterEqual(len(reconstruction["quartic"]), 5)
        self.assertLessEqual(len(reconstruction["quartic"]), 15)
        self.assertEqual(reconstruction["aronhold_bitangent_checks"], [True] * 7)

    def test_p224_quotient_kummer_map_has_selected_kernel_fiber(self):
        engine = theta.P224ThetaEngine()
        quotient = engine.quotient_theta_data()
        image = engine.quotient_kummer_image(engine.generic, quotient)
        # A nonzero generator of the selected order-27 kernel must be invisible
        # to the quotient map.  Exact equality is used, not a numerical test.
        translated = theta.add_product(
            engine.generic, engine.kernel[(1, 0, 0)], engine.a
        )
        self.assertEqual(image, engine.quotient_kummer_image(translated, quotient))


if __name__ == "__main__":
    unittest.main()
