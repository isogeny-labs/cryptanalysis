"""Unit tests of the fail-closed parts of verify_receipt.py and of the frozen schedule's pairing.

The raw-record tests are the parent's (`koblitz-n83-closure-indexlift-20261019`,
itself index-lift's on main). The tests this replication adds cover:

* a missing required gate;
* the command-line and runner identity checks;
* the two-stage paired bootstrap, which must keep A and B of a pair together;
* the schedule: strict alternation, one A and one B per pair with one rank
  seed, and the A/A and planted seeds.
"""

import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import make_schedule
from verify_receipt import (REQUIRED_CHECKS, command_issues, decide, raw_record, ratio_of_sums, runner_checks,
                            two_stage)

HERE = Path(__file__).resolve().parent


class DecideTests(unittest.TestCase):
    def checks(self, **override):
        checks = {key: True for key in REQUIRED_CHECKS}
        checks.update(override)
        return checks

    def stats(self, **override):
        stats = {
            "aa_e2e_B_over_Baa": {"estimate": 1.0},
            "aa_cold_B_over_Baa": {"estimate": 1.0},
            "planted_rank_attempt_kM38IX_over_kM38I": {"ci95": [1.5, 2.0]},
            "primary_e2e_paired_A_over_B": {"ci95": [5.0, 7.0]},
        }
        stats.update(override)
        return stats

    def test_all_true_gates_can_pass_controls(self):
        self.assertEqual(decide(self.checks(), self.stats())[0], "improvement")

    def test_unknown_gate_is_invalid(self):
        for key in REQUIRED_CHECKS:
            with self.subTest(key=key):
                self.assertEqual(decide(self.checks(**{key: None}), self.stats())[0], "invalid")

    def test_missing_required_gate_is_invalid(self):
        for key in REQUIRED_CHECKS:
            with self.subTest(key=key):
                checks = self.checks()
                del checks[key]
                self.assertEqual(decide(checks, self.stats())[0], "invalid")

    def test_extra_unknown_gate_is_invalid(self):
        self.assertEqual(decide(self.checks(some_new_gate=None), self.stats())[0], "invalid")

    def test_failed_planted_exactness_is_invalid(self):
        decision, controls = decide(self.checks(pre_timing_tables_and_closure_bases_verified=False), self.stats())
        self.assertEqual(decision, "invalid")
        self.assertFalse(controls["planted_exactness_corruptions_rejected"])

    def test_aa_outside_band_is_invalid(self):
        for key in ("aa_e2e_B_over_Baa", "aa_cold_B_over_Baa"):
            with self.subTest(key=key):
                self.assertEqual(decide(self.checks(), self.stats(**{key: {"estimate": 1.05}}))[0], "invalid")

    def test_planted_not_detected_is_invalid(self):
        stats = self.stats(planted_rank_attempt_kM38IX_over_kM38I={"ci95": [0.99, 1.2]})
        self.assertEqual(decide(self.checks(), stats)[0], "invalid")

    def test_interval_straddling_one_is_not_separated(self):
        stats = self.stats(primary_e2e_paired_A_over_B={"ci95": [0.9, 1.1]})
        self.assertEqual(decide(self.checks(), stats)[0], "not_separated")

    def test_regression(self):
        stats = self.stats(primary_e2e_paired_A_over_B={"ci95": [0.5, 0.9]})
        self.assertEqual(decide(self.checks(), stats)[0], "regression")

    def test_missing_primary_is_invalid(self):
        stats = self.stats()
        del stats["primary_e2e_paired_A_over_B"]
        self.assertEqual(decide(self.checks(), stats)[0], "invalid")


class RawRecordTests(unittest.TestCase):
    def read_raw(self, raw_bytes, digest_bytes=None):
        scheduled = {"arm": "cPI", "kind": "ic_cold", "point_id": "s000", "point": ["1", "2"], "seed": 7}
        summary_digest = hashlib.sha256(digest_bytes or raw_bytes).hexdigest()
        stdout = "raw_b64=" + base64.b64encode(raw_bytes).decode() + "\n"
        stdout += "online_ms=1.000000 verified=1 raw_result_sha256=%s\n" % summary_digest
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory)
            (receipt / "stdout.txt").write_text(stdout)
            return raw_record(receipt, {"stdout_file": "stdout.txt"}, scheduled, "ic_cold")

    def raw(self, **override):
        raw = {"arm": "cPI", "kind": "ic_cold", "panel": "s000", "point": ["1", "2"],
               "seed": 7, "fields": {"online_ms": 1.0}}
        raw.update(override)
        return json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()

    def test_untampered_raw_record_has_no_issue(self):
        raw, issues = self.read_raw(self.raw())
        self.assertEqual(issues, [])
        self.assertEqual(raw["arm"], "cPI")

    def test_raw_byte_tampering_fails_digest_check(self):
        _, issues = self.read_raw(self.raw(fields={"online_ms": 2.0}), digest_bytes=self.raw())
        self.assertIn("raw producer record digest differs from wrapper summary", issues)

    def test_raw_schedule_identity_mismatch_fails(self):
        for key, value in (("panel", "s001"), ("arm", "cM38I"), ("seed", 8), ("point", ["1", "3"]),
                           ("kind", "ic_rank")):
            with self.subTest(key=key):
                _, issues = self.read_raw(self.raw(**{key: value}))
                self.assertIn("raw producer record %s differs from the frozen schedule" % key, issues)

    def test_invalid_base64_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory)
            (receipt / "stdout.txt").write_text("raw_b64=!!!\nonline_ms=1 verified=1 raw_result_sha256=0\n")
            raw, issues = raw_record(receipt, {"stdout_file": "stdout.txt"},
                                     {"arm": "cPI", "point_id": "s000", "point": ["1", "2"], "seed": 7}, "ic_cold")
        self.assertIsNone(raw)
        self.assertTrue(issues[0].startswith("raw producer record is not valid base64 JSON"))


