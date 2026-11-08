"""Unit tests of the fail-closed parts of verify_receipt.py and of the frozen schedule's pairing.

The k4c400 experiment's tests with this experiment's arms: BOTH sides on the D4 base, side A
= kD4FO + cD4FO on the field-ops binary `ic_online_fieldops_r770`, side B = kD4R1 + cD4R1 on
the field-ops-2 binary `ic_online_fieldops2_r770`, the planted pairs cD4R1X against cD4R1
(cold, index build), the A/A end-to-end rule as a point estimate inside [0.97, 1.03], the
probe-law attempts gate, and D4's frozen identity. They cover:

* a missing required gate;
* the command-line and runner identity checks (each arm on its own binary);
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
from verify_receipt import (PLANTED_KEY, PROTOCOL, REQUIRED_CHECKS, command_issues, decide, pipeline_failures,
                            planted_ratio, raw_record, ratio_of_sums, runner_checks, two_stage)

HERE = Path(__file__).resolve().parent


class DecideTests(unittest.TestCase):
    def checks(self, **override):
        checks = {key: True for key in REQUIRED_CHECKS}
        checks.update(override)
        return checks

    def stats(self, **override):
        stats = {
            "aa_e2e_B_over_Baa": {"estimate": 1.0, "ci95": [0.9, 1.1]},
            "aa_cold_B_over_Baa": {"estimate": 1.0},
            PLANTED_KEY: {"ci95": [1.5, 2.0]},
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

    def test_aa_cold_outside_band_is_invalid(self):
        self.assertEqual(decide(self.checks(), self.stats(aa_cold_B_over_Baa={"estimate": 1.05}))[0], "invalid")

    def test_aa_e2e_point_estimate_must_be_inside_the_band(self):
        for estimate in (0.96, 1.04):
            with self.subTest(estimate=estimate):
                stats = self.stats(aa_e2e_B_over_Baa={"estimate": estimate, "ci95": [0.9, 1.1]})
                self.assertEqual(decide(self.checks(), stats)[0], "invalid")

    def test_aa_e2e_interval_not_containing_one_is_still_valid_inside_the_band(self):
        stats = self.stats(aa_e2e_B_over_Baa={"estimate": 1.02, "ci95": [1.01, 1.03]})
        self.assertEqual(decide(self.checks(), stats)[0], "improvement")

    def test_law_attempts_gate_is_required(self):
        self.assertIn("probe_law_attempts_at_least_64", REQUIRED_CHECKS)
        self.assertEqual(decide(self.checks(probe_law_attempts_at_least_64=False), self.stats())[0], "invalid")

    def test_planted_not_detected_is_invalid(self):
        stats = self.stats(**{PLANTED_KEY: {"ci95": [0.99, 1.2]}})
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

    def binary_rows(self, arm, name, digest):
        return [{"serial": 1, "arm": arm, "status": "valid",
                 "row": {"command": ["python3", "arm.py", "--binary", "/bin/dir/" + name], "binary_sha256": digest,
                         "placement": {"Cpus_allowed_list": "0", "execution_cpu": 0}}}]

    def binary_check(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory)
            (receipt / "runner_start.json").write_text(json.dumps({
                "smoke_subset": {}, "execution_cpu": 0,
                "binaries_sha256": {"ic_online_rankfinder_r770": "a" * 64, "ic_online_fieldops_r770": "b" * 64,
                                    "ic_online_fieldops2_r770": "e" * 64, "rho_tuned_r770": "c" * 64}}))
            checks, _ = runner_checks(receipt, rows, partial=False)
        return checks["every_row_ran_its_arms_binary"]

    def test_row_on_its_arms_binary_passes(self):
        for arm in ("cD4FO", "kD4FO"):
            self.assertIs(self.binary_check(self.binary_rows(arm, "ic_online_fieldops_r770", "b" * 64)), True, arm)
        for arm in ("cD4R1", "kD4R1", "cD4R1aa", "kD4R1aa", "cD4R1X"):
            self.assertIs(self.binary_check(self.binary_rows(arm, "ic_online_fieldops2_r770", "e" * 64)), True, arm)

    def test_row_on_another_binary_fails(self):
        # each side's arm on the OTHER side's listed binary, on another listed binary, or on a digest not listed
        self.assertIs(self.binary_check(self.binary_rows("cD4R1", "ic_online_fieldops_r770", "b" * 64)), False)
        self.assertIs(self.binary_check(self.binary_rows("kD4FO", "ic_online_fieldops2_r770", "e" * 64)), False)
        self.assertIs(self.binary_check(self.binary_rows("cD4FO", "ic_online_rankfinder_r770", "a" * 64)), False)
        self.assertIs(self.binary_check(self.binary_rows("cD4R1", "ic_online_fieldops2_r770", "d" * 64)), False)

    def test_rank_probe_pipeline_gate(self):
        def row(arm, pipeline, present=True):
            return {"serial": 1, "arm": arm, "rank_probe_pipeline": pipeline, "summary_present": present}
        self.assertEqual(pipeline_failures([row(arm, "linear_canon_lanes8") for arm in
                                            ("kD4FO", "cD4FO", "kD4R1", "cD4R1", "cD4R1X")], PROTOCOL), [])
        for bad in (row("kD4R1", None), row("kD4FO", None), row("cD4FO", "other"),
                    row("kD4FO", "linear_canon_lanes8", present=False)):
            with self.subTest(bad=bad):
                self.assertEqual(pipeline_failures([bad], PROTOCOL), [1])

    def test_field_ops_pipeline_gate(self):
        pipeline_a = PROTOCOL["arms"]["cD4FO"]["field_ops_pipeline"]
        pipeline_b = PROTOCOL["arms"]["cD4R1"]["field_ops_pipeline"]
        self.assertEqual(pipeline_b, pipeline_a + "+n83_const_reduce_shift")

        def row(arm, value, present=True):
            return {"serial": 1, "arm": arm, "field_ops_pipeline": value, "summary_present": present}
        good = [row(arm, pipeline_a) for arm in ("kD4FO", "cD4FO")] + \
            [row(arm, pipeline_b) for arm in ("kD4R1", "cD4R1", "kD4R1aa", "cD4R1aa", "cD4R1X")]
        self.assertEqual(pipeline_failures(good, PROTOCOL, "field_ops_pipeline"), [])
        for bad in (row("kD4R1", None), row("cD4R1X", pipeline_a), row("kD4FO", pipeline_b), row("cD4FO", None),
                    row("cD4R1", "other"), row("kD4FO", pipeline_a, present=False)):
            with self.subTest(bad=bad):
                self.assertEqual(pipeline_failures([bad], PROTOCOL, "field_ops_pipeline"), [1])

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


class PlantedTests(unittest.TestCase):
    def runs(self, ratios):
        out = []
        for i, (x, b) in enumerate(ratios):
            unit = "s%03d" % i
            out.append({"status": "valid", "role": "planted", "unit": unit, "arm": "cD4R1X", "f": {"index_ms": x}})
            out.append({"status": "valid", "role": "planted", "unit": unit, "arm": "cD4R1", "f": {"index_ms": b}})
        return out

    def test_planted_pairs_stay_together(self):
        result = planted_ratio(self.runs([(2.0 * b, b) for b in (1.0, 10.0, 100.0, 1000.0)]), 3)
        self.assertAlmostEqual(result["estimate"], 2.0)
        self.assertAlmostEqual(result["ci95"][0], 2.0)
        self.assertAlmostEqual(result["ci95"][1], 2.0)
        self.assertEqual(result["pairs"], 4)

    def test_no_planted_effect_is_not_detected(self):
        result = planted_ratio(self.runs([(b * f, b) for b, f in zip((5.0, 6.0, 7.0, 8.0, 9.0, 10.0),
                                                                      (0.9, 1.1, 0.95, 1.05, 1.0, 0.98))]), 3)
        self.assertLess(result["ci95"][0], 1.0)

    def test_the_planted_arm_is_cold_with_the_lift_plant_index(self):
        self.assertEqual(PROTOCOL["arms"]["cD4R1X"]["kind"], "ic_cold")
        self.assertEqual(PROTOCOL["arms"]["cD4R1X"]["index_canon"], "lift_plant")
        self.assertEqual(PROTOCOL["arms"]["cD4R1"]["index_canon"], "lift")
        self.assertEqual(PROTOCOL["arms"]["cD4R1X"]["binary"], PROTOCOL["arms"]["cD4R1"]["binary"])


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
                self.assertEqual(sorted(r["arm"] for r in rows), ["cD4FO", "cD4R1", "kD4FO", "kD4R1"])
                self.assertEqual(len({r["seed"] for r in rows if r["arm"].startswith("k")}), 1)
            for i in range(0, len(runs), 2):
                self.assertEqual(self.protocol["arms"][runs[i]["arm"]]["kind"], "ic_rank")
                self.assertEqual(self.protocol["arms"][runs[i + 1]["arm"]]["kind"], "ic_cold")

    def test_aa_and_planted_reuse_primary_seeds(self):
        for segment in self.schedule["segments"]:
            if segment["panel"] != "P":
                continue
            primary = {r["pair"]: r["seed"] for r in segment["runs"] if r["role"] == "primary" and r["arm"] == "kD4FO"}
            for r in segment["runs"]:
                if r["role"] == "aa" and r["arm"].startswith("k"):
                    self.assertEqual(r["seed"], primary[r["pair"]])
                if r["role"] == "planted":
                    self.assertEqual(self.protocol["arms"][r["arm"]]["kind"], "ic_cold")
                    self.assertEqual(r["seed"], 7)
            planted = [r["arm"] for r in segment["runs"] if r["role"] == "planted"]
            self.assertEqual(sorted(planted), ["cD4R1", "cD4R1X"])
            labels = [r["side"] for r in segment["runs"] if r["role"] == "aa"][::2]
            self.assertTrue(all(a != b for a, b in zip(labels, labels[1:])), labels)

    def test_starts_are_balanced_and_seeds_new(self):
        starts = [s["starts"]["primary"] for s in self.schedule["segments"] if s["panel"] == "P"]
        self.assertIn("A", starts)
        self.assertIn("B", starts)
        seeds = {r["seed"] for s in self.schedule["segments"] for r in s["runs"]
                 if r["arm"].startswith("k")}
        self.assertEqual(seeds, set(range(2601, 2637)))
        self.assertFalse(seeds & (set(range(2201, 2237)) | set(range(2301, 2361)) | set(range(2501, 2561))))

    def test_sides_differ_in_binary_and_pipeline_only(self):
        arms = self.protocol["arms"]
        for new, old in (("cD4R1", "cD4FO"), ("kD4R1", "kD4FO"), ("cD4R1aa", "cD4FO"), ("kD4R1aa", "kD4FO")):
            a, b = dict(arms[new]), dict(arms[old])
            for key in ("role", "parent_source", "derived_from", "binary", "field_ops_pipeline"):
                a.pop(key, None)
                b.pop(key, None)
            self.assertEqual(a, b, new)
            self.assertEqual(arms[new]["binary"], "ic_online_fieldops2_r770")
            self.assertEqual(arms[old]["binary"], "ic_online_fieldops_r770")
            self.assertEqual(arms[new]["base"], "D4")
            self.assertEqual(arms[old]["base"], "D4")
        ic = {n: a for n, a in arms.items() if a["kind"] != "rho_tuned"}
        self.assertEqual({a["base"] for a in ic.values()}, {"D4"})
        self.assertEqual(len({a["rank_probe_pipeline"] for a in ic.values()}), 1)
        self.assertEqual(len({a["index_build_pipeline"] for a in ic.values()}), 1)

    def test_planted_arm_is_the_cold_arm_with_lift_plant(self):
        a, b = dict(self.protocol["arms"]["cD4R1X"]), dict(self.protocol["arms"]["cD4R1"])
        for key in ("role", "derived_from", "index_canon"):
            a.pop(key, None)
            b.pop(key, None)
        self.assertEqual(a, b)

    def test_arms_are_the_fieldops2_arms_on_d4(self):
        fo2 = json.loads((HERE.parent / "koblitz-n83-fieldops2-20261107" / "protocol.json").read_text())
        for new, old in (("kD4FO", "kM38FO"), ("cD4FO", "cM38FO"), ("kD4R1", "kM38R1"), ("cD4R1", "cM38R1"),
                         ("cD4R1X", "cM38R1X"), ("rT", "rT")):
            got, want = dict(self.protocol["arms"][new]), dict(fo2["arms"][old])
            for key in ("parent_source", "derived_from", "role", "base"):
                got.pop(key, None)
                want.pop(key, None)
            self.assertEqual(got, want, new)

    def test_the_one_base_is_the_k4c400_frozen_d4(self):
        k4 = json.loads((HERE.parent / "koblitz-n83-k4c400-20261107" / "protocol.json").read_text())
        d4, want = dict(self.protocol["online"]["bases"]["D4"]), dict(k4["online"]["bases"]["D4"])
        d4.pop("parent_source", None)
        want.pop("parent_source", None)
        self.assertEqual(d4, want)
        self.assertEqual(set(self.protocol["online"]["bases"]), {"D4"})
        self.assertEqual((d4["orbit_columns"], d4["index_orbits"], d4["orbits_per_column"]), (4, 400, 100))
        self.assertEqual(d4["regular_states"], 83 * 400 ** 2)
        self.assertEqual(self.protocol["online"]["subgroup_order"], "8569786107849059")

    def test_primary_choice_is_frozen_end_to_end(self):
        self.assertTrue(self.protocol["primary_choice"]["frozen_before_data"])
        self.assertIn("end to end", self.protocol["primary_choice"]["primary"])

    def test_owner_ruling_is_recorded_verbatim_with_its_date(self):
        ruling = self.protocol["owner_ruling"]
        self.assertEqual(ruling["date"], "2026-11-07")
        self.assertIn("K' >= 4 unknown-log columns counts as an index-calculus row", ruling["verbatim_in_chat"])
        self.assertIn("K' = 0 stays a known-log reference row", ruling["verbatim_in_chat"])


if __name__ == "__main__":
    unittest.main()
