#!/usr/bin/env python3
"""Render report figures from the frozen two-x panel audit."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "tier1-two-x-cpu40-audit.json").read_text())
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "svg.hashsalt": "cryptanalysis-two-x-panel-v1",
                     "figure.facecolor": "white"})

def save_svg(fig, name):
    path = OUT / name
    fig.savefig(path, bbox_inches="tight", metadata={"Date": None})
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")

fig, ax = plt.subplots(figsize=(8.2, 4.5), constrained_layout=True)
labels = ["Affine-layer\n(reference)", "Two-x table\n(candidate)"]
values = [DATA["reference_online_ms_mean"], DATA["candidate_online_ms_mean"]]
bars = ax.bar(labels, values, color=["#73879c", "#177e89"], width=0.58)
ax.set_ylabel("Mean online time for 12,288 outputs (ms)\n(lower is faster)")
ax.set_title("Two-coordinate affine rotation table")
ax.set_ylim(0, max(values) * 1.5)
ax.grid(axis="y", alpha=0.22)
ax.set_axisbelow(True)
for bar, value in zip(bars, values):
    ax.text(bar.get_x()+bar.get_width()/2, value+0.8, f"{value:.3f} ms", ha="center", va="bottom", fontweight="bold")
lo, hi = DATA["paired_bootstrap95_by_repeat"]
ax.text(0.5, 0.91, f"Paired ratio {DATA['qualified_comparison_ratio']:.4f}×  (bootstrap 95% CI {lo:.4f}–{hi:.4f})\n16 comparison pairs; all adjacent A/A gates passed",
        transform=ax.transAxes, ha="center", va="top", fontsize=8.5,
        bbox={"boxstyle":"round,pad=0.35", "facecolor":"#f1f5f8", "edgecolor":"#d2dce5"})
ax.text(0.5, -0.20, "CPU 40 · frozen 12,288-scalar fixture · table preparation reported separately",
        transform=ax.transAxes, ha="center", fontsize=8, color="#405064")
save_svg(fig, "tier1-throughput.svg")
fig.savefig(OUT / "tier1-throughput.pdf", bbox_inches="tight", metadata={"CreationDate": None, "ModDate": None})
plt.close(fig)

fig, ax = plt.subplots(figsize=(9.2, 3.4), constrained_layout=True)
ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
boxes=[(0.04,"Affine-layer\ntable stores (x,y)","#e9eef4"),(0.38,"Two-x table stores\n(x, x+βx, y)","#e6f3f1"),(0.72,"β rotations use\nfield additions", "#fff1df")]
for x,label,color in boxes:
    ax.add_patch(plt.Rectangle((x,.39),.24,.34,facecolor=color,edgecolor="#536273",linewidth=1.2,zorder=2))
    ax.text(x+.12,.56,label,ha="center",va="center",fontsize=10,zorder=3)
for a,b in [(.28,.38),(.62,.72)]:
    ax.annotate("",xy=(b,.56),xytext=(a,.56),arrowprops={"arrowstyle":"->","lw":1.6,"color":"#536273"})
ax.text(.5,.93,"Representation change replaces constant-multiply leaf rotations",ha="center",fontsize=11,fontweight="bold")
ax.text(.5,.13,"The identity follows from β²+β+1=0. The panel measures prepared-table batch throughput;\ncurve-specific correctness is checked by the native replay and every timed output is verified.",ha="center",fontsize=8.5,color="#405064")
save_svg(fig,"two-x-dataflow.svg")
fig.savefig(OUT / "two-x-dataflow.pdf",bbox_inches="tight",metadata={"CreationDate":None,"ModDate":None})
plt.close(fig)
