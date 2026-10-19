#!/usr/bin/env python3
"""Render committed, A/A-qualified paired batch panels; never runs a benchmark."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PANELS = [
    ("18-pos / 190−τ", "tier1-batch64-analysis.json", "qualified_comparison_ratio", "paired_bootstrap95_by_repeat"),
    ("18-pos / 233−τ", "tier1-batch-analysis.json", "qualified_comparison_ratio", "paired_bootstrap95_by_repeat"),
    ("233−τ / 190−τ", "tier1-batch190-analysis.json", "qualified_comparison_ratio", "paired_bootstrap95_by_repeat"),
]

def main():
    labels, values, lows, highs, counts = [], [], [], [], []
    for label, filename, metric, interval in PANELS:
        d = json.loads((ROOT / filename).read_text())
        if d.get("measurement_tier") != "tier1_instance" or d.get("aa_failed_comparisons"):
            raise SystemExit(f"panel is not A/A-qualified: {filename}")
        lo, hi = d[interval]
        labels.append(label)
        values.append(d[metric])
        lows.append(d[metric] - lo)
        highs.append(hi - d[metric])
        counts.append(f"{d['completed_pairs']} pairs; {d['operations_per_arm']:,} ops/arm")
    fig, ax = plt.subplots(figsize=(7.4, 4.8), layout="constrained")
    y = list(range(len(labels)))
    ax.axvline(1.0, color="#444", linewidth=1, linestyle="--", label="equal throughput")
    ax.errorbar(values, y, xerr=[lows, highs], fmt="o", capsize=5, color="#176b87", ecolor="#176b87", label="paired median ± repeat-bootstrap 95% interval")
    ax.set_yticks(y, [f"{label}\n{count}" for label, count in zip(labels, counts)])
    ax.invert_yaxis()
    ax.set_xlim(.995, 1.115)
    ax.set_xlabel("Candidate / reference hot-table throughput ratio")
    ax.set_title("Tier 1 paired batch panels (one RunPod allocation)")
    ax.text(.5, -.19, "All 96 arms and 48 pairs passed each adjacent A/A gate.\nIntervals cover repeats on this allocation only.", transform=ax.transAxes, ha="center", fontsize=8.5)
    ax.grid(axis="x", alpha=.25)
    ax.legend(loc="lower right", fontsize=8)
    for ext in ("svg", "pdf"):
        fig.savefig(HERE / f"radix-throughput.{ext}")
    plt.close(fig)

if __name__ == "__main__":
    main()