class IdentityTests(unittest.TestCase):
    scheduled = {"arm": "kPI", "point_id": "s003", "point": ["11", "12"], "seed": 1210}

    def argv(self, **override):
        values = {"--arm": "kPI", "--kind": "ic_rank", "--panel": "s003", "--seed": "1210", "--point": "11,12"}
        values.update(override)
        return ["python3", "arm.py"] + [x for kv in values.items() for x in kv]

    def test_matching_command_has_no_issue(self):
        self.assertEqual(command_issues({"command": self.argv()}, self.scheduled, "ic_rank"), [])

    def test_command_mismatch_is_reported(self):
        for flag, value in (("--arm", "kM38I"), ("--seed", "1211"), ("--point", "11,13"), ("--panel", "s004")):
            with self.subTest(flag=flag):
                self.assertTrue(command_issues({"command": self.argv(**{flag: value})}, self.scheduled, "ic_rank"))

    def test_runner_start_with_another_protocol_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory)
            (receipt / "runner_start.json").write_text(json.dumps({
                "protocol_sha256": "0" * 64, "schedule_sha256": "0" * 64, "arm_wrapper_sha256": "0" * 64,
                "runner_sha256": "0" * 64, "smoke_subset": {}, "execution_cpu": 0}))
            checks, _ = runner_checks(receipt, [], partial=False)
        self.assertIs(checks["runner_identity_matches_frozen_files"], False)
        self.assertIsNone(checks["binaries_unchanged"])  # no runner_end.json: unknown, so the run is invalid
        self.assertIsNone(checks["placement_pinned_every_process"])

    def test_missing_runner_start_is_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            checks, _ = runner_checks(Path(directory), [], partial=False)
        self.assertIsNone(checks["runner_identity_matches_frozen_files"])


class BootstrapTests(unittest.TestCase):
    def test_pairs_stay_together(self):
        # A = 2 B exactly in every pair while B varies a lot: a paired bootstrap gives exactly 2.
        points = [[(2.0 * b, b) for b in (1.0, 10.0, 100.0)] for _ in range(5)]
        result = two_stage(points, ratio_of_sums, 1, draws=500)
        self.assertAlmostEqual(result["estimate"], 2.0)
        self.assertAlmostEqual(result["ci95"][0], 2.0)
        self.assertAlmostEqual(result["ci95"][1], 2.0)
        self.assertEqual(result["n_pairs"], 15)

    def test_fixed_seed_is_reproducible(self):
        points = [[(1.0 + 0.1 * i + 0.01 * j, 1.0) for j in range(3)] for i in range(6)]
        self.assertEqual(two_stage(points, ratio_of_sums, 7, draws=300), two_stage(points, ratio_of_sums, 7, draws=300))


class ScheduleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads((HERE / "protocol.json").read_text())
        cls.schedule = make_schedule.build(cls.protocol)

    def test_primary_sides_alternate_and_pairs_share_seed(self):
        design = self.protocol["design"]
        for segment in self.schedule["segments"]:
            if segment["panel"] != "P":
                continue
            runs = [r for r in segment["runs"] if r["role"] == "primary"]
            labels = [r["side"] for r in runs[::2]]
            self.assertEqual(len(labels), 2 * design["primary_pairs_per_point"])
            self.assertTrue(all(a != b for a, b in zip(labels, labels[1:])), labels)
            for pair in range(1, design["primary_pairs_per_point"] + 1):
                rows = [r for r in runs if r["pair"] == pair]
                self.assertEqual(sorted(r["arm"] for r in rows), ["cM38I", "cPI", "kM38I", "kPI"])
                self.assertEqual(len({r["seed"] for r in rows if r["arm"].startswith("k")}), 1)
            for i in range(0, len(runs), 2):
                self.assertEqual(self.protocol["arms"][runs[i]["arm"]]["kind"], "ic_rank")
                self.assertEqual(self.protocol["arms"][runs[i + 1]["arm"]]["kind"], "ic_cold")

    def test_aa_and_planted_reuse_primary_seeds(self):
        for segment in self.schedule["segments"]:
            if segment["panel"] != "P":
                continue
            primary = {r["pair"]: r["seed"] for r in segment["runs"] if r["role"] == "primary" and r["arm"] == "kPI"}
            for r in segment["runs"]:
                if r["role"] == "aa" and r["arm"].startswith("k"):
                    self.assertEqual(r["seed"], primary[r["pair"]])
                if r["role"] == "planted":
                    self.assertEqual(r["seed"], primary[max(primary)])
            labels = [r["side"] for r in segment["runs"] if r["role"] == "aa"][::2]
            self.assertTrue(all(a != b for a, b in zip(labels, labels[1:])), labels)

    def test_starts_are_balanced_and_seeds_new(self):
        starts = [s["starts"]["primary"] for s in self.schedule["segments"] if s["panel"] == "P"]
        self.assertIn("A", starts)
        self.assertIn("B", starts)
        seeds = {r["seed"] for s in self.schedule["segments"] for r in s["runs"] if r["arm"].startswith("k")}
        self.assertEqual(seeds, set(range(1201, 1231)))


if __name__ == "__main__":
    unittest.main()
