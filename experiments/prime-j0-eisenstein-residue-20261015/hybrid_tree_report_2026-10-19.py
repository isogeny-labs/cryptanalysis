#!/usr/bin/env python3
"""Render the hybrid reduction diagrams from the independently audited receipt."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
RECEIPT = json.loads((HERE / "alt-hybrid-audit.json").read_text())
OUT = HERE / "hybrid-tree-figures"
OUT.mkdir(exist_ok=True)


def trim_svg(path: Path) -> None:
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5})
fig, ax = plt.subplots(figsize=(10, 4.3))
ax.set_xlim(0, 10)
ax.set_ylim(0, 4.3)
ax.axis("off")

def box(x, y, w, h, title, body, color="#eef4fa"):
    patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                           linewidth=1.3, edgecolor="#274060", facecolor=color)
    ax.add_patch(patch)
    ax.text(x+w/2, y+h*0.69, title, ha="center", va="center", weight="bold", color="#18324d")
    ax.text(x+w/2, y+h*0.35, body, ha="center", va="center", linespacing=1.3, fontsize=8.5)

box(0.15, 1.45, 2.2, 1.25, "Frozen input", "12,288 distinct scalars\nsecp256k1 uniform fixture")
box(3.1, 2.35, 2.25, 1.25, "Hybrid depth 2", "2 batched affine layers\nthen XYZZ tree joins", "#e9f2f9")
box(3.1, 0.45, 2.25, 1.25, "Hybrid depth 3", "3 batched affine layers\nthen XYZZ tree joins", "#e9f2f9")
box(6.35, 1.45, 2.0, 1.25, "Normalize", "Batch-normalize\n128 outputs per chunk")
box(8.85, 1.45, 1.0, 1.25, "Check", "Exact\nreplay", "#edf5ed")
for start, end in [((2.35, 2.08), (3.02, 2.85)), ((2.35, 2.08), (3.02, 1.08)),
                   ((5.42, 2.98), (6.27, 2.15)), ((5.42, 1.08), (6.27, 1.85)),
                   ((8.42, 2.08), (8.78, 2.08))]:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=15,
                                 linewidth=1.25, color="#536b83"))
ax.text(5, 4.0, "Hybrid reduction tree: alternative affine/projective split points",
        ha="center", fontsize=12, weight="bold")
ax.text(5, 0.1, "Both variants use the same 27,429,548-byte norm-110557 table; geometry and timing are diagnostic.",
        ha="center", fontsize=8.2, color="#4a4a4a")
fig.tight_layout()
fig.savefig(OUT / "hybrid-tree-pipeline.svg", bbox_inches="tight")
fig.savefig(OUT / "hybrid-tree-pipeline.png", dpi=180, bbox_inches="tight")
trim_svg(OUT / "hybrid-tree-pipeline.svg")
plt.close(fig)

depths = RECEIPT["hybrid_depths"]
labels = ["2 affine levels", "3 affine levels"]
prep = [depths["2"]["preparation_ms_diagnostic"], depths["3"]["preparation_ms_diagnostic"]]
online = [depths["2"]["online_ms_diagnostic"], depths["3"]["online_ms_diagnostic"]]
colors = ["#496f93", "#d18b40"]
fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.1))
for ax, vals, title, unit in [
    (axes[0], prep, "Table preparation", "ms (diagnostic)"),
    (axes[1], online, "12,288-output online interval", "ms (diagnostic)"),
]:
    bars = ax.bar(labels, vals, color=colors, width=0.6)
    ax.set_title(title, loc="left", weight="bold", fontsize=10)
    ax.set_ylabel(unit)
    ax.grid(axis="y", color="#d8dee5", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    for b, v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, b.get_height(), f"{v:,.3f}",
                ha="center", va="bottom", fontsize=8.5, weight="bold")
fig.suptitle("Hybrid tree phase costs; one diagnostic run per variant", x=0.08,
             ha="left", fontsize=12, weight="bold")
fig.text(0.08, 0.015,
         "Each run checked 12,288 distinct fixture points; no paired interval or Tier 1 ranking is available.",
         fontsize=8.4, color="#4a4a4a")
fig.tight_layout(rect=(0, 0.07, 1, 0.93))
fig.savefig(OUT / "hybrid-tree-phase-costs.svg", bbox_inches="tight")
fig.savefig(OUT / "hybrid-tree-phase-costs.png", dpi=180, bbox_inches="tight")
trim_svg(OUT / "hybrid-tree-phase-costs.svg")
plt.close(fig)

print("rendered hybrid-tree pipeline and audited phase costs")
