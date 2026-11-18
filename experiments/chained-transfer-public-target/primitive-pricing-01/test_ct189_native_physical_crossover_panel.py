#!/usr/bin/env python3
"""CT189 strictly source/mocked tests. Native children are NEVER spawned here."""
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

import ct176_cold_process_collector as native
import ct188_physical_crossover_design as design
import ct189_native_physical_crossover_panel as panel

FIXTURE = (Path(__file__).resolve().parent.parent /
           "evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json")


def fake_trial(binary, packet, arm, row, unused_timeout):
    """Construct an internally consistent SYNTHETIC CT175-shaped transcript."""
    child = {
        "schema": native.CHILD_SCHEMA,
        "packet_index": packet,
        "from": row["from"], "to": row["to"], "sector": row["sector"],
        "scalar_label_outside_runtime": row["scalar_OUTSIDE_runtime"],
        "fixture_rows_checked": 48,
        "preflight_native_routes": 0, "preflight_native_inverses": 0,
        "arm": arm,
        "rustc_child_process_spawned": False,
        "external_os_loader_wall_included": False,
        "public_source_packet": row["input"],
        "verified_canonical_target": row["whole_outputs_equal"],
        "native_calls": row[arm],
        "native_sample": {"complete_counter_match": True, "elapsed_ns_decimal": "10"},
        "same_process_setup_ns_decimal": "4",
        "in_process_total_ns_decimal": "25",
        "peak_rss_kib_linux": 1024,
    }
    raw = (json.dumps(child, separators=(",", ":")) + "\n").encode()
    return {
        "argv": [str(binary), "--cold-route", str(packet), arm],
        "external_wall_ns_decimal": "50",
        "exit_code": 0,
        "stdout": raw.decode(), "stderr": "",
        "stdout_base64": base64.b64encode(raw).decode(),
        "stderr_base64": "",
        "stdout_sha256": hashlib.sha256(raw).hexdigest(),
        "stderr_sha256": hashlib.sha256(b"").hexdigest(),
        "capture_complete": True, "peak_rss_kib_linux": 1024,
        "verified": True, "error": None,
    }


def change_child(line, callback):
    record = json.loads(line)
    child = json.loads(record["stdout"])
    callback(child)
    raw = (json.dumps(child, separators=(",", ":")) + "\n").encode()
    record["stdout"] = raw.decode()
    record["stdout_base64"] = base64.b64encode(raw).decode()
    record["stdout_sha256"] = hashlib.sha256(raw).hexdigest()
    return json.dumps(record)


