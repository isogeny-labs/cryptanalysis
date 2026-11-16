"""Synthetic alignment/negative controls; these are not experiment results."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from compare_reports import ARMS, SAMPLER, compare_reports


def reports():
    special = {
        "schema_version": 1, "operation": "auxiliary-prime-field-ic", "field_bits": 7,
        "source_commit": "1" * 40, "binary_blake3": "2" * 64,
        "public": {"p": 127, "a": 2, "b": 51, "n": 109, "P": [3, 46], "Q": [6, 122]},
        "factor_base": {"raw_roots": 8, "affine_points": 6, "folded_columns": 3,
                        "columns_blake3": "3" * 64, "backend": "scalar",
                        "uses_auxiliary_maps": True, "uses_circuit": True,
                        "encoding": {"kind": "auxiliary"}},
        "configured_search": {"seed": 43, "max_queries": 17, "walk_lanes": 8,
                              "max_relations": 40, "max_proof_nodes": 100, "max_millis": None},
        "mode": "bounded-relation-yield", "sampler": SAMPLER,
        "status": "complete", "stop_reason": "QueryBudget", "certificate": None,
        "work": {"queries": 17, "generated_targets": 24, "lane_rounds": 3, "relations": 5,
                 "duplicate_rows": 4, "circuit_queries": 16, "matrix_rank": 0,
                 "proof_nodes": 0, "backend": "scalar"},
    }
    direct = copy.deepcopy(special)
    direct["factor_base"].update(uses_auxiliary_maps=False, uses_circuit=False, encoding={"kind": "direct"})
    direct["work"]["circuit_queries"] = 0
    random = copy.deepcopy(direct)
    random["factor_base"].update(raw_roots=3, columns_blake3="4" * 64,
        selection_encoding={"kind": "random-subgroup", "seed": 701, "columns": 3, "cofactor": 1, "max_draws": 100},
        random_preparation={"sampler": "splitmix64-rejection-field-coordinates-cofactor-clear-negation-fold",
                            "seed": 701, "cofactor": 1, "draws": 11, "field_rejections": 0,
                            "non_lifts": 3, "cleared_to_identity": 0, "duplicate_columns": 5})
    random["work"].update(relations=6, duplicate_rows=3)
    return dict(zip(ARMS, (special, direct, random)))


class AlignmentTests(unittest.TestCase):
    def refused(self, data, expected=None):
        result = compare_reports(data)
        self.assertEqual(result["status"], "incomparable")
        self.assertIsNone(result["qualified_speedup"])
        self.assertIsNone(result["end_to_end_cost_comparison"])
        self.assertTrue(all("derived_counts" not in arm for arm in result["arms"].values()))
        if expected:
            self.assertIn(expected, result["issues"][0])
        return result

    def test_aligned_prefix_uses_failed_queries_in_exact_denominators(self):
        result = compare_reports(reports())
        self.assertEqual(result["status"], "aligned")
        self.assertEqual(result["arms"]["auxiliary"]["derived_counts"]["distinct_rows_per_query"],
                         {"numerator": 5, "denominator": 17})
        self.assertEqual(result["arms"]["random"]["derived_counts"]["hits_per_query"],
                         {"numerator": 9, "denominator": 17})
        self.assertIsNone(result["qualified_speedup"])

    def test_public_binary_and_sampler_mismatches_are_rejected(self):
        mutations = [("source_commit", "5" * 40), ("binary_blake3", "6" * 64),
                     ("sampler", "other"), ("field_bits", 5)]
        for key, value in mutations:
            with self.subTest(key=key):
                data = reports(); data["random"][key] = value; self.refused(data)
        data = reports(); data["random"]["public"]["Q"] = [3, 46]; self.refused(data, "public")
        for key in ("seed", "walk_lanes", "max_queries", "max_relations", "max_proof_nodes", "max_millis"):
            with self.subTest(key=key):
                data = reports(); data["random"]["configured_search"][key] = 1; self.refused(data)

    def test_same_base_identity_and_rows_must_really_match(self):
        for key, value in [("columns_blake3", "5" * 64), ("raw_roots", 7), ("folded_columns", 4)]:
            with self.subTest(key=key):
                data = reports(); data["same_base"]["factor_base"][key] = value; self.refused(data)
        for key in ("relations", "duplicate_rows"):
            data = reports(); data["same_base"]["work"][key] -= 1; self.refused(data, key)

    def test_random_selection_and_draw_accounting_are_checked(self):
        for section, key, value in [
            ("selection_encoding", "kind", "auxiliary"), ("selection_encoding", "columns", 8),
            ("selection_encoding", "max_draws", 10), ("random_preparation", "seed", 702),
            ("random_preparation", "cofactor", 2), ("random_preparation", "draws", 12),
            ("random_preparation", "cleared_to_identity", 1),
        ]:
            with self.subTest(key=key):
                data = reports(); data["random"]["factor_base"][section][key] = value; self.refused(data)

    def test_incomplete_arms_are_retained_without_derived_comparisons(self):
        for name in ARMS:
            for reason in ("QueryBudget", "TimeBudget", "RelationBudget"):
                with self.subTest(arm=name, reason=reason):
                    data = reports(); data[name].update(status="incomplete", stop_reason=reason)
                    data[name]["work"].update(queries=8, generated_targets=8, lane_rounds=1,
                                             relations=3, duplicate_rows=2,
                                             circuit_queries=8 if name == "auxiliary" else 0)
                    result = self.refused(data, "incomplete")
                    self.assertEqual(result["arms"][name]["work"]["queries"], 8)

    def test_replay_decomposition_and_full_solves_are_not_yield_results(self):
        for mode in ("public-relation-certificate-replay", "bounded-single-target-search", "single-decomposition-control"):
            data = reports()
            for report in data.values(): report["mode"] = mode
            self.refused(data, "separate")

    def test_numeric_types_lane_padding_and_recovery_work_are_checked(self):
        for key, value in [("queries", True), ("queries", 17.0), ("queries", -1),
                           ("queries", 16), ("generated_targets", 17), ("lane_rounds", 2),
                           ("relations", 18), ("matrix_rank", 1), ("proof_nodes", 1),
                           ("circuit_queries", 18), ("backend", "avx2")]:
            with self.subTest(key=key):
                data = reports(); data["random"]["work"][key] = value; self.refused(data)

    def test_missing_and_zero_budget_metadata_fail_closed(self):
        for key in ("public", "source_commit", "binary_blake3", "configured_search", "certificate", "factor_base"):
            data = reports(); del data["random"][key]; self.refused(data)
        data = reports(); del data["random"]["factor_base"]["columns_blake3"]; self.refused(data)
        data = reports()
        for report in data.values(): report["configured_search"]["max_queries"] = 0
        self.refused(data)

    def test_a_valid_random_coincidence_is_flagged_and_retained(self):
        data = reports(); data["random"]["factor_base"]["columns_blake3"] = "3" * 64
        result = compare_reports(data)
        self.assertEqual(result["status"], "aligned")
        self.assertTrue(result["random_base_coincides_with_special"])

    def run_cli(self, folder, data):
        paths = []
        for name in ARMS:
            path = folder / (name + ".json")
            path.write_text(json.dumps(data[name])); paths += ["--" + name.replace("_", "-"), str(path)]
        output = folder / "comparison.json"
        command = [sys.executable, str(Path(__file__).with_name("compare_reports.py")), *paths, "--output", str(output)]
        return command, output

    def test_cli_pins_inputs_and_writes_aligned_or_incomplete_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for complete in (True, False):
                data = reports()
                if not complete: data["random"]["status"] = "incomplete"
                command, output = self.run_cli(folder, data)
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0 if complete else 2, result.stderr)
                saved = json.loads(output.read_text())
                self.assertEqual(len(saved["raw_data"]), 3)
                self.assertTrue(all(len(row["sha256"]) == 64 for row in saved["raw_data"]))

    def test_invalid_json_is_retained_as_an_input_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp); command, output = self.run_cli(folder, reports())
            for content in ('{"work":NaN}', '[]', '{not json'):
                (folder / "random.json").write_text(content)
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, result.stderr)
                saved = json.loads(output.read_text())
                self.assertEqual(saved["status"], "incomparable")
                self.assertTrue(saved["issues"])

    def test_duplicate_status_cannot_overwrite_an_incomplete_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp); command, output = self.run_cli(folder, reports())
            path = folder / "random.json"
            valid = path.read_text()
            path.write_text('{"status":"incomplete",' + valid[1:])
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            saved = json.loads(output.read_text())
            self.assertEqual(saved["status"], "incomparable")
            self.assertTrue(any("duplicate JSON key: status" in issue for issue in saved["issues"]))


if __name__ == "__main__":
    unittest.main()
