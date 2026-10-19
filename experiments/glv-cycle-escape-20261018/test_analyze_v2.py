"""Invalid reruns must never publish a comparison, even over an existing result."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("analyze_v2", Path(__file__).with_name("analyze_v2.py"))
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


class AnalysisAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.output = self.root / "result.json"
        self.output.write_text("previous validated result\n")
        self.rows = {}
        for variant in analysis.VARIANTS:
            self.rows[variant] = [
                {"kind": "run", "family": family, "r_bits": bits,
                 "curve_index": 0, "target": 0, "arm": arm,
                 "r": 101, "group_ops": 100, "correct": True}
                for family in analysis.THEORY for bits in analysis.SIZES
                for arm in ("rho", "curve_solve")
            ]

    def run_analysis(self):
        for variant, rows in self.rows.items():
            (self.root / f"rows_v2_{variant}.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in rows))
        with patch.object(analysis, "HERE", self.root), patch.object(analysis, "CURVES", 1), \
                patch.object(analysis, "TARGETS", 1), contextlib.redirect_stdout(io.StringIO()):
            return analysis.main(["--boot", "1", "--json-out", str(self.output)])

    def assert_rejected(self, message):
        with self.assertRaisesRegex(ValueError, message):
            self.run_analysis()
        self.assertEqual(self.output.read_text(), "previous validated result\n")

    def test_wrong_answer_in_each_arm_is_rejected(self):
        for variant in analysis.VARIANTS:
            with self.subTest(variant=variant):
                self.rows[variant][0]["correct"] = False
                self.assert_rejected("incorrect answers")
                self.rows[variant][0]["correct"] = True

    def test_changed_rho_control_is_rejected(self):
        self.rows["patched"][0]["group_ops"] += 1
        self.assert_rejected("rho control mismatches")

    def test_changed_random_curve_control_is_rejected(self):
        row = next(row for row in self.rows["escape"]
                   if row["family"] == "random" and row["arm"] == "curve_solve")
        row["group_ops"] += 1
        self.assert_rejected("random-curve control mismatches")

    def test_missing_solve_in_all_arms_is_rejected(self):
        for rows in self.rows.values():
            rows.pop()
        self.assert_rejected("protocol grid differs")

    def test_duplicate_solve_is_rejected(self):
        self.rows["legacy"].append(self.rows["legacy"][0].copy())
        self.assert_rejected("duplicate solve")


if __name__ == "__main__":
    unittest.main()
