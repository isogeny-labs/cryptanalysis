#!/usr/bin/env python3
"""Plot archived split/orbit tradeoff ratios; does not launch any benchmark."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "tier1-analysis.json"

def main():
    d = json.loads(DATA.read_text())
    if d.get("aggregate_status") != "qualified" or d.get("aa_failed_comparisons"):
        raise SystemExit("the archived panel is not A/A-qualified")
    metrics = [
        ("Hot-table throughput", d["split_over_orbit_throughput_median"], d["paired_bootstrap95_by_repeat"], "paired median; repeat-bootstrap 95% interval"),
        ("Retained table bytes", d["candidate_retained_bytes"][0]/d["reference_retained_bytes"][0], None, "145,808 / 4,178,836 bytes"),
        ("Table preparation time", d["candidate_preparation_ms_mean"]/d["reference_preparation_ms_mean"], None, "90.61 / 733.50 ms mean"),
    ]
    fig, ax = plt.subplots(figsize=(7.4, 4.7), layout="constrained")
    y = list(range(len(metrics)))
    ax.axvline(1, color="#444", linewidth=1, linestyle="--", label="orbit reference = 1")
    for i, (label, value, interval, description) in enumerate(metrics):
        if interval:
            low, high = interval
            ax.errorbar(value, i, xerr=[[value-low], [high-value]], fmt="o", capsize=5, color="#176b87", ecolor="#176b87")
        else:
            ax.plot(value, i, "o", color="#176b87")
    ax.set_xscale("log")
    ax.set_xlim(.02, 1.4)
    ax.set_yticks(y, [m[0] for m in metrics])
    ax.invert_yaxis()
    ax.set_xlabel("Unit-basis split / orbit reference ratio (log scale)")
    ax.set_title("Compact-table tradeoff, Tier 1 RunPod panel")
    ax.grid(axis="x", which="both", alpha=.25)
    for i, (_, value, interval, description) in enumerate(metrics):
        if i > 0:
            ax.annotate(f"{value:.4f}  ({description})", (value, i), xytext=(7, 8), textcoords="offset points", fontsize=8)
    ax.text(.5, -.20, "Throughput interval spans 16 repeats on one allocation; setup/memory ratios are reported separately.", transform=ax.transAxes, ha="center", fontsize=8.5)
    ax.legend(loc="upper left", fontsize=8)
    for ext in ("svg", "pdf"):
        fig.savefig(HERE / f"unit-basis-tradeoff.{ext}")
    plt.close(fig)

if __name__ == "__main__":
    main()
