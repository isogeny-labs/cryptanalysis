import importlib.util
import sys
import unittest
from pathlib import Path


MODULE = Path(__file__).parents[1] / "src" / "p256_aronhold_frobenius.py"
SPEC = importlib.util.spec_from_file_location("p256_aronhold_frobenius", MODULE)
certificate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["p256_aronhold_frobenius"] = certificate
SPEC.loader.exec_module(certificate)


class P256AronholdFrobeniusTests(unittest.TestCase):
    def test_full_odd_orbit_decomposition(self):
        result = certificate.build_certificate()
        self.assertEqual(result["all_odd_characteristics_count"], 28)
        self.assertEqual(result["full_odd_frobenius_orbit_histogram"], {"1": 1, "3": 9})
        self.assertEqual(result["rational_bitangent_count_predicted"], 1)

    def test_selected_seven_lines_do_not_close(self):
        result = certificate.build_certificate()
        self.assertFalse(result["selected_aronhold_stable"])
        self.assertEqual(result["images_remaining_in_selected_aronhold_system"], 1)
        self.assertEqual(result["remaining_odd_as_pairwise_aronhold_sums"], 21)


if __name__ == "__main__":
    unittest.main()
