#!/usr/bin/env python3
"""Render the design-stage power figure from `analysis/power.json` (not a result).

`figures/power.svg`, `figures/power.pdf` and `figures/power.png`. The left
panel shows the simulated power of the frozen primary rule (lower 95% bound
of the paired E2E ratio above 1) against the true end-to-end effect. The
right panel shows the estimated job time against the 285-minute time guard
and the 300-minute job limit. The design diagram is `figures/design.tex`,
rendered with pdflatex and pdftoppm.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent


def main():
    power = json.loads((HERE / "analysis" / "power.json").read_text())
    cells = {k: v for k, v in power["cells"].items() if k != "modelled"}
    effects = sorted(float(k) for k in cells)
    values = [cells["%.2f" % e]["power"] for e in effects]
    errors = [1.96 * cells["%.2f" % e]["mc_se"] for e in effects]
    fig, (left, right) = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [1.5, 1]})
    left.errorbar(effects, values, yerr=errors, marker="o", color="#3b6ea8", capsize=3)
    left.axhline(0.025, color="#999999", lw=0.8, ls=":")
    left.axvline(power["min_delta"], color="#c0504d", lw=0.8, ls="--")
    left.set_xscale("log")
    left.set_xticks(effects)
    left.set_xticklabels(["%.2f" % e for e in effects])
    left.minorticks_off()
    left.set_xlabel("true end-to-end effect E2E(A)/E2E(B)")
    left.set_ylabel("P(lower 95% bound > 1)")
    left.set_ylim(-0.03, 1.05)
    modelled = power["cells"]["modelled"]
    left.set_title("Power, %d points x %d pairs (%d sims; MC 95%% bars)\nmodelled (parent's costs, about %.2f): %.3f"
                   % (power["design"]["points"], power["design"]["primary_pairs_per_point"],
                      400, power["expected_ratio_at_prior_means"], modelled["power"]), fontsize=9)
    left.annotate("minimal effect 1.5", (power["min_delta"], 0.5), xytext=(4, 0), textcoords="offset points",
                  fontsize=8, color="#c0504d")
    rt = power["runtime"]
    labels = ["estimate", "1.5x slower host"]
    totals = [rt["job_total_min"], rt["job_total_min_on_a_1.5x_slower_host"]]
    right.barh(labels, totals, color=["#3b6ea8", "#9bb7d4"])
    right.axvline(rt["time_guard_deadline_min"], color="#c0504d", ls="--", lw=1)
    right.axvline(rt["job_limit_min"], color="#333333", ls="-", lw=1)
    right.text(rt["time_guard_deadline_min"] - 3, 0.5, "guard 285", fontsize=8, color="#c0504d", ha="right",
               rotation=90, va="center")
    right.text(rt["job_limit_min"], -0.45, "limit 300", fontsize=8, ha="right")
    for y, t in enumerate(totals):
        right.text(t / 2, y, "%.0f min" % t, va="center", ha="center", color="white", fontsize=9)
    right.set_xlabel("job minutes (archived walls x counts + fixed)")
    right.set_xlim(0, 320)
    right.set_title("Runtime, one job (%.0f min schedule)" % rt["schedule_min"], fontsize=9)
    fig.tight_layout()
    for ext in ("svg", "pdf", "png"):
        fig.savefig(HERE / "figures" / ("power." + ext), dpi=150, metadata={"Date": None} if ext == "svg" else None)
    print("figures/power.{svg,pdf,png}")


if __name__ == "__main__":
    main()
