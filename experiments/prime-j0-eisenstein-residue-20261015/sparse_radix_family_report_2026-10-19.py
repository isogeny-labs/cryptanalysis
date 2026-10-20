#!/usr/bin/env python3
"""Render the sparse radix-family screen and existing Tier 1 audit receipts."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
SCREEN = json.loads((HERE / "sparse-radix-family-screen.json").read_text())
AUDITS = {
    "cold_76": json.loads((HERE / "tier1-tau64-cold-cpu40-audit.json").read_text()),
    "online_76": json.loads((HERE / "tier1-tau64-online-cpu40-audit.json").read_text()),
    "cold_65": json.loads((HERE / "tier1-tau32-cold-cpu40-audit.json").read_text()),
    "online_65": json.loads((HERE / "tier1-tau32-online-cpu40-audit.json").read_text()),
}
OUT = HERE / "sparse-radix-family-figures"
OUT.mkdir(exist_ok=True)


def trim_svg(path: Path) -> None:
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.2})

# Algebra-to-screen method diagram.
fig, ax = plt.subplots(figsize=(8.8, 3.2))
ax.set_xlim(0, 8.8)
ax.set_ylim(0, 3.2)
ax.axis("off")
stages = [
    (0.16, "Choose k", "t = 2ᵏ\nπₖ = (t−1)+tτ", "#eef4fa"),
    (2.38, "Recoding", "centered residue\nand exact quotient", "#f1f4e8"),
    (4.60, "Check finite stream", "12,288 scalar pairs\nreconstruct exactly", "#f8f0e8"),
    (6.82, "Measure separately", "one-scalar cold\nprepared-table batch", "#f3eef8"),
]
for x, title, body, color in stages:
    box = FancyBboxPatch((x, 0.88), 1.82, 1.38, boxstyle="round,pad=0.07",
                         linewidth=1.2, edgecolor="#274060", facecolor=color)
    ax.add_patch(box)
    ax.text(x+0.91, 1.83, title, ha="center", va="center", weight="bold", color="#18324d", fontsize=8.6)
    ax.text(x+0.91, 1.30, body, ha="center", va="center", linespacing=1.35, fontsize=7.8)
for x in (2.18, 4.40, 6.62):
    ax.add_patch(FancyArrowPatch((x, 1.57), (x+0.18, 1.57), arrowstyle="-|>",
                                 mutation_scale=13, linewidth=1.1, color="#536b83"))
ax.text(4.4, 2.87, "Sparse Eisenstein radix family", ha="center", weight="bold", fontsize=12)
ax.text(4.4, 0.34, "πₖP = [2ᵏ](P+τP)−P; digit caps and point-map refinement remain separate proof obligations.",
        ha="center", fontsize=7.9, color="#4a4a4a")
fig.tight_layout()
fig.savefig(OUT / "sparse-radix-family-method.svg", bbox_inches="tight")
fig.savefig(OUT / "sparse-radix-family-method.png", dpi=180, bbox_inches="tight")
trim_svg(OUT / "sparse-radix-family-method.svg")
plt.close(fig)

rows = SCREEN["candidates"]
ks = [r["k"] for r in rows]
seeds = [r["digit_seed_count_including_zero"] for r in rows]
steps = [r["first_frozen_fixture_terminal_step"] for r in rows]
records = [
    ("k7 / k6 cold", AUDITS["cold_76"], "qualified_cold_ratio"),
    ("k6 / k5 cold", AUDITS["cold_65"], "qualified_cold_ratio"),
    ("k7 / k6 prepared", AUDITS["online_76"], "qualified_online_ratio"),
    ("k6 / k5 prepared", AUDITS["online_65"], "qualified_online_ratio"),
]
ratios = [item[1]["comparison"][item[2]] for item in records]
intervals = [item[1]["comparison"]["paired_bootstrap95_by_repeat"] for item in records]

fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.1), gridspec_kw={"width_ratios": [1, 1.45]})
ax = axes[0]
bar = ax.bar([str(k) for k in ks], seeds, color=["#9bb2c6", "#668ba7", "#315f83"], width=0.58)
ax.set_xlabel("k in πₖ = (2ᵏ−1)+2ᵏτ")
ax.set_ylabel("Orbit-folded digit seeds (incl. zero)")
ax.set_title("Finite recoding screen", loc="left", weight="bold", fontsize=9.1)
ax.set_ylim(0, 22500)
ax.grid(axis="y", color="#d8dee5", linewidth=0.8)
ax.set_axisbelow(True)
ax.spines[["top", "right"]].set_visible(False)
for b, n, st in zip(bar, seeds, steps):
    ax.text(b.get_x()+b.get_width()/2, n+450, f"{n:,}\n{st} steps", ha="center", va="bottom", fontsize=7.6)

ax = axes[1]
y = list(range(len(records)))
for yi, ratio, (lo, hi) in zip(y, ratios, intervals):
    ax.errorbar([ratio], [yi], xerr=[[ratio-lo], [hi-ratio]], fmt="o", capsize=3.5,
                color="#315f83", markersize=5.5, linewidth=1.7)
ax.axvline(1, color="#565c63", linestyle="--", linewidth=1.2)
ax.set_yticks(y, [r[0] for r in records])
ax.invert_yaxis()
ax.set_xlim(0.90, 3.45)
ax.set_xlabel("Reference / candidate time ratio (95% paired bootstrap interval)")
ax.set_title("Tier 1 panels; 16 pairs per row", loc="left", weight="bold", fontsize=9.1)
ax.grid(axis="x", color="#d8dee5", linewidth=0.8)
ax.spines[["top", "right", "left"]].set_visible(False)
for yi, ratio, (lo, hi) in zip(y, ratios, intervals):
    ax.text(ratio+0.04, yi, f"{ratio:.3f} [{lo:.3f}, {hi:.3f}]", va="center", fontsize=7.4)
fig.suptitle("Radix size trades cold setup against prepared throughput", x=0.055,
             ha="left", fontsize=11.2, weight="bold")
fig.text(0.055, 0.02,
         "One RunPod instance thyvmdqmzsz5ik, CPU 40; A/A gates passed. Ratios compare adjacent k values only.",
         fontsize=7.6, color="#4a4a4a")
fig.tight_layout(rect=(0, 0.08, 1, 0.89))
fig.savefig(OUT / "sparse-radix-family-evidence.svg", bbox_inches="tight")
fig.savefig(OUT / "sparse-radix-family-evidence.png", dpi=180, bbox_inches="tight")
trim_svg(OUT / "sparse-radix-family-evidence.svg")
plt.close(fig)
print("rendered sparse radix-family method diagram and receipt-derived graphs")
