#!/usr/bin/env python3
"""Render the design-stage figures of the round-2 experiment (not results).

* `figures/profile.{svg,pdf,png}` from `inputs/local_profile.json`: the
  LOCAL DIAGNOSTIC split of the row producer's index build on the M38 base
  (bench medians of 5 interleaved rounds: the state loop and the insert
  pipeline on a pre-faulted table; the canonicalization and the prefetched
  insert alone from the profile process), the round-2 build's parts, and the
  candidates with their modelled savings and status.
* `figures/power.{svg,pdf,png}` from `analysis/power.json`: simulated power
  of the frozen primary rule against the true end-to-end effect, and the job
  runtime against the time guard and the job limit.

The design diagram is `figures/design.tex`, rendered with pdflatex and
pdftoppm (`figures/design.pdf`, `figures/design.png`).
"""

import json
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
COLORS = {"inv": "#c0504d", "prep": "#e6a0a0", "fin": "#d98c5f", "norm": "#f2c38f", "push": "#bfbfbf",
          "canon": "#3b6ea8", "insert": "#8fb0d6", "self": "#6a9a58"}


def save(fig, stem):
    for ext in ("svg", "pdf", "png"):
        fig.savefig(HERE / "figures" / ("%s.%s" % (stem, ext)), dpi=150,
                    metadata={"Date": None} if ext == "svg" else None)


def profile_figure():
    prof = json.loads((HERE / "inputs" / "local_profile.json").read_text())
    b = prof["breakdown_median_ms"]
    c = prof["candidates"]
    canon = prof["canonicalizers_ms (all 30.7 M roots, median of 3; equal to lift_scan on every root: True)"]
    state_a = c["C9_sum_inverse_states"]["producer_bench_state_loop_ms"]
    state_b = c["C9_sum_inverse_states"]["bench_state_loop_ms"]
    pipe_a = c["C7_linear_canon_lanes8"]["producer_bench_pipeline_ms"]
    pipe_b = c["C7_linear_canon_lanes8"]["bench_pipeline_ms"]
    selftest = b["bench_scan_selftest_ms (producer, 2 keys, median of 5)"]
    parent_parts = [("state loop (S3 roots, to_normal, push)", state_a, "inv"),
                    ("insert pipeline (lift_scan keys + prefetched insert)", pipe_a, "canon"),
                    ("scan self-test (2 keys, unchanged)", selftest, "self")]
    derived_parts = [("state loop, 7 products per state (C9)", state_b, "fin"),
                     ("insert pipeline, linear keys x8 (C7)", pipe_b, "insert"),
                     ("scan self-test (2 keys, unchanged)", selftest, "self")]
    fig, (left, right) = plt.subplots(1, 2, figsize=(12.5, 4.6), gridspec_kw={"width_ratios": [1.35, 1]})
    for y, parts in ((1, parent_parts), (0, derived_parts)):
        x = 0.0
        for label, ms, color in parts:
            left.barh(y, ms / 1000, left=x, color=COLORS[color], edgecolor="white", height=0.55)
            left.text(x + ms / 2000, y, "%.1f" % (ms / 1000), ha="center", va="center", fontsize=8)
            x += ms / 1000
        left.text(x + 0.2, y, "%.1f s" % x, va="center", fontsize=9)
    left.set_yticks([1, 0])
    left.set_yticklabels(["current row\n(round-1 producer)", "round-2 producer\n(same index, same verdict)"])
    left.set_xlabel("seconds, M38 base (bench medians of 5 interleaved rounds; table pre-faulted)")
    left.set_xlim(0, 15)
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLORS[col]) for _, _, col in parent_parts + derived_parts[:2]]
    left.legend(handles, [p[0] for p in parent_parts + derived_parts[:2]], fontsize=7, loc="upper center", ncol=2,
                frameon=False, bbox_to_anchor=(0.5, -0.2))
    left.set_title("Index build and self-test (15.3 M stored states, 30.7 M roots, 1 GiB table)", fontsize=9,
                   loc="left")
    insert_alone = b["insert_alone_prefetch32_ms (incl. faults)"]
    c6 = c["C6_bucketed_insert"]["per_bucket_count"]["log2_buckets_12"]
    cands = [("C9 states from 1/l, 1/r, 1/(l+r)", c["C9_sum_inverse_states"]["modelled_saving_ms"], "implemented"),
             ("C7 linear run finder, 8 lanes", c["C7_linear_canon_lanes8"]["modelled_saving_ms"], "implemented"),
             ("S3 branch-free self-test", c["S3_branchfree_selftest"]["producer_bench_ms"] -
              c["S3_branchfree_selftest"]["bench_ms"], "rejected"),
             ("C8 pclmul codegen (C9 loop)", statistics.median(c["C9_sum_inverse_states"]["profile_runs_ms"]["c9"]) -
              statistics.median(c["C8_pclmul_codegen"]["profile_runs_ms"]["c9_tf"]), "rejected"),
             ("C6 bucketed insert, 2^12 buckets\n(partition + insert vs prefetched insert)",
              insert_alone - (c6["partition_ms"] + c6["insert_ms"]), "rejected")]
    status_color = {"implemented": "#3b6ea8", "rejected": "#c0504d"}
    for y, (label, ms, status) in enumerate(reversed(cands)):
        right.barh(y, ms / 1000, color=status_color[status], height=0.6)
        right.text(max(ms, 0) / 1000 + 0.1, y, "%+.2f s  %s" % (-ms / 1000, status), va="center", fontsize=7.5)
    right.set_yticks(range(len(cands)))
    right.set_yticklabels([x[0] for x in reversed(cands)], fontsize=7.5)
    right.axvline(0, color="#333333", lw=0.8)
    right.set_xlim(-2.0, 3.5)
    right.set_xlabel("modelled saving (s, local); labels: time change")
    right.set_title("Candidates (every one checked byte-identical)", fontsize=9, loc="left")
    fig.suptitle("LOCAL DIAGNOSTIC on the shared cloud-agent VM (inputs/local_profile.json): ranks candidates and "
                 "sizes the design; not evidence. lift_scan alone %.2f s, linear %.2f s (all roots)" % (
                     canon["lift_scan"] / 1000, canon["linear"] / 1000), fontsize=9.5, color="#c0504d")
    fig.tight_layout()
    save(fig, "profile")
    plt.close(fig)


