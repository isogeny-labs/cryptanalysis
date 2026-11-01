import importlib.util
from fractions import Fraction
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
ANALYZER_PATH = (
    REPO
    / "experiments"
    / "performance-saturation-20261101"
    / "go"
    / "analyze_remote_peer_key_ab.py"
)
SPEC = importlib.util.spec_from_file_location("go_peer_key_ab_analyzer", ANALYZER_PATH)
assert SPEC is not None and SPEC.loader is not None
ANALYZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYZER)


def row(case: str, replicate: int, arm: str, *, allocation_ratio: int = 5) -> dict:
    baseline = arm == ANALYZER.BASELINE_ARM
    metrics = {
        "B/op": 100 if baseline else allocation_ratio,
        "allocs/op": 100 if baseline else allocation_ratio,
        "ns/op": 105 if baseline else 100,
        "cpu-ns/op": 105 if baseline else 100,
    }
    return {
        "warmup": False,
        "case": case,
        "replicate": replicate,
        "arm": arm,
        "parsed": {"fingerprints": {"answer": case}, "metrics": metrics},
    }


class IsolationPrimitiveTests(unittest.TestCase):
    def test_numeric_psi_gate_is_exact(self) -> None:
        snapshot = {
            "psi_cpu": (
                "some avg10=10.00 avg60=20.00 avg300=30.00 total=1\n"
                "full avg10=0.00 avg60=9.00 avg300=9.00 total=0"
            ),
            "psi_memory": (
                "some avg10=0.00 avg60=1.00 avg300=1.00 total=0\n"
                "full avg10=0.00 avg60=1.00 avg300=1.00 total=0"
            ),
        }
        self.assertTrue(ANALYZER.pressure_snapshot_passes(snapshot))
        snapshot["psi_cpu"] = snapshot["psi_cpu"].replace("10.00", "10.01", 1)
        self.assertFalse(ANALYZER.pressure_snapshot_passes(snapshot))

    def test_cgroup_deltas_require_identical_non_decreasing_inventory(self) -> None:
        self.assertEqual(
            ANALYZER.counter_deltas("low 2\nhigh 3", "low 2\nhigh 3"),
            {"high": 0, "low": 0},
        )
        with self.assertRaisesRegex(ValueError, "inventory"):
            ANALYZER.counter_deltas("low 2", "low 2\nhigh 0")
        with self.assertRaisesRegex(ValueError, "decreased"):
            ANALYZER.counter_deltas("low 2", "low 1")


class FormalDecisionTests(unittest.TestCase):
    def test_terminal_vocabulary_and_precedence(self) -> None:
        decide = ANALYZER.choose_verdict
        common = dict(complete=True, correctness=True)
        self.assertEqual(
            decide(**common, allocation=True, timing_numeric=True, timing_isolation=True),
            "supported_within_scope",
        )
        self.assertEqual(
            decide(**common, allocation=True, timing_numeric=False, timing_isolation=True),
            "allocation_only",
        )
        self.assertEqual(
            decide(**common, allocation=False, timing_numeric=True, timing_isolation=True),
            "timing_only",
        )
        self.assertEqual(
            decide(**common, allocation=False, timing_numeric=False, timing_isolation=True),
            "unsupported",
        )
        self.assertEqual(
            decide(**common, allocation=False, timing_numeric=True, timing_isolation=False),
            "invalid_measurement",
        )
        self.assertEqual(
            decide(
                complete=True,
                correctness=False,
                allocation=True,
                timing_numeric=True,
                timing_isolation=True,
            ),
            "wrong_answer",
        )
        self.assertEqual(
            decide(
                complete=False,
                correctness=False,
                allocation=False,
                timing_numeric=False,
                timing_isolation=False,
            ),
            "inconclusive",
        )

    def test_all_six_cases_use_exact_thresholds_and_distribution(self) -> None:
        cases = [f"case-{index}" for index in range(6)]
        rows = [
            row(case, replicate, arm)
            for case in cases
            for replicate in range(1, 21)
            for arm in (ANALYZER.BASELINE_ARM, ANALYZER.CANDIDATE_ARM)
        ]
        results, allocation, timing, pairs = ANALYZER.compute_case_results(rows, cases)
        self.assertTrue(allocation)
        self.assertTrue(timing)
        self.assertEqual(pairs, 120)
        self.assertEqual(len(results), 6)
        metric = results[0]["metrics"]["ns/op"]
        self.assertEqual(metric["paired_median"]["numerator"], "21")
        self.assertEqual(metric["paired_median"]["denominator"], "20")
        self.assertEqual(metric["simultaneous_lower_bound"]["numerator"], "21")
        self.assertEqual(metric["lower_quantile"], "1/480")
        self.assertEqual(ANALYZER.LOWER_QUANTILE, Fraction(1, 480))

    def test_allocation_requires_both_metrics_in_every_case(self) -> None:
        cases = ["case"]
        rows = [
            row("case", replicate, arm, allocation_ratio=6)
            for replicate in range(1, 21)
            for arm in (ANALYZER.BASELINE_ARM, ANALYZER.CANDIDATE_ARM)
        ]
        _, allocation, timing, pairs = ANALYZER.compute_case_results(rows, cases)
        self.assertFalse(allocation)
        self.assertTrue(timing)
        self.assertEqual(pairs, 20)

    def test_exact_276_row_mismatch_flow_is_wrong_answer_after_nonzero_exit(self) -> None:
        cases = [f"case-{index}" for index in range(6)]
        rows = [
            row(case, replicate, arm)
            for case in cases
            for replicate in range(1, 21)
            for arm in (ANALYZER.BASELINE_ARM, ANALYZER.CANDIDATE_ARM)
        ]
        for case in cases:
            for replicate in range(1, 4):
                for arm in (ANALYZER.BASELINE_ARM, ANALYZER.CANDIDATE_ARM):
                    warmup = row(case, replicate, arm)
                    warmup["warmup"] = True
                    rows.append(warmup)
        self.assertEqual(len(rows), 276)
        rows[0]["parsed"]["fingerprints"] = {"answer": "different"}
        matches, mismatches = ANALYZER.correctness_inventory(rows, cases)
        self.assertEqual((matches, mismatches), (119, 1))
        self.assertTrue(ANALYZER.transport_is_complete(1, mismatches))
        self.assertEqual(
            ANALYZER.choose_verdict(
                complete=True,
                correctness=False,
                allocation=False,
                timing_numeric=False,
                timing_isolation=True,
            ),
            "wrong_answer",
        )


if __name__ == "__main__":
    unittest.main()
