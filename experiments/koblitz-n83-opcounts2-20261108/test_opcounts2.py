#!/usr/bin/env python3
"""Tests of the counted-source derivation and the counted-band script.

The derivation tests need the field-ops-2 snapshot restored
(`../koblitz-n83-fieldops2-20261107/snapshots/r770`); they are skipped without it.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import counted_band  # noqa: E402
import make_counted2_source as derivation  # noqa: E402

SNAPSHOT = derivation.FIELDOPS2 / "snapshots" / "r770" / "examples" / "koblitz_orbit_dlp_fast_online_fieldops2.rs"


@unittest.skipUnless(SNAPSHOT.exists(), "field-ops-2 snapshot not restored")
class Derivation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = derivation.derive()

    def test_inverts_to_the_frozen_parent(self):
        self.assertTrue(derivation.check_inverse(self.text))

    def test_output_is_the_committed_derivation(self):
        self.assertEqual(derivation.OUTPUT.read_text(), self.text)

    def test_every_edit_only_adds_counting_or_counted_calls(self):
        parent = derivation.parent_text()
        for name, old, new, _ in derivation.edits():
            if name in ("head", "import", "tests", "group_law", "summary", "record"):
                continue
            stripped = "\n".join(line for line in new.splitlines() if "oc::" not in line and "opcount::" not in line
                                 and "let _inversion" not in line and "ops_" not in line)
            stripped = (stripped.replace("counted_add(fast, ", "fast.add(")
                        .replace("counted_scalar_mul(fast, ", "fast.scalar_mul(")
                        .replace("s3_x_roots_128_counted(", "s3_x_roots_128("))
            self.assertEqual(stripped, "\n".join(old.splitlines()), name)
            self.assertIn(old, parent)

    def test_counting_writes_nothing_unless_enabled(self):
        self.assertIn("if oc::on() {\n                record[\"op_counts\"]", self.text)
        self.assertIn("if oc::on() {\n            summary[\"op_counts\"]", self.text)
        self.assertEqual(self.text.count('["op_counts"] ='), 2)


def counts(phase_value, target_value):
    phases = {p: {"ec_add": phase_value, "root_index_probes": phase_value}
              for p in ("setup", "rank_stage", "linear_algebra", "between_linear_algebra_and_targets",
                        "targets", "after_targets_index_digest")}
    return {"enabled": True, "phases": phases}, {"ec_add": target_value, "root_index_probes": target_value}


class CountedBand(unittest.TestCase):
    def test_unit_is_rank_stage_plus_cold_phases_plus_target(self):
        rank_summary, _ = counts(10, 0)
        cold_summary, cold_record = counts(1, 100)
        rows = [{"arm": "B", "point_id": "s000", "pair": 1, "process": "rank", "summary_op_counts": rank_summary,
                 "record_op_counts": {}},
                {"arm": "B", "point_id": "s000", "pair": 1, "process": "cold", "summary_op_counts": cold_summary,
                 "record_op_counts": cold_record}]
        unit = counted_band.ic_units(rows)["B"]["s000"]
        # rank_stage 10 + cold setup, linear algebra, between (1 each) + target 100; the rank
        # process's setup and the after-targets digest are not charged.
        self.assertEqual(unit["ec_add"], 113)
        self.assertEqual(unit["root_index_probes"], 113)
        self.assertEqual(unit["field_mul"], 0)

    def test_a_process_without_counting_is_refused(self):
        rows = [{"arm": "B", "point_id": "s000", "pair": 1, "process": p, "summary_op_counts": {"enabled": False},
                 "record_op_counts": None} for p in ("rank", "cold")]
        with self.assertRaises(ValueError):
            counted_band.ic_units(rows)

    def test_band_from_a_receipt_and_counts(self):
        import base64
        with tempfile.TemporaryDirectory() as d:
            panel = Path(d)
            charges = {"canonicalizations": 5, "failed_collisions": 0, "group_additions": 1000,
                       "partition_hashes": 1000, "scalar_multiplications": 2, "table_inserts": 10,
                       "table_queries": 10}
            runs = []
            rows = []
            for i in range(3):
                point = "s%03d" % i
                raw = {"records": [{"outcome": {"charges_setup_and_solve": charges}}]}
                (panel / ("%s.out" % point)).write_text(
                    "raw_b64=" + base64.b64encode(json.dumps(raw).encode()).decode() + "\n")
                runs.append({"status": "valid", "arm": "rT", "point_id": point, "stdout_file": "%s.out" % point})
                rank_summary, _ = counts(100 + i, 0)
                cold_summary, cold_record = counts(1, 50)
                rows += [{"arm": "B", "point_id": point, "pair": 1, "process": "rank",
                          "summary_op_counts": rank_summary, "record_op_counts": {}},
                         {"arm": "B", "point_id": point, "pair": 1, "process": "cold",
                          "summary_op_counts": cold_summary, "record_op_counts": cold_record}]
            (panel / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in runs))
            count_file = panel / "counts.jsonl"
            count_file.write_text("".join(json.dumps(r) + "\n" for r in rows))
            out = panel / "out"
            sys.argv = ["counted_band.py", "--receipt-dir", str(panel), "--counts", str(count_file),
                        "--out-dir", str(out), "--draws", "200"]
            counted_band.main()
            result = json.loads((out / "counted_band.json").read_text())
            self.assertIn("COUNTED band", result["band"]["label"])
            self.assertEqual(set(result["band"]["arms"]), {"B", "rT"})


if __name__ == "__main__":
    unittest.main()
