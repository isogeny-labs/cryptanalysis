#!/usr/bin/env python3
"""Producer-only negative controls for CT176; no native curve arithmetic or cost."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct176_cold_process_collector as panel


def fake_row():
    calls = {f"counter_{i:02d}": i for i in range(21)}
    return {
        "from": 0, "to": 2, "sector": 0, "scalar_OUTSIDE_runtime": 0,
        "input": [0] * 19, "whole_outputs_equal": [1] * 19,
        "direct_composite": calls,
        "strongest_retained_lift_chain": dict(calls),
    }


def fake_observation(row):
    return {
        "schema": panel.CHILD_SCHEMA,
        "packet_index": 0, "from": 0, "to": 2,
        "sector": 0, "scalar_label_outside_runtime": 0,
        "fixture_rows_checked": 48, "preflight_native_routes": 0,
        "preflight_native_inverses": 0,
        "arm": "direct_composite",
        "rustc_child_process_spawned": False,
        "external_os_loader_wall_included": False,
        "public_source_packet": row["input"],
        "verified_canonical_target": row["whole_outputs_equal"],
        "native_calls": row["direct_composite"],
        "native_sample": {
            "elapsed_ns_decimal": "19", "complete_counter_match": True,
        },
        "same_process_setup_ns_decimal": "20",
        "in_process_total_ns_decimal": "99",
        "peak_rss_kib_linux": 1024,
    }


class CT176Tests(unittest.TestCase):
    def setUp(self):
        self.row = fake_row()
        self.obs = fake_observation(self.row)

    def test_accept_correct_record(self):
        self.assertTrue(panel.verify_native(self.obs, self.row, 0, "direct_composite"))

    def bad(self, mutation):
        bad = copy.deepcopy(self.obs)
        mutation(bad)
        with self.assertRaises((ValueError, TypeError)):
            panel.verify_native(bad, self.row, 0, "direct_composite")

    def test_reject_changed_target(self):
        self.bad(lambda x: x["verified_canonical_target"].__setitem__(0, 2))

    def test_reject_changed_source(self):
        self.bad(lambda x: x["public_source_packet"].__setitem__(0, 1))

    def test_reject_bool_counter(self):
        self.bad(lambda x: x["native_calls"].__setitem__("counter_00", False))

    def test_reject_float_counter(self):
        self.bad(lambda x: x["native_calls"].__setitem__("counter_01", 1.0))

    def test_reject_extra_counter(self):
        self.bad(lambda x: x["native_calls"].__setitem__("malicious_extra", 1))

    def test_reject_missing_counter(self):
        self.bad(lambda x: x["native_calls"].pop("counter_20"))

    def test_reject_wrong_arm(self):
        self.bad(lambda x: x.__setitem__("arm", "strongest_retained_lift_chain"))

    def test_reject_falsified_cohort(self):
        self.bad(lambda x: x.__setitem__("sector", 2))

    def test_reject_preflight(self):
        self.bad(lambda x: x.__setitem__("preflight_native_routes", 144))

    def test_reject_extra_child_process(self):
        self.bad(lambda x: x.__setitem__("rustc_child_process_spawned", True))

    def test_reject_float_index(self):
        self.bad(lambda x: x.__setitem__("packet_index", 0.0))

    def test_reject_boolean_index(self):
        self.bad(lambda x: x.__setitem__("packet_index", False))

    def test_reject_wrong_timer_type(self):
        self.bad(lambda x: x["native_sample"].__setitem__("elapsed_ns_decimal", 19))

    def test_reject_noncanonical_timer(self):
        self.bad(lambda x: x["native_sample"].__setitem__("elapsed_ns_decimal", "0019"))

    def test_reject_wrong_counter_schema(self):
        self.bad(lambda x: x.__setitem__("native_calls", {}))

    def test_reject_wrong_output_length(self):
        self.bad(lambda x: x["verified_canonical_target"].pop())

    def test_roster_fixed_and_pairing(self):
        samples = list(panel.sample_order())
        self.assertEqual(len(samples), 2304)
        self.assertEqual(len({(b, i) for b, i, _, _ in samples}), 384)
        for block in range(8):
            for index in range(48):
                arms = [arm for b, i, _, arm in samples
                        if b == block and i == index]
                self.assertEqual(arms, list(panel.ARMS))
        self.assertEqual(panel.ARMS[0:4],
                         ("direct_composite", "strongest_retained_lift_chain",
                          "strongest_retained_lift_chain", "direct_composite"))
        self.assertEqual(panel.ARMS[-2:], ("direct_composite", "direct_composite"))

    def test_terminal_incomplete_is_refused(self):
        terminal = panel.terminal_status(2303, None)
        self.assertFalse(terminal["verified_complete"])
        self.assertEqual(terminal["refusal"], "incomplete process population")
        self.assertEqual(terminal["attempted"], 2303)

    def test_terminal_preserves_failure(self):
        terminal = panel.terminal_status(18, "child nonzero exit")
        self.assertFalse(terminal["verified_complete"])
        self.assertEqual(terminal["refusal"], "child nonzero exit")

    def test_terminal_all_complete(self):
        terminal = panel.terminal_status(2304, None)
        self.assertTrue(terminal["verified_complete"])
        self.assertIsNone(terminal["refusal"])

    def test_subprocess_validates_public_mock_not_math(self):
        with tempfile.TemporaryDirectory() as tmp:
            child = Path(tmp) / "mock_ct175.py"
            child.write_text("#!" + sys.executable + "\n" +
                             "print(" + repr(json.dumps(self.obs)) + ")\n")
            os.chmod(child, 0o700)
            result = panel.run_sample(child, 0, "direct_composite",
                                      self.row, 5)
            self.assertTrue(result["verified"], result)
            self.assertEqual(result["exit_code"], 0)
            self.assertGreater(int(result["external_wall_ns_decimal"]), 0)
            self.assertEqual(result["peak_rss_kib_linux"], 1024)

    def test_subprocess_wrong_evidence_preserved_as_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            child = Path(tmp) / "mock_ct175.py"
            mutated = copy.deepcopy(self.obs)
            mutated["verified_canonical_target"][0] = 2
            child.write_text("#!" + sys.executable + "\n" +
                             "print(" + repr(json.dumps(mutated)) + ")\n")
            os.chmod(child, 0o700)
            result = panel.run_sample(child, 0, "direct_composite",
                                      self.row, 5)
            self.assertFalse(result["verified"])
            self.assertEqual(result["exit_code"], 0)
            self.assertIn("target differs", result["error"])
            self.assertTrue(result["stdout_sha256"])
            self.assertTrue(result["stdout_base64"])

    def test_bounded_stdout_flood_during_child_execution(self):
        # Negative control: old subprocess.run(capture_output=True) buffered all
        # of this output and only rejected it after child termination.
        with tempfile.TemporaryDirectory() as tmp:
            child = Path(tmp) / "flood_stdout.py"
            child.write_text("#!" + sys.executable + "\n" +
                             "import os\nos.write(1, b'x' * (1024 * 1024))\n")
            os.chmod(child, 0o700)
            result = panel.run_sample(child, 0, "direct_composite", self.row, 5)
            self.assertFalse(result["verified"])
            self.assertEqual(result["error"], "capture limit exceeded")
            self.assertIs(result["capture_complete"], False)
            captured = __import__("base64").b64decode(result["stdout_base64"])
            self.assertEqual(len(captured), panel.MAX_CAPTURE + 1)
            self.assertEqual(result["stdout_sha256"],
                             __import__("hashlib").sha256(captured).hexdigest())
            self.assertGreater(int(result["external_wall_ns_decimal"]), 0)

    def test_bounded_stderr_flood_during_child_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            child = Path(tmp) / "flood_stderr.py"
            child.write_text("#!" + sys.executable + "\n" +
                             "import os\nos.write(2, b'e' * (1024 * 1024))\n")
            os.chmod(child, 0o700)
            result = panel.run_sample(child, 0, "direct_composite", self.row, 5)
            self.assertFalse(result["verified"])
            self.assertEqual(result["error"], "capture limit exceeded")
            self.assertIs(result["capture_complete"], False)
            self.assertEqual(len(__import__("base64").b64decode(
                result["stderr_base64"])), panel.MAX_CAPTURE + 1)

    def test_both_pipes_drained_concurrently_without_deadlock(self):
        with tempfile.TemporaryDirectory() as tmp:
            child = Path(tmp) / "both_pipes.py"
            child.write_text("#!" + sys.executable + "\n" +
                             "import os\n" +
                             "os.write(2, b'e' * 100000)\n" +
                             "os.write(1, " + repr(json.dumps(self.obs).encode("utf-8") + b"\n") +
                             ")\n")
            os.chmod(child, 0o700)
            result = panel.run_sample(child, 0, "direct_composite", self.row, 5)
            self.assertTrue(result["verified"], result["error"])
            self.assertIs(result["capture_complete"], True)
            self.assertEqual(len(__import__("base64").b64decode(
                result["stderr_base64"])), 100000)

    def test_silent_child_timeout_is_terminal_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            child = Path(tmp) / "silent_sleep.py"
            child.write_text("#!" + sys.executable + "\n" +
                             "import time\ntime.sleep(30)\n")
            os.chmod(child, 0o700)
            result = panel.run_sample(child, 0, "direct_composite", self.row, 1)
            self.assertFalse(result["verified"])
            self.assertEqual(result["error"], "timeout")
            self.assertIs(result["capture_complete"], False)
            self.assertLess(int(result["external_wall_ns_decimal"]), 5_000_000_000)

    def test_nonzero_exit_retains_bounded_stderr(self):
        with tempfile.TemporaryDirectory() as tmp:
            child = Path(tmp) / "nonzero.py"
            child.write_text("#!" + sys.executable + "\n" +
                             "import sys\nsys.stderr.write('failure witness')\nsys.exit(7)\n")
            os.chmod(child, 0o700)
            result = panel.run_sample(child, 0, "direct_composite", self.row, 5)
            self.assertFalse(result["verified"])
            self.assertEqual(result["error"], "child nonzero exit")
            self.assertEqual(result["exit_code"], 7)
            self.assertEqual(result["stderr"], "failure witness")
            self.assertIs(result["capture_complete"], True)

    def test_missing_binary_is_censored_not_crash(self):
        result = panel.run_sample(Path("/does/not/exist/ct175"), 0,
                                  "direct_composite", self.row, 1)
        self.assertFalse(result["verified"])
        self.assertEqual(result["error"], "process spawn failed")
        self.assertIsNone(result["exit_code"])


if __name__ == "__main__":
    unittest.main()
