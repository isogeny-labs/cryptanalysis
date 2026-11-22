#!/usr/bin/env python3
"""Render the design-stage figures (not results).

* `figures/profile.{svg,pdf,png}` from `inputs/local_profile.json`: the
  LOCAL DIAGNOSTIC breakdown of the row producer's index build and scan
  self-test on the M38 base (median of three profile processes), the derived
  build's components, and the candidates ranked by modelled saving.
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
COLORS = {"inv": "#c0504d", "prep": "#e6a0a0", "fin": "#d98c5f", "norm": "#f2c38f", "push": "#bfbfbf",
          "canon": "#3b6ea8", "insert": "#8fb0d6", "self": "#6a9a58"}


def save(fig, stem):
    for ext in ("svg", "pdf", "png"):
        fig.savefig(HERE / "figures" / ("%s.%s" % (stem, ext)), dpi=150,
                    metadata={"Date": None} if ext == "svg" else None)


def profile_figure():
    prof = json.loads((HERE / "inputs" / "local_profile.json").read_text())
    b = prof["breakdown_median_ms"]
    sp, tp = b["state_loop_parts_ms"], b["table_insert_parts_ms"]
    v = prof["variant_median_ms"]
    selftest = b["scan_selftest_full_two_keys_ms"]
    lanes = prof["arm_cold_processes_s000"]["indexbuild"]["scan_selftest_ms"]
    parent_parts = [("field inversion (1 per state)", sp["s3_field_inversion"], "inv"),
                    ("S3 prepare", sp["s3_prepare"], "prep"), ("S3 finish", sp["s3_finish"], "fin"),
                    ("to_normal x2", sp["to_normal_two_roots"], "norm"),
                    ("state push + faults", sp["state_push_and_first_touch"], "push"),
                    ("lift_scan canon", tp["lift_scan_canonicalization"], "canon"),
                    ("insert: misses + faults", tp["insert_with_first_touch_faults"], "insert"),
                    ("scan self-test (2 keys)", selftest, "self")]
    states_new = v["states_batched_rows1"]
    insert_new = v["insert_prefetch32"]
    derived_parts = [("row-batched S3 solve + to_normal + push", states_new, "inv"),
                     ("lift_scan canon", tp["lift_scan_canonicalization"], "canon"),
                     ("prefetched insert", insert_new, "insert"),
                     ("self-test, 8 lanes", lanes, "self")]
    fig, (left, right) = plt.subplots(1, 2, figsize=(12.5, 4.6), gridspec_kw={"width_ratios": [1.45, 1]})
    for y, parts in ((1, parent_parts), (0, derived_parts)):
        x = 0.0
        for label, ms, color in parts:
            left.barh(y, ms / 1000, left=x, color=COLORS[color], edgecolor="white", height=0.55)
            if ms > 900:
                left.text(x + ms / 2000, y, "%.1f" % (ms / 1000), ha="center", va="center", fontsize=8)
            x += ms / 1000
        left.text(x + 0.2, y, "%.1f s" % x, va="center", fontsize=9)
    left.set_yticks([1, 0])
    left.set_yticklabels(["row producer\n(index build + self-test)", "derived producer\n(same index, same verdict)"])
    left.set_xlabel("seconds per M38 cold process (component medians of 3 profile runs)")
    left.set_xlim(0, 22)
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLORS[c]) for _, _, c in parent_parts]
    left.legend(handles, [p[0] for p in parent_parts], fontsize=7, loc="upper center", ncol=4, frameon=False,
                bbox_to_anchor=(0.5, -0.2))
    left.set_title("Where the index build goes (M38 base, 15.3 M stored states, 1 GiB table)", fontsize=9,
                   loc="left")
    cands = [("C1 one inversion per state row", b["state_loop_ms"] - states_new, "implemented"),
             ("C2 look-ahead canon + prefetch", tp["insert_with_first_touch_faults"] - insert_new, "implemented"),
             ("S1 self-test, 8 images at a time", selftest - lanes, "implemented"),
             ("S2 sampled self-test + one full check\n(changes the evidence)", lanes, "not used"),
             ("C6 bucketed insert order (est. bound)", 1000.0, "not implemented"),
             ("C7 cheaper canonicalizer (est. bound)", 1000.0, "not implemented"),
             ("C3 hugepages (in the full build)",
              prof["candidate_processes"]["4,32,plain"]["candidate_index_ms"] -
              prof["candidate_processes"]["4,32,huge"]["candidate_index_ms"], "rejected"),
             ("C4 prefault the table", prof["candidate_processes"]["4,32,plain"]["candidate_index_ms"] -
              prof["candidate_processes"]["4,32,prefault"]["candidate_index_ms"], "rejected")]
    status_color = {"implemented": "#3b6ea8", "not used": "#9bb7d4", "not implemented": "#cccccc",
                    "rejected": "#c0504d"}
    for y, (label, ms, status) in enumerate(reversed(cands)):
        right.barh(y, ms / 1000, color=status_color[status], height=0.6)
        right.text(max(ms, 0) / 1000 + 0.1, y, "%+.1f s  %s" % (-ms / 1000, status), va="center", fontsize=7.5)
    right.set_yticks(range(len(cands)))
    right.set_yticklabels([c[0] for c in reversed(cands)], fontsize=7.5)
    right.axvline(0, color="#333333", lw=0.8)
    right.set_xlim(-2.5, 10.5)
    right.set_xlabel("modelled saving per cold process (s, local)")
    right.set_title("Candidates ranked (byte-identical index unless noted)", fontsize=9, loc="left")
    fig.suptitle("LOCAL DIAGNOSTIC on the shared cloud-agent VM (inputs/local_profile.json): ranks candidates and "
                 "sizes the design; not evidence", fontsize=9.5, color="#c0504d")
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
    right.set_xlabel("job minutes (template walls x counts + fixed)")
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
