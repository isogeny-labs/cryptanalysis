#!/usr/bin/env python3
"""Plot committed qualified Tier 1 panels; this script does not run benchmarks."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PANELS = [
    ("18-position / 140−τ", "tier1-18v17-96-analysis.json"),
    ("16-position / 140−τ", "tier1-16v17-analysis.json"),
]

def main():
    labels, values, lows, highs, ops = [], [], [], [], []
    for label, filename in PANELS:
        d = json.loads((ROOT / filename).read_text())
        if d.get("aggregate_status") != "qualified" or d.get("aa_failed_comparisons"):
            raise SystemExit(f"panel is not A/A-qualified: {filename}")
        lo, hi = d["paired_bootstrap95_by_repeat"]
        labels.append(label)
        values.append(d["qualified_comparison_ratio"])
        lows.append(d["qualified_comparison_ratio"] - lo)
        highs.append(hi - d["qualified_comparison_ratio"])
        ops.append(f"48 pairs; {d['operations_per_arm']:,} ops/arm")
    fig, ax = plt.subplots(figsize=(7.3, 4.4), layout="constrained")
    y = list(range(len(labels)))
    ax.axvline(1, color="#444", linewidth=1, linestyle="--", label="equal throughput")
    ax.errorbar(values, y, xerr=[lows, highs], fmt="o", capsize=5, color="#176b87", ecolor="#176b87", label="paired median ± repeat-bootstrap 95% interval")
    ax.set_xlim(.94, 1.05)
    ax.set_yticks(y, [f"{label}\n{count}" for label, count in zip(labels, ops)])
    ax.invert_yaxis()
    ax.set_xlabel("140−τ / reference hot-table throughput ratio")
    ax.set_title("A/A-qualified 96-pass Tier 1 panels (one RunPod allocation)")
    ax.text(.5, -.20, "96 arms and 48 pairs per panel; intervals span repetitions on this allocation only.", transform=ax.transAxes, ha="center", fontsize=8.5)
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="x", alpha=.25)
    for ext in ("svg", "pdf"):
        fig.savefig(HERE / f"radix-140-throughput.{ext}")
    plt.close(fig)

if __name__ == "__main__":
    main()
