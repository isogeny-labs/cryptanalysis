#!/usr/bin/env python3
"""Regenerate the fixed-14 payload and measured Tier 1 figures."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "fixed14-ordered-prime-norm"
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = Path(__file__).resolve().parent
OUT = HERE / "figures"


def read_json(name):
    return json.loads((HERE / name).read_text())


def save_figure(fig, stem):
    for ext in ("svg", "pdf"):
        metadata = {"Creator": "visuals.py"}
        if ext == "svg":
            metadata["Date"] = None
        else:
            metadata["CreationDate"] = None
            metadata["ModDate"] = None
        path = OUT / f"{stem}.{ext}"
        fig.savefig(path, metadata=metadata)
        if ext == "svg":
            lines = path.read_text().splitlines()
            path.write_text("\n".join(line.rstrip() for line in lines) + "\n")


def payload_figure():
    screen = read_json("screen14.json")
    fixed = screen["fixed_payload_minimum"]
    ordered = screen["local_payload_minimum"]
    values = [fixed["point_payload_bytes"] / 1e6,
              ordered["point_payload_bytes"] / 1e6]
    labels = ["Fixed 371−τ × 14", "394, 380, 380, 371−τ × 11"]

    fig, ax = plt.subplots(figsize=(8.4, 3.6), constrained_layout=True)
    colors = ["#55728c", "#4b8a73"]
    bars = ax.barh(labels[::-1], values[::-1], color=colors[::-1], height=0.55)
    ax.set_xlim(0, max(values) * 1.22)
    ax.set_xlabel("Direct point payload (MB; 64 bytes per point)", fontsize=11)
    ax.set_title("Direct point payload by 14-position prime-norm schedule", fontsize=12, pad=20)
    ax.set_ylim(-0.5, 2.0)
    ax.text(0.5, 0.97,
            "Ordered screen saves 46,784 bytes (0.210%); native execution unmeasured",
            transform=ax.transAxes, ha="center", va="top", fontsize=9)
    ax.grid(axis="x", alpha=0.22)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, values[::-1]):
        ax.text(value + max(values) * 0.012, bar.get_y() + bar.get_height()/2,
                f"{value:.6f} MB", va="center", fontsize=10)
    save_figure(fig, "ordered-payload")
    plt.close(fig)


def tier1_figure():
    result = read_json("tier1-fixed14-analysis.json")
    candidate = result["candidate_online_ms_mean"]
    reference = result["reference_online_ms_mean"]
    preparation_ratio = (result["candidate_preparation_ms_mean"] /
                         result["reference_preparation_ms_mean"])
    retained_ratio = (result["candidate_retained_bytes"][0] /
                      result["reference_retained_bytes"][0])
    ratio = result["qualified_comparison_ratio"]
    low, high = result["paired_bootstrap95_by_repeat"]

    fig, (ax, stats) = plt.subplots(
        1, 2, figsize=(7.2, 3.8), gridspec_kw={"width_ratios": [1.2, 1]},
        constrained_layout=True)
    ax.errorbar([ratio], [0], xerr=[[ratio-low], [high-ratio]], fmt="o",
                color="#287a60", capsize=5, markersize=7, linewidth=2)
    ax.axvline(1.0, color="#666666", linestyle="--", linewidth=1)
    ax.set_xlim(0.99, 1.04)
    ax.set_ylim(-0.65, 0.65)
    ax.set_yticks([])
    ax.set_xlabel("Reference / candidate online time", fontsize=10)
    ax.set_title("Tier 1 paired throughput ratio", fontsize=12)
    ax.grid(axis="x", alpha=0.22)
    ax.text(ratio, 0.18, f"{ratio:.6f}×\n95% [{low:.6f}, {high:.6f}]",
            ha="center", va="bottom", fontsize=10)

    stats.axis("off")
    lines = [
        ("Online mean / 12,288 outputs", f"{candidate:.3f} ms vs {reference:.3f} ms"),
        ("Table preparation", f"{result['candidate_preparation_ms_mean']:.1f} ms vs "
         f"{result['reference_preparation_ms_mean']:.1f} ms ({preparation_ratio:.2f}×)"),
        ("Retained native table", f"{result['candidate_retained_bytes'][0]/1e6:.3f} MB vs "
         f"{result['reference_retained_bytes'][0]/1e6:.3f} MB ({retained_ratio:.2f}×)"),
        ("Panel", "48 pairs; all adjacent A/A gates passed"),
    ]
    y = 0.92
    for label, value in lines:
        stats.text(0.02, y, label, fontsize=10, weight="bold", va="top")
        stats.text(0.02, y-0.08, value, fontsize=10, va="top")
        y -= 0.23
    stats.set_title("Fixed 371−τ vs 268−τ reference", pad=8, fontsize=11)
    save_figure(fig, "tier1-throughput")
    plt.close(fig)


def process_diagram():
    fig, ax = plt.subplots(figsize=(9.2, 3.2), constrained_layout=True)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3.2)
    ax.axis("off")

    boxes = [
        (0.15, 1.72, 2.0, 0.9, "Exact residue screen\n50 prime-norm radices"),
        (2.65, 1.72, 2.0, 0.9, "Four coordinate-search\nstarts; local result only"),
        (5.15, 1.72, 2.0, 0.9, "Ordered schedule\n394, 380, 380, 371×11"),
        (7.65, 1.72, 2.0, 0.9, "14 exact quotient steps\nterminal radius < 200"),
    ]
    for x, y, w, h, label in boxes:
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                               facecolor="#edf3f6", edgecolor="#3c6478",
                               linewidth=1.2)
        ax.add_patch(patch)
        ax.text(x+w/2, y+h/2, label, ha="center", va="center", fontsize=10)
    for start, end in ((2.16, 2.63), (4.66, 5.13), (7.16, 7.63)):
        ax.annotate("", xy=(end, 2.17), xytext=(start, 2.17),
                    arrowprops={"arrowstyle": "->", "lw": 1.3, "color": "#526b77"})
    ax.text(5, 1.27,
            "Separate native measurement: fixed 371−τ × 14 vs fixed 268−τ × 15\n"
            "1.020033× online throughput ratio; ordered schedule has not been measured",
            ha="center", va="center", fontsize=10, color="#222222",
            bbox={"boxstyle": "round,pad=0.45", "facecolor": "#f7f1df",
                  "edgecolor": "#b58a31"})
    ax.text(5, 0.35,
            "The residue/radius screen and the Tier 1 timing panel answer different questions.",
            ha="center", va="center", fontsize=9, color="#555555")
    save_figure(fig, "search-and-measurement")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    payload_figure()
    tier1_figure()
    process_diagram()