class CT189SourceTests(unittest.TestCase):
    @staticmethod
    def execution_args(path):
        binary = Path(sys.executable).resolve()
        return [
            "--fixture", str(FIXTURE),
            "--execute", "--admission-approved",
            "--executable", str(binary),
            "--executable-sha256", panel.digest_file(binary),
            "--output", str(path),
            "--panel-wall-seconds", "120",
        ]

    def test_pinned_plan_only_and_exact_physical_roster(self):
        with mock.patch.object(native, "run_sample",
                               side_effect=AssertionError("native spawn prohibited")) as stub:
            with contextlib.redirect_stdout(io.StringIO()) as sink:
                self.assertEqual(panel.main(["plan", "--fixture", str(FIXTURE)]), 0)
            stub.assert_not_called()
        result = json.loads(sink.getvalue())
        self.assertTrue(result["plan_only"])
        self.assertEqual(result["schema"], panel.SCHEMA)
        self.assertEqual(result["processes"], 2304)
        self.assertEqual(result["roster_sha256"], design.roster_sha256())
        self.assertEqual(result["fixture_git_blob"], native.FIXTURE_GIT_BLOB)
        self.assertTrue(panel.checked_design())
        self.assertEqual(set(arm for _, _, pos, arm in design.roster() if pos < 4),
                         set(design.ARMS.values()))

    def test_plan_cannot_smuggle_execution_or_admission(self):
        cases = [
            ["plan", "--fixture", str(FIXTURE), "--execute"],
            ["plan", "--fixture", str(FIXTURE), "--admission-approved"],
            ["plan", "--fixture", str(FIXTURE), "--panel-wall-seconds", "600"],
        ]
        for args in cases:
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as exc:
                    panel.main(args)
                self.assertEqual(exc.exception.code, 2)

    def test_execution_requires_external_approval_budget_and_exact_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "no_write.jsonl"
            args = self.execution_args(output)
            cases = [
                [x for x in args if x != "--admission-approved"],
                [x for x in args if x not in ("--panel-wall-seconds", "120")],
                args[:args.index("--executable-sha256") + 1] +
                ["0" * 64] + args[args.index("--executable-sha256") + 2:],
            ]
            with mock.patch.object(native, "run_sample",
                                   side_effect=AssertionError("unauthorized spawn")):
                for argv in cases:
                    with self.subTest(args=argv), contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit) as exc:
                            panel.collect(argv)
                        self.assertEqual(exc.exception.code, 2)
                        self.assertFalse(output.exists())

    def test_first_failed_sample_preserves_refusal_not_statistics(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "refused.jsonl"
            def bad(*args):
                record = fake_trial(*args)
                record.update(verified=False, error="synthetic failure",
                              capture_complete=False)
                return record
            with mock.patch.object(native, "run_sample", side_effect=bad) as stub:
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(panel.collect(self.execution_args(path)), 1)
                self.assertEqual(stub.call_count, 1)
            entries = [json.loads(x) for x in path.read_text().splitlines()]
            self.assertEqual(len(entries), 3)
            self.assertEqual(entries[-1]["attempted"], 1)
            self.assertFalse(entries[-1]["verified_complete"])
            with self.assertRaises(ValueError):
                panel.adjudicate(path, FIXTURE)

    def test_full_2304_mock_to_reader_and_native_arm_fidelity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mocked.jsonl"
            with mock.patch.object(native, "run_sample", side_effect=fake_trial) as stub:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(panel.collect(self.execution_args(path)), 0)
                self.assertEqual(stub.call_count, design.N)
                actual = [call.args[2] for call in stub.call_args_list]
                self.assertEqual(actual, [a for _, _, _, a in design.roster()])
                self.assertEqual(set(actual), set(design.ARMS.values()))
            outcome = panel.adjudicate(path, FIXTURE)
            self.assertEqual(outcome["observed_complete_processes"], 2304)
            self.assertEqual(outcome["processes_missing_peak_rss"], 0)
            self.assertTrue(outcome["complete_memory_evidence"])
            self.assertAlmostEqual(
                outcome["conditional_source_model_diagnostic"]
                ["median_direct_over_retained_ratio_conditional_model"], 1)
            self.assertFalse(outcome["signed_independent_pcc"])
            self.assertFalse(outcome["complete_single_target_ecdlp_advantage_established"])
            lines = path.read_text().splitlines()
            def check_change(position, field, value):
                mutated = list(lines)
                item = json.loads(mutated[position])
                item[field] = value
                mutated[position] = json.dumps(item)
                tampered = Path(tmp) / "tampered.jsonl"
                tampered.write_text("\n".join(mutated) + "\n")
                with self.assertRaises(ValueError):
                    panel.adjudicate(tampered, FIXTURE)
            for position, field, value in [
                (0, "schema", "ct176-cold-public-process-panel/v1"),
                (1, "arm", "forged"),
                (1, "argv", ["not-the-binary"]),
                (1, "stdout_sha256", "0" * 64),
                (1, "external_wall_ns_decimal", "1"),
                (-1, "attempted", 2303),
            ]:
                with self.subTest(field=field):
                    check_change(position, field, value)
            changed = list(lines)
            changed[1] = change_child(lines[1], lambda obj: obj["native_calls"].__setitem__(
                next(iter(obj["native_calls"])),
                next(iter(obj["native_calls"].values())) + 1))
            mutated = Path(tmp) / "tampered.jsonl"
            mutated.write_text("\n".join(changed) + "\n")
            with self.assertRaises(ValueError):
                panel.adjudicate(mutated, FIXTURE)
            changed[1] = change_child(lines[1],
                                      lambda obj: obj.__setitem__(
                                          "in_process_total_ns_decimal", "1000"))
            mutated.write_text("\n".join(changed) + "\n")
            with self.assertRaises(ValueError):
                panel.adjudicate(mutated, FIXTURE)
            truncated = Path(tmp) / "truncated.jsonl"
            truncated.write_text("\n".join(lines[:-1]) + "\n")
            with self.assertRaises(ValueError):
                panel.adjudicate(truncated, FIXTURE)


if __name__ == "__main__":
    unittest.main()
