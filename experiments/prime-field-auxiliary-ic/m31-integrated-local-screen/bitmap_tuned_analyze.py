"""Independent local audit and paired summary for the bitmap validation."""
import csv
import hashlib
import json
import runpy
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
public = json.loads((HERE / "fresh-public.json").read_text())
curve_api = runpy.run_path(str(HERE.parent / "m31-full-rust-comparison/replay.py"))
curve = curve_api["Curve"](public["p"], a4=public["a"], a6=public["b"])
rows = list(csv.DictReader((HERE / "bitmap-tuned-raw.csv").open()))
labels = {"control384", "tuned384", "control768", "tuned768", "rho"}
assert len(rows) == 75
blocks = defaultdict(dict)
for row in rows:
    target = int(row["target"])
    seed = int(row["seed"])
    label = row["configuration"]
    assert 0 <= target < 5 and 0 <= seed < 3 and label in labels
    assert row["status"] == "solved" and row["exit_code"] == "0"
    assert curve.mul(int(row["scalar"]), tuple(public["G"])) == tuple(public["targets"][target]["Q"])
    assert label not in blocks[(target, seed)]
    blocks[(target, seed)][label] = row
    stem = f"bitmap-t{target}-s{seed}-{label}"
    if label == "rho":
        metrics = json.loads((HERE / f"{stem}.metrics.json").read_text())
        digest = hashlib.sha256(json.dumps(metrics, sort_keys=True).encode()).hexdigest()
        assert int(row["scalar"]) == metrics["recovered"]
    else:
        report = (HERE / f"{stem}.stdout").read_bytes()
        digest = hashlib.sha256(report).hexdigest()
        data = json.loads(report)
        assert data["status"] == "solved" and data["scalar"] == int(row["scalar"])
        assert data["Q"] == public["targets"][target]["Q"]
        assert data["work"]["queries"] == int(row["queries_or_steps"])
        assert data["work"]["relations"] == int(row["relations"])
        assert data["setup_pair_counts"]["entries"] == int(row["entries"])
        row["identity"] = (data["base_points"], data["scalar"], data["certificate"],
                           data["work"], data["setup_pair_counts"], data["online_pair_counts"])
    assert row["report_sha256"] == digest
    assert int(row["wall_ns"]) > 0 and int(row["cpu_ns"]) > 0

assert len(blocks) == 15 and all(set(block) == labels for block in blocks.values())
for block in blocks.values():
    assert block["control384"]["identity"] == block["tuned384"]["identity"]
    assert block["control768"]["identity"] == block["tuned768"]["identity"]
    assert len({int(row["scalar"]) for row in block.values()}) == 1

for label in sorted(labels):
    print(label, "wall_ms", round(statistics.median(int(v[label]["wall_ns"])
                                                  for v in blocks.values()) / 1e6, 3),
          "cpu_ms", round(statistics.median(int(v[label]["cpu_ns"])
                                            for v in blocks.values()) / 1e6, 3))
for numerator, denominator in (("control384", "tuned384"),
                               ("control768", "tuned768"),
                               ("control768", "tuned384"),
                               ("rho", "tuned384")):
    for metric in ("wall_ns", "cpu_ns"):
        ratios = [int(v[numerator][metric]) / int(v[denominator][metric])
                  for v in blocks.values()]
        print(numerator, denominator, metric, "paired_median",
              round(statistics.median(ratios), 4), "denominator_wins",
              sum(ratio > 1 for ratio in ratios), "/15")
