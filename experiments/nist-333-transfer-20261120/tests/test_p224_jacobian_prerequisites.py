import importlib.util
import sys
import unittest
from pathlib import Path


MODULE = Path(__file__).parents[1] / "src" / "p224_jacobian_prerequisites.py"
SPEC = importlib.util.spec_from_file_location("p224_jacobian_prerequisites", MODULE)
prereq = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["p224_jacobian_prerequisites"] = prereq
SPEC.loader.exec_module(prereq)


class P224JacobianPrerequisiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = prereq.build_certificate()

    def test_rational_bitangent_factorization(self):
        bitangent = self.result["rational_bitangent"]
        self.assertTrue(bitangent["factorization_verified"])
        self.assertEqual(bitangent["intersection_divisor"], "2*P1 + 2*P2")

    def test_contact_points_are_smooth_and_tangent(self):
        for point in self.result["points"]:
            self.assertEqual(point["quartic_value_mod_p"], "0")
            self.assertTrue(point["smooth"])
            self.assertEqual(point["tangent_line"], "X=0")
            self.assertEqual(point["contact_multiplicity"], 2)

    def test_basepoint_encoding_is_over_prime_field(self):
        representation = self.result["jacobian_representation"]
        self.assertEqual(representation["chosen_rational_basepoint"], "P1")
        self.assertIn("D3 - 3*P1", representation["generic_genus_three_encoding"])
        self.assertTrue(self.result["verification"]["all_checks_pass"])


if __name__ == "__main__":
    unittest.main()
