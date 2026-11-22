"""Tests for the instruction-cost ledger checker."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import ledger  # noqa: E402


def base_doc():
    return {
        "name": "test",
        "unit": "instructions per step",
        "rows": [
            {"stage": "walk", "count": 100},
            {"stage": "table", "count": 50},
        ],
        "declared_total": 150,
        "baseline": {
            "rows": [
                {"stage": "walk", "count": 100},
                {"stage": "table", "count": 80},
            ],
            "declared_total": 180,
        },
        "improvement": {"bits": "0.263034"},
        "break_even": [
            {"moved": "walk", "saved": "table", "moved_fanout": 1, "saved_fanout": 1}
        ],
        "claim": {
            "quantity": "log2(T)",
            "exact": "124.9214702494968",
            "decimals": 12,
            "declared": "124.921470249497",
        },
    }


def failures(doc):
    checks, _ = ledger.check_ledger(doc)
    return [check for check in checks if not check["ok"]]


class LedgerCheckTest(unittest.TestCase):
    def test_valid_ledger_passes(self):
        self.assertEqual(failures(base_doc()), [])

    def test_example_passes(self):
        path = HERE / "examples" / "secp256k1-truncated-fraction.json"
        checks, summary = ledger.check_ledger(json.loads(path.read_text()))
        self.assertTrue(summary["ok"], [c for c in checks if not c["ok"]])

    def test_total_mismatch_fails(self):
        doc = base_doc()
        doc["declared_total"] = 151
        self.assertTrue(any("sum to declared total" in c["name"] for c in failures(doc)))

    def test_normalization_is_applied(self):
        doc = base_doc()
        doc["normalization"] = {"factor": 0.5, "note": "two units per row"}
        doc["declared_total"] = 75
        doc["baseline"]["normalization"] = {"factor": 0.5}
        doc["baseline"]["declared_total"] = 90
        self.assertEqual(failures(doc), [])

    def test_stage_sets_must_match(self):
        doc = base_doc()
        doc["baseline"]["rows"][1]["stage"] = "other"
        self.assertTrue(any("same stages" in c["name"] for c in failures(doc)))

    def test_negative_count_rejected(self):
        doc = base_doc()
        doc["rows"][0]["count"] = -1
        with self.assertRaises(ledger.LedgerError):
            ledger.check_ledger(doc)

    def test_duplicate_stage_rejected(self):
        doc = base_doc()
        doc["rows"][1]["stage"] = "walk"
        with self.assertRaises(ledger.LedgerError):
            ledger.check_ledger(doc)

    def test_improvement_must_be_log2(self):
        doc = base_doc()
        doc["improvement"] = {"bits": "0.300000"}
        self.assertTrue(any("log2" in c["name"] for c in failures(doc)))

    def test_break_even_holds_when_nothing_is_paid(self):
        doc = base_doc()
        doc["baseline"]["rows"][1]["count"] = 90  # table saved 40, walk unchanged
        doc["baseline"]["declared_total"] = 190
        doc["improvement"] = {"bits": "0.341037"}
        doc["break_even"] = [
            {"moved": "walk", "saved": "table", "moved_fanout": 1, "saved_fanout": 1}
        ]
        self.assertEqual(failures(doc), [])

    def test_break_even_fanout_can_kill_a_change(self):
        doc = base_doc()
        doc["rows"][0]["count"] = 120          # walk costs 20 more
        doc["declared_total"] = 170
        doc["improvement"] = {"bits": "0.082515"}
        doc["break_even"] = [
            {"moved": "walk", "saved": "table", "moved_fanout": 100, "saved_fanout": 1}
        ]
        self.assertTrue(any("break-even" in c["name"] for c in failures(doc)))

    def test_claim_rounds_up(self):
        doc = base_doc()
        doc["claim"]["declared"] = "124.921470249496"  # one ulp too low
        self.assertTrue(any("least" in c["name"] for c in failures(doc)))

    def test_claim_too_high_fails(self):
        doc = base_doc()
        doc["claim"]["declared"] = "124.921470249498"
        self.assertTrue(any("least" in c["name"] for c in failures(doc)))

    def test_claim_decimal_places_must_match(self):
        doc = base_doc()
        doc["claim"]["declared"] = "124.9214702494970"
        self.assertTrue(any("least" in c["name"] for c in failures(doc)))

    def test_claim_exact_integer(self):
        doc = base_doc()
        doc["claim"] = {"quantity": "count", "exact": "150",
                        "decimals": 0, "declared": "150"}
        self.assertEqual(failures(doc), [])

    def test_template_is_checkable(self):
        checks, summary = ledger.check_ledger(ledger.TEMPLATE)
        self.assertTrue(summary["ok"], [c for c in checks if not c["ok"]])


class CommandLineTest(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(HERE / "ledger.py"), *args],
            capture_output=True, text=True,
        )

    def test_example_exit_zero(self):
        result = self.run_cli(
            "check", str(HERE / "examples" / "secp256k1-truncated-fraction.json"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_bad_ledger_exit_one_and_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            doc = base_doc()
            doc["declared_total"] = 999
            path.write_text(json.dumps(doc))
            result = self.run_cli("check", "--json", str(path))
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])

    def test_template_is_valid_json(self):
        result = self.run_cli("template")
        self.assertEqual(result.returncode, 0)
        self.assertIsInstance(json.loads(result.stdout), dict)


if __name__ == "__main__":
    unittest.main(verbosity=2)
