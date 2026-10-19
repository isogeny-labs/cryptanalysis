#!/usr/bin/env python3
"""Render the frozen distinct-input affine stream panel from its audit JSON."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "tier1-affine-stream-cpu40-audit.json").read_text())
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)

def normalize_svg(path: Path) -> None:
    """Remove generator-added trailing whitespace for clean, stable diffs."""
    text = path.read_text(encoding="utf-8")
    path.write_text("\n".join(line.rstrip() for line in text.splitlines()) + "\n", encoding="utf-8")


plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "svg.hashsalt": "cryptanalysis-affine-stream-panel-v1",
    "figure.facecolor": "white",
})

fig, ax = plt.subplots(figsize=(8.2, 4.5), constrained_layout=True)
labels = ["Ordinary affine\n(reference)", "Full two-x\n(candidate)"]
values = [DATA["reference_online_ms_mean"], DATA["candidate_online_ms_mean"]]
colors = ["#73879c", "#177e89"]
bars = ax.bar(labels, values, color=colors, width=0.58)
ax.set_ylabel("Mean online time for 12,288 outputs (ms)\n(lower is faster)")
ax.set_title("Fresh-input affine batch throughput")
ax.set_ylim(0, max(values) * 1.5)
ax.grid(axis="y", alpha=0.22)
ax.set_axisbelow(True)
for bar, value in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width()/2, value + 0.8, f"{value:.3f} ms",
            ha="center", va="bottom", fontweight="bold")
ratio = DATA["qualified_comparison_ratio"]
lo, hi = DATA["paired_bootstrap95_by_repeat"]
ax.text(0.5, 0.91,
        f"Paired ordinary/full-two-x ratio {ratio:.4f}×  (bootstrap 95% CI {lo:.4f}–{hi:.4f})\n"
        "16 comparison pairs; 48 total paired repetitions; all adjacent A/A gates passed",
        transform=ax.transAxes, ha="center", va="top", fontsize=8.5,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "#f1f5f8", "edgecolor": "#d2dce5"})
ax.text(0.5, -0.20,
        "CPU 40 · frozen 12,288 distinct-scalar arithmetic-progression fixture · table build excluded",
        transform=ax.transAxes, ha="center", fontsize=8, color="#405064")
fig.savefig(OUT / "tier1-throughput.svg", bbox_inches="tight", metadata={"Date": None})
normalize_svg(OUT / "tier1-throughput.svg")
fig.savefig(OUT / "tier1-throughput.pdf", bbox_inches="tight", metadata={"CreationDate": None, "ModDate": None})
plt.close(fig)

fig, ax = plt.subplots(figsize=(9.2, 3.4), constrained_layout=True)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
boxes = [
    (0.04, 0.39, 0.24, 0.34, "128 validated base scalars\nand secp256k1 points", "#e9eef4"),
    (0.38, 0.39, 0.24, 0.34, "96 batches × 128\nunique scalars", "#e6f3f1"),
    (0.72, 0.39, 0.24, 0.34, "Both table variants\nverify every output", "#fff1df"),
]
for x, y, w, h, label, color in boxes:
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=color, edgecolor="#536273", linewidth=1.2, zorder=2))
    ax.text(x+w/2, y+h/2, label, ha="center", va="center", fontsize=10, zorder=3)
for start, end in [(0.28, 0.38), (0.62, 0.72)]:
    ax.annotate("", xy=(end, 0.56), xytext=(start, 0.56),
                arrowprops={"arrowstyle": "->", "lw": 1.6, "color": "#536273"})
ax.text(0.5, 0.93, "Frozen distinct-input panel: fixture generation → timed batches → correctness replay",
        ha="center", va="center", fontsize=11, fontweight="bold")
ax.text(0.5, 0.13,
        "The fixture is a deterministic scalar arithmetic progression derived from a checked base panel.\n"
        "This supports a batch-throughput result for this input law; uniform random scalars and single-scalar latency remain unmeasured here.",
        ha="center", va="center", fontsize=8.5, color="#405064")
fig.savefig(OUT / "fixture-flow.svg", bbox_inches="tight", metadata={"Date": None})
normalize_svg(OUT / "fixture-flow.svg")
fig.savefig(OUT / "fixture-flow.pdf", bbox_inches="tight", metadata={"CreationDate": None, "ModDate": None})
plt.close(fig)
