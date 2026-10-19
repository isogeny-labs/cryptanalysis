#!/usr/bin/env python3
"""Render the frozen direct-versus-rolling RunPod panel from its committed analysis."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "tier1-analysis.json"
OUT = HERE

def main():
    d = json.loads(DATA.read_text())
    rows = d["per_case"]
    xs = [x["case_index"] + 1 for x in rows]
    ys = [x["median_direct_over_rolling"] for x in rows]
    lo = [y - x["min_direct_over_rolling"] for y, x in zip(ys, rows)]
    hi = [x["max_direct_over_rolling"] - y for y, x in zip(ys, rows)]
    fig, ax = plt.subplots(figsize=(7.2, 4.2), layout="constrained")
    ax.axhspan(d["aa_acceptance_range"][0], d["aa_acceptance_range"][1], color="#edf4fb", alpha=.8, label="A/A acceptance band (not a candidate CI)")
    ax.axhline(1, color="#444", linewidth=1, linestyle="--", label="equal wall time")
    ax.errorbar(xs, ys, yerr=[lo, hi], fmt="o", capsize=4, color="#176b87", ecolor="#176b87", label="per-scalar median; min–max observed")
    ax.set(xlabel="Frozen scalar case", ylabel="Direct / rolling online wall time", xticks=xs,
           title="Direct versus rolling orbit evaluator")
    ax.text(.01, -.24, "40 descriptive scalar comparisons; 5 A/A controls failed. Latency ranking is unqualified; no confidence interval is claimed.", transform=ax.transAxes, fontsize=8.5, wrap=True)
    ax.legend(loc="best", fontsize=8)
    ax.grid(axis="y", alpha=.25)
    for ext in ("svg", "pdf"):
        fig.savefig(OUT / f"direct-vs-rolling.{ext}")
    plt.close(fig)

if __name__ == "__main__":
    main()
