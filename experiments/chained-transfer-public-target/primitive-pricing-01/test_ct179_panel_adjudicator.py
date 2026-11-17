#!/usr/bin/env python3
"""CT179 synthetic controls only. Never runs Rust or performs a DLP."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct179_panel_adjudicator as judge

FIXTURE = (Path(__file__).resolve().parent.parent /
           "evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json")
EXE = "/synthetic/never-executed/ct172-replay"


class CT179SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.fixture_hash = judge.frozen_fixture(FIXTURE)

    def child(self, i, arm):
        row = self.rows[i]
        return {
            "schema": judge.CHILD_SCHEMA,
            "packet_index": i, "from": row["from"], "to": row["to"],
            "sector": row["sector"],
            "scalar_label_outside_runtime": row["scalar_OUTSIDE_runtime"],
            "fixture_rows_checked": 48, "preflight_native_routes": 0,
            "preflight_native_inverses": 0,
            "arm": arm, "rustc_child_process_spawned": False,
            "external_os_loader_wall_included": False,
            "public_source_packet": row["input"],
            "verified_canonical_target": row["whole_outputs_equal"],
            "native_calls": row[arm],
            "native_sample": {"elapsed_ns_decimal": "120",
                              "complete_counter_match": True},
            "same_process_setup_ns_decimal": "110",
            "in_process_total_ns_decimal": "330",
            "peak_rss_kib_linux": 1024,
        }

    def sample(self, i, arm, pos, wall=None):
        if wall is None:
            wall = 2_000_000 if pos in (1, 2) else 3_000_000
        child = (json.dumps(self.child(i, arm), sort_keys=True) + "\n").encode()
        empty = b""
        return {
            "type": "sample", "argv": [EXE, "--cold-route", str(i), arm],
            "verified": True, "capture_complete": True,
            "exit_code": 0, "error": None,
            "external_wall_ns_decimal": str(wall),
            "stdout": child.decode(), "stderr": "",
            "stdout_base64": base64.b64encode(child).decode(),
            "stderr_base64": base64.b64encode(empty).decode(),
            "stdout_sha256": hashlib.sha256(child).hexdigest(),
            "stderr_sha256": hashlib.sha256(empty).hexdigest(),
            "peak_rss_kib_linux": 1024,
        }

    def panel(self, path, mutate=None):
        manifest = {
            "type": "manifest", "schema": judge.SCHEMA,
            "fixture_git_blob": judge.FIXTURE_BLOB,
            "fixture_sha256": self.fixture_hash,
            "blocks": judge.BLOCKS, "seed": judge.SEED,
            "processes": judge.N, "packets": 48,
            "arms_in_each_block": list(judge.ARMS),
            "executable_sha256": "a" * 64,
            "executable_path": EXE,
            "host": {"hostname": "synthetic-host"},
            "panel_wall_seconds": 3600, "timeout_seconds": 120,
        }
        with path.open("w", encoding="utf-8") as f:
            def line(v):
                f.write(json.dumps(v, separators=(",", ":")) + "\n")
            line(manifest)
            for block, index, position, arm in judge.roster():
                s = self.sample(index, arm, position)
                s.update({"block": block, "packet_index": index,
                          "position": position, "arm": arm})
                if mutate:
                    mutate(s, block, index, position)
                line(s)
            line({"type": "terminal", "attempted": judge.N,
                  "planned": judge.N, "verified_complete": True,
                  "refusal": None})

    def test_strict_duplicate_and_nonfinite_json(self):
        for bad in ('{"x":1,"x":2}', '{"time":NaN}', '{"time":Infinity}'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                judge.decode_json(bad)

    def test_bad_counter_rejected(self):
        record = self.sample(0, "direct_composite", 0)
        fake = self.child(0, "direct_composite")
        fake["native_calls"][next(iter(fake["native_calls"]))] = False
        bad = (json.dumps(fake) + "\n").encode()
        record["stdout"] = bad.decode()
        record["stdout_base64"] = base64.b64encode(bad).decode()
        record["stdout_sha256"] = hashlib.sha256(bad).hexdigest()
        with self.assertRaisesRegex(ValueError, "native counter"):
            judge.valid_sample(record, self.rows[0], 0, "direct_composite")

    def test_modified_stdout_digest_rejected(self):
        s = self.sample(0, "direct_composite", 0)
        s["stdout_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            judge.valid_sample(s, self.rows[0], 0, "direct_composite")

    def test_wrong_target_rejected(self):
        s = self.sample(0, "direct_composite", 0)
        bad = self.child(0, "direct_composite")
        bad["verified_canonical_target"] = [999] * 19
        encoded = (json.dumps(bad) + "\n").encode()
        s["stdout_base64"] = base64.b64encode(encoded).decode()
        s["stdout_sha256"] = hashlib.sha256(encoded).hexdigest()
        s["stdout"] = encoded.decode()
        with self.assertRaisesRegex(ValueError, "changed"):
            judge.valid_sample(s, self.rows[0], 0, "direct_composite")

    def test_historical_partial_panel_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "panel.jsonl"
            path.write_text('{"type":"manifest"}\n')
            with self.assertRaisesRegex(ValueError, "manifest"):
                judge.adjudicate(path, FIXTURE)

    def test_full_synthetic_panel_not_a_speedup(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "panel.jsonl"
            self.panel(path)
            v = judge.adjudicate(path, FIXTURE)
            self.assertEqual(v["observed_complete_processes"], 2304)
            self.assertEqual(len(v["strata"]), 16)
            self.assertFalse(v["complete_single_target_ecdlp_advantage_established"])
            self.assertFalse(v["signed_independent_pcc"])
            self.assertTrue(v["complete_memory_evidence"])
            for g in v["strata"]:
                self.assertAlmostEqual(g["direct_over_retained_transfer_wall_ratio"],
                                       1.5, places=10)
                self.assertAlmostEqual(g["aa_abs_log_ratio_p95"], 0)
                self.assertEqual(g["cluster_bootstrap_ratio_ci95"] is None,
                                 g["class"] == "identity")

    def test_spoofed_argv_in_complete_panel_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "panel.jsonl"
            def change(s, block, i, pos):
                if block == 0 and i == 0 and pos == 0:
                    s["argv"][0] = "/another/executable"
            self.panel(path, change)
            with self.assertRaisesRegex(ValueError, "spawned command mismatch"):
                judge.adjudicate(path, FIXTURE)

    def test_failed_sample_in_full_panel_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "panel.jsonl"
            def change(s, block, i, pos):
                if block == 0 and i == 0 and pos == 0:
                    s["verified"] = False
                    s["error"] = "timeout"
            self.panel(path, change)
            with self.assertRaisesRegex(ValueError, "censored sample"):
                judge.adjudicate(path, FIXTURE)

    def test_aa_drift_reported(self):
        matrix = {}
        for block in range(judge.BLOCKS):
            for i in range(48):
                matrix[(block, i)] = [300, 200, 200, 300, 300, 150]
        summary = judge.paired_statistics(matrix, self.rows)
        self.assertEqual(len(summary), 16)
        for cohort in summary:
            self.assertAlmostEqual(cohort["aa_abs_log_ratio_p95"],
                                   __import__("math").log(2))


if __name__ == "__main__":
    unittest.main()
