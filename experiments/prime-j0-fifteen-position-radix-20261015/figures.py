#!/usr/bin/env python3
"""Render source-linked research visuals from the frozen radix15 evidence."""
from pathlib import Path
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


HERE = Path(__file__).resolve().parent
OUT = HERE / "figures"
OUT.mkdir(exist_ok=True)
ANALYSIS = json.loads((HERE / "tier1-analysis.json").read_text())
RULES = json.loads((HERE / "tier1-rules.json").read_text())


def diagram():
    fig, ax = plt.subplots(figsize=(12.0, 5.7))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")
    labels = [
        (0.25, 4.45, 2.0, 1.1, "Prime norm radix\n268−τ; N=71,023"),
        (2.65, 4.45, 2.0, 1.1, "Finite selector\n35,512 canonical residues"),
        (5.05, 4.45, 2.0, 1.1, "15 contractions\nterminal norm < 82²"),
        (7.45, 4.45, 2.0, 1.1, "Independent checks\n388 affine; 128 native"),
        (9.85, 4.45, 1.9, 1.1, "Frozen Tier 1 panel\n48 pairs; 16 repeats"),
    ]
    for x, y, w, h, label in labels:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                                    facecolor="#eef4fb", edgecolor="#345b7e", linewidth=1.3))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=9.5)
    for i in range(len(labels) - 1):
        x, y, w, h, _ = labels[i]
        nx = labels[i + 1][0]
        ax.add_patch(FancyArrowPatch((x + w + 0.08, y + h / 2), (nx - 0.08, y + h / 2),
                                     arrowstyle="-|>", mutation_scale=12, color="#526b7b"))
    ax.text(6, 3.55,
            "Proof scope: integer recoding and runtime tie rule; candidate-specific secp256k1 group bridge remains open",
            ha="center", va="center", fontsize=10, color="#7a3e20",
            bbox=dict(boxstyle="round,pad=0.45", facecolor="#fff3e7", edgecolor="#c27642"))
    ax.text(6, 3.0,
            "The throughput result covers repeated hot-table scalar multiplication plus affine recovery; preparation and memory are reported separately.",
            ha="center", va="center", fontsize=9, color="#333333")
    history = FancyBboxPatch((0.35, 0.45), 5.1, 1.8, boxstyle="round,pad=0.10",
                             facecolor="#fff3e7", edgecolor="#c27642", linewidth=1.4)
    ax.add_patch(history)
    ax.text(2.9, 1.35,
            "Historical panel: source e195374… and per-child RSS missing\n"
            "Throughput remains qualified; original acceptance criteria are open",
            ha="center", va="center", fontsize=9, color="#713d22")
    rebuild = FancyBboxPatch((6.5, 0.45), 5.1, 1.8, boxstyle="round,pad=0.10",
                             facecolor="#eef4fb", edgecolor="#345b7e", linewidth=1.4)
    ax.add_patch(rebuild)
    ax.text(9.05, 1.35,
            "Reconstruction protocol v1: pinned recoverable source + frozen fingerprints\n"
            "Future separate build; per-process RSS required; not run",
            ha="center", va="center", fontsize=9, color="#263f54")
    ax.add_patch(FancyArrowPatch((5.55, 1.35), (6.45, 1.35), arrowstyle="-|>",
                                 mutation_scale=12, color="#526b7b"))
    ax.text(6, 1.75, "new snapshot", ha="center", va="center", fontsize=7.5,
            color="#526b7b", bbox=dict(facecolor="white", edgecolor="none", pad=1))
    fig.tight_layout()
    fig.savefig(OUT / "radix15-evidence-flow.svg", bbox_inches="tight")
    fig.savefig(OUT / "radix15-evidence-flow.pdf", bbox_inches="tight")
    plt.close(fig)


def performance():
    fig, ax = plt.subplots(figsize=(9.0, 4.4))
    ratio = ANALYSIS["radix15_over_radix16_throughput_median"]
    lo, hi = ANALYSIS["paired_bootstrap95_by_repeat"]
    ax.axvline(1.0, color="#75889a", linestyle="--", linewidth=1.2,
               label="equal throughput (1.0×)")
    ax.errorbar([ratio], [0], xerr=[[ratio - lo], [hi - ratio]], fmt="o",
                color="#217c68", ecolor="#182d32", elinewidth=2,
                capsize=7, capthick=1.8, markersize=8)
    ax.set_yticks([0], ["Radix 15 / radix 16"])
    ax.set_xlim(0.985, 1.042)
    ax.set_ylim(-0.65, 0.75)
    ax.set_xlabel("Throughput ratio (reference online time / candidate online time)")
    ax.set_ylabel("")
    ax.set_title("Frozen same-point hot-table panel: 15-position / 16-position")
    ax.grid(axis="x", alpha=0.25)
    ax.legend(loc="upper left", frameon=False, fontsize=8)
    ax.text(ratio, 0.36, f"median {ratio:.4f}×\n95% interval [{lo:.4f}, {hi:.4f}]",
            ha="center", va="bottom", fontsize=9)
    ax.text(1.0135, -0.52,
            f"{ANALYSIS['completed_pairs']} valid pairs · {RULES['repetitions']} alternating repetitions · "
            f"{ANALYSIS['operations_per_arm']:,} scalar operations per arm\n"
            "Tier 1 instance, one allocation; affinity does not establish host exclusivity",
            ha="center", va="center", fontsize=8.5,
            bbox=dict(boxstyle="round,pad=0.45", facecolor="#f1f4f6", edgecolor="#aebac3"))
    fig.tight_layout()
    fig.savefig(OUT / "radix15-tier1-throughput.svg", bbox_inches="tight")
    fig.savefig(OUT / "radix15-tier1-throughput.pdf", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    diagram()
    performance()
    for svg in OUT.glob("*.svg"):
        svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
