#!/usr/bin/env python3
"""Render the retained toy HECDLP evidence without re-running benchmarks."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "artifacts" / "end_to_end_hecdlp.json"


def main() -> None:
    payload = json.loads(DATA.read_text())
    rows = payload["rows"]
    q = [row["field_size_q"] for row in rows]
    candidates = [row["relation_candidates"] for row in rows]
    orders = [row["jacobian_order"] for row in rows]
    rho_adds = [row["median_pollard_rho_jacobian_additions"] for row in rows]
    crossover = [row["measured_crossover_target"] for row in rows]

    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.6))
    axes[0].loglog(q, candidates, "o-", color="#2563eb")
    axes[0].set(xlabel="field size q", ylabel="relation candidates", title="Relation collection")
    axes[0].grid(True, which="both", alpha=0.25)
    axes[0].text(0.04, 0.93, "fit slope 1.1216", transform=axes[0].transAxes, va="top")

    axes[1].loglog(orders, rho_adds, "s-", color="#7c3aed")
    axes[1].set(xlabel="Jacobian order", ylabel="median rho additions", title="Same-group rho")
    axes[1].grid(True, which="both", alpha=0.25)
    axes[1].text(0.04, 0.93, "fit slope 0.5047", transform=axes[1].transAxes, va="top")

    axes[2].bar([str(value) for value in q], crossover, color="#d97706")
    axes[2].set(xlabel="field size q", ylabel="targets", title="Measured amortization crossover")
    axes[2].set_ylim(0, max(crossover) + 1)
    axes[2].grid(True, axis="y", alpha=0.25)

    fig.suptitle("Retrospective toy HECDLP evidence (producer-checked; pcc:unverified)", fontsize=11)
    fig.tight_layout()
    for suffix in ("svg", "png"):
        fig.savefig(ROOT / "figures" / f"hecdlp-evidence.{suffix}", dpi=150, bbox_inches="tight")


if __name__ == "__main__":
    main()
