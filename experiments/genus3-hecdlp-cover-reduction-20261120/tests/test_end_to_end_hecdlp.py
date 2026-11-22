import importlib.util
import sys
import unittest
from pathlib import Path


MODULE = Path(__file__).parents[1] / "src" / "end_to_end_hecdlp.py"
SPEC = importlib.util.spec_from_file_location("end_to_end_hecdlp", MODULE)
hecdlp = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["end_to_end_hecdlp"] = hecdlp
SPEC.loader.exec_module(hecdlp)


class EndToEndHecdlpTests(unittest.TestCase):
    def test_cantor_group_law_and_prime_order(self):
        curve = hecdlp.CURVES[0]
        base = hecdlp.factor_base(curve)
        point = hecdlp.point_divisor(*base[0], curve)
        self.assertEqual(
            hecdlp.compose(point, hecdlp.negate_divisor(point, curve), curve),
            hecdlp.IDENTITY,
        )
        self.assertEqual(hecdlp.scalar_mul(curve.jacobian_order, point, curve), hecdlp.IDENTITY)
        self.assertEqual(hecdlp.point_count_order(curve)[0], curve.jacobian_order)

    def test_complete_toy_hecdlp_solve(self):
        result = hecdlp.benchmark_curve(hecdlp.CURVES[0], seed=91, target_trials=1)
        self.assertEqual(result["independent_relations"], result["factor_base_size"])
        self.assertTrue(result["all_factor_base_logs_verified"])
        self.assertTrue(result["all_target_logs_recovered"])
        self.assertTrue(result["sparse_dense_solutions_equal"])
        self.assertGreater(result["sparse_pivot_nonzeros"], 0)
        self.assertGreater(result["median_pollard_rho_jacobian_additions"], 0)


if __name__ == "__main__":
    unittest.main()
