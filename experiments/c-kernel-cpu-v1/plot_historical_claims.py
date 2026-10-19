#!/usr/bin/env python3
"""Plot only the historical summary values copied from PR #880's body."""
import csv
from pathlib import Path
import matplotlib.pyplot as plt

root = Path(__file__).parent
rows = list(csv.DictReader((root / "historical-claims.csv").open()))
fig, axes = plt.subplots(1, 2, figsize=(12, 5.6), constrained_layout=True)
fig.suptitle("PR #880 historical summaries — unverified, raw records absent", fontsize=15, weight="bold")

ax = axes[0]
labels = ["C PI, one thread\n95% CI", "C rho, two threads\n95% CI", "Callgrind Ir PI\npoint only"]
select = rows[:3]
for y, (label, row) in enumerate(zip(labels, select)):
    lo, hi = float(row["low"]), float(row["high"])
    center = 1.089 if y == 2 else (1.099 if y == 0 else 1.152)
    ax.plot([lo, hi], [y, y], color="#4178a8", lw=3, solid_capstyle="round")
    ax.scatter([center], [y], s=45, color="#173d5d", zorder=3)
    ax.text(hi + 0.012, y, f"{center:.3f}×" + (f" [{lo:.3f}, {hi:.3f}]" if y < 2 else ""), va="center", fontsize=9)
ax.axvline(1, color="#777", ls="--", lw=1)
ax.set_yticks(range(3), labels)
ax.set_xlim(0.97, 1.23)
ax.set_xlabel("Reported ratio (×); values transcribed from PR body")
ax.grid(axis="x", alpha=0.2)
ax.set_title("C library summaries")

ax = axes[1]
for y, (label, row) in enumerate([
    ("Original CPU walk", rows[3]),
    ("Candidate CPU walk", rows[4]),
]):
    lo, hi = float(row["low"]), float(row["high"])
    ax.plot([lo, hi], [y, y], color="#bf7e38", lw=8, solid_capstyle="round")
    ax.scatter([lo, hi], [y, y], color="#7a4c1d", s=28, zorder=3)
    ax.text(hi + 0.12, y, f"{lo:.2f}–{hi:.2f}", va="center", fontsize=9)
ax.set_yticks([0, 1], ["Original CPU walk", "Candidate CPU walk"])
ax.set_xlim(4.4, 9.2)
ax.set_xlabel("Reported throughput (M iterations/s)")
ax.grid(axis="x", alpha=0.2)
ax.set_title("ECC2K-130 one-worker summaries")

fig.text(0.5, -0.015,
         "Historical summaries only. No host receipt, raw paired rows, original commands, or independent replay. Not a new measurement.",
         ha="center", fontsize=9, color="#7b2222")
for ext in ("png", "svg"):
    fig.savefig(root / f"historical-claims.{ext}", dpi=180, bbox_inches="tight")