def power_figure():
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
    left.set_xticklabels(["%.2f" % e for e in effects], rotation=45)
    left.minorticks_off()
    left.set_xlabel("true end-to-end effect E2E(A)/E2E(B)")
    left.set_ylabel("P(lower 95% bound > 1)")
    left.set_ylim(-0.03, 1.05)
    modelled = power["cells"]["modelled"]
    left.set_title("Power, %d points x %d pairs (400 sims; MC 95%% bars)\nmodelled (about %.2f): %.3f" % (
        power["design"]["points"], power["design"]["primary_pairs_per_point"],
        power["expected_ratio_at_prior_means"], modelled["power"]), fontsize=9)
    left.annotate("minimal effect %.2f" % power["min_delta"], (power["min_delta"], 0.5), xytext=(4, 0),
                  textcoords="offset points", fontsize=8, color="#c0504d")
    rt = power["runtime"]
    labels = ["estimate", "1.5x slower host"]
    totals = [rt["job_total_min"], rt["job_total_min_on_a_1.5x_slower_host"]]
    right.barh(labels, totals, color=["#3b6ea8", "#9bb7d4"])
    right.axvline(rt["time_guard_deadline_min"], color="#c0504d", ls="--", lw=1)
    right.axvline(rt["job_limit_min"], color="#333333", ls="-", lw=1)
    right.text(rt["time_guard_deadline_min"] - 3, 0.5, "guard %d" % rt["time_guard_deadline_min"], fontsize=8,
               color="#c0504d", ha="right", rotation=90, va="center")
    right.text(rt["job_limit_min"], -0.45, "limit %d" % rt["job_limit_min"], fontsize=8, ha="right")
    for y, t in enumerate(totals):
        right.text(t / 2, y, "%.0f min" % t, va="center", ha="center", color="white", fontsize=9)
    right.set_xlabel("job minutes (parent-run walls x counts + fixed)")
    right.set_xlim(0, rt["job_limit_min"] + 15)
    right.set_title("Runtime, one job (%.0f min schedule)" % rt["schedule_min"], fontsize=9)
    fig.tight_layout()
    save(fig, "power")
    plt.close(fig)


def main():
    (HERE / "figures").mkdir(exist_ok=True)
    profile_figure()
    power_figure()
    print("figures/profile.{svg,pdf,png} figures/power.{svg,pdf,png}")


if __name__ == "__main__":
    main()
