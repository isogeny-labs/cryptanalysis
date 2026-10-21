#!/usr/bin/env python3
"""Power and runtime of the rank-finder design (before any timing).

Prior: `inputs/power_prior.json` (`make_power_prior.py`), the parent's
archived run 39464544962: 36 primary pairs of the current row's processes
(the parent's side B: kM38IC rank stage; cM38IC cold, index build and
self-test) on 12 points, and 24 A/A pairs of the same producer (B / Baa
ratios).

The design (`make_protocol.py`) has POINTS points, each with K alternating
primary pairs. Side A = (kM38IC, cM38IC), the current row; side B =
(kM38RF, cM38RF), the rank-finder producer; both rank processes of a pair
use the pair's rank seed. E2E(side) = rank stage + cold. The primary is
R = sum E2E(A) / sum E2E(B) over the pairs with the two-stage paired
bootstrap of `verify_receipt.py`.

Each simulated pair draws one archived primary pair of one archived point
(a point keeps its archived point across its K pairs):

* A: rank = archived rank stage x a rank factor; cold = archived cold x a
  cold factor;
* B: rank = the same archived rank stage x f_r x an independent rank factor
  (the same seed gives the same rank work, a gate of the run); cold = the
  same archived cold x an independent cold factor (the change is in the
  rank stage's probe loop only; the cold process never runs it).

The factors are the archived A/A ratios (B / Baa, 24 pairs): one ratio of
two processes used as one process's factor overstates its noise by about
sqrt(2), so the power figures are conservative. For an effect cell E, f_r is
set so that the E2E ratio at the prior means equals E (E = 1.00: type I).
The `modelled` cell takes f_r from the local diagnostic
(`inputs/local_profile.json`, `modelled.rank_stage_factor`: the rank-finder
producer's rank stage over the row's, in alternating local rank processes).

Controls simulated:

* A/A: K_AA alternating pairs per point of B against Baa (same seed), both
  with the modelled B costs and independent factors; the rate at which the
  E2E and cold point estimates are inside [0.97, 1.03];
* planted: kM38RFX / kM38RF rank stage over POINTS planted pairs, with the
  planted factor PLANT (a conservative 1.5, below the local 2.1) and
  independent rank factors; the rate at which the 95% lower bound exceeds 1;
* probe law: kM38IC's pooled probes per relation over POINTS * K distinct
  seeds (16 attempts each) in [0.80, 1.20], resampled from the parent run's
  576 attempts, at the archived law and at a law 1.5x worse.

Runtime: mean process walls per arm (the parent run for side A's arms, cPIC,
cM10IC and rT; side B's rank arms modelled as side A's rank wall minus the
modelled saving, its cold arms as side A's; the planted arm as side B's
rank wall plus PLANT_EXTRA_S), counts from the design, plus the fixed cost
before the schedule (FIXED_BEFORE_MIN) and after it. This is the parent's
`power_check.py` with the arms, the prior and the modelled stage changed.
"""

import argparse
import base64
import hashlib
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
ENTRIES_M38 = 30366551
COLUMNS = 16
POINTS = 12
K = 3
K_AA = 2
K_PLANTED = 1
EFFECTS = (1.0, 1.01, 1.02, 1.03, 1.05, 1.10)
MIN_DELTA = 1.03
BAND = (0.80, 1.20)
AA_BAND = (0.97, 1.03)
PLANT = 1.5
PLANT_EXTRA_S = 8.0      # local: frame_plant adds about 5.7 s to the rank-finder rank stage (exactness_M38_plant)
SIMULATIONS = 400
DRAWS = 500
SEED = 2026102141
FIXED_BEFORE_MIN = 17.0  # parent job: 68 min, schedule 52.9 min: about 15 min before and after the schedule
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


