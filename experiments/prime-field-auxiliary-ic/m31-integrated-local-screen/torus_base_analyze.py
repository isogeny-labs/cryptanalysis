"""Audit the complete public M31 torus/interval/random/rho panel."""
import csv
import hashlib
import json
import runpy
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
public = json.loads((HERE / "fresh-public.json").read_text())
api = runpy.run_path(str(HERE.parent / "m31-full-rust-comparison/replay.py"))
curve = api["Curve"](public["p"], a4=public["a"], a6=public["b"])
rows = list(csv.DictReader((HERE / "torus-base-raw.csv").open()))
labels = {"interval", "torus", "random", "rho"}
assert len(rows) == 60
blocks = defaultdict(dict)
for row in rows:
    target, seed, arm = int(row["target"]), int(row["seed"]), row["arm"]
    assert 0 <= target < 5 and 0 <= seed < 3 and arm in labels
    assert arm not in blocks[(target, seed)]
    blocks[(target, seed)][arm] = row
    assert row["status"] == "solved" and row["exit_code"] == "0"
    scalar = int(row["scalar"])
    assert curve.mul(scalar, tuple(public["G"])) == tuple(public["targets"][target]["Q"])
    stem = f"torus-t{target}-s{seed}-{arm}"
    stdout = (HERE / f"{stem}.stdout").read_bytes()
    assert hashlib.sha256(stdout).hexdigest() == row["stdout_sha256"]
    if arm == "rho":
        metrics = json.loads((HERE / f"{stem}.metrics.json").read_text())
        assert metrics["recovered"] == scalar
        assert metrics["walk_steps"] == int(row["queries"])
    else:
        data = json.loads(stdout)
        assert data["Q"] == public["targets"][target]["Q"]
        assert data["base_kind"] == arm and data["scalar"] == scalar
        assert data["work"]["queries"] == int(row["queries"])
        assert data["work"]["relations"] == int(row["relations"])
        assert data["work"]["matrix_rank"] == int(row["rank"])
        assert data["setup_pair_counts"]["entries"] == int(row["pair_entries"])
        digest = hashlib.sha256(json.dumps(data["base_points"], separators=(",", ":")).encode()).hexdigest()
        assert digest == row["basis_sha256"]
    assert int(row["wall_ns"]) > 0 and int(row["cpu_ns"]) > 0

assert len(blocks) == 15 and all(set(block) == labels for block in blocks.values())
assert all(len({int(row["scalar"]) for row in block.values()}) == 1 for block in blocks.values())
for arm in ("interval", "torus", "random", "rho"):
    vals = list(block[arm] for block in blocks.values())
    print(arm, "wall_ms", round(statistics.median(int(v["wall_ns"]) for v in vals)/1e6, 3),
          "cpu_ms", round(statistics.median(int(v["cpu_ns"]) for v in vals)/1e6, 3),
          "queries", statistics.median(int(v["queries"]) for v in vals))
for numerator, denominator in (("interval", "torus"), ("random", "torus"),
                               ("rho", "torus"), ("interval", "random")):
    for metric in ("wall_ns", "cpu_ns"):
        ratios = [int(v[numerator][metric])/int(v[denominator][metric]) for v in blocks.values()]
        target_medians = [statistics.median(int(v[numerator][metric])/int(v[denominator][metric])
                                           for (target, _), v in blocks.items() if target == t)
                          for t in range(5)]
        print(numerator, denominator, metric, "paired", round(statistics.median(ratios), 4),
              "denominator_wins", sum(q > 1 for q in ratios), "/15",
              "target_medians", [round(q, 3) for q in target_medians])
