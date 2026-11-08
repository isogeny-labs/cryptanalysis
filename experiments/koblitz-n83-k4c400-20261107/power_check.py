#!/usr/bin/env python3
"""Power, variance and runtime of the K'=4 / 400-orbit design (before any timing).

This is a SIZING check by simulation. Nothing in it is a result of the run.

Prior. `inputs/power_prior.json` (`make_power_prior.py`): the field-ops
experiment's archived run 41869146827, 36 primary pairs of the M38 side's
processes (kM38FO rank stage with its 16 per-attempt times and probe counts;
cM38FO cold, index build, self-test and online) on 12 points, which is exactly
this experiment's side A. There is no archived D4 measurement on the runner
class. The D4 side is therefore MODELLED from the M38 archive and the
local identity/prototype (`inputs/local_profile.json`), as follows.

Modelled D4 side (B), for one simulated pair. B draws its own archived M38
pair (A and B run different bases, so their online targets and rank
attempts are independent draws; one point keeps its archived pairs across
its K pairs):

* index build   = archived index build x `index_build_factor` (the local
  prototype's cold D4 / M38 ratio, 1827 / 4579);
* self-test     = archived self-test x `selftest_factor` (0.25: the Feistel
  domain steps down 2^26 -> 2^24 when the logical states fall below 2^24; the
  local cold ratio 207 / 1540 is not used, its M38 self-test is the
  unexplained-high one of the prototype);
* other setup   = archived cold - index - self-test - online (base load,
  linear algebra, table load), unchanged;
* online        = archived online x `work_factor` (E_M38 / E_D4 = 2.406:
  probes per relation rise as 1 / E; ns per probe unchanged, the prototype
  measured it 0 to 12% lower, which is not credited);
* rank stage    = the sum of K' = 4 attempts, each drawn from the pooled 576
  archived attempt times, x `work_factor`. This keeps the heavy tail: a sum
  of four exponentials has CV 0.5.

Effect cells. For an effect E the modelled B costs are all multiplied by one
common constant so that E2E(A) / E2E(B) at the prior means equals E (E = 1.00:
type I). The `modelled` cell uses the factors above unscaled. The minimum
effect of interest is MIN_DELTA = 1.20.

Primary rule simulated: R = sum E2E(A) / sum E2E(B), two-stage paired
bootstrap of `verify_receipt.py` (points then pairs), lower bound > 1.

Controls simulated: A/A (B against Baa, two modelled draws): cold ratio point
estimate inside [0.97, 1.03] and the END-TO-END ratio's 95% two-stage interval
containing 1. (The field-ops template required the
end-to-end POINT estimate inside [0.97, 1.03]. Here that would fail a true null
about half the time, simulated below as `e2e_point_inside_0.97_1.03_rate`,
because D4's per-pair E2E noise is 0.23: the rule is replaced.); planted (cD4X / cD4 index build, factor PLANT 1.5
over the modelled index build, lower bound > 1); probe law (kD4's pooled
probes per relation over POINTS * K * 4 attempts inside [0.80, 1.20], drawn
from the pooled archived attempt probes scaled to D4's law, at a true law
ratio of 1.00, of 1.15 (the prototype's point estimate, 40 attempts) and of
1.30).

Variance power check. The rank stage is heavy-tailed, so besides the primary
rate the script reports, per design, the coefficient of variation of the
simulated D4 rank stage and online stage and of E2E per side, the width of
the bootstrap interval (hi / lo), and the number of distinct rank seeds (= K'
independent exponential attempts each). The design table compares
(POINTS, K) = (12, 3), (16, 3) and (20, 3); `--design` selects the one written
to `analysis/power.json` as the frozen design.

Runtime: mean process walls of the M38 arms from the archive; D4 arms modelled
as the M38 wall minus the modelled stage savings (the untimed remainder of the
wall, mostly the post-target index digest, scaled by the stored-state ratio).
"""

import argparse
import json
import math
import random
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "inputs" / "power_prior.json"
PROFILE = HERE / "inputs" / "local_profile.json"
OUT = HERE / "analysis" / "power.json"
R = 8569786107849059
ENTRIES = {"M38": 30366551, "D4": 12618968}
STORED = {"M38": 15341360, "D4": 6640200}
COLUMNS_D = 4
DESIGNS = ((12, 3), (16, 3), (20, 3))
K_AA = 2
K_PLANTED = 1
EFFECTS = (1.0, 1.02, 1.05, 1.10, 1.20, 1.50)
MIN_DELTA = 1.20
BAND = (0.80, 1.20)
AA_BAND = (0.97, 1.03)     # the cold process (low variance): point estimate
# end to end (heavy-tailed rank and online): the 95% two-stage interval must contain 1
PLANT = 1.5
PLANT_EXTRA_S = 4.0
SIMULATIONS = 400
DRAWS = 500
SEED = 2026110781
FIXED_BEFORE_MIN = 17.0
FIXED_AFTER_MIN = 2.0
DEADLINE_MIN = 165
JOB_LIMIT_MIN = 180


