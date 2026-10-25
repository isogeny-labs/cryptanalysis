"""Acceptance regressions for complete versus truncated/failed count panels."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import analyze_v2 as checked


class PanelAcceptanceTests(unittest.TestCase):
    def run_panel(self, mutate=None, corrupt_record=False):
        expected = checked.plan()
        self.assertEqual(len(expected), 62)
        rows, archive, records = [], {}, {}
        for item in expected:
            row = dict(item, status="valid", stdout_file=f"new-{item['serial']}.json")
            old = dict(row, stdout_file=f"old-{item['serial']}.json")
            archive[item["archived_serial"]] = old
            scalar = str(int(item["point_id"][1:]) + 1)
            if item["arm"] == checked.RHO_ARM:
                record = {"fields": {"recovered_scalar": scalar}, "records": [
                    {"outcome": {"charges_setup_and_solve": {"group_additions": 100}}}]}
            else:
                record = {"records": [
                    {"kind": "compact_orbit_dlp_target", "recovered_scalar": scalar,
                     "op_counts": {"ec_add": 1}},
                    {"kind": "compact_orbit_dlp_summary", "op_counts": {
                        "enabled": True, "end_to_end": {"ec_add": 4},
                        "phases": {phase: {"ec_add": 1} for phase in
                            ("rank_stage", "setup", "linear_algebra", "between_linear_algebra_and_targets")}}}]}
            records[row["stdout_file"]] = copy.deepcopy(record)
            records[old["stdout_file"]] = copy.deepcopy(record)
            rows.append(row)
        if corrupt_record:
            records[rows[2]["stdout_file"]]["records"][0]["recovered_scalar"] = "different"
        if mutate:
            mutate(rows)
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "runs.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
            (directory / "band.md").write_text("historical v1 report\n")
            (directory / "band-v2.md").write_text("stale v2 report\n")
            with patch.object(checked, "archived_rows", return_value=archive), \
                 patch.object(checked, "decode", side_effect=lambda path: records[Path(path).name]), \
                 patch.object(checked.band, "analyse", return_value={}) as band_call, \
                 patch.object(checked.band, "markdown", return_value="verified band\n"), \
                 contextlib.redirect_stdout(io.StringIO()):
                code = checked.analyze(SimpleNamespace(receipt_dir=directory, draws=10))
            result = json.loads((directory / "opcounts_result-v2.json").read_text())
            self.assertEqual((directory / "band.md").read_text(), "historical v1 report\n")
            return code, result, (directory / "band-v2.md").exists(), band_call.call_count

    def assert_rejected(self, mutate=None, corrupt_record=False):
        code, result, has_band, band_calls = self.run_panel(mutate, corrupt_record)
        self.assertEqual(code, 1)
        self.assertEqual(result["verdict"], "counts_fail")
        self.assertFalse(has_band)
        self.assertEqual(band_calls, 0)

    def test_complete_matched_panel_publishes_both_bands(self):
        code, result, has_band, calls = self.run_panel()
        self.assertEqual(code, 0)
        self.assertEqual(result["verdict"], "counts_identical")
        self.assertTrue(result["checks"]["complete_frozen_panel"])
        self.assertTrue(has_band)
        self.assertEqual(calls, 2)

    def test_malformed_ledger_clears_stale_success_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            for name in ("band-v2.md", "opcounts_result-v2.json", "counts-v2.json"):
                (directory / name).write_text("old successful output")
            (directory / "runs.jsonl").write_text("{truncated")
            with self.assertRaises(json.JSONDecodeError):
                checked.analyze(SimpleNamespace(receipt_dir=directory, draws=10))
            for name in ("band-v2.md", "opcounts_result-v2.json", "counts-v2.json"):
                self.assertFalse((directory / name).exists())

    def test_one_rank_row_cannot_pass(self):
        self.assert_rejected(lambda rows: rows.__delitem__(slice(1, None)))

    def test_missing_last_target_cannot_pass(self):
        self.assert_rejected(lambda rows: rows.pop())

    def test_duplicate_replacing_a_target_cannot_pass(self):
        self.assert_rejected(lambda rows: rows.__setitem__(-1, copy.deepcopy(rows[-2])))

    def test_wrong_seed_cannot_pass(self):
        self.assert_rejected(lambda rows: rows[3].__setitem__("seed", 99))

    def test_invalid_run_does_not_publish_band(self):
        self.assert_rejected(lambda rows: rows[3].__setitem__("status", "invalid"))

    def test_archive_mismatch_does_not_publish_band(self):
        self.assert_rejected(corrupt_record=True)


if __name__ == "__main__":
    unittest.main()
