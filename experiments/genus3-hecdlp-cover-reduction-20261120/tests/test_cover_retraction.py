import importlib.util
import sys
import unittest
from pathlib import Path


MODULE = Path(__file__).parents[1] / "src" / "cover_retraction.py"
SPEC = importlib.util.spec_from_file_location("cover_retraction", MODULE)
retract = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["cover_retraction"] = retract
SPEC.loader.exec_module(retract)


class CoverRetractionTests(unittest.TestCase):
    def test_cover_only_certificate(self):
        result = retract.certificate(101, cover_degree=3)
        self.assertTrue(result["coprime_to_subgroup_order"])
        self.assertEqual(result["composed_multiplier"], 3)
        self.assertEqual((3 * result["recovery_scalar_mod_n"]) % 101, 1)

    def test_smith_composition(self):
        result = retract.certificate(101, cover_degree=3, isogeny_multiplier=2)
        self.assertEqual(result["composed_multiplier"], 6)
        self.assertEqual((6 * result["recovery_scalar_mod_n"]) % 101, 1)

    def test_non_coprime_case_stays_open(self):
        result = retract.certificate(3, cover_degree=3)
        self.assertFalse(result["coprime_to_subgroup_order"])
        self.assertIsNone(result["recovery_map"])

    def test_nist_333_composed_scalars(self):
        bundle = retract.build_bundle()
        for result in bundle["nist_333_diagonal_composition"].values():
            n = result["subgroup_order"]
            self.assertEqual(result["composed_multiplier"], 9)
            self.assertEqual((9 * result["recovery_scalar_mod_n"]) % n, 1)


if __name__ == "__main__":
    unittest.main()
