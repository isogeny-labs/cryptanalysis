"""Validate retained native rho answers, counters, and build identity."""

import hashlib
import json
import math
import statistics
from pathlib import Path

from sage.all import EllipticCurve, GF


HERE = Path(__file__).resolve().parent


def main():
    record = json.loads((HERE / "rho_run.json").read_text())
    build = json.loads((HERE / "rho_build.json").read_text())
    assert build["binary_sha256"] == record["binary_sha256"]
    binary = Path(build["binary_path"])
    if binary.exists():
        assert hashlib.sha256(binary.read_bytes()).hexdigest() == build["binary_sha256"]
    assert build["source_commit_at_run"] == record["source_commit"]
    assert record["seeds"] == list(range(1, 17))
    assert record["curve_p_a_b_order"] == [10007, 10004, 7, 10193]
    assert record["generator_xy"] == [4634, 6322]
    assert record["target_xy"] == [9780, 4658]
    field = GF(10007)
    curve = EllipticCurve(field, [-3, 7])
    generator = curve(field(4634), field(6322))
    target = curve(field(9780), field(4658))
    assert int(curve.order()) == generator.order() == 10193
    assert 7001 * generator == target

    ops = []
    for seed, run in enumerate(record["runs"], 1):
        assert run["seed"] == seed
        argv = run["argv"]
        assert argv[1:] == [
            "solve", "--alg", "rho", "--group", "ec", "--p", "10007",
            "--a", "10004", "--b", "7", "--order", "10193",
            "--g", "4634,6322", "--h", "9780,4658", "--threads", "1",
            "--seed", str(seed), "--max-ops", "1000000",
        ]
        assert run["stderr"] == "" and run["exit_code"] == 0
        result = json.loads(run["stdout"])
        assert result == run["result"]
        assert result["status"] == "ok" and result["alg"] == "rho"
        assert result["x"] == 7001 and result["x"] * generator == target
        assert result["threads"] == 1 and run["verified"]
        assert run["wall_seconds"] >= 0 and run["cpu_seconds"] >= 0
        ops.append(result["ops"])

    summary = record["summary"]
    assert summary["attempts"] == summary["verified"] == 16
    assert summary["failed_or_censored_seeds"] == []
    assert [summary["ops_min"], summary["ops_median"], summary["ops_max"]] == [
        min(ops), statistics.median(ops), max(ops)
    ]
    assert math.isclose(summary["total_wall_seconds"],
                        sum(run["wall_seconds"] for run in record["runs"]), abs_tol=1e-12)
    assert math.isclose(summary["total_cpu_seconds"],
                        sum(run["cpu_seconds"] for run in record["runs"]), abs_tol=1e-12)
    print(json.dumps({"all_verified": True, "runs": 16, "ops_min": min(ops),
                      "ops_median": statistics.median(ops), "ops_max": max(ops),
                      "outlier_seed": 9, "outlier_ops": ops[8]}, sort_keys=True))


if __name__ == "__main__":
    main()
