#!/usr/bin/env python3
"""CT184 exact-revision CT183 producer -> CT182 reader source-only integration.

All child records are SYNTHETIC, returned through a mocked run_sample.
No native executable is launched. Ratios are programmed controls, not data.
"""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

SOURCE_DIR = Path(__file__).resolve().parent
READER_ENV = os.environ.get("CT182_SOURCE_ROOT")
if not READER_ENV:
    raise RuntimeError("CT182_SOURCE_ROOT must identify the immutable pinned CT182 checkout")
READER_DIR = Path(READER_ENV).resolve(strict=True)
if not (READER_DIR / "ct182_v2_panel_adjudicator.py").is_file():
    raise RuntimeError("CT182_SOURCE_ROOT lacks the pinned offline reader")
sys.path.insert(0, str(SOURCE_DIR))
sys.path.insert(1, str(READER_DIR))

import ct176_cold_process_collector as bounded
import ct183_v2_cold_process_collector as producer
import ct179_panel_adjudicator as legacy
import ct181_order_design as design
import ct182_v2_panel_adjudicator as reader
import test_ct179_panel_adjudicator as legacy_fixture

FIXTURE = SOURCE_DIR.parent / "evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json"
ROSTER_HASH = "1dddb4839321ad6560fd429330778aa083ff3a13625393250e964c05f9fc5ee4"
EXPECTED_READER_SCHEMA = "ct182-counterbalanced-cold-public-process-panel/v2"


