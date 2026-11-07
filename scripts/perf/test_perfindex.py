"""Synthetic metadata regressions; never launches a benchmark."""
import copy
import importlib.util
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("perfindex", Path(__file__).with_name("perfindex.py"))
pi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pi)


class ComparisonIntegrityTest(unittest.TestCase):
    def setUp(self):
        self.kernels = [{"id": "one", "area": "test"}]
        self.per = {"one": {arm: [{"median_ns": value, "fingerprint": "same", "round": r}
                                  for r in range(3)]
                            for arm, value in (("A", 100), ("B", 80), ("A2", 100))}}

    def summary(self, weights=None):
        return pi.summarize(self.kernels, self.per, weights or {}, random.Random(0))

    def test_valid_paired_summary(self):
        result = self.summary()
        self.assertTrue(result["valid"])
        self.assertAlmostEqual(result["performance_index"], 1.25)
        self.assertEqual(result["rounds"], 3)

    def test_incomplete_arms_and_rounds_are_rejected(self):
        for arm in ("A", "B", "A2"):
            with self.subTest(arm=arm):
                original = copy.deepcopy(self.per)
                self.per["one"][arm].pop()
                with self.assertRaises(ValueError):
                    self.summary()
                self.per = original
        self.per["one"]["B"][1]["round"] = 2
        with self.assertRaises(ValueError):
            self.summary()

    def test_cross_kernel_round_counts_must_match(self):
        self.kernels.append({"id": "two", "area": "test"})
        self.per["two"] = {arm: rows[:2] for arm, rows in self.per["one"].items()}
        with self.assertRaises(ValueError):
            self.summary()

    def test_nonpositive_nonfinite_and_boolean_samples_rejected(self):
        for value in (0, -1, float("nan"), float("inf"), True):
            with self.subTest(value=value):
                self.per["one"]["B"][0]["median_ns"] = value
                with self.assertRaises(ValueError):
                    self.summary()

    def test_empty_workload_and_invalid_weights_rejected(self):
        for weights in ({"test": -1}, {"test": 0}, {"test": float("nan")}, {"test": True}):
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                self.summary(weights)
        self.kernels = []
        with self.assertRaises(ValueError):
            self.summary()

    def test_mismatched_kernel_rosters_cannot_be_silently_intersected(self):
        a = type("Args", (), {"base": "a", "cand": "b", "full": False, "filter": ""})()
        for candidate in ([], [{"id": "two", "area": "test"}],
                          [{"id": "one", "area": "different"}],
                          self.kernels + self.kernels):
            with self.subTest(candidate=candidate):
                with patch.object(pi, "list_kernels", side_effect=[self.kernels, candidate]):
                    with self.assertRaises(ValueError):
                        pi.matched_kernels(a)

    def test_fingerprint_change_still_refuses_index(self):
        self.per["one"]["B"][0]["fingerprint"] = "different"
        self.assertFalse(self.summary()["valid"])
        self.assertIsNone(self.summary()["performance_index"])

    def test_commands_refuse_roster_mismatch_before_measured_invocation(self):
        for command in (pi.cmd_compare, pi.cmd_instr):
            with self.subTest(command=command.__name__), tempfile.TemporaryDirectory() as tmp:
                args = type("Args", (), {"base": "a", "cand": "b", "full": False,
                                         "filter": [], "out": str(Path(tmp) / "output"), "seed": 0})()
                with patch.object(pi, "list_kernels", side_effect=[self.kernels, []]), \
                        patch.object(pi, "invoke") as invoke, patch.object(pi, "instr_one") as instr:
                    with self.assertRaises(ValueError):
                        command(args)
                    invoke.assert_not_called()
                    instr.assert_not_called()


if __name__ == "__main__":
    unittest.main()
