import importlib.util
import sys
import unittest
from pathlib import Path


MODULE = Path(__file__).parents[1] / "src" / "nist_333.py"
SPEC = importlib.util.spec_from_file_location("nist_333", MODULE)
nist_333 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["nist_333"] = nist_333
SPEC.loader.exec_module(nist_333)


class Nist333Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = nist_333.run()

    def test_kernel_matrix_is_maximal_isotropic_and_transverse(self):
        matrix = nist_333.KERNEL_MATRIX
        self.assertEqual(nist_333.rank_mod3(matrix), 3)
        self.assertEqual(nist_333.symplectic_gram(matrix), [[0, 0, 0]] * 3)
        self.assertTrue(nist_333.factor_transverse(matrix))

    def test_repeated_factor_diagonal_census(self):
        self.assertEqual(len(nist_333.projective_lines_f3()), 13)
        self.assertEqual(len(nist_333.scalar_diagonal_incidence(nist_333.KERNEL_MATRIX)), 4)
        alternate = nist_333.P224_ZERO_DIAGONAL_INCIDENCE_KERNEL_MATRIX
        self.assertEqual(nist_333.symplectic_gram(alternate), [[0, 0, 0]] * 3)
        self.assertTrue(nist_333.factor_transverse(alternate))
        self.assertEqual(nist_333.scalar_diagonal_incidence(alternate), [])

    def test_full_evidence_run(self):
        self.assertEqual(self.result["curves"]["P-224"]["kernel"]["cardinality"], 27)
        self.assertEqual(self.result["curves"]["P-256"]["kernel"]["cardinality"], 27)
        self.assertGreater(self.result["curves"]["P-224"]["lagrangian_census"]["factor_transverse"], 0)
        self.assertGreater(self.result["curves"]["P-256"]["lagrangian_census"]["factor_transverse"], 0)
        self.assertEqual(
            self.result["curves"]["P-224"]["lagrangian_census"]["scalar_diagonal_incidence_histogram"],
            {"0": 192, "1": 240, "2": 288, "4": 48},
        )
        self.assertEqual(
            self.result["curves"]["P-256"]["lagrangian_census"]["scalar_diagonal_incidence_histogram"],
            {"4": 12},
        )
        for label in ["P-192", "P-384", "P-521"]:
            self.assertEqual(self.result["negative_controls"][label]["census"]["factor_transverse"], 0)

    def test_published_cost_substitution_is_worse_than_rho(self):
        for label in ["P-224", "P-256"]:
            parameters = self.result["curves"][label]["parameters"]
            n = int(parameters["n"], 16)
            inverse_nine = int(parameters["composed_diagonal_recovery_scalar_9_inverse_mod_n"], 16)
            self.assertEqual((9 * inverse_nine) % n, 1)
            self.assertGreater(
                self.result["curves"][label]["cost_model"]["destination_minus_rho_log2"],
                100,
            )


if __name__ == "__main__":
    unittest.main()
