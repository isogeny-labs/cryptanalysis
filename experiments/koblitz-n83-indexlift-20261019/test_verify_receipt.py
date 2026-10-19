import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from verify_receipt import decide, raw_record


class DecideTests(unittest.TestCase):
    def checks(self, q0=True):
        return {
            "all_executed_rows_valid": True,
            "q0_matches_archived_feistel_identity": q0,
            "every_scheduled_row_present": True,
            "all_points_complete": True,
            "all_rank_blocks_complete": True,
        }

    def stats(self):
        return {
            "aa_e2e_shared_cP_over_cPaa": {"estimate": 1.0},
            "aa_cold_cP_over_cPaa": {"estimate": 1.0},
            "sharing_rank_attempt_kPI_over_kP": {"estimate": 1.0},
            "planted_cold_cPIX_over_cPI": {"ci95": [1.01, 1.1]},
            "primary_e2e_shared_cP_over_cPI": {"ci95": [1.01, 1.1]},
        }

    def test_missing_q0_identity_is_invalid(self):
        decision, _ = decide(self.checks(q0=None), self.stats())

        self.assertEqual(decision, "invalid")

    def test_all_true_gates_can_pass_controls(self):
        decision, _ = decide(self.checks(), self.stats())

        self.assertEqual(decision, "improvement")

    def read_raw(self, raw_bytes, digest_bytes=None):
        scheduled = {"arm": "cP", "kind": "ic_cold", "point_id": "s000",
                     "point": ["1", "2"], "seed": 7}
        summary_digest = hashlib.sha256(digest_bytes or raw_bytes).hexdigest()
        stdout = "raw_b64=" + base64.b64encode(raw_bytes).decode() + "\n"
        stdout += "online_ms=1.000000 verified=1 raw_result_sha256=%s\n" % summary_digest
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory)
            (receipt / "stdout.txt").write_text(stdout)
            return raw_record(receipt, {"stdout_file": "stdout.txt"}, scheduled, "ic_cold")

    def test_raw_byte_tampering_fails_digest_check(self):
        raw = {"arm": "cP", "kind": "ic_cold", "panel": "s000", "point": ["1", "2"],
               "seed": 7, "fields": {"online_ms": 1.0}}
        original = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
        raw["fields"]["online_ms"] = 2.0
        tampered = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()

        _, issues = self.read_raw(tampered, digest_bytes=original)

        self.assertIn("raw producer record digest differs from wrapper summary", issues)

    def test_raw_schedule_identity_mismatch_fails(self):
        raw = {"arm": "cP", "kind": "ic_cold", "panel": "s001", "point": ["1", "2"],
               "seed": 7, "fields": {"online_ms": 1.0}}
        encoded = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()

        _, issues = self.read_raw(encoded)

        self.assertIn("raw producer record panel differs from the frozen schedule", issues)


if __name__ == "__main__":
    unittest.main()
