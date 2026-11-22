import importlib.util
import random
import sys
import unittest
from pathlib import Path


MODULE = Path(__file__).parents[1] / "src" / "empirical_benchmark.py"
SPEC = importlib.util.spec_from_file_location("empirical_benchmark", MODULE)
bench = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["empirical_benchmark"] = bench
SPEC.loader.exec_module(bench)


class EmpiricalBenchmarkTests(unittest.TestCase):
    def test_pollard_rho_recovers_toy_log(self):
        modulus, order, generator = bench.safe_prime_subgroup(12)
        secret = 317 % order
        recovered, operations, _ = bench.pollard_rho_log(
            generator,
            pow(generator, secret, modulus),
            modulus,
            order,
            random.Random(9),
        )
        self.assertEqual(recovered, secret)
        self.assertGreater(operations, 0)

    def test_quartic_relations_are_actual_split_intersections(self):
        result = bench.benchmark_quartic([43], 0.2, 17)
        row = result["rows"][0]
        self.assertEqual(row["relations_collected"], row["target_relations"])
        self.assertTrue(row["all_intersection_points_verified"])
        self.assertGreaterEqual(row["candidate_lines_tested"], row["relations_collected"])


if __name__ == "__main__":
    unittest.main()
