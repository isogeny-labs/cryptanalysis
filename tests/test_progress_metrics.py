"""Controls for the committed-state progress exporter."""

import contextlib
import io
import json
from unittest.mock import patch

from tools import progress_metrics


def test_invalid_paired_runs_cannot_supply_performance_metrics():
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
    assert rows["ecc2k130.gpu.paired_runs"]["value"] == 3
    assert rows["ecc2k130.gpu.paired_runs_valid"]["value"] == 1
    assert rows["ecc2k130.gpu.return_rate_gps_max"]["value"] == 12.5
    assert rows["ecc2k130.gpu.paired_median_ratio"]["value"] == 1.2
    assert "valid paired runs" in rows["ecc2k130.gpu.return_rate_gps_max"]["label"]
