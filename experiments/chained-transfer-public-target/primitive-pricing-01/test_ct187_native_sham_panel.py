#!/usr/bin/env python3
"""Source-only CT187 native-sham producer/reader handshake. No native child spawned."""
import base64
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import ct176_cold_process_collector as bounded
import ct186_same_route_sham as sham
import ct187_native_sham_panel as panel

FIXTURE = (Path(__file__).resolve().parent.parent /
           "evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json")


def fake_trial(binary, index, arm, row, unused_timeout):
    # Authentically shaped but entirely SYNTHETIC child transcript.
    child = {
        "schema": bounded.CHILD_SCHEMA, "packet_index": index,
        "from": row["from"], "to": row["to"], "sector": row["sector"],
        "scalar_label_outside_runtime": row["scalar_OUTSIDE_runtime"],
        "fixture_rows_checked": 48,
        "preflight_native_routes": 0, "preflight_native_inverses": 0,
        "arm": arm, "rustc_child_process_spawned": False,
        "external_os_loader_wall_included": False,
        "public_source_packet": row["input"],
        "verified_canonical_target": row["whole_outputs_equal"],
        "native_calls": row[arm],
        "native_sample": {
            "complete_counter_match": True, "elapsed_ns_decimal": "10",
        },
        "same_process_setup_ns_decimal": "4",
        "in_process_total_ns_decimal": "25",
        "peak_rss_kib_linux": 1024,
    }
    stdout = (json.dumps(child, separators=(",", ":")) + "\n").encode("utf-8")
    stderr = b""
    return {
        "argv": [str(binary), "--cold-route", str(index), arm],
        "external_wall_ns_decimal": "50",
        "exit_code": 0,
        "stdout": stdout.decode(), "stderr": "",
        "stdout_base64": base64.b64encode(stdout).decode("ascii"),
        "stderr_base64": "",
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "capture_complete": True,
        "peak_rss_kib_linux": 1024,
        "verified": True, "error": None,
    }


class CT187SourceTests(unittest.TestCase):
    @staticmethod
    def execution_args(output):
        binary = Path(sys.executable).resolve()
        return [
            "--fixture", str(FIXTURE), "--execute", "--admission-approved",
            "--executable", str(binary), "--executable-sha256",
            panel.digest_file(binary), "--output", str(output),
            "--panel-wall-seconds", "120",
        ]

    def test_plan_is_strictly_no_spawn_and_pinned(self):
        with mock.patch.object(bounded, "run_sample",
                               side_effect=AssertionError("no child")) as stub:
            with contextlib.redirect_stdout(io.StringIO()) as buf:
                self.assertEqual(panel.collect(["--fixture", str(FIXTURE)]), 0)
            stub.assert_not_called()
        plan = json.loads(buf.getvalue())
        self.assertTrue(plan["plan_only"])
        self.assertEqual(plan["schema"], panel.SCHEMA)
        self.assertEqual(plan["processes"], 1536)
        self.assertEqual(plan["roster_sha256"], sham.roster_sha256())
        self.assertEqual(plan["physical_arm"], sham.PHYSICAL_ARM)

    def test_outer_plan_mode_cannot_smuggle_execute(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as e:
                panel.main(["plan", "--fixture", str(FIXTURE), "--execute",
                            "--admission-approved"])
        self.assertEqual(e.exception.code, 2)

    def test_execution_refuses_absent_authorization_budget_or_hash(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "panel.jsonl"
            args = self.execution_args(output)
            cases = [
                [a for a in args if a != "--admission-approved"],
                [a for a in args if a not in ("--panel-wall-seconds", "120")],
                args[:args.index("--executable-sha256")+1] +
                ["0"*64] + args[args.index("--executable-sha256")+2:],
            ]
            with mock.patch.object(bounded, "run_sample",
                                   side_effect=AssertionError("unauthorized child")):
                for argv in cases:
                    with self.subTest(argv=argv):
                        with contextlib.redirect_stderr(io.StringIO()):
                            with self.assertRaises(SystemExit) as e:
                                panel.collect(argv)
                        self.assertEqual(e.exception.code, 2)
                        self.assertFalse(output.exists())

    def test_failed_sample_retained_and_not_passed_to_reader(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / "incomplete.jsonl"
            def refuse(binary, index, arm, row, timeout):
                trial = fake_trial(binary, index, arm, row, timeout)
                trial.update({"verified": False, "error": "synthetic failure",
                              "capture_complete": False})
                return trial
            with mock.patch.object(bounded, "run_sample", side_effect=refuse) as stub:
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(panel.collect(self.execution_args(output)), 1)
                self.assertEqual(stub.call_count, 1)
            entries = [json.loads(t) for t in output.read_text().splitlines()]
            self.assertEqual(len(entries), 3)
            self.assertEqual(entries[-1]["attempted"], 1)
            self.assertEqual(entries[-1]["planned"], 1536)
            self.assertFalse(entries[-1]["verified_complete"])
            with self.assertRaises(ValueError):
                panel.adjudicate(output, FIXTURE)

    def test_complete_mock_panel_and_fail_closed_mutations(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / "source_synthetic.jsonl"
            with mock.patch.object(bounded, "run_sample", side_effect=fake_trial) as stub:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(panel.collect(self.execution_args(output)), 0)
                self.assertEqual(stub.call_count, 1536)
                self.assertEqual({c.args[2] for c in stub.call_args_list},
                                 {sham.PHYSICAL_ARM})
            result = panel.adjudicate(output, FIXTURE)
            self.assertEqual(result["observed_complete_processes"], 1536)
            self.assertTrue(result["complete_memory_evidence"])
            self.assertEqual(result["sham_diagnostic"]["median_sham_ratio"], 1)
            self.assertFalse(result["signed_independent_pcc"])
            self.assertFalse(result["complete_single_target_ecdlp_advantage_established"])
            lines = output.read_text().splitlines()
            for pos, field, value in [
                (1, "label", "unblinded"),
                (1, "physical_arm", "strongest_retained_lift_chain"),
                (1, "stdout_sha256", "0"*64),
                (-1, "attempted", 1535),
            ]:
                changed = list(lines)
                obj = json.loads(changed[pos])
                obj[field] = value
                changed[pos] = json.dumps(obj)
                altered = Path(d) / "altered.jsonl"
                altered.write_text("\n".join(changed) + "\n")
                with self.subTest(field=field):
                    with self.assertRaises(ValueError):
                        panel.adjudicate(altered, FIXTURE)
            short = Path(d) / "truncated.jsonl"
            short.write_text("\n".join(lines[:-1]) + "\n")
            with self.assertRaises(ValueError):
                panel.adjudicate(short, FIXTURE)


if __name__ == "__main__":
    unittest.main()
