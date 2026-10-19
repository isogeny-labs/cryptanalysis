"""Editable figures for the radix-128 Eisenstein Montgomery report.

Reads only the frozen pair ledger and its independent audit summary; it does
not rerun arithmetic or modify any study receipt.
"""
from json import loads
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
OUT = HERE / "eisenstein-montgomery-report-figures"
OUT.mkdir(exist_ok=True)
JOB = "273359b6d2724700ad59ea1ddc978da8"
PAIRS = [loads(line) for line in (HERE / JOB / "pairs.jsonl").read_text().splitlines()]
AUDIT = loads((HERE / "tier1-eisenstein-montgomery-cpu40-audit.json").read_text())
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})

fig, ax = plt.subplots(figsize=(9.2, 3.2))
ax.set_xlim(0, 10)
ax.set_ylim(0, 3.2)
ax.axis("off")
ax.text(5, 2.92, "Radix-128 quotient-field reduction", ha="center", fontsize=12, weight="bold")
boxes = [
    (0.15, 1.2, 1.65, 0.9, "Raw pair product\n(x, y)"),
    (2.1, 1.2, 1.8, 0.9, "Adjugate numerators\nN₁, N₂"),
    (4.2, 1.2, 1.8, 0.9, "Centered quotients\nqᵢ = −p⁻¹Nᵢ mod 2¹²⁸"),
    (6.3, 1.2, 1.7, 0.9, "Exact division\nby 2¹²⁸"),
    (8.3, 1.2, 1.55, 0.9, "Canonical bound\ncorrection if needed"),
]
for x, y, w, h, label in boxes:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=.04", fc="#e9f1fa", ec="#315b7d", lw=1.2))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=8)
for a, b in [(1.8, 2.1), (3.9, 4.2), (6.0, 6.3), (8.0, 8.3)]:
    ax.add_patch(FancyArrowPatch((a, 1.65), (b, 1.65), arrowstyle="-|>", mutation_scale=11, color="#315b7d", lw=1.2))
ax.text(5, .65, "The adjugate numerators and centered quotients make both coordinates divisible by the radix.", ha="center", fontsize=8.5)
ax.text(5, .28, "Canonical correction is required only when the divided pair exceeds the 128-bit coordinate bound.", ha="center", fontsize=8, color="#555")
fig.tight_layout()
fig.savefig(OUT / "montgomery-method.svg", bbox_inches="tight")
fig.savefig(OUT / "montgomery-method.png", dpi=180, bbox_inches="tight")
plt.close(fig)

ratios = [row["speedup"] for row in PAIRS if row["case"] == "compare"]
assert len(ratios) == 16 and all(row["status"] == "valid" for row in PAIRS if row["case"] == "compare")
median = AUDIT["qualified_comparison_ratio"]
low, high = AUDIT["paired_bootstrap95_by_repeat"]
fig, ax = plt.subplots(figsize=(7.6, 3.8))
ax.axvspan(low, high, color="#3d7c91", alpha=.14, label="Paired bootstrap 95% interval")
ax.axvline(1.0, color="#555", linestyle="--", linewidth=1, label="Equal elapsed time")
for i, value in enumerate(ratios, 1):
    ax.scatter(value, i, color="#3d7c91", s=30, zorder=3)
ax.axvline(median, color="#ad6b4e", linewidth=1.5, label=f"Median {median:.3f}×")
ax.set_ylim(0, 17)
ax.set_yticks([1, 4, 8, 12, 16])
ax.set_xlabel("Fixed-limb Solinas / radix-128 Montgomery elapsed time")
ax.set_ylabel("Comparison repeat")
ax.set_title("Tier 1 same-input paired results · 16 comparison pairs")
ax.grid(axis="x", alpha=.22)
ax.legend(loc="lower right", fontsize=8)
ax.text(.5, -.2, "Ratios above 1 favor Montgomery; all adjacent A/A controls passed the frozen gate.", transform=ax.transAxes, ha="center", fontsize=8)
fig.tight_layout()
fig.savefig(OUT / "montgomery-tier1-ratios.svg", bbox_inches="tight")
fig.savefig(OUT / "montgomery-tier1-ratios.png", dpi=180, bbox_inches="tight")
plt.close(fig)
