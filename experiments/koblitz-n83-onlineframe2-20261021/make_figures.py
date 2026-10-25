#!/usr/bin/env python3
"""Render the design-stage figures of the online-frame round-2 experiment (not results).

* `figures/power.{svg,pdf,png}` from `analysis/power.json`: simulated power
  of the frozen primary rule against the true end-to-end effect (with the
  modelled and the PR #988-archived online factors marked), the prior's
  end-to-end composition (the online share that bounds the effect), and the
  job runtime against the time guard and the job limit.

The design diagram is `figures/design.tex`, rendered with pdflatex and
pdftoppm (`figures/design.pdf`, `figures/design.png`).
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent


def save(fig, stem):
    for ext in ("svg", "pdf", "png"):
        fig.savefig(HERE / "figures" / ("%s.%s" % (stem, ext)), dpi=150,
                    metadata={"Date": None} if ext == "svg" else None)


def power_figure():
    power = json.loads((HERE / "analysis" / "power.json").read_text())
    cells = power["cells"]
    numeric = sorted((float(k), v) for k, v in cells.items() if k[0].isdigit())
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2), gridspec_kw={"width_ratios": [1.4, 1, 1]})
    ax = axes[0]
    ax.plot([e for e, _ in numeric], [v["power"] for _, v in numeric], "o-", color="#3b6ea8",
            label="P(95% lower bound > 1)")
    for key, color, label in (("modelled", "#c0504d", "modelled (row's frame ns/probe)"),
                              ("archived_onlineframe", "#6a9a58", "PR #988 online ratio 1.573")):
        c = cells[key]
        ax.plot([c["expected_e2e_ratio"]], [c["power"]], "s", color=color, ms=8, label="%s: %.4f" % (
            label, c["expected_e2e_ratio"]))
    ax.axvline(power["min_delta"], color="grey", ls=":", label="minimal effect of interest %.3f" % power["min_delta"])
    ax.axhline(0.8, color="grey", ls="--", lw=0.8)
    ax.set_xlabel("true end-to-end ratio E2E(A)/E2E(B)")
    ax.set_ylabel("power (simulated, %d per cell)" % 400)
    ax.set_title("Primary rule, 16 points x 4 pairs (design, not a result)", fontsize=10)
    ax.set_ylim(-0.03, 1.05)
    ax.legend(fontsize=7, loc="lower right")
    ax = axes[1]
    m = power["prior_means_ms"]
    rest = m["cold_ms"] - m["index_ms"] - m["scan_selftest_ms"] - m["online_ms"]
    parts = [("rank stage", m["rank_stage_ms"], "#8fb0d6"), ("index build", m["index_ms"], "#bfbfbf"),
             ("self-test", m["scan_selftest_ms"], "#d9d9d9"), ("rest of setup", rest, "#eeeeee"),
             ("online (changed)", m["online_ms"], "#c0504d")]
    bottom = 0.0
    for name, value, color in parts:
        ax.bar([0], [value / 1000], bottom=[bottom / 1000], color=color, edgecolor="black", lw=0.5,
               label="%s %.0f ms" % (name, value))
        bottom += value
    saving = (1 - power["candidate_model"]["online_factor"]) * m["online_ms"]
    ax.bar([1], [(bottom - saving) / 1000], color="#f2c38f", edgecolor="black", lw=0.5,
           label="side B modelled (-%.0f ms)" % saving)
    ax.set_xticks([0, 1], ["A (prior means)", "B (modelled)"])
    ax.set_ylabel("seconds per target, end to end")
    ax.set_title("Row's E2E, run 39464544962 (prior)", fontsize=10)
    ax.legend(fontsize=7, loc="lower center")
    ax = axes[2]
    rt = power["runtime"]
    bars = [("before", rt["fixed_before_schedule_min"]), ("schedule", rt["schedule_min"]),
            ("after", rt["fixed_after_schedule_min"])]
    left = 0.0
    for name, value in bars:
        ax.barh([1], [value], left=[left], label="%s %.0f min" % (name, value))
        left += value
    ax.barh([0], [rt["job_total_min_on_a_1.5x_slower_host"]], color="#bfbfbf",
            label="1.5x slower host %.0f min" % rt["job_total_min_on_a_1.5x_slower_host"])
    ax.axvline(rt["time_guard_deadline_min"], color="#c0504d", ls="--", label="time guard %d min" %
               rt["time_guard_deadline_min"])
    ax.axvline(rt["job_limit_min"], color="black", ls=":", label="job limit %d min" % rt["job_limit_min"])
    ax.set_yticks([0, 1], ["slow host", "modelled"])
    ax.set_xlabel("minutes")
    ax.set_title("Runtime (design estimate)", fontsize=10)
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    save(fig, "power")


if __name__ == "__main__":
    power_figure()
