import importlib.util
import sys
import unittest
from pathlib import Path


MODULE = Path(__file__).parents[1] / "src" / "complex_theta_diagnostic.py"
SPEC = importlib.util.spec_from_file_location("complex_theta_diagnostic", MODULE)
theta = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["complex_theta_diagnostic"] = theta
SPEC.loader.exec_module(theta)


class ComplexThetaDiagnosticTests(unittest.TestCase):
    def test_shared_kernel_has_nonhyperelliptic_sample(self):
        result = theta.diagnose(theta.nist.KERNEL_MATRIX, 0.17 + 1.3j, cutoff=6)
        self.assertEqual(result["even_nonzero_count"], 36)
        self.assertGreater(result["even_min_absolute_value"], 1e-3)
        self.assertLess(result["odd_max_absolute_value"], 1e-10)
        self.assertLess(result["max_cutoff_delta"], 1e-10)

    def test_alternate_kernel_graph_is_symmetric(self):
        matrix = theta.nist.P224_ZERO_DIAGONAL_INCIDENCE_KERNEL_MATRIX
        graph = theta.graph_matrix(matrix)
        self.assertEqual(graph, theta.nist.transpose(graph))
        result = theta.diagnose(matrix, -0.23 + 1.1j, cutoff=6)
        self.assertEqual(result["even_nonzero_count"], 36)


if __name__ == "__main__":
    unittest.main()
