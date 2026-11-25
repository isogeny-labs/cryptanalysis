import importlib.util
import sys
import unittest
from pathlib import Path


MODULE = Path(__file__).parents[1] / "src" / "p256_descent_status.py"
SPEC = importlib.util.spec_from_file_location("p256_descent_status", MODULE)
status_module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["p256_descent_status"] = status_module
SPEC.loader.exec_module(status_module)


class P256DescentStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = status_module.build_status()

    def test_candidate_is_exactly_cubic_not_quadratic(self):
        audit = self.result["exact_field_audit"]
        self.assertTrue(audit["all_quadratic_extension_components_zero"])
        self.assertTrue(audit["all_coefficients_fixed_by_p_cubed"])
        self.assertFalse(audit["all_coefficients_fixed_by_p"])

    def test_base_field_descent_is_not_overclaimed(self):
        self.assertTrue(self.result["reconstruction"]["candidate_constructed"])
        self.assertFalse(self.result["descent_diagnostic"]["external_validation_completed"])
        self.assertIn("unverified", self.result["obstruction_certificate"]["safe_claim"])

    def test_seven_known_bitangents_do_not_close_under_frobenius(self):
        audit = self.result["local_frobenius_bitangent_audit"]
        self.assertEqual(audit["orbit_histogram"], {"1": 1, "3": 9})
        self.assertEqual(audit["known_aronhold_lines_preserved"], 1)
        self.assertFalse(audit["seven_line_shortcut_available"])


if __name__ == "__main__":
    unittest.main()
