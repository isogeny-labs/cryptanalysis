#!/usr/bin/env python3
"""Regression tests for the PARI and Magma rank adapters."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import rank_magma
import rank_pari
import tool_controls


class IntervalSemanticsTests(unittest.TestCase):
    def test_three_way_classification(self):
        self.assertEqual(rank_pari.classify(0, 2, 3)[0], "CERT_LT")
        self.assertEqual(rank_pari.classify(3, 5, 3)[0], "CERT_GE")
        self.assertEqual(rank_pari.classify(2, 3, 3)[0], "UNKNOWN")

    def test_pari_parser_exact_block(self):
        transcript = (
            "XEDNI_RANK_BEGIN\n"
            "LOWER=1\nUPPER=3\nSHA2_RANK=2\nPOINT_COUNT=1\nPARISIZEMAX=2147483648\n"
            "XEDNI_RANK_END\n"
        )
        self.assertEqual(
            rank_pari.parse_transcript(transcript),
            {"LOWER": 1, "UPPER": 3, "SHA2_RANK": 2, "POINT_COUNT": 1, "PARISIZEMAX": 2147483648},
        )

    def test_pari_parser_rejects_mutations(self):
        mutations = [
            "LOWER=0\nUPPER=0\nSHA2_RANK=0\nPOINT_COUNT=0\nPARISIZEMAX=2147483648\n",
            "XEDNI_RANK_BEGIN\nLOWER=2\nUPPER=1\nSHA2_RANK=0\nPOINT_COUNT=0\nPARISIZEMAX=2147483648\nXEDNI_RANK_END\n",
            "XEDNI_RANK_BEGIN\nLOWER=0\nUPPER=0\nPOINT_COUNT=0\nPARISIZEMAX=2147483648\nXEDNI_RANK_END\n",
            "XEDNI_RANK_BEGIN\nLOWER=0\nUPPER=0\nSHA2_RANK=0\nPOINT_COUNT=0\nPARISIZEMAX=2147483648\nXEDNI_RANK_END\nXEDNI_RANK_END\n",
        ]
        for transcript in mutations:
            with self.subTest(transcript=transcript), self.assertRaises(ValueError):
                rank_pari.parse_transcript(transcript)

    def test_magma_parser_rejects_mutations(self):
        good = "XEDNI_RANK_BEGIN\nLOWER=0\nUPPER=2\nXEDNI_RANK_END\n"
        self.assertEqual(rank_magma.parse_transcript(good), {"LOWER": 0, "UPPER": 2})
        for transcript in [
            good.replace("UPPER=2", "UPPER=-1"),
            good.replace("XEDNI_RANK_END", "BROKEN_END"),
            good + "XEDNI_RANK_BEGIN\n",
        ]:
            with self.subTest(transcript=transcript), self.assertRaises(ValueError):
                rank_magma.parse_transcript(transcript)

    def test_scripts_are_reproducible_and_request_certified_bounds(self):
        pari = rank_pari.make_script((0, 0, 1, -1, 0), 0)
        magma = rank_magma.make_script((0, 0, 1, -1, 0), 2)
        self.assertEqual(pari, rank_pari.make_script((0, 0, 1, -1, 0), 0))
        self.assertIn("ellrank(E,0)", pari)
        self.assertIn("default(parisizemax,2147483648)", pari)
        self.assertIn("SetSeed(1);", magma)
        self.assertIn("RankBounds(E : Effort := 2)", magma)
        self.assertNotIn("TwoSelmerGroup", magma)


class AdapterExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="xedni-rank-tests-")
        cls.directory = Path(cls.temporary.name)
        cls.fake = tool_controls.install_fake_tool(cls.directory)
        cls.pari_tool = rank_pari.probe_tool(str(cls.fake))
        cls.magma_tool = rank_magma.probe_tool(str(cls.fake))

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @staticmethod
    def row(suffix: int, r: int = 1):
        return {"row_id": f"row-{suffix}", "r": r, "ainvs": [0, 0, 0, 0, suffix]}

    def assert_execution_audit(self, result: dict):
        execution = result["execution"]
        self.assertIsInstance(execution["command"], list)
        self.assertEqual(execution["returncode"], 0)
        self.assertEqual(execution["script_sha256"], hashlib.sha256(execution["script"].encode()).hexdigest())
        self.assertIsInstance(execution["stdout"], str)
        self.assertIsInstance(execution["stderr"], str)
        self.assertGreaterEqual(execution["wall_ns"], 0)
        self.assertEqual(result["tool"]["version_returncode"], 0)
        self.assertIsInstance(result["tool"]["version_command"], list)
        self.assertIsInstance(result["tool"]["version_stdout"], str)
        self.assertGreaterEqual(result["tool"]["version_wall_ns"], 0)

    def test_pari_classifications_and_audit(self):
        cases = [(9101, "CERT_LT"), (9102, "CERT_GE"), (9103, "UNKNOWN")]
        for suffix, expected in cases:
            with self.subTest(suffix=suffix):
                result = rank_pari.process_row(self.row(suffix), self.pari_tool, 2.0, 0)
                self.assertEqual(result["classification"], expected)
                self.assert_execution_audit(result)

    def test_pari_failures_are_unknown(self):
        cases = [(9104, "parser_error"), (9105, "parser_error"), (9106, "tool_nonzero_exit")]
        for suffix, reason in cases:
            with self.subTest(suffix=suffix):
                result = rank_pari.process_row(self.row(suffix), self.pari_tool, 2.0, 0)
                self.assertEqual((result["classification"], result["reason"]), ("UNKNOWN", reason))
        timed = rank_pari.process_row(self.row(9107), self.pari_tool, 0.03, 0)
        self.assertEqual((timed["classification"], timed["reason"]), ("UNKNOWN", "timeout"))
        self.assertTrue(timed["execution"]["timed_out"])
        self.assertIsNone(timed["execution"]["returncode"])

    def test_malformed_and_missing_pari_are_unknown(self):
        malformed = rank_pari.process_row(
            {"row_id": "bad", "r": 1, "ainvs": [0]}, self.pari_tool, 2.0, 0
        )
        self.assertEqual((malformed["classification"], malformed["reason"]), ("UNKNOWN", "invalid_input"))
        missing_tool = rank_pari.probe_tool(str(self.directory / "absent-gp"))
        missing = rank_pari.process_row(self.row(9101), missing_tool, 2.0, 0)
        self.assertEqual((missing["classification"], missing["reason"]), ("UNKNOWN", "missing_tool"))
        self.assertIn("executable not found", missing["error"])

    def test_magma_classifications_failures_and_version(self):
        self.assertIn("2.29-10-fake", self.magma_tool["version_stdout"])
        self.assertIn("major, minor, patch := GetVersion()", self.magma_tool["version_script"])
        for suffix, expected in [(9101, "CERT_LT"), (9102, "CERT_GE"), (9103, "UNKNOWN")]:
            with self.subTest(suffix=suffix):
                result = rank_magma.process_row(self.row(suffix), self.magma_tool, 2.0)
                self.assertEqual(result["classification"], expected)
                self.assert_execution_audit(result)
        malformed = rank_magma.process_row(self.row(9104), self.magma_tool, 2.0)
        self.assertEqual((malformed["classification"], malformed["reason"]), ("UNKNOWN", "parser_error"))
        timed = rank_magma.process_row(self.row(9107), self.magma_tool, 0.03)
        self.assertEqual((timed["classification"], timed["reason"]), ("UNKNOWN", "timeout"))

    def test_magma_missing_is_explicit_unknown(self):
        tool = rank_magma.probe_tool(str(self.directory / "absent-magma"))
        result = rank_magma.process_row(self.row(9101), tool, 2.0)
        self.assertEqual((result["classification"], result["reason"]), ("UNKNOWN", "missing_tool"))
        self.assertIn("executable not found", result["error"])

    def test_pari_jsonl_cli_order_invalid_json_and_canonical_output(self):
        rows = [
            json.dumps(self.row(9102), separators=(",", ":")),
            "{mutated-json",
            json.dumps(self.row(9101), separators=(",", ":")),
        ]
        raw_input = "\n".join(rows) + "\n"
        completed = subprocess.run(
            [
                sys.executable,
                str(Path(rank_pari.__file__)),
                "--gp",
                str(self.fake),
                "--timeout",
                "2",
            ],
            input=raw_input,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        lines = completed.stdout.splitlines()
        self.assertEqual(len(lines), 3)
        parsed = [json.loads(line) for line in lines]
        self.assertEqual([item["row_id"] for item in parsed], ["row-9102", "invalid-json-line-2", "row-9101"])
        self.assertEqual([item["reason"] for item in parsed], ["certified_lower_at_least_r", "invalid_json", "certified_upper_below_r"])
        self.assertEqual(parsed[1]["input_sha256"], hashlib.sha256((rows[1] + "\n").encode()).hexdigest())
        for line, value in zip(lines, parsed):
            self.assertEqual(line, json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))

    def test_full_synthetic_control_suite(self):
        records = tool_controls.synthetic_controls(self.fake, 0.03)
        self.assertGreaterEqual(len(records), 16)
        self.assertTrue(all(item["passed"] for item in records))


if __name__ == "__main__":
    unittest.main()
