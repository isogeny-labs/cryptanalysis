#!/usr/bin/env python3
"""CT183 source-only and fake-sample controls; no native arithmetic or timed DLP."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct176_cold_process_collector as v1
import ct183_v2_cold_process_collector as v2

FIXTURE = (Path(__file__).resolve().parent.parent /
           "evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json")


class CT183SourceTests(unittest.TestCase):
    def test_v2_roster_exact_digest_and_per_packet_balance(self):
        roster = list(v2.roster())
        self.assertEqual(len(roster), 2304)
        self.assertEqual(len(set(roster)), 2304)
        self.assertEqual(v2.roster_sha256(), v2.EXPECTED_ROSTER_SHA256)
        self.assertEqual(v2.EXPECTED_ROSTER_SHA256,
                         "1dddb4839321ad6560fd429330778aa083ff3a13625393250e964c05f9fc5ee4")
        for i in range(48):
            order_names = []
            for block in range(8):
                sample = [arm for b, index, _, arm in roster
                          if b == block and index == i]
                self.assertEqual(sample, list(v2.treatment_order(block, i)))
                self.assertEqual(sample.count(v2.A), 4)
                self.assertEqual(sample.count(v2.B), 2)
                self.assertEqual(sample[-2:], [v2.A, v2.A])
                order_names.append(tuple(sample[:4]))
            self.assertEqual(order_names.count((v2.A, v2.B, v2.B, v2.A)), 4)
            self.assertEqual(order_names.count((v2.B, v2.A, v2.A, v2.B)), 4)

    def test_v1_unchanged_and_schema_strictly_distinct(self):
        self.assertEqual(v1.SCHEMA, "ct176-cold-public-process-panel/v1")
        self.assertEqual(v1.ARMS[:4], (v2.A, v2.B, v2.B, v2.A))
        self.assertNotEqual(v2.SCHEMA, v1.SCHEMA)
        self.assertEqual(v2.ORDER_SCHEDULE,
                         "ct181-block-packet-parity-ABBA-BAAB/v2")
        for bad in (True, -1, 8, 1.0, "0"):
            with self.subTest(block=bad):
                with self.assertRaises(ValueError):
                    v2.treatment_order(bad, 0)

    def test_plan_only_uses_original_48_packets_and_never_runs_child(self):
        output = io.StringIO()
        with mock.patch.object(v1, "run_sample", side_effect=AssertionError("child called")):
            with contextlib.redirect_stdout(output):
                rc = v2.run(["--fixture", str(FIXTURE)])
        self.assertEqual(rc, 0)
        manifest = json.loads(output.getvalue())
        self.assertTrue(manifest["plan_only"])
        self.assertEqual(manifest["schema"], v2.SCHEMA)
        self.assertEqual(manifest["order_roster_sha256"], v2.EXPECTED_ROSTER_SHA256)
        self.assertEqual(manifest["fixture_git_blob"], v1.FIXTURE_GIT_BLOB)
        self.assertEqual(manifest["processes"], 2304)
        self.assertEqual(manifest["packets"], 48)
        self.assertNotIn("executable_path", manifest)

    def test_execute_requires_admission_before_binary_or_output(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as got:
                v2.run(["--fixture", str(FIXTURE), "--execute"])
        self.assertEqual(got.exception.code, 2)

    def test_execute_requires_aggregate_budget(self):
        with tempfile.TemporaryDirectory() as d:
            args = self.execution_args(Path(d) / "panel.jsonl")
            for bad in ([], ["--panel-wall-seconds", "0"],
                        ["--panel-wall-seconds", "-1"]):
                with self.subTest(bad=bad):
                    with contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit) as got:
                            v2.run(args + bad)
                    self.assertEqual(got.exception.code, 2)
                    self.assertFalse((Path(d) / "panel.jsonl").exists())

    @staticmethod
    def execution_args(output):
        binary = Path(sys.executable).resolve()
        return ["--fixture", str(FIXTURE), "--execute",
                "--admission-approved", "--executable", str(binary),
                "--executable-sha256", hashlib.sha256(binary.read_bytes()).hexdigest(),
                "--output", str(output)]

    def test_executable_sha_rejected_without_opening_output(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "panel.jsonl"
            args = self.execution_args(path)
            ix = args.index("--executable-sha256") + 1
            args[ix] = "0" * 64
            # No helper may spawn before the executable SHA is checked.
            with mock.patch.object(v1, "run_sample",
                                   side_effect=AssertionError("unexpected child")) as child:
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as got:
                        v2.run(args + ["--panel-wall-seconds", "1"])
                self.assertEqual(got.exception.code, 2)
                child.assert_not_called()
            self.assertFalse(path.exists())

    def test_failed_mock_sample_persists_censored_v2_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / "panel.jsonl"
            called = []
            def fake_run(binary, index, arm, row, seconds):
                called.append((index, arm))
                return {"verified": False, "error": "synthetic first-child refusal",
                        "argv": [str(binary), "--cold-route", str(index), arm],
                        "capture_complete": False,
                        "external_wall_ns_decimal": "1"}
            with mock.patch.object(v1, "run_sample", side_effect=fake_run):
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(v2.run(self.execution_args(output) +
                                            ["--panel-wall-seconds", "60"]), 1)
            records = [json.loads(line) for line in output.read_text().splitlines()]
            self.assertEqual(len(records), 3)
            self.assertEqual(records[0]["schema"], v2.SCHEMA)
            self.assertEqual(records[0]["order_roster_sha256"],
                             v2.EXPECTED_ROSTER_SHA256)
            self.assertEqual(records[1]["arm"], v2.A)
            self.assertEqual(records[1]["packet_index"], 6)
            self.assertEqual(records[1]["error"], "synthetic first-child refusal")
            self.assertEqual(len(called), 1)
            self.assertFalse(records[-1]["verified_complete"])
            self.assertEqual(records[-1]["attempted"], 1)
            self.assertEqual(records[-1]["planned"], 2304)
            self.assertEqual(records[-1]["refusal"], "synthetic first-child refusal")

    def test_terminal_refuses_deadline_even_if_all_samples_existed(self):
        outcome = v1.terminal_status(v2.N, "aggregate panel wall deadline exhausted")
        self.assertFalse(outcome["verified_complete"])
        self.assertIn("deadline", outcome["refusal"])


if __name__ == "__main__":
    unittest.main()
