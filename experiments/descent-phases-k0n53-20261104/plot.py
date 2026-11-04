"""Stacked per-phase wall time per trial from data/phases-*.jsonl (plotting only)."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
runs = []
for name, label in (("phases-simd.jsonl", "AVX-512 on"), ("phases-scalar.jsonl", "AVX-512 off")):
    for i, line in enumerate((HERE / "data" / name).read_text().splitlines()):
        runs.append((f"{label} #{i + 1}", json.loads(line)))
phases = list(runs[0][1]["phases"])
colors = ["#bbbbbb", "#9467bd", "#c5b0d5", "#d62728", "#ff9896", "#2f6db3", "#9ecae1"]
(HERE / "figures").mkdir(exist_ok=True)
fig, ax = plt.subplots(figsize=(9, 3.6))
for j, (label, d) in enumerate(runs):
    left = 0.0
    for p, c in zip(phases, colors):
        v = d["phases"][p]["ns_per_trial"]
        ax.barh(j, v, left=left, color=c, label=p if j == 0 else None)
        left += v
    ax.text(left + 1, j, f"{d['total_ns'] / d['trials']:.0f} ns", va="center", fontsize=7)
ax.set_yticks(range(len(runs)), [r[0] for r in runs], fontsize=8)
ax.invert_yaxis()
ax.set_xlabel("wall ns per trial (k0n53, 512 walks, 64 targets, 12.07M trials; L0, CPU 3)", fontsize=8)
ax.legend(fontsize=7, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.25))
ax.set_title("k0n53 walked descent: native time by phase", fontsize=9)
fig.tight_layout()
for ext, kw in (("svg", {}), ("png", {"dpi": 150})):
    fig.savefig(HERE / "figures" / f"phases.{ext}", bbox_inches="tight", **kw)
