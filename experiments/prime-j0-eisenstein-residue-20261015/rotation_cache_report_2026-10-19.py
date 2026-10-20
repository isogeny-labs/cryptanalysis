#!/usr/bin/env python3
"""Render the rotation-cache transfer and Tier 1 evidence from audited JSON."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
TRANSFER = json.loads((HERE / "rotation-seed-transfer-audit.json").read_text())
PANEL = json.loads((HERE / "tier1-cache10-cpu40-audit.json").read_text())
OUT = HERE / "rotation-cache-figures"
OUT.mkdir(exist_ok=True)


def trim_svg(path: Path) -> None:
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5})
fig, ax = plt.subplots(figsize=(8.3, 3.5))
ax.set_xlim(0, 8.3)
ax.set_ylim(0, 3.4)
ax.axis("off")


def box(x, title, body, color="#eef4fa"):
    patch = FancyBboxPatch((x, 0.85), 1.95, 1.45, boxstyle="round,pad=0.08",
                           linewidth=1.3, edgecolor="#274060", facecolor=color)
    ax.add_patch(patch)
    ax.text(x+0.975, 1.85, title, ha="center", va="center", weight="bold", color="#18324d", fontsize=8.5)
    ax.text(x+0.975, 1.32, body, ha="center", va="center", linespacing=1.4, fontsize=7.5)


box(0.05, "Training", "20,000 SHAKE scalars\nselect row seeds from counts")
box(2.13, "Held-out eval", "12,288 distinct scalars\nindependent derivation domain")
box(4.21, "Transfer screen", "Compare trained top-k hits\nwith held-out and uniform share", "#f1f4e8")
box(6.29, "Panel", "7 vs 10\ncache rows", "#f8f0e8")
for start, end in [((2.04, 1.58), (2.12, 1.58)), ((4.12, 1.58), (4.20, 1.58)),
                   ((6.20, 1.58), (6.28, 1.58))]:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=15,
                                 linewidth=1.25, color="#536b83"))
ax.text(4.15, 3.02, "Held-out rotation-cache selection and evaluation", ha="center",
        fontsize=12, weight="bold")
ax.text(5, 0.33, "Terminal row has a separate distribution and remains ordinary affine in both candidates.",
        ha="center", fontsize=8.2, color="#4a4a4a")
fig.tight_layout()
fig.savefig(OUT / "rotation-cache-method.svg", bbox_inches="tight")
fig.savefig(OUT / "rotation-cache-method.png", dpi=180, bbox_inches="tight")
trim_svg(OUT / "rotation-cache-method.svg")
plt.close(fig)

rows = TRANSFER["rows"][:14]
ks = [100, 1000, 5000, 10000]
train = [sum(r["top_by_training"][str(k)]["train_hit_fraction"] for r in rows)/len(rows) for k in ks]
held = [sum(r["top_by_training"][str(k)]["heldout_hit_fraction"] for r in rows)/len(rows) for k in ks]
uniform = [k / 22756 for k in ks]

fig, axes = plt.subplots(1, 2, figsize=(10, 4.3))
ax = axes[0]
x = range(len(ks))
ax.plot(x, train, marker="o", linewidth=2, color="#315f83", label="Training hit share")
ax.plot(x, held, marker="o", linewidth=2, color="#d18b40", label="Held-out hit share")
ax.plot(x, uniform, linestyle="--", linewidth=1.7, color="#565c63", label="Uniform share")
ax.set_xticks(list(x), [f"{k:,}" for k in ks])
ax.set_xlabel("Top seeds per digit row, selected on training data")
ax.set_ylabel("Mean selection share")
ax.set_title("Transfer of trained hot seeds", loc="left", weight="bold", fontsize=9.5)
ax.grid(axis="y", color="#d8dee5", linewidth=0.8)
ax.set_axisbelow(True)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False, fontsize=8)

ax = axes[1]
comp = PANEL["comparison"]
cache_labels = ["7-row reference", "10-row candidate"]
times = [comp["reference_online_ms_mean"], comp["candidate_online_ms_mean"]]
bytes_mb = [x/1_000_000 for x in [comp["reference_retained_bytes"][0], comp["candidate_retained_bytes"][0]]]
bars = ax.bar(cache_labels, times, color=["#8ca6bd", "#315f83"], width=0.58)
ax.set_ylabel("Mean online time (ms; 12,288 outputs)")
ax.set_title("Cache panel: unqualified result", loc="left", weight="bold", fontsize=9.5)
ax.set_ylim(0, 82)
ax.grid(axis="y", color="#d8dee5", linewidth=0.8)
ax.set_axisbelow(True)
ax.spines[["top", "right"]].set_visible(False)
for b, t, mem in zip(bars, times, bytes_mb):
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.35,
            f"{t:.3f} ms\n{mem:.2f} MB", ha="center", va="bottom", fontsize=8.2)
fig.suptitle("Rotation-cache transfer screen and timing evidence", x=0.07,
             ha="left", fontsize=12, weight="bold")
fig.text(0.07, 0.015,
         "Two A/A controls failed; qualified ratio is null. Transfer averages 14 rows; panel has 96 arms / 48 pairs. No speedup claim.",
         fontsize=8.1, color="#4a4a4a")
fig.tight_layout(rect=(0, 0.10, 1, 0.82))
fig.savefig(OUT / "rotation-cache-evidence.svg", bbox_inches="tight")
fig.savefig(OUT / "rotation-cache-evidence.png", dpi=180, bbox_inches="tight")
trim_svg(OUT / "rotation-cache-evidence.svg")
plt.close(fig)

print("rendered rotation-cache method diagram and audit-derived evidence graph")
