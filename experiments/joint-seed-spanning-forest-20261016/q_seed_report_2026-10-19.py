"""Editable method and operation-count figures for the Q-seed report."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent / "q-seed-report-figures"
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})

fig, ax = plt.subplots(figsize=(8.8, 3.1))
ax.set_xlim(0, 10)
ax.set_ylim(0, 3.2)
ax.axis("off")
ax.text(5, 2.92, "One-restart unit-root seed schedule", ha="center", fontsize=12, weight="bold")
boxes = [
    (0.25, 1.2, 1.7, 0.9, "Prepared Q powers\nshared input"),
    (2.5, 1.2, 1.7, 0.9, "Direct root\n(−2, 1)"),
    (4.75, 1.2, 1.7, 0.9, "Auxiliary vertices\n(−32, 19), (−2, 5)"),
    (7.0, 1.2, 2.5, 0.9, "21 requested Q seeds\n22 graph edges"),
]
for x, y, w, h, label in boxes:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=.04", fc="#e9f1fa", ec="#315b7d", lw=1.2))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=8.5)
for a, b in [(1.95, 2.5), (4.2, 4.75), (6.45, 7.0)]:
    ax.add_patch(FancyArrowPatch((a, 1.65), (b, 1.65), arrowstyle="-|>", mutation_scale=11, color="#315b7d", lw=1.2))
ax.text(5, .65, "16 unit rotations; four graph edges dispatch to mixed addition.", ha="center", fontsize=8.5)
ax.text(5, .28, "Diagram summarizes the frozen plan; shared powers and online evaluation are outside this count.", ha="center", fontsize=8, color="#555")
fig.tight_layout()
fig.savefig(OUT / "q-seed-method.svg", bbox_inches="tight")
fig.savefig(OUT / "q-seed-method.png", dpi=180, bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(7.4, 4.1))
labels = ["Cost-aware unit-root", "Earlier unit-root", "One-auxiliary", "Earlier refined"]
muls = [390, 394, 422, 437]
squares = [105, 106, 113, 117]
colors = ["#3d7c91", "#54899b", "#ad8050", "#ad6b4e"]
for label, x, y, color in zip(labels, muls, squares, colors):
    ax.scatter(x, y, s=75, color=color, zorder=3)
    ax.annotate(label, (x, y), xytext=(6, 5), textcoords="offset points", fontsize=8)
ax.set_xlim(380, 455)
ax.set_ylim(101, 121)
ax.set_xlabel("Modeled field multiplications")
ax.set_ylabel("Modeled field squares")
ax.set_title("One-restart Q-seed schedules · source-formula model")
ax.grid(alpha=.22)
ax.text(.5, -.17, "Lower-left is lower in both modeled counts; points are not elapsed-time measurements.", transform=ax.transAxes, ha="center", fontsize=8)
fig.tight_layout()
fig.savefig(OUT / "q-seed-cost-model.svg", bbox_inches="tight")
fig.savefig(OUT / "q-seed-cost-model.png", dpi=180, bbox_inches="tight")
plt.close(fig)
