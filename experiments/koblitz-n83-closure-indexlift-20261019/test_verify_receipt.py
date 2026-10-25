"""Unit tests of the fail-closed parts of verify_receipt.py.

`koblitz-n83-indexlift-20261019`'s `test_verify_receipt.py` (main) with this
experiment's gates, controls and arms, plus the cases this experiment adds
(an unknown pre-timing record, a failed layout gate, a failed planted
exactness check, a probe-law miss).
"""

import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from verify_receipt import decide, raw_record


class DecideTests(unittest.TestCase):
    def checks(self, **override):
        checks = {
            "all_executed_rows_valid": True,
            "pre_timing_tables_and_closure_bases_verified": True,
            "one_scalar_per_point_ic_and_rho": True,
            "oracle_replay": True,
            "one_relation_per_point_and_base": True,
            "one_probe_count_per_point_and_base": True,
            "one_index_and_layout_digest_set_per_base_equal_frozen": True,
            "q0_matches_archived_and_frozen_identities": True,
            "rank_tables_equal_frozen_verified_tables": True,
            "rank_relations_probes_root_calls_and_counters_identical_per_block": True,
            "primary_probe_law_inside_frozen_band": True,
            "receipt_matches_schedule": True,
            "every_scheduled_row_present": True,
            "all_points_complete": True,
            "all_rank_blocks_complete": True,
        }
        checks.update(override)
        return checks

    def stats(self, **override):
        stats = {
            "aa_e2e_kM38I_cM38I_over_kM38Iaa_cM38Iaa": {"estimate": 1.0},
            "aa_cold_cM38I_over_cM38Iaa": {"estimate": 1.0},
            "planted_rank_attempt_kM38IX_over_kM38I": {"ci95": [1.5, 2.0]},
            "primary_e2e_kPI_cPI_over_kM38I_cM38I": {"ci95": [5.0, 7.0]},
        }
        stats.update(override)
        return stats

    def test_all_true_gates_can_pass_controls(self):
        self.assertEqual(decide(self.checks(), self.stats())[0], "improvement")

    def test_unknown_gate_is_invalid(self):
        for key in ("q0_matches_archived_and_frozen_identities", "pre_timing_tables_and_closure_bases_verified",
                    "one_index_and_layout_digest_set_per_base_equal_frozen", "primary_probe_law_inside_frozen_band"):
            with self.subTest(key=key):
                self.assertEqual(decide(self.checks(**{key: None}), self.stats())[0], "invalid")

    def test_failed_layout_gate_is_invalid(self):
        checks = self.checks(one_index_and_layout_digest_set_per_base_equal_frozen=False)
        self.assertEqual(decide(checks, self.stats())[0], "invalid")

    def test_failed_planted_exactness_is_invalid(self):
        checks = self.checks(pre_timing_tables_and_closure_bases_verified=False)
        decision, controls = decide(checks, self.stats())
        self.assertEqual(decision, "invalid")
        self.assertFalse(controls["planted_exactness_corruptions_rejected"])

    def test_aa_outside_band_is_invalid(self):
        stats = self.stats(aa_cold_cM38I_over_cM38Iaa={"estimate": 1.05})
        self.assertEqual(decide(self.checks(), stats)[0], "invalid")

    def test_planted_not_detected_is_invalid(self):
        stats = self.stats(planted_rank_attempt_kM38IX_over_kM38I={"ci95": [0.99, 1.2]})
        self.assertEqual(decide(self.checks(), stats)[0], "invalid")

    def test_interval_straddling_one_is_not_separated(self):
        stats = self.stats(primary_e2e_kPI_cPI_over_kM38I_cM38I={"ci95": [0.9, 1.1]})
        self.assertEqual(decide(self.checks(), stats)[0], "not_separated")

    def read_raw(self, raw_bytes, digest_bytes=None):
        scheduled = {"arm": "cPI", "kind": "ic_cold", "point_id": "s000",
                     "point": ["1", "2"], "seed": 7}
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
        for key, value in (("panel", "s001"), ("arm", "cM38I"), ("seed", 8), ("point", ["1", "3"])):
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


if __name__ == "__main__":
    unittest.main()
