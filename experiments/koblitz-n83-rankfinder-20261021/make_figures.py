#!/usr/bin/env python3
"""Render the design-stage figures of the rank-finder experiment (not results).

* `figures/profile.{svg,pdf,png}` from `inputs/local_profile.json`: the
  LOCAL DIAGNOSTIC split of the rank stage (M38, rank seed 1501, 16
  attempts, 30.2 M probe keys, means of two rounds) into frame setup, key
  derivation and the probe loop, for the row's producer and the rank-finder
  producer; the canonicalization alone per key (lift_scan against the
  linear run finder, on the same real partner words); and the rank-stage
  ratio per base in the alternating exactness processes.
* `figures/power.{svg,pdf,png}` from `analysis/power.json`: simulated power
  of the frozen primary rule against the true end-to-end effect, and the job
  runtime against the time guard and the job limit.

The design diagram is `figures/design.tex`, rendered with pdflatex and
pdftoppm (`figures/design.pdf`, `figures/design.png`).
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
COLORS = {"setup": "#9aa5b1", "keys": "#3b6ea8", "probe": "#d9a441", "lift": "#c0504d", "linear": "#3b6ea8",
          "frame": "#3b6ea8", "plant": "#6a9a58"}


def save(fig, stem):
    (HERE / "figures").mkdir(exist_ok=True)
    for ext in ("svg", "pdf", "png"):
        fig.savefig(HERE / "figures" / ("%s.%s" % (stem, ext)), dpi=150,
                    metadata={"Date": None} if ext == "svg" else None)
    plt.close(fig)


def profile_figure():
    prof = json.loads((HERE / "inputs" / "local_profile.json").read_text())
    p = prof["profile_M38_seed1501"]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4), gridspec_kw={"width_ratios": [1.6, 1, 1]})
    left, mid, right = axes
    rows = (("row (lift_scan keys)", p["parent"]), ("rank finder (linear keys x8)", p["derived"]))
    for y, (label, side) in zip((1, 0), rows):
        x = 0.0
        for key, name, color in (("frame_setup_ms", "frame setup", "setup"),
                                 ("key_derivation_ms", "key derivation", "keys"),
                                 ("probe_loop_and_rest_ms", "probe loop + rest", "probe")):
            ms = side[key]
            left.barh(y, ms / 1000, left=x, color=COLORS[color], edgecolor="white", height=0.55,
                      label=name if y == 1 else None)
            left.text(x + ms / 2000, y, "%.2f" % (ms / 1000), ha="center", va="center", fontsize=8, color="white")
            x += ms / 1000
        left.text(x + 0.05, y, "%.2f s" % (side["rank_stage_ms"] / 1000), va="center", fontsize=9)
    left.set_yticks([1, 0], [r[0] for r in rows])
    left.set_xlabel("rank stage, s (M38, seed 1501, 16 attempts, %.1f M keys)" % (p["parent"]["keys"] / 1e6))
    left.set_xlim(0, 6.0)
    left.legend(fontsize=8, loc="lower right", frameon=False)
    left.set_title("LOCAL DIAGNOSTIC: rank-stage split (mean of 2 rounds)", fontsize=10)
    for side_name, side in (("row", p["parent"]),):
        names = ["lift_scan\n(per key)", "linear run finder\n(8 lanes)"]
        vals = [side["ns_per_key"]["lift_scan_alone_ms"], side["ns_per_key"]["linear_lanes8_alone_ms"]]
        bars = mid.bar(names, vals, color=[COLORS["lift"], COLORS["linear"]], width=0.55)
        for bar, v in zip(bars, vals):
            mid.text(bar.get_x() + bar.get_width() / 2, v + 0.8, "%.1f ns" % v, ha="center", fontsize=9)
    mid.set_ylabel("ns per key, canonicalization alone")
    mid.set_ylim(0, 55)
    mid.set_title("same real partner words, both exact", fontsize=10)
    per = prof["rank_stage_per_base"]
    order = [k for k in ("M38", "M10", "K600", "M38_frame_plant") if k in per]
    vals = [per[k]["derived_over_parent_rank_stage"] for k in order]
    bars = right.bar(["%s\n(%d seeds)" % (k.replace("_frame_plant", "\nframe_plant"), len(per[k]["seeds"]))
                      for k in order], vals,
                     color=[COLORS["plant"] if "plant" in k else COLORS["frame"] for k in order], width=0.6)
    for bar, v in zip(bars, vals):
        right.text(bar.get_x() + bar.get_width() / 2, v + 0.01, "%.3f" % v, ha="center", fontsize=9)
    right.axhline(1.0, color="black", lw=0.8, ls="--")
    right.set_ylim(0, 1.1)
    right.set_ylabel("rank stage, rank finder / row (ratio of sums)")
    right.set_title("alternating exactness processes", fontsize=10)
    fig.tight_layout()
    save(fig, "profile")


def power_figure():
    power = json.loads((HERE / "analysis" / "power.json").read_text())
    cells = power["cells"]
    effects = sorted(float(k) for k in cells if k != "modelled")
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4.0), gridspec_kw={"width_ratios": [1.4, 1]})
    left.plot(effects, [cells["%.2f" % e]["power"] for e in effects], "o-", color=COLORS["keys"])
    m = cells["modelled"]
    left.plot([m["median_estimate"]], [m["power"]], "s", color=COLORS["probe"],
              label="modelled %.3f (local factor %.3f)" % (m["median_estimate"], m["rank_stage_factor"]))
    left.axvline(power["min_delta"], color="gray", ls=":", label="minimal effect of interest %.2f" % power["min_delta"])
    left.axhline(0.025, color="gray", lw=0.6)
    left.set_xlabel("true end-to-end effect E2E(A)/E2E(B)")
    left.set_ylabel("P(95% lower bound > 1)")
    left.set_ylim(-0.03, 1.05)
    left.set_title("Design power (%d simulations per cell; not a result)" % 400, fontsize=10)
    left.legend(fontsize=8, loc="center right", frameon=False)
    rt = power["runtime"]
    labels = ["fixed before", "schedule", "fixed after"]
    vals = [rt["fixed_before_schedule_min"], rt["schedule_min"], rt["fixed_after_schedule_min"]]
    x = 0.0
    for label, v, c in zip(labels, vals, ("#9aa5b1", COLORS["keys"], "#9aa5b1")):
        right.barh(1, v, left=x, color=c, edgecolor="white", height=0.5)
        right.text(x + v / 2, 1, "%.0f" % v, ha="center", va="center", color="white", fontsize=8)
        x += v
    right.barh(0, rt["job_total_min_on_a_1.5x_slower_host"], color="#c9d6e8", height=0.5)
    right.text(rt["job_total_min_on_a_1.5x_slower_host"] + 2, 0, "%.0f" % rt["job_total_min_on_a_1.5x_slower_host"],
               va="center", fontsize=8)
    right.text(x + 2, 1, "%.0f" % x, va="center", fontsize=8)
    right.axvline(rt["time_guard_deadline_min"], color=COLORS["lift"], ls="--", label="time guard %d" % rt["time_guard_deadline_min"])
    right.axvline(rt["job_limit_min"], color="black", ls=":", label="job limit %d" % rt["job_limit_min"])
    right.set_yticks([1, 0], ["modelled job", "1.5x slower host"])
    right.set_xlabel("minutes")
    right.set_xlim(0, 190)
    right.legend(fontsize=8, loc="center", frameon=False)
    right.set_title("Runtime (282 processes)", fontsize=10)
    fig.tight_layout()
    save(fig, "power")


if __name__ == "__main__":
    profile_figure()
    power_figure()
