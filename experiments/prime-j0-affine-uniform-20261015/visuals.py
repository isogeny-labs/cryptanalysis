#!/usr/bin/env python3
"""Regenerate figures for the SHAKE-derived affine-table panel."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "affine-uniform-tier1"
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = Path(__file__).resolve().parent
OUT = HERE / "figures"


def load(name):
    return json.loads((HERE / name).read_text())


def save(fig, stem):
    for ext in ("svg", "pdf"):
        path = OUT / f"{stem}.{ext}"
        metadata = {"Creator": "visuals.py"}
        if ext == "svg":
            metadata["Date"] = None
        else:
            metadata["CreationDate"] = None
            metadata["ModDate"] = None
        fig.savefig(path, metadata=metadata)
        if ext == "svg":
            lines = path.read_text().splitlines()
            path.write_text("\n".join(line.rstrip() for line in lines) + "\n")


def workflow():
    fig, ax = plt.subplots(figsize=(8.4, 3.6), constrained_layout=True)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3.8)
    ax.axis("off")
    boxes = [
        (0.2, 2.05, 2.15, 1.0, "Frozen 128-point base\nfixture SHA-256 seed"),
        (2.62, 2.05, 2.15, 1.0, "SHAKE256 counter stream\nreject invalid/duplicate"),
        (5.04, 2.05, 2.15, 1.0, "12,288 unique scalars\nindependent binary points"),
        (7.46, 2.05, 2.3, 1.0, "Same binary and inputs\naffine layer vs full two-x"),
    ]
    for x, y, w, h, label in boxes:
        shape = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                               facecolor="#edf3f6", edgecolor="#3c6478",
                               linewidth=1.2)
        ax.add_patch(shape)
        ax.text(x+w/2, y+h/2, label, ha="center", va="center", fontsize=10)
    for start, end in ((2.37, 2.60), (4.79, 5.02), (7.21, 7.44)):
        ax.annotate("", xy=(end, 2.55), xytext=(start, 2.55),
                    arrowprops={"arrowstyle": "->", "lw": 1.3, "color": "#526b77"})
    panel = FancyBboxPatch((1.2, 0.42), 7.6, 1.02,
                           boxstyle="round,pad=0.08", facecolor="#f7f1df",
                           edgecolor="#b58a31", linewidth=1.2)
    ax.add_patch(panel)
    ax.text(5, 0.93,
            "16 alternating comparison repeats · 48 pairs · adjacent A/A controls\n"
            "Time batch evaluation after table preparation; verify every output after timing",
            ha="center", va="center", fontsize=10)
    ax.text(5, 0.1, "Tier 1 cloud-instance batch throughput; physical-host exclusivity unverified",
            ha="center", va="center", fontsize=9, color="#555555")
    save(fig, "fixture-and-panel")
    plt.close(fig)


def measurement():
    result = load("tier1-affine-uniform-cpu40-audit.json")
    ratio = result["qualified_comparison_ratio"]
    low, high = result["paired_bootstrap95_by_repeat"]
    ref = result["reference_online_ms_mean"]
    cand = result["candidate_online_ms_mean"]
    prep_ratio = (result["candidate_preparation_ms_mean"] /
                  result["reference_preparation_ms_mean"])
    memory_ratio = (result["candidate_retained_bytes"][0] /
                    result["reference_retained_bytes"][0])

    fig, (ax, stats) = plt.subplots(
        1, 2, figsize=(7.2, 3.8), gridspec_kw={"width_ratios": [1.15, 1]},
        constrained_layout=True)
    ax.errorbar([ratio], [0], xerr=[[ratio-low], [high-ratio]], fmt="o",
                color="#287a60", capsize=5, markersize=7, linewidth=2)
    ax.axvline(1.0, color="#666666", linestyle="--", linewidth=1)
    ax.set_xlim(1.08, 1.19)
    ax.set_ylim(-0.65, 0.65)
    ax.set_yticks([])
    ax.set_xlabel("Ordinary-affine / full-two-x online time", fontsize=10)
    ax.set_title("Tier 1 paired batch-throughput ratio", fontsize=12)
    ax.grid(axis="x", alpha=0.22)
    ax.text(ratio, 0.18, f"{ratio:.6f}×\n95% [{low:.6f}, {high:.6f}]",
            ha="center", va="bottom", fontsize=10)

    stats.axis("off")
    rows = [
        ("Online mean / 12,288 outputs", f"{ref:.3f} ms vs {cand:.3f} ms"),
        ("Table preparation", f"{result['reference_preparation_ms_mean']:.1f} ms vs "
         f"{result['candidate_preparation_ms_mean']:.1f} ms ({prep_ratio:.3f}×)"),
        ("Retained table", f"{result['reference_retained_bytes'][0]/1e6:.3f} MB vs "
         f"{result['candidate_retained_bytes'][0]/1e6:.3f} MB ({memory_ratio:.3f}×)"),
        ("Panel", "48 pairs; all adjacent A/A gates passed"),
    ]
    y = 0.92
    for label, value in rows:
        stats.text(0.02, y, label, fontsize=10, weight="bold", va="top")
        stats.text(0.02, y-0.08, value, fontsize=10, va="top")
        y -= 0.23
    stats.set_title("Ordinary affine vs full two-x", pad=8, fontsize=11)
    save(fig, "tier1-throughput")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    workflow()
    measurement()
