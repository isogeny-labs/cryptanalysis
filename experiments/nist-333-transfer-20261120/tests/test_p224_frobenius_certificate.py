import importlib.util
import sys
import unittest
from pathlib import Path


MODULE = Path(__file__).parents[1] / "src" / "p224_frobenius_certificate.py"
SPEC = importlib.util.spec_from_file_location("p224_frobenius_certificate", MODULE)
frobenius = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["p224_frobenius_certificate"] = frobenius
SPEC.loader.exec_module(frobenius)


class P224FrobeniusCertificateTests(unittest.TestCase):
    def test_cube_expansion_and_functional_equation(self):
        result = frobenius.build_certificate()
        p = int(result["elliptic_curve"]["p"])
        t = int(result["elliptic_curve"]["trace_t"])
        coefficients = [int(x) for x in result["expected_jacobian"]["l_polynomial_coefficients_low_to_high"]]
        self.assertEqual(coefficients, frobenius.cube_quadratic_coefficients(p, t))
        self.assertTrue(all(result["expected_jacobian"]["functional_equation_checks"].values()))

    def test_no_independent_point_count_is_overclaimed(self):
        status = frobenius.build_certificate()["certification_status"]
        self.assertTrue(status["expected_polynomial_exact"])
        self.assertFalse(status["independent_full_point_count_completed"])
        self.assertFalse(status["full_independent_certification"])


if __name__ == "__main__":
    unittest.main()
