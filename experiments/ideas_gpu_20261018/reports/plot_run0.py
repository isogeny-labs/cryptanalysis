"""Render recorded native counters only; performs no cryptographic computation."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

study = Path(__file__).resolve().parents[1]
arms = ["none", "det", "reselect", "baseline"]
rows = [json.loads((study / "remote/run-0" / ("negation-" + arm + ".stdout")).read_text()) for arm in arms]
labels = ["none\ncensored", "det\ncensored", "reselect\ncensored", "baseline\ncollision flag"]
fig, axes = plt.subplots(1, 3, figsize=(10, 3.6), sharex=True)
for axis, counter, title in zip(axes, ["mul", "sqr", "inv"], ["Field multiplications", "Field squarings", "Field inversions"]):
    bars = axis.bar(labels, [row[counter] for row in rows], color=["#b95b58", "#b95b58", "#b95b58", "#477d64"])
    for bar, row in zip(bars, rows):
        if row["censored"]:
            bar.set_hatch("//")
    axis.set_title(title, fontsize=10)
    axis.set_ylabel("Recorded calls")
    axis.tick_params(axis="x", labelsize=8)
    axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    axis.spines[["top", "right"]].set_visible(False)
fig.suptitle("Run 0: one frozen seed; three censored quotient arms", fontsize=12)
fig.text(0.5, 0.015, "Affine native diagnostic; no completed-solve ratio or independently verified scalar", ha="center", fontsize=9)
fig.tight_layout(rect=(0, 0.06, 1, 0.92))
fig.savefig(study / "reports/run0-operation-counters.svg")
fig.savefig(study / "reports/run0-operation-counters.png", dpi=150)
