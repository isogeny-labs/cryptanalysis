"""Recheck fresh public M31 panel identities and paired timing summaries."""
import csv
import json
import runpy
import statistics as stats
from pathlib import Path

HERE = Path(__file__).resolve().parent
helpers = runpy.run_path(str(HERE.parent / "m31-full-rust-comparison/replay.py"))
public = json.loads((HERE / "fresh-public.json").read_text())
curve = helpers["Curve"](public["p"], a4=public["a"], a6=public["b"])
rows = list(csv.DictReader((HERE / "fresh-raw.csv").open()))
labels = {"original256", "original384", "inline384", "original768", "inline768", "rho"}
assert len(rows) == 90
arms = {}
for row in rows:
    key = (int(row["target"]), int(row["seed"]), row["configuration"])
    assert key not in arms and row["configuration"] in labels
    assert row["status"] == "solved" and row["exit_code"] == "0"
    q = tuple(public["targets"][key[0]]["Q"])
    assert curve.mul(int(row["scalar"]), tuple(public["G"])) == q
    arms[key] = row
assert len(arms) == 90
for target in range(5):
    for seed in range(3):
        for size in (384, 768):
            a = arms[target, seed, f"original{size}"]
            b = arms[target, seed, f"inline{size}"]
            assert (a["scalar"], a["queries_or_steps"], a["relations"], a["entries"]) == (
                b["scalar"], b["queries_or_steps"], b["relations"], b["entries"])

for candidate, control in (("inline384", "original384"), ("inline768", "original768"),
                           ("inline384", "original256"), ("inline768", "original256"),
                           ("inline384", "rho"), ("inline768", "rho")):
    for metric in ("wall_ns", "cpu_ns"):
        ratios = [int(arms[target, seed, candidate][metric]) /
                  int(arms[target, seed, control][metric])
                  for target in range(5) for seed in range(3)]
        print(candidate, control, metric, "median", round(stats.median(ratios), 4),
              "wins", sum(x < 1 for x in ratios), "/15")