def counts():
    per_point = {"kM38IC": K, "cM38IC": K, "kM38RF": K + K_AA + K_PLANTED, "cM38RF": K + K_AA,
                 "kM38RFaa": K_AA, "cM38RFaa": K_AA, "kM38RFX": K_PLANTED, "rT": 1}
    q0 = {"cPIC": 1, "cPRF": 1, "cM10IC": 1, "cM10RF": 1, "cM38IC": 1, "cM38RF": 1}
    return per_point, q0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--law-run-dir", type=Path, required=True,
                        help="a copy of the parent's run_github_39464544962 (for kM38IC attempt probes)")
    args = parser.parse_args()
    sims = 40 if args.quick else SIMULATIONS
    prior = json.loads(PRIOR.read_text())
    profile = json.loads(PROFILE.read_text())
    f_model = profile["modelled"]["rank_stage_factor"]
    by_point = {}
    for key, side in sorted(prior["side_A_primary_pairs"].items()):
        by_point.setdefault(key.split("/")[0], []).append(side)
    points_prior = [v for _, v in sorted(by_point.items())]
    flat = [s for v in points_prior for s in v]
    aa = list(prior["aa_ratios_B_over_Baa"].values())
    rank_f = [a["rank_stage"] for a in aa]
    cold_f = [a["cold"] for a in aa]
    mean = {k: statistics.mean(s[k] for s in flat) for k in ("rank_stage_ms", "cold_ms", "index_ms",
                                                            "scan_selftest_ms")}
    e2e_a = mean["rank_stage_ms"] + mean["cold_ms"]

    e2e_b_modelled = f_model * mean["rank_stage_ms"] + mean["cold_ms"]
    rng = random.Random(SEED)
    pick = lambda xs: xs[rng.randrange(len(xs))]  # noqa: E731

    cells = {}
    for effect in EFFECTS + ("modelled",):
        if effect == "modelled":
            fr = f_model
        else:
            saving = e2e_a - e2e_a / effect
            fr = 1 - saving / mean["rank_stage_ms"]
        hits, estimates, widths = 0, [], []
        for _ in range(sims):
            points = []
            for _ in range(POINTS):
                q = pick(points_prior)
                pairs = []
                for _ in range(K):
                    s = pick(q)
                    a = s["rank_stage_ms"] * pick(rank_f) + s["cold_ms"] * pick(cold_f)
                    b = s["rank_stage_ms"] * fr * pick(rank_f) + s["cold_ms"] * pick(cold_f)
                    pairs.append((a, b))
                points.append(pairs)
            est, lo, hi = two_stage(points, rng, DRAWS)
            hits += lo > 1.0
            estimates.append(est)
            widths.append(hi / lo)
        power = hits / sims
        cells["modelled" if effect == "modelled" else "%.2f" % effect] = {
            "rank_stage_factor": fr, "power": power,
            "mc_se": math.sqrt(max(power * (1 - power), 1e-12) / sims),
            "median_estimate": statistics.median(estimates), "median_ci_hi_over_lo": statistics.median(widths)}

    aa_e2e_in = aa_cold_in = 0
    for _ in range(sims):
        e2e_pairs, cold_pairs = [], []
        for _ in range(POINTS):
            q = pick(points_prior)
            for _ in range(K_AA):
                s = pick(q)
                c1, c2 = (s["cold_ms"] * pick(cold_f) for _ in range(2))
                r1, r2 = (s["rank_stage_ms"] * f_model * pick(rank_f) for _ in range(2))
                e2e_pairs.append((r1 + c1, r2 + c2))
                cold_pairs.append((c1, c2))
        e = sum(a for a, _ in e2e_pairs) / sum(b for _, b in e2e_pairs)
        c = sum(a for a, _ in cold_pairs) / sum(b for _, b in cold_pairs)
        aa_e2e_in += AA_BAND[0] <= e <= AA_BAND[1]
        aa_cold_in += AA_BAND[0] <= c <= AA_BAND[1]

    planted_hits = 0
    for _ in range(sims):
        pairs = []
        for _ in range(POINTS * K_PLANTED):
            s = pick(flat)
            base = s["rank_stage_ms"] * f_model
            pairs.append((PLANT * base * pick(rank_f), base * pick(rank_f)))
        values = []
        for _ in range(DRAWS):
            d = [pick(pairs) for _ in pairs]
            values.append(sum(x for x, _ in d) / sum(y for _, y in d))
        values.sort()
        planted_hits += values[int(0.025 * DRAWS)] > 1.0

    # Probe law: the parent run's kM38IC attempt probes (576 attempts, 36 seeds), read from its raw records.
    runs_path = args.law_run_dir / "panel" / "runs.jsonl"
    if hashlib.sha256(runs_path.read_bytes()).hexdigest() != prior["sources"]["runs_jsonl_sha256"]:
        raise SystemExit("law run directory differs from the prior's archive")
    probes = []
    for line in runs_path.read_text().splitlines():
        row = json.loads(line)
        if row["status"] == "valid" and row["arm"] == "kM38IC" and row.get("role") == "primary":
            lines = (args.law_run_dir / "panel" / row["stdout_file"]).read_text().splitlines()
            raw = json.loads(base64.b64decode(next(l[8:] for l in lines if l.startswith("raw_b64="))))
            summary = next(r for r in raw["records"] if r.get("kind") == "compact_orbit_dlp_summary")
            probes += summary["rank_attempt_probes"]
    law = R / (166 * ENTRIES_M38)
    ratios = [p / law for p in probes]
    n_law = POINTS * K * COLUMNS
    passes = rejects_worse = 0
    for _ in range(4000):
        m = statistics.mean(ratios[rng.randrange(len(ratios))] for _ in range(n_law))
        passes += BAND[0] <= m <= BAND[1]
        rejects_worse += not (BAND[0] <= 1.5 * m <= BAND[1])

    walls = {arm: statistics.mean(v) / 1000 for arm, v in prior["process_wall_ms"].items()}
    save_s = (1 - f_model) * mean["rank_stage_ms"] / 1000
    walls = {arm: walls[arm] for arm in ("kM38IC", "cM38IC", "cPIC", "cM10IC", "rT")}
    walls.update({"kM38RF": walls["kM38IC"] - save_s, "cM38RF": walls["cM38IC"],
                  "kM38RFaa": walls["kM38IC"] - save_s, "cM38RFaa": walls["cM38IC"],
                  "kM38RFX": walls["kM38IC"] - save_s + PLANT_EXTRA_S, "cPRF": walls["cPIC"],
                  "cM10RF": walls["cM10IC"]})
    per_point, q0 = counts()
    point_s = sum(n * walls[arm] for arm, n in per_point.items())
    schedule_s = POINTS * point_s + sum(n * walls[arm] for arm, n in q0.items())
    total_min = FIXED_BEFORE_MIN + schedule_s / 60 + FIXED_AFTER_MIN
    slow_min = FIXED_BEFORE_MIN * 1.5 + 1.5 * schedule_s / 60 + FIXED_AFTER_MIN
    out = {
        "schema": 1,
        "prior": "inputs/power_prior.json (run 39464544962, the parent's archived run, the current row's producer)",
        "candidate_model": {"source": "inputs/local_profile.json modelled (LOCAL DIAGNOSTIC)",
                            "rank_stage_factor": f_model},
        "design": {"points": POINTS, "primary_pairs_per_point": K, "aa_pairs_per_point": K_AA,
                   "planted_pairs_per_point": K_PLANTED, "attempts_per_rank_block": COLUMNS,
                   "primary_pairs": POINTS * K, "distinct_rank_seeds": POINTS * K},
        "method": ("simulated receipts drawn from the prior; primary statistic and two-stage paired bootstrap of "
                   "verify_receipt.py (%d simulations per cell, %d bootstrap draws each)" % (sims, DRAWS)),
        "prior_means_ms": dict(mean, E2E_A=e2e_a, E2E_B_modelled=e2e_b_modelled),
        "expected_ratio_at_prior_means": e2e_a / e2e_b_modelled,
        "expected_rank_stage_ratio": 1 / f_model,
        "min_delta": MIN_DELTA,
        "cells": cells,
        "power_at_min_delta": cells["%.2f" % MIN_DELTA]["power"],
        "type_i_at_1.00": cells["1.00"]["power"],
        "aa_control": {"pairs": POINTS * K_AA, "e2e_point_estimate_inside_band_rate": aa_e2e_in / sims,
                       "cold_point_estimate_inside_band_rate": aa_cold_in / sims, "band": list(AA_BAND)},
        "law_gate": {"attempts": n_law, "band": list(BAND), "pass_rate_at_archived_law": passes / 4000,
                     "rejection_rate_for_law_1.5x_worse": rejects_worse / 4000,
                     "archived_pooled_ratio": statistics.mean(ratios), "archived_attempts": len(ratios)},
        "planted_control": {"pairs": POINTS * K_PLANTED, "modelled_rank_stage_factor": PLANT,
                            "lower_bound_above_1_rate": planted_hits / sims},
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
    print(json.dumps({k: out[k] for k in ("expected_ratio_at_prior_means", "expected_rank_stage_ratio",
                                          "power_at_min_delta", "type_i_at_1.00", "aa_control", "law_gate",
                                          "planted_control")}, sort_keys=True))
    print(json.dumps(out["runtime"], sort_keys=True))
    print(json.dumps(cells, sort_keys=True))


if __name__ == "__main__":
    main()
