"""Controls for the committed-state progress exporter."""

import contextlib
import hashlib
import io
import json
import unittest
from unittest.mock import patch

from tools import progress_metrics


class ProgressMetricsTests(unittest.TestCase):
    def test_invalid_paired_runs_cannot_supply_performance_metrics(self):
        prefix = "ecc2k130/runner/research/production/panel/runs"
        paths = [f"{prefix}/{name}/result.json" for name in ("invalid", "malformed", "valid")]
        records = {
            paths[0]: {
                "started_at_utc": "2026-10-15T01:00:00Z",
                "valid": False,
                "population_results": [
                    {"return_rate_billion_per_second": 999, "median_ratio": 99}
                ],
            },
            paths[1]: {
                "started_at_utc": "2026-10-15T01:01:00Z",
                "valid": "true",
                "population_results": [
                    {"return_rate_billion_per_second": 888, "median_ratio": 88}
                ],
            },
            paths[2]: {
                "started_at_utc": "2026-10-15T01:02:00Z",
                "valid": True,
                "population_results": [
                    {"return_rate_billion_per_second": 12.5, "median_ratio": 1.2}
                ],
            },
        }
        output = io.StringIO()
        with (
            patch.object(progress_metrics, "ls", return_value=paths),
            patch.object(progress_metrics, "show", side_effect=lambda _ref, path: json.dumps(records[path])),
            contextlib.redirect_stdout(output),
        ):
            progress_metrics.ecc2k130_runs("HEAD", "2026-10-01")

        rows = {row["metric"]: row for row in map(json.loads, output.getvalue().splitlines())}
        self.assertEqual(rows["ecc2k130.gpu.paired_runs"]["value"], 3)
        self.assertEqual(rows["ecc2k130.gpu.paired_runs_valid"]["value"], 1)
        self.assertEqual(rows["ecc2k130.gpu.return_rate_gps_max"]["value"], 12.5)
        self.assertEqual(rows["ecc2k130.gpu.paired_median_ratio"]["value"], 1.2)
        self.assertIn("valid paired runs", rows["ecc2k130.gpu.return_rate_gps_max"]["label"])

    def test_d79_metrics_require_a_passing_audit_and_keep_cohorts_separate(self):
        index_path = "experiments/hecke-d79-live-seven-20261027/index.json"
        audit_path = index_path.removesuffix("index.json") + "audit.json"
        summary_path = "experiments/hecke-d79-live-seven-20261027/cases/fresh-summary.json"
        summary_text = json.dumps({"row_counts": {"four": 105, "five": 3, "six": 134, "seven": 406}})
        index = {
            "status": "COMPLETE",
            "cases": [
                {"cohort": "known_control", "final_rank_mod_q": 39, "source_count": 14},
                {"cohort": "fresh", "final_rank_mod_q": 39, "source_count": 35,
                 "summary": "cases/fresh-summary.json", "summary_sha256": hashlib.sha256(summary_text.encode()).hexdigest()},
                {"cohort": "fresh", "final_rank_mod_q": 38, "source_count": 40},
            ],
        }
        records = {index_path: json.dumps(index), audit_path: json.dumps({"status": "PASS"}),
                   summary_path: summary_text}
        output = io.StringIO()
        with patch.object(progress_metrics, "show", side_effect=lambda _ref, path: records.get(path)), \
                contextlib.redirect_stdout(output):
            progress_metrics._emit_d79_index("HEAD", index_path, "2026-10-27")
        rows = {row["metric"]: row for row in map(json.loads, output.getvalue().splitlines())}
        self.assertEqual(rows["hecke.d79.live-seven.known_control.rank39_cases"]["value"], 1)
        self.assertEqual(rows["hecke.d79.live-seven.known_control.first_rank39_source_count_median"]["value"], 14)
        self.assertEqual(rows["hecke.d79.live-seven.fresh.rank39_cases"]["value"], 1)
        self.assertEqual(rows["hecke.d79.live-seven.fresh.rank39_fraction"]["value"], 0.5)
        self.assertEqual(rows["hecke.d79.live-seven.fresh.relation_rows.support4.total"]["value"], 105)
        self.assertIn("hash-checked per-case summaries",
                      rows["hecke.d79.live-seven.fresh.relation_rows.support4.total"]["source"])

        index["cases"][1]["summary_sha256"] = "0" * 64
        records[index_path] = json.dumps(index)
        output = io.StringIO()
        with patch.object(progress_metrics, "show", side_effect=lambda _ref, path: records.get(path)), \
                contextlib.redirect_stdout(output):
            progress_metrics._emit_d79_index("HEAD", index_path, "2026-10-27")
        rows = {row["metric"]: row for row in map(json.loads, output.getvalue().splitlines())}
        self.assertNotIn("hecke.d79.live-seven.fresh.relation_rows.support4.total", rows)

        records[audit_path] = json.dumps({"status": "FAIL"})
        output = io.StringIO()
        with patch.object(progress_metrics, "show", side_effect=lambda _ref, path: records.get(path)), \
                contextlib.redirect_stdout(output):
            progress_metrics._emit_d79_index("HEAD", index_path, "2026-10-27")
        self.assertEqual(output.getvalue(), "")

    def test_d79_support_eight_metrics_preserve_censored_and_full_runs(self):
        root = progress_metrics.D79_SUPPORT_EIGHT
        records = {
            root + "/audit.json": json.dumps({"status": "PASS"}),
            root + "/result.json": json.dumps({
                "status": "CENSORED_PROBE_CAP", "p": 1825517, "q": 6091,
                "quintuple_sign_probes": 12000000, "rank_before": 38, "rank_after": 38,
            }),
            root + "/full/result.json": json.dumps({
                "status": "RANK_39_FOUND", "p": 1825517, "q": 6091,
                "quintuple_sign_probes": 12323269, "rank_before": 38, "rank_after": 39,
                "verified_rows": 225, "anchored_log_replay": "PASS",
            }),
        }
        output = io.StringIO()
        with patch.object(progress_metrics, "show", side_effect=lambda _ref, path: records.get(path)), \
                contextlib.redirect_stdout(output):
            progress_metrics.hecke_d79_metrics("HEAD", "2026-10-27")
        rows = {row["metric"]: row for row in map(json.loads, output.getvalue().splitlines())}
        prefix = "hecke.d79.support_eight_residual.retained_p1825517"
        self.assertEqual(rows[prefix + ".initial_cap.signed_quintuple_probes"]["value"], 12000000)
        self.assertEqual(rows[prefix + ".full_followup.signed_quintuple_probes"]["value"], 12323269)
        self.assertEqual(rows[prefix + ".full_followup.rank_gain"]["value"], 1)
        self.assertIn("not a fresh panel", rows[prefix + ".full_followup.rank_gain"]["label"])

    def test_d79_query_order_yields_keep_order_names_distinct_from_support_size(self):
        index_path = "experiments/hecke-d79-query-order-20261027/index.json"
        audit_path = "experiments/hecke-d79-query-order-20261027/audit.json"
        summary_path = "experiments/hecke-d79-query-order-20261027/cases/p-summary.json"
        summary_text = json.dumps({"row_counts": {"four": 20, "lex_eight": 120, "reverse_lex_eight": 100}})
        index = {
            "status": "COMPLETE",
            "cases": [{
                "cohort": "fresh", "final_rank_eight_mod_q": {"lex": 39, "reverse_lex": 39},
                "first_eight_source_count": {"lex": 30, "reverse_lex": 30},
                "summary": "cases/p-summary.json",
                "summary_sha256": hashlib.sha256(summary_text.encode()).hexdigest(),
            }],
        }
        records = {
            index_path: json.dumps(index),
            audit_path: json.dumps({"status": "PASS"}),
            summary_path: summary_text,
        }
        output = io.StringIO()
        with patch.object(progress_metrics, "show", side_effect=lambda _ref, path: records.get(path)), \
                contextlib.redirect_stdout(output):
            progress_metrics._emit_d79_index("HEAD", index_path, "2026-10-27")
        rows = {row["metric"]: row for row in map(json.loads, output.getvalue().splitlines())}
        self.assertEqual(rows["hecke.d79.query-order.fresh.relation_rows.order_lex_eight.total"]["value"], 120)
        self.assertEqual(rows["hecke.d79.query-order.fresh.relation_rows.order_reverse_lex_eight.total"]["value"], 100)
        self.assertNotIn("hecke.d79.query-order.fresh.relation_rows.support8.total", rows)
