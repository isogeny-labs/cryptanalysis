#!/usr/bin/env python3
"""Render scalar-local digit synthesis from committed run audit receipts."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
COLD = json.loads((HERE / "tier1-tau32-demand-cold-cpu40-audit.json").read_text())
FULL = json.loads((HERE / "tier1-tau32-demand-full-replay-cpu40-audit.json").read_text())
OUT = HERE / "on-demand-digit-figures"
OUT.mkdir(exist_ok=True)


def trim_svg(path: Path) -> None:
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.2})
fig, ax = plt.subplots(figsize=(8.6, 3.3))
ax.set_xlim(0, 8.6)
ax.set_ylim(0, 3.3)
ax.axis("off")
stages = [
    (0.12, "Scalar", "one frozen input", "#eef4fa"),
    (1.83, "Recoding", "20 exact pair\nquotient steps", "#f1f4e8"),
    (3.54, "Select", "unique signed digits\nplus terminal", "#f8f0e8"),
    (5.25, "Synthesize", "materialize selected\npoints at G", "#f3eef8"),
    (6.96, "Evaluate", "Horner chain\nand output check", "#eef4fa"),
]
for x, title, body, color in stages:
    box = plt.Rectangle((x, 0.95), 1.52, 1.24, linewidth=1.2,
                        edgecolor="#274060", facecolor=color, joinstyle="round")
    ax.add_patch(box)
    ax.text(x+0.76, 1.76, title, ha="center", va="center", weight="bold", color="#18324d", fontsize=8.3)
    ax.text(x+0.76, 1.30, body, ha="center", va="center", linespacing=1.3, fontsize=7.4)
for x in (1.69, 3.40, 5.11, 6.82):
    ax.annotate("", xy=(x+0.13, 1.57), xytext=(x, 1.57),
                arrowprops={"arrowstyle": "-|>", "color": "#536b83", "lw": 1.1})
ax.text(4.3, 2.86, "Scalar-local `31+32τ` digit synthesis", ha="center", weight="bold", fontsize=11.4)
ax.text(4.3, 0.40, "At most 22 selected entries in the tested inputs; selection size and work depend on the scalar.",
        ha="center", fontsize=7.8, color="#8a3e32")
fig.tight_layout()
fig.savefig(OUT / "on-demand-digit-method.svg", bbox_inches="tight")
fig.savefig(OUT / "on-demand-digit-method.png", dpi=180, bbox_inches="tight")
trim_svg(OUT / "on-demand-digit-method.svg")
plt.close(fig)

cold = COLD["comparison"]
full_rows = FULL["results"]
fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8), gridspec_kw={"width_ratios": [1, 1]})
ax = axes[0]
means = [cold["reference_cold_ms_mean"], cold["candidate_cold_ms_mean"]]
labels = ["Full-table k=5", "Scalar-local"]
bars = ax.bar(labels, means, color=["#8ca6bd", "#315f83"], width=0.60)
ax.set_ylabel("Cold preparation + one scalar (ms)")
ax.set_title("Tier 1 cold paired panel", loc="left", weight="bold", fontsize=9.0)
ax.set_ylim(0, 76)
ax.grid(axis="y", color="#d8dee5", linewidth=0.8)
ax.set_axisbelow(True)
ax.spines[["top", "right"]].set_visible(False)
for bar, mean in zip(bars, means):
    ax.text(bar.get_x()+bar.get_width()/2, mean+1.0, f"{mean:.2f} ms",
            ha="center", va="bottom", fontsize=8.2)
ax.text(0.5, 0.94,
        f"Ref/candidate {cold['qualified_cold_ratio']:.3f}× [{cold['paired_bootstrap95_by_repeat'][0]:.3f}, {cold['paired_bootstrap95_by_repeat'][1]:.3f}]; n=16 pairs",
        transform=ax.transAxes, ha="center", va="top", fontsize=7.5, color="#18324d")

ax = axes[1]
times = [r["online_ms"]/1000 for r in full_rows]
bars = ax.bar(["Arm 1", "Arm 2"], times, color=["#8ca6bd", "#315f83"], width=0.60)
ax.set_ylabel("Full 12,288-output replay (s)")
ax.set_title("Correctness A/A replay", loc="left", weight="bold", fontsize=9.0)
ax.set_ylim(0, 48)
ax.grid(axis="y", color="#d8dee5", linewidth=0.8)
ax.set_axisbelow(True)
ax.spines[["top", "right"]].set_visible(False)
for bar, sec in zip(bars, times):
    ax.text(bar.get_x()+bar.get_width()/2, sec+0.7, f"{sec:.3f} s",
            ha="center", va="bottom", fontsize=8.2)
ax.text(0.5, 0.94, "Both arms checked 12,288 outputs; A/A only, no speed comparison.",
        transform=ax.transAxes, ha="center", va="top", fontsize=7.4, color="#4a4a4a")
fig.suptitle("Scalar-local digit synthesis: separate cold and full-stream evidence", x=0.06,
             ha="left", fontsize=10.7, weight="bold")
fig.text(0.06, 0.02, "Same RunPod instance thyvmdqmzsz5ik, CPU 40. Candidate selected-entry count ≤22 in both frozen inputs.",
         fontsize=7.6, color="#4a4a4a")
fig.tight_layout(rect=(0, 0.08, 1, 0.87))
fig.savefig(OUT / "on-demand-digit-evidence.svg", bbox_inches="tight")
fig.savefig(OUT / "on-demand-digit-evidence.png", dpi=180, bbox_inches="tight")
trim_svg(OUT / "on-demand-digit-evidence.svg")
plt.close(fig)
print("rendered scalar-local digit method diagram and audit-derived timing graph")