def two_stage(points, rng, draws):
    def value(sample):
        return sum(a for pairs in sample for a, _ in pairs) / sum(b for pairs in sample for _, b in pairs)

    est = value(points)
    values = []
    n = len(points)
    for _ in range(draws):
        sample = []
        for _ in range(n):
            pairs = points[rng.randrange(n)]
            sample.append([pairs[rng.randrange(len(pairs))] for _ in pairs])
        values.append(value(sample))
    values.sort()
    return est, values[int(0.025 * draws)], values[int(0.975 * draws) - 1]


def cv(values):
    return statistics.pstdev(values) / statistics.mean(values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--design", default="20x3", help="POINTSxK written as the frozen design")
    args = parser.parse_args()
    sims = 40 if args.quick else SIMULATIONS
    prior = json.loads(PRIOR.read_text())
    profile = json.loads(PROFILE.read_text())
    mod = profile["modelled"]
    f_i, f_s = float(mod["index_build_factor"]), float(mod["selftest_factor"])
    work = ENTRIES["M38"] / ENTRIES["D4"]
    by_point = {}
    for key, side in sorted(prior["side_A_primary_pairs"].items()):
        by_point.setdefault(key.split("/")[0], []).append(side)
    points_prior = [v for _, v in sorted(by_point.items())]
    flat = [s for v in points_prior for s in v]
    aa = list(prior["aa_ratios_B_over_Baa"].values())
    rank_f = [a["rank_stage"] for a in aa]
    cold_f = [a["cold"] for a in aa]
    index_f = [a["index"] for a in aa]
    attempts_ns = [x / 1e6 for s in flat for x in s["rank_attempt_ns"]]
    attempts_probes = [x for s in flat for x in s["rank_attempt_probes"]]
    law_m38 = R / (166 * ENTRIES["M38"])
    law_d4 = R / (166 * ENTRIES["D4"])
    mean = {k: statistics.mean(s[k] for s in flat) for k in ("rank_stage_ms", "cold_ms", "index_ms",
                                                            "scan_selftest_ms", "online_ms")}
    rng = random.Random(SEED)
    pick = lambda xs: xs[rng.randrange(len(xs))]  # noqa: E731

    def side_a(s):
        return s["rank_stage_ms"] + s["cold_ms"]

    def side_b(s, scale=1.0, plant=1.0):
        """Modelled D4 side from one archived M38 pair: (rank, cold, index, online) in ms before the cell scale."""
        other = s["cold_ms"] - s["index_ms"] - s["scan_selftest_ms"] - s["online_ms"]
        index = s["index_ms"] * f_i * plant
        cold = other + index + s["scan_selftest_ms"] * f_s + s["online_ms"] * work
        rank = sum(pick(attempts_ns) for _ in range(COLUMNS_D)) * work
        return rank * scale, cold * scale, index * scale, s["online_ms"] * work * scale

    e2e_a = side_a(mean)
    mean_b = [0.0] * 4
    probe = 20000
    for _ in range(probe):
        v = side_b(pick(flat))
        for i in range(4):
            mean_b[i] += v[i] / probe
    e2e_b_modelled = mean_b[0] + mean_b[1]

    def design_block(points, k):
        cells, spread = {}, {}
        for effect in EFFECTS + ("modelled",):
            scale = 1.0 if effect == "modelled" else (e2e_a / effect) / e2e_b_modelled
            hits, estimates, widths = 0, [], []
            ra, rb, oa, ob, ea, eb = [], [], [], [], [], []
            for _ in range(sims):
                pts = []
                for _ in range(points):
                    q = pick(points_prior)
                    pairs = []
                    for _ in range(k):
                        sa, sb = pick(q), pick(q)
                        a = side_a(sa)
                        rk, cd, _, on = side_b(sb, scale)
                        b = rk + cd
                        pairs.append((a, b))
                        if effect == "modelled":
                            ra.append(sa["rank_stage_ms"]); rb.append(rk)
                            oa.append(sa["online_ms"]); ob.append(on)
                            ea.append(a); eb.append(b)
                    pts.append(pairs)
                est, lo, hi = two_stage(pts, rng, DRAWS)
                hits += lo > 1.0
                estimates.append(est)
                widths.append(hi / lo)
            power = hits / sims
            cells["modelled" if effect == "modelled" else "%.2f" % effect] = {
                "power": power, "mc_se": math.sqrt(max(power * (1 - power), 1e-12) / sims),
                "median_estimate": statistics.median(estimates), "median_ci_hi_over_lo": statistics.median(widths)}
            if effect == "modelled":
                spread = {"cv_rank_stage_A": cv(ra), "cv_rank_stage_B": cv(rb), "cv_online_A": cv(oa),
                          "cv_online_B": cv(ob), "cv_e2e_A": cv(ea), "cv_e2e_B": cv(eb)}
        # A/A: two modelled B draws
        aa_hit = aa_cold_hit = aa_ci_hit = 0
        for _ in range(sims):
            e2e_pts, cold_pairs = [], []
            for _ in range(points):
                q = pick(points_prior)
                pairs = []
                for _ in range(K_AA):
                    x, y = side_b(pick(q)), side_b(pick(q))
                    x = (x[0] * pick(rank_f), x[1] * pick(cold_f), x[2], x[3])
                    y = (y[0] * pick(rank_f), y[1] * pick(cold_f), y[2], y[3])
                    pairs.append((x[0] + x[1], y[0] + y[1]))
                    cold_pairs.append((x[1], y[1]))
                e2e_pts.append(pairs)
            e, lo, hi = two_stage(e2e_pts, rng, DRAWS)
            c = sum(a for a, _ in cold_pairs) / sum(b for _, b in cold_pairs)
            aa_hit += AA_BAND[0] <= e <= AA_BAND[1]
            aa_cold_hit += AA_BAND[0] <= c <= AA_BAND[1]
            aa_ci_hit += lo <= 1.0 <= hi
        planted_hits = 0
        for _ in range(sims):
            pairs = []
            for _ in range(points * K_PLANTED):
                s = pick(flat)
                base = s["index_ms"] * f_i
                pairs.append((PLANT * base * pick(index_f), base * pick(index_f)))
            values = []
            for _ in range(DRAWS):
                d = [pick(pairs) for _ in pairs]
                values.append(sum(x for x, _ in d) / sum(y for _, y in d))
            values.sort()
            planted_hits += values[int(0.025 * DRAWS)] > 1.0
        # probe law of kD4: attempts of the D4 base drawn from the archived normalised attempts
        norm = [p / law_m38 for p in attempts_probes]
        n_law = points * k * COLUMNS_D
        law_pass = {}
        for true_ratio in (1.0, 1.15, 1.30):
            passes = 0
            for _ in range(4000):
                m = statistics.mean(norm[rng.randrange(len(norm))] for _ in range(n_law)) * true_ratio
                passes += BAND[0] <= m <= BAND[1]
            law_pass["%.2f" % true_ratio] = passes / 4000
        return {"points": points, "primary_pairs_per_point": k, "primary_pairs": points * k,
                "distinct_rank_seeds": points * k, "kD4_attempts_for_law_gate": n_law, "cells": cells,
                "power_at_min_delta": cells["%.2f" % MIN_DELTA]["power"], "type_i_at_1.00": cells["1.00"]["power"],
                "variance": spread,
                "aa_control": {"pairs": points * K_AA, "e2e_point_inside_0.97_1.03_rate": aa_hit / sims,
                               "e2e_interval_contains_1_rate": aa_ci_hit / sims,
                               "cold_point_inside_0.97_1.03_rate": aa_cold_hit / sims, "band": list(AA_BAND)},
                "planted_control": {"pairs": points * K_PLANTED, "modelled_index_build_factor": PLANT,
                                    "lower_bound_above_1_rate": planted_hits / sims},
                "law_gate": {"attempts": n_law, "band": list(BAND), "pass_rate_by_true_law_ratio": law_pass}}

    designs = {"%dx%d" % (p, k): design_block(p, k) for p, k in DESIGNS}
    chosen = designs[args.design]
    p_chosen, k_chosen = (int(v) for v in args.design.split("x"))
    walls = {arm: statistics.mean(v) / 1000 for arm, v in prior["process_wall_ms"].items()}
    ratio = STORED["D4"] / STORED["M38"]
    cold_save = (mean["index_ms"] * (1 - f_i) + mean["scan_selftest_ms"] * (1 - f_s)) / 1000
    online_cost = mean["online_ms"] * (work - 1) / 1000
    untimed_cold = walls["cM38FO"] - mean["cold_ms"] / 1000
    walls_d = {"cD4FO": walls["cM38FO"] - cold_save + online_cost - untimed_cold * (1 - ratio),
               "kD4FO": (walls["kM38FO"] - mean["rank_stage_ms"] / 1000 - cold_save - untimed_cold * (1 - ratio)
                         + COLUMNS_D * statistics.mean(attempts_ns) * work / 1000)}
    walls.update({"kD4FOaa": walls_d["kD4FO"], "cD4FOaa": walls_d["cD4FO"], "cD4FO": walls_d["cD4FO"],
                  "kD4FO": walls_d["kD4FO"], "cD4FOX": walls_d["cD4FO"] + PLANT_EXTRA_S})
    per_point = {"kM38FO": k_chosen, "cM38FO": k_chosen, "kD4FO": k_chosen + K_AA, "cD4FO": k_chosen + K_AA + K_PLANTED,
                 "kD4FOaa": K_AA, "cD4FOaa": K_AA, "cD4FOX": K_PLANTED, "rT": 1}
    q0 = {"cM38FO": 1, "cD4FO": 1}
    point_s = sum(n * walls[arm] for arm, n in per_point.items())
    schedule_s = p_chosen * point_s + sum(n * walls[arm] for arm, n in q0.items())
    total_min = FIXED_BEFORE_MIN + schedule_s / 60 + FIXED_AFTER_MIN
    slow_min = FIXED_BEFORE_MIN * 1.5 + 1.5 * schedule_s / 60 + FIXED_AFTER_MIN
    out = {
        "schema": 1,
        "label": "sizing by simulation; the D4 side is modelled; no result",
        "prior": "inputs/power_prior.json (run 41869146827, the field-ops archive: the M38 side)",
        "candidate_model": {"source": "inputs/local_profile.json modelled (LOCAL DIAGNOSTIC) and the entry ratio",
                            "index_build_factor": f_i, "selftest_factor": f_s, "work_factor_E_M38_over_E_D4": work,
                            "rank_attempts_per_process": COLUMNS_D},
        "method": ("simulated receipts drawn from the prior; primary statistic and two-stage paired bootstrap of "
                   "verify_receipt.py (%d simulations per cell, %d bootstrap draws each)" % (sims, DRAWS)),
        "prior_means_ms": dict(mean, E2E_A=e2e_a, E2E_B_modelled=e2e_b_modelled),
        "expected_ratio_at_prior_means": e2e_a / e2e_b_modelled,
        "min_delta": MIN_DELTA,
        "designs": designs,
        "chosen_design": args.design,
        "design": {"points": p_chosen, "primary_pairs_per_point": k_chosen, "aa_pairs_per_point": K_AA,
                   "planted_pairs_per_point": K_PLANTED, "attempts_per_rank_block_B": COLUMNS_D,
                   "primary_pairs": p_chosen * k_chosen, "distinct_rank_seeds": p_chosen * k_chosen},
        "cells": chosen["cells"],
        "power_at_min_delta": chosen["power_at_min_delta"],
        "type_i_at_1.00": chosen["type_i_at_1.00"],
        "aa_control": chosen["aa_control"], "law_gate": chosen["law_gate"],
        "planted_control": chosen["planted_control"], "variance": chosen["variance"],
        "runtime": {"mean_process_wall_s": walls, "processes_per_point": per_point, "q0_processes": q0,
                    "point_segment_s": point_s, "schedule_min": schedule_s / 60,
                    "fixed_before_schedule_min": FIXED_BEFORE_MIN, "fixed_after_schedule_min": FIXED_AFTER_MIN,
                    "job_total_min": total_min, "job_total_min_on_a_1.5x_slower_host": slow_min,
                    "time_guard_deadline_min": DEADLINE_MIN, "job_limit_min": JOB_LIMIT_MIN,
                    "fits_one_job": slow_min < DEADLINE_MIN},
    }
    OUT.parent.mkdir(exist_ok=True)
    if not args.quick:
        OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    summary = {k: {"power_min_delta": v["power_at_min_delta"], "type_i": v["type_i_at_1.00"],
                   "cells": {c: round(x["power"], 3) for c, x in v["cells"].items()},
                   "aa": v["aa_control"], "planted": v["planted_control"]["lower_bound_above_1_rate"],
                   "law": v["law_gate"]["pass_rate_by_true_law_ratio"], "var": v["variance"]}
               for k, v in designs.items()}
    print(json.dumps({"expected_ratio": out["expected_ratio_at_prior_means"], "designs": summary}, indent=1, sort_keys=True))
    print(json.dumps(out["runtime"], sort_keys=True))


if __name__ == "__main__":
    main()
