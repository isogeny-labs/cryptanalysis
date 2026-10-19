#!/usr/bin/env python3
"""Render the sparse-tau recoding and its frozen Tier 1 comparison."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
SCREEN = json.loads((HERE / "sparse-tau-radix-screen.json").read_text())
AUDIT = json.loads((HERE / "tier1-sparse-tau-cpu40-audit.json").read_text())
comparison = AUDIT["comparison"]
OUT = HERE / "sparse-tau-report-figures"
OUT.mkdir(exist_ok=True)


def trim_svg(path: Path) -> None:
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5})

# Algorithm diagram: exact pair operations and the implementation boundary.
fig, ax = plt.subplots(figsize=(9, 3.3))
ax.set_xlim(0, 9)
ax.set_ylim(0, 3.3)
ax.axis("off")
stages = [
    (0.12, "Scalar lattice", "choose pair (a,b)\nfrom four corners", "#eef4fa"),
    (2.33, "Digit step", "centered residue\nchoose digit d", "#f1f4e8"),
    (4.54, "Exact quotient", "divide inverse-matrix\nnumerators by 114049", "#f8f0e8"),
    (6.75, "Horner point path", "15 radix actions\nthen terminal table", "#f3eef8"),
]
for x, title, body, color in stages:
    box = FancyBboxPatch((x, 0.9), 2.0, 1.35, boxstyle="round,pad=0.07",
                         linewidth=1.2, edgecolor="#274060", facecolor=color)
    ax.add_patch(box)
    ax.text(x+1, 1.83, title, ha="center", va="center", weight="bold", color="#18324d", fontsize=8.7)
    ax.text(x+1, 1.32, body, ha="center", va="center", linespacing=1.35, fontsize=8)
for x in (2.14, 4.35, 6.56):
    ax.add_patch(FancyArrowPatch((x, 1.58), (x+0.18, 1.58), arrowstyle="-|>",
                                 mutation_scale=13, linewidth=1.1, color="#536b83"))
ax.text(4.5, 2.9, "Sparse Eisenstein radix 127 + 128τ", ha="center", weight="bold", fontsize=12)
ax.text(4.5, 0.38, "πP = [128](P + τP) − P; exact pair reconstruction screened on 12,288 frozen scalars.",
        ha="center", fontsize=8.1, color="#4a4a4a")
fig.tight_layout()
fig.savefig(OUT / "sparse-tau-method.svg", bbox_inches="tight")
fig.savefig(OUT / "sparse-tau-method.png", dpi=180, bbox_inches="tight")
trim_svg(OUT / "sparse-tau-method.svg")
plt.close(fig)

# Quantitative panel: timing, memory, and paired-ratio uncertainty.
ref_ms = comparison["reference_online_ms_mean"]
candidate_ms = comparison["sparse_online_ms_mean"]
ref_mb = comparison["reference_retained_bytes"] / 1_000_000
candidate_mb = comparison["sparse_retained_bytes"] / 1_000_000
ratio = comparison["qualified_online_ratio"]
low, high = comparison["paired_bootstrap95_by_repeat"]
fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.0), gridspec_kw={"width_ratios": [1.35, 1]})
ax = axes[0]
bars = ax.bar(["334−τ reference", "127+128τ sparse"], [ref_ms, candidate_ms],
              color=["#8ca6bd", "#315f83"], width=0.62)
ax.set_ylabel("Mean online time (ms; 12,288 outputs)")
ax.set_title("Matched prepared-table panel", loc="left", weight="bold", fontsize=9.2)
ax.set_ylim(0, 1030)
ax.grid(axis="y", color="#d8dee5", linewidth=0.8)
ax.set_axisbelow(True)
ax.spines[["top", "right"]].set_visible(False)
for bar, ms, mb in zip(bars, [ref_ms, candidate_ms], [ref_mb, candidate_mb]):
    ax.text(bar.get_x()+bar.get_width()/2, ms+22, f"{ms:.1f} ms\n{mb:.3f} MB",
            ha="center", va="bottom", fontsize=8.1)

ax = axes[1]
ax.errorbar([ratio], [0], xerr=[[ratio-low], [high-ratio]], fmt="o", capsize=5,
            color="#315f83", markersize=6, linewidth=2)
ax.axvline(1, color="#565c63", linestyle="--", linewidth=1.3, label="equal online time")
ax.set_xlim(0.9, 1.48)
ax.set_ylim(-0.7, 0.7)
ax.set_yticks([])
ax.set_xlabel("Reference / sparse time ratio")
ax.set_title("Paired ratio (16 pairs)", loc="left", weight="bold", fontsize=9.2)
ax.text(ratio, 0.2, f"{ratio:.4f}\n[{low:.4f}, {high:.4f}]", ha="center", va="bottom", fontsize=8.7)
ax.grid(axis="x", color="#d8dee5", linewidth=0.8)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.legend(frameon=False, loc="lower right", fontsize=7.8)
fig.suptitle("Sparse-tau radix versus prior 334−τ Horner path", x=0.06,
             ha="left", fontsize=11.5, weight="bold")
fig.text(0.06, 0.025,
         "Tier 1 single RunPod instance, CPU 40; 96 arms / 48 pairs; A/A controls passed. Ratio interval: paired bootstrap.",
         fontsize=7.8, color="#4a4a4a")
fig.tight_layout(rect=(0, 0.08, 1, 0.90))
fig.savefig(OUT / "sparse-tau-panel.svg", bbox_inches="tight")
fig.savefig(OUT / "sparse-tau-panel.png", dpi=180, bbox_inches="tight")
trim_svg(OUT / "sparse-tau-panel.svg")
plt.close(fig)
print("rendered sparse-tau method diagram and audited Tier 1 graph")
