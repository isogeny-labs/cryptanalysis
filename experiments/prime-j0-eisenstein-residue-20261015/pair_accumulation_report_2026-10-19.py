#!/usr/bin/env python3
"""Render the pair-accumulation diagnostic from its audited receipt."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
RECEIPT = json.loads((HERE / "pair-accumulation-audit.json").read_text())
OUT = HERE / "pair-accumulation-figures"
OUT.mkdir(exist_ok=True)


def trim_svg(path: Path) -> None:
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})

fig, ax = plt.subplots(figsize=(10, 3.1))
ax.set_xlim(0, 10)
ax.set_ylim(0, 3)
ax.axis("off")
labels = [
    (0.25, "Prepare", "28,825,228 B retained\n4,900.577 ms diagnostic"),
    (3.65, "Pair-field online", "12,288 checked outputs\n1,036.845 ms diagnostic"),
    (7.05, "Verify", "Exact point replay\nreceipt status: verified"),
]
for x, title, body in labels:
    box = FancyBboxPatch((x, 0.65), 2.7, 1.55, boxstyle="round,pad=0.08",
                         linewidth=1.4, edgecolor="#274060", facecolor="#eef4fa")
    ax.add_patch(box)
    ax.text(x + 1.35, 1.75, title, ha="center", va="center", weight="bold", color="#18324d")
    ax.text(x + 1.35, 1.2, body, ha="center", va="center", linespacing=1.45)
for x in (3.0, 6.4):
    ax.add_patch(FancyArrowPatch((x, 1.42), (x + 0.55, 1.42), arrowstyle="-|>",
                                 mutation_scale=16, linewidth=1.4, color="#536b83"))
ax.text(5, 2.65, "Balanced Eisenstein-pair accumulation diagnostic", ha="center",
        fontsize=13, weight="bold")
ax.text(5, 0.18, "Preparation and online timings are separate phases of the same local diagnostic; neither is a Tier 1 comparison.",
        ha="center", fontsize=8.5, color="#4a4a4a")
fig.tight_layout()
fig.savefig(OUT / "pair-accumulation-pipeline.svg", bbox_inches="tight")
fig.savefig(OUT / "pair-accumulation-pipeline.png", dpi=180, bbox_inches="tight")
trim_svg(OUT / "pair-accumulation-pipeline.svg")
plt.close(fig)

fig, ax = plt.subplots(figsize=(8.3, 4.5))
names = ["Table preparation", "Online accumulation"]
values = [RECEIPT["preparation_ms_diagnostic"], RECEIPT["online_ms_diagnostic"]]
colors = ["#8ca6bd", "#315f83"]
bars = ax.barh(names, values, color=colors, height=0.56)
ax.invert_yaxis()
ax.set_xlabel("Elapsed time (ms; diagnostic, unisolated local run)")
ax.set_title("Pair-field accumulation: phase costs", loc="left", weight="bold", pad=12)
ax.grid(axis="x", color="#d8dee5", linewidth=0.8)
ax.set_axisbelow(True)
ax.spines[["top", "right", "left"]].set_visible(False)
for bar, value in zip(bars, values):
    ax.text(value + max(values) * 0.018, bar.get_y() + bar.get_height()/2,
            f"{value:,.3f} ms", va="center", fontsize=10, weight="bold")
ax.set_xlim(0, max(values) * 1.28)
fig.text(0.12, 0.025,
         f"n={RECEIPT['count']:,} outputs; exact replay verified. Phases shown separately; no paired interval or Tier 1 claim.",
         fontsize=8.5, color="#4a4a4a")
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(OUT / "pair-accumulation-phase-costs.svg", bbox_inches="tight")
fig.savefig(OUT / "pair-accumulation-phase-costs.png", dpi=180, bbox_inches="tight")
trim_svg(OUT / "pair-accumulation-phase-costs.svg")
plt.close(fig)

print("rendered pair-accumulation pipeline and phase costs from audited receipt")
