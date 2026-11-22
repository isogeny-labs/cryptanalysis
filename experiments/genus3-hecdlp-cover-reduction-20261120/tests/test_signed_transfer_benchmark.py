import importlib.util
import sys
import unittest
from pathlib import Path


MODULE = Path(__file__).parents[1] / "src" / "signed_transfer_benchmark.py"
SPEC = importlib.util.spec_from_file_location("signed_transfer_benchmark", MODULE)
signed = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["signed_transfer_benchmark"] = signed
SPEC.loader.exec_module(signed)


class SignedTransferBenchmarkTests(unittest.TestCase):
    def test_signed_map_dual_and_recovery(self):
        row = signed.benchmark_profile(signed.PROFILES[0], seed=7, repetitions=10)
        self.assertTrue(all(row["identities"].values()))
        self.assertGreater(row["median_transfer_nanoseconds"], 0)
        self.assertGreater(row["median_dual_recovery_nanoseconds"], 0)


if __name__ == "__main__":
    unittest.main()