class CT184CrossStackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.fixture_sha = legacy.frozen_fixture(FIXTURE)
        cls.helper = legacy_fixture.CT179SourceTests("test_strict_duplicate_and_nonfinite_json")
        cls.helper.rows = cls.rows
        cls.binary = Path(sys.executable).resolve(strict=True)
        cls.binary_sha = hashlib.sha256(cls.binary.read_bytes()).hexdigest()

    def test_independent_exact_roster_and_manifest(self):
        self.assertEqual(producer.SCHEMA, reader.SCHEMA)
        self.assertEqual(producer.SCHEMA, EXPECTED_READER_SCHEMA)
        self.assertEqual(producer.ORDER_SCHEDULE, reader.ORDER_SCHEDULE)
        self.assertEqual(producer.roster_sha256(), ROSTER_HASH)
        self.assertEqual(reader.roster_sha256(), ROSTER_HASH)
        self.assertEqual(list(producer.roster()), list(reader.roster()))
        self.assertEqual(len(list(producer.roster())), 2304)
        self.assertEqual(bounded.FIXTURE_GIT_BLOB, legacy.FIXTURE_BLOB)
        self.assertEqual(producer.manifest(self.fixture_sha, {"hostname": "synthetic"})["order_roster_sha256"], ROSTER_HASH)
        self.assertNotEqual(producer.SCHEMA, bounded.SCHEMA)

    def simulate_producer(self, target, a=1, b=1):
        """Run real producer writer with mocked child; never spawn native code."""
        self.assertTrue(type(a) is int and type(b) is int and a > 0 and b > 0)
        stable_host = {"hostname": "CT184-SYNTHETIC-ONLY", "cpu_affinity": [0]}
        calls = []

        def fake_child(binary, index, arm, row, timeout):
            self.assertEqual(Path(binary), self.binary)
            self.assertEqual(row, self.rows[index])
            self.assertGreater(timeout, 0)
            # Independently supplied position factors; no need to trust the
            # reader's sample generator or its assigned arm sequence.
            block, packet, position, expected_arm = next_slot[len(calls)]
            self.assertEqual((index, arm), (packet, expected_arm))
            self.assertIn(position, range(6))
            factor = (3, 2, 2, 3, 3, 3)[position]
            wall = 1_000_000 * factor * (a if arm == producer.A else b)
            sample = self.helper.sample(index, arm, position, wall=wall)
            # CT179 helper uses a never-executed dummy path; real producer
            # must bind its own binary identity and same argv.
            sample["argv"] = [str(self.binary), "--cold-route", str(index), arm]
            calls.append((block, index, position, arm))
            return sample

        next_slot = list(producer.roster())
        args = [
            "--fixture", str(FIXTURE), "--executable", str(self.binary),
            "--executable-sha256", self.binary_sha,
            "--output", str(target), "--execute", "--admission-approved",
            "--timeout-seconds", "120", "--panel-wall-seconds", "120",
        ]
        with mock.patch.object(bounded, "host_metadata", return_value=stable_host), \\
             mock.patch.object(bounded, "run_sample", side_effect=fake_child), \\
             mock.patch.object(bounded, "bounded_subprocess", side_effect=AssertionError("native subprocess FORBIDDEN")):
            with contextlib.redirect_stdout(io.StringIO()):
                rc = producer.run(args)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 2304)
        self.assertEqual(calls, next_slot)
        return reader.adjudicate_v2(target, FIXTURE)

    def test_actual_producer_bytes_are_accepted_by_pinned_reader_and_mutations_refused(self):
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            path = directory / "fake-null.jsonl"
            report = self.simulate_producer(path, a=1, b=1)
            self.assertEqual(report["schema"], reader.REPORT_SCHEMA)
            self.assertEqual(report["observed_complete_processes"], 2304)
            self.assertEqual(report["roster_sha256"], ROSTER_HASH)
            self.assertEqual(len(report["strata"]), 16)
            self.assertTrue(report["complete_memory_evidence"])
            self.assertFalse(report["signed_independent_pcc"])
            self.assertFalse(report["original_full_695_701_custody_replayed"])
            self.assertFalse(report["complete_single_target_ecdlp_advantage_established"])
            for stratum in report["strata"]:
                self.assertAlmostEqual(stratum["direct_over_retained_transfer_wall_ratio"], 1.0, places=9)
                self.assertAlmostEqual(stratum["aa_abs_log_ratio_p95"], 0.0, places=12)
                self.assertEqual(stratum["balanced_abba_blocks"], stratum["balanced_baab_blocks"])

            rows = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(rows), 2306)  # manifest + 2304 child rows + terminal
            mutants = {}
            first = json.loads(rows[1])
            first["arm"] = producer.A if first["arm"] == producer.B else producer.B
            mutants["wrong_arm"] = (1, first)
            first = json.loads(rows[1])
            first["stdout_sha256"] = "0" * 64
            mutants["wrong_stdout_digest"] = (1, first)
            first = json.loads(rows[1])
            first["external_wall_ns_decimal"] = "1"  # less than child internal wall
            mutants["impossible_clock"] = (1, first)
            m = json.loads(rows[0])
            m["schema"] = bounded.SCHEMA
            mutants["legacy_v1_schema"] = (0, m)
            for name, (index, obj) in mutants.items():
                with self.subTest(mutation=name):
                    altered = list(rows)
                    altered[index] = json.dumps(obj, sort_keys=True, separators=(",", ":"))
                    file = directory / (name + ".jsonl")
                    file.write_text("\n".join(altered) + "\n", encoding="utf-8")
                    with self.assertRaises(ValueError):
                        reader.adjudicate_v2(file, FIXTURE)
            cut = directory / "missing_terminal.jsonl"
            cut.write_text("\n".join(rows[:-1]) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                reader.adjudicate_v2(cut, FIXTURE)

    def test_programmed_positive_ratio_is_not_real_speedup(self):
        with tempfile.TemporaryDirectory() as td:
            report = self.simulate_producer(Path(td) / "fake-positive.jsonl", a=5, b=4)
        for stratum in report["strata"]:
            self.assertAlmostEqual(stratum["direct_over_retained_transfer_wall_ratio"], 1.25, places=9)
        self.assertFalse(report["complete_single_target_ecdlp_advantage_established"])


if __name__ == "__main__":
    unittest.main()
