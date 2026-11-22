#!/usr/bin/env python3
"""CT182 deterministic synthetic counterbalanced-panel tests; no native runs."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct179_panel_adjudicator as legacy
import ct181_order_design as design
import ct182_v2_panel_adjudicator as v2
import test_ct179_panel_adjudicator as fixtures

FIXTURE = fixtures.FIXTURE
EXE = fixtures.EXE


class CT182SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.fixture_hash = legacy.frozen_fixture(FIXTURE)
        # Reuse CT179 synthetic child's exact 19-word/counter fixture machinery.
        cls.helper = fixtures.CT179SourceTests("test_full_synthetic_panel_not_a_speedup")
        cls.helper.rows = cls.rows

    def manifest(self):
        return {
            "type": "manifest", "schema": v2.SCHEMA,
            "fixture_git_blob": legacy.FIXTURE_BLOB,
            "fixture_sha256": self.fixture_hash,
            "blocks": design.BLOCKS, "seed": legacy.SEED,
            "packets": 48, "processes": v2.N,
            "order_schedule": v2.ORDER_SCHEDULE,
            "order_roster_sha256": v2.roster_sha256(),
            "executable_sha256": "a" * 64,
            "executable_path": EXE,
            "host": {"hostname": "synthetic-only"},
            "panel_wall_seconds": 3600, "timeout_seconds": 120,
        }

    def write_panel(self, path, a=1, b=1, mutate=None):
        with path.open("x", encoding="utf-8") as fh:
            def line(value):
                fh.write(json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n")
            m = self.manifest()
            if mutate:
                mutate("manifest", m)
            line(m)
            for block, index, pos, arm in v2.roster():
                # Stationary slot-only multiplicative factors independent of arm.
                duration = 1_000_000 * design.SLOT_FACTORS[pos] * (
                    a if arm == v2.ARM_NAME["A"] else b)
                s = self.helper.sample(index, arm, pos, wall=duration)
                s.update({"block": block, "packet_index": index,
                          "position": pos, "arm": arm})
                if mutate:
                    mutate("sample", s)
                line(s)
            line({"type": "terminal", "attempted": v2.N,
                  "planned": v2.N, "verified_complete": True, "refusal": None})

    def test_roster_balances_and_has_deterministic_digest(self):
        r = list(v2.roster())
        self.assertEqual(len(r), 2304)
        self.assertEqual(len(set(r)), 2304)
        self.assertEqual(len(v2.roster_sha256()), 64)
        counts = {(i, arm): 0 for i in range(48) for arm in ("ABBA", "BAAB")}
        for block, i, pos, arm in r:
            self.assertEqual(arm, v2.ARM_NAME[design.order(block, i)[pos]])
            if pos == 0:
                counts[(i, "".join(design.order(block, i)[:4]))] += 1
        self.assertTrue(all(count == 4 for count in counts.values()))

    def test_null_and_true_effect_remain_separate_from_complete_solve(self):
        with tempfile.TemporaryDirectory() as d:
            for a, b, expected in ((1, 1, 1.0), (5, 4, 1.25)):
                with self.subTest(a=a, b=b):
                    path = Path(d) / f"synthetic-{a}-{b}.jsonl"
                    self.write_panel(path, a=a, b=b)
                    result = v2.adjudicate_v2(path, FIXTURE)
                    self.assertEqual(result["schema"], v2.REPORT_SCHEMA)
                    self.assertEqual(result["observed_complete_processes"], 2304)
                    self.assertEqual(len(result["strata"]), 16)
                    self.assertTrue(result["complete_memory_evidence"])
                    self.assertFalse(result["signed_independent_pcc"])
                    self.assertFalse(result["original_full_695_701_custody_replayed"])
                    self.assertFalse(result["complete_single_target_ecdlp_advantage_established"])
                    for cohort in result["strata"]:
                        self.assertAlmostEqual(
                            cohort["direct_over_retained_transfer_wall_ratio"],
                            expected, places=10)
                        self.assertEqual(cohort["balanced_abba_blocks"],
                                         cohort["balanced_baab_blocks"])
                        self.assertAlmostEqual(cohort["aa_abs_log_ratio_p95"], 0)
                        if cohort["cluster_bootstrap_ratio_ci95"]:
                            for endpoint in cohort["cluster_bootstrap_ratio_ci95"]:
                                self.assertAlmostEqual(endpoint, expected)

    def test_v1_manifest_never_accepted_as_v2(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "v1.jsonl"
            m = self.manifest()
            m["schema"] = legacy.SCHEMA
            p.write_text(json.dumps(m) + "\n")
            with self.assertRaisesRegex(ValueError, "v2 manifest schema"):
                v2.adjudicate_v2(p, FIXTURE)

    def test_mutated_roster_refused_with_correct_child_and_digest(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "order-mutated.jsonl"
            seen = [False]
            def mutate(typ, item):
                if typ == "sample" and not seen[0]:
                    item["position"] = 1
                    seen[0] = True
            self.write_panel(path, mutate=mutate)
            with self.assertRaisesRegex(ValueError, "roster mismatch"):
                v2.adjudicate_v2(path, FIXTURE)

    def test_manifest_roster_digest_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "wrong-roster.jsonl"
            def mutate(typ, item):
                if typ == "manifest":
                    item["order_roster_sha256"] = "0" * 64
            self.write_panel(path, mutate=mutate)
            with self.assertRaisesRegex(ValueError, "order_roster_sha256"):
                v2.adjudicate_v2(path, FIXTURE)

    def test_partial_panel_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "partial.jsonl"
            path.write_text(json.dumps(self.manifest()) + "\n")
            with self.assertRaisesRegex(ValueError, "missing or oversized"):
                v2.adjudicate_v2(path, FIXTURE)

    def test_censored_correctly_digest_bound_child_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "censored.jsonl"
            seen = [False]
            def mutate(typ, item):
                if typ == "sample" and not seen[0]:
                    item["verified"] = False
                    item["error"] = "timeout"
                    seen[0] = True
            self.write_panel(path, mutate=mutate)
            with self.assertRaisesRegex(ValueError, "failed or censored sample"):
                v2.adjudicate_v2(path, FIXTURE)

    def test_bad_or_boolean_sample_duration_refused(self):
        rows = self.rows
        matrix = {(b, i): [3, 2, 2, 3, 3, 3]
                  for b in range(8) for i in range(48)}
        matrix[(0, 0)][0] = True
        with self.assertRaisesRegex(ValueError, "positive integer"):
            v2.paired_statistics_v2(matrix, rows)


if __name__ == "__main__":
    unittest.main()
