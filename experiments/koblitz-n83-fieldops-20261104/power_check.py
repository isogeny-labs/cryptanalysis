#!/usr/bin/env python3
"""Power and runtime of the field-ops design (before any timing).

Prior: `inputs/power_prior.json` (`make_power_prior.py`), the parent's
archived run 39527997793: 36 primary pairs of the current row's processes
(the parent's side B: kM38RF rank stage; cM38RF cold, index build, self-test
and online) on 12 points, and 24 A/A pairs of the same producer (B / Baa
ratios).

The design (`make_protocol.py`) has POINTS points, each with K alternating
primary pairs. Side A = (kM38RF, cM38RF), the current row; side B =
(kM38FO, cM38FO), the field-ops producer; both rank processes of a pair use
the pair's rank seed. E2E(side) = rank stage + cold. The primary is
R = sum E2E(A) / sum E2E(B) over the pairs with the two-stage paired
bootstrap of `verify_receipt.py`.

Each simulated pair draws one archived primary pair of one archived point
(a point keeps its archived point across its K pairs):

* A: rank = archived rank stage x a rank factor; cold = archived cold x a
  cold factor;
* B: rank = the same archived rank stage x f_r x an independent rank factor
  (the same seed gives the same rank work, a gate of the run); cold =
  (archived cold - (1 - f_i) x archived index build - (1 - f_s) x archived
  scan self-test - (1 - f_o) x archived online) x an independent cold
  factor.

The factors are the archived A/A ratios (B / Baa, 24 pairs): one ratio of
two processes used as one process's factor overstates its noise by about
sqrt(2), so the power figures are conservative. For an effect cell E the
four modelled savings (1 - f_r) x rank stage, (1 - f_i) x index build,
(1 - f_s) x self-test and (1 - f_o) x online are scaled by one common
multiplier m (the modelled stage shares kept) so that the E2E ratio at the
prior means equals E (E = 1.00: m = 0, type I). The `modelled` cell takes
the four factors from the local diagnostic (`inputs/local_profile.json`,
`modelled`: index_build_factor, selftest_factor, rank_stage_factor,
online_factor, each the field-ops producer's stage over the row's, B / A, in
alternating local processes). The run stops with a message if that file does
not carry all four.

Controls simulated:

* A/A: K_AA alternating pairs per point of B against Baa (same seed), both
  with the modelled B costs and independent factors; the rate at which the
  E2E and cold point estimates are inside [0.97, 1.03];
* planted: cM38FOX / cM38FO index build over POINTS planted pairs, with the
  planted factor PLANT (a conservative 1.5) and independent index factors;
  the rate at which the 95% lower bound exceeds 1;
* probe law: kM38RF's pooled probes per relation over POINTS * K distinct
  seeds (16 attempts each) in [0.80, 1.20], resampled from the parent run's
  576 attempts, at the archived law and at a law 1.5x worse.

Runtime: mean process walls per arm (the parent run for side A's arms, cPRF,
cM10RF and rT). Side B's rank arms are modelled as side A's rank wall minus
the modelled rank-stage, index-build and self-test savings (the rank process
builds the same index and runs the same self-test), its cold arms as side A's
cold wall minus the modelled index-build, self-test and online savings; the
planted arm as side B's cold wall plus PLANT_EXTRA_S. Counts are the design's,
plus the fixed cost before the schedule (FIXED_BEFORE_MIN) and after it. This
is the parent's `power_check.py` with the arms, the prior and the modelled
stages changed (round 2's planted design: cold processes, index build).
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
PLANT_EXTRA_S = 9.0      # round 2: lift_plant added 7.9 s in its run, about 11 s on a slower VM (not re-measured here)
SIMULATIONS = 400
DRAWS = 500
SEED = 2026110441
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
    per_point = {"kM38RF": K, "cM38RF": K, "kM38FO": K + K_AA, "cM38FO": K + K_AA + K_PLANTED,
                 "kM38FOaa": K_AA, "cM38FOaa": K_AA, "cM38FOX": K_PLANTED, "rT": 1}
    q0 = {"cPRF": 1, "cPFO": 1, "cM10RF": 1, "cM10FO": 1, "cM38RF": 1, "cM38FO": 1}
    return per_point, q0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--law-run-dir", type=Path, required=True,
                        help="a copy of the parent's run_github_39527997793 (for kM38RF attempt probes)")
    args = parser.parse_args()
    sims = 40 if args.quick else SIMULATIONS
    prior = json.loads(PRIOR.read_text())
    if not PROFILE.exists():
        raise SystemExit("inputs/local_profile.json is missing: the local profile must exist before this check")
    profile = json.loads(PROFILE.read_text())
    keys = ("index_build_factor", "selftest_factor", "rank_stage_factor", "online_factor")
    missing = [k for k in keys if not isinstance((profile.get("modelled") or {}).get(k), (int, float))]
    if missing:
        raise SystemExit("inputs/local_profile.json `modelled` lacks %s: the local profile must give the four "
                         "stage factors (B / A) before this check" % ", ".join(missing))
    f_i, f_s, f_r, f_o = (float(profile["modelled"][k]) for k in keys)
    by_point = {}
    for key, side in sorted(prior["side_A_primary_pairs"].items()):
        by_point.setdefault(key.split("/")[0], []).append(side)
    points_prior = [v for _, v in sorted(by_point.items())]
    flat = [s for v in points_prior for s in v]
    aa = list(prior["aa_ratios_B_over_Baa"].values())
    rank_f = [a["rank_stage"] for a in aa]
    cold_f = [a["cold"] for a in aa]
    index_f = [a["index"] for a in aa]
    mean = {k: statistics.mean(s[k] for s in flat) for k in ("rank_stage_ms", "cold_ms", "index_ms",
                                                            "scan_selftest_ms", "online_ms")}
    e2e_a = mean["rank_stage_ms"] + mean["cold_ms"]

    def stage_factors(m):
        """The four modelled factors with their savings scaled by m (m = 1: the local model)."""
        return tuple(1 - m * (1 - f) for f in (f_r, f_i, f_s, f_o))

    def rank_b(side, fr):
        return side["rank_stage_ms"] * fr

    def cold_b(side, fi, fs, fo):
        return side["cold_ms"] - (1 - fi) * side["index_ms"] - (1 - fs) * side["scan_selftest_ms"] - \
            (1 - fo) * side["online_ms"]

    def e2e_b(side, factors):
        fr, fi, fs, fo = factors
        return rank_b(side, fr) + cold_b(side, fi, fs, fo)

    model = stage_factors(1.0)
    e2e_b_modelled = e2e_b(mean, model)
    saving_modelled = e2e_a - e2e_b_modelled
    rng = random.Random(SEED)
    pick = lambda xs: xs[rng.randrange(len(xs))]  # noqa: E731

    cells = {}
    for effect in EFFECTS + ("modelled",):
        if effect == "modelled":
            factors = model
        else:
            if saving_modelled <= 0:
                raise SystemExit("the local model saves nothing end to end: no effect cell can be scaled from it")
            factors = stage_factors((e2e_a - e2e_a / effect) / saving_modelled)
        fr, fi, fs, fo = factors
        hits, estimates, widths = 0, [], []
        for _ in range(sims):
            points = []
            for _ in range(POINTS):
                q = pick(points_prior)
                pairs = []
                for _ in range(K):
                    s = pick(q)
                    a = s["rank_stage_ms"] * pick(rank_f) + s["cold_ms"] * pick(cold_f)
                    b = rank_b(s, fr) * pick(rank_f) + cold_b(s, fi, fs, fo) * pick(cold_f)
                    pairs.append((a, b))
                points.append(pairs)
            est, lo, hi = two_stage(points, rng, DRAWS)
            hits += lo > 1.0
            estimates.append(est)
            widths.append(hi / lo)
        power = hits / sims
        cells["modelled" if effect == "modelled" else "%.2f" % effect] = {
            "rank_stage_factor": fr, "index_build_factor": fi, "selftest_factor": fs, "online_factor": fo,
            "power": power,
            "mc_se": math.sqrt(max(power * (1 - power), 1e-12) / sims),
            "median_estimate": statistics.median(estimates), "median_ci_hi_over_lo": statistics.median(widths)}

    aa_e2e_in = aa_cold_in = 0
    for _ in range(sims):
        e2e_pairs, cold_pairs = [], []
        for _ in range(POINTS):
            q = pick(points_prior)
            for _ in range(K_AA):
                s = pick(q)
                c1, c2 = (cold_b(s, f_i, f_s, f_o) * pick(cold_f) for _ in range(2))
                r1, r2 = (rank_b(s, f_r) * pick(rank_f) for _ in range(2))
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
            base = s["index_ms"] * f_i
            pairs.append((PLANT * base * pick(index_f), base * pick(index_f)))
        values = []
        for _ in range(DRAWS):
            d = [pick(pairs) for _ in pairs]
            values.append(sum(x for x, _ in d) / sum(y for _, y in d))
        values.sort()
        planted_hits += values[int(0.025 * DRAWS)] > 1.0

    # Probe law: the parent run's kM38RF attempt probes (576 attempts, 36 seeds), read from its raw records.
    runs_path = args.law_run_dir / "panel" / "runs.jsonl"
    if hashlib.sha256(runs_path.read_bytes()).hexdigest() != prior["sources"]["runs_jsonl_sha256"]:
        raise SystemExit("law run directory differs from the prior's archive")
    probes = []
    for line in runs_path.read_text().splitlines():
        row = json.loads(line)
        if row["status"] == "valid" and row["arm"] == "kM38RF" and row.get("role") == "primary":
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
    save_rank_s = ((1 - f_r) * mean["rank_stage_ms"] + (1 - f_i) * mean["index_ms"] +
                   (1 - f_s) * mean["scan_selftest_ms"]) / 1000
    save_cold_s = ((1 - f_i) * mean["index_ms"] + (1 - f_s) * mean["scan_selftest_ms"] +
                   (1 - f_o) * mean["online_ms"]) / 1000
    walls = {arm: walls[arm] for arm in ("kM38RF", "cM38RF", "cPRF", "cM10RF", "rT")}
    walls.update({"kM38FO": walls["kM38RF"] - save_rank_s, "cM38FO": walls["cM38RF"] - save_cold_s,
                  "kM38FOaa": walls["kM38RF"] - save_rank_s, "cM38FOaa": walls["cM38RF"] - save_cold_s,
                  "cM38FOX": walls["cM38RF"] - save_cold_s + PLANT_EXTRA_S, "cPFO": walls["cPRF"] - save_cold_s,
                  "cM10FO": walls["cM10RF"] - save_cold_s})
    per_point, q0 = counts()
    point_s = sum(n * walls[arm] for arm, n in per_point.items())
    schedule_s = POINTS * point_s + sum(n * walls[arm] for arm, n in q0.items())
    total_min = FIXED_BEFORE_MIN + schedule_s / 60 + FIXED_AFTER_MIN
    slow_min = FIXED_BEFORE_MIN * 1.5 + 1.5 * schedule_s / 60 + FIXED_AFTER_MIN
    out = {
        "schema": 1,
        "prior": "inputs/power_prior.json (run 39527997793, the parent's archived run, the current row's producer)",
        "candidate_model": {"source": "inputs/local_profile.json modelled (LOCAL DIAGNOSTIC)",
                            "index_build_factor": f_i, "selftest_factor": f_s, "rank_stage_factor": f_r,
                            "online_factor": f_o},
        "design": {"points": POINTS, "primary_pairs_per_point": K, "aa_pairs_per_point": K_AA,
                   "planted_pairs_per_point": K_PLANTED, "attempts_per_rank_block": COLUMNS,
                   "primary_pairs": POINTS * K, "distinct_rank_seeds": POINTS * K},
        "method": ("simulated receipts drawn from the prior; primary statistic and two-stage paired bootstrap of "
                   "verify_receipt.py (%d simulations per cell, %d bootstrap draws each)" % (sims, DRAWS)),
        "prior_means_ms": dict(mean, E2E_A=e2e_a, E2E_B_modelled=e2e_b_modelled),
        "expected_ratio_at_prior_means": e2e_a / e2e_b_modelled,
        "expected_index_build_ratio": 1 / f_i, "expected_selftest_ratio": 1 / f_s,
        "expected_rank_stage_ratio": 1 / f_r, "expected_online_ratio": 1 / f_o,
        "min_delta": MIN_DELTA,
        "cells": cells,
        "power_at_min_delta": cells["%.2f" % MIN_DELTA]["power"],
        "type_i_at_1.00": cells["1.00"]["power"],
        "aa_control": {"pairs": POINTS * K_AA, "e2e_point_estimate_inside_band_rate": aa_e2e_in / sims,
                       "cold_point_estimate_inside_band_rate": aa_cold_in / sims, "band": list(AA_BAND)},
        "law_gate": {"attempts": n_law, "band": list(BAND), "pass_rate_at_archived_law": passes / 4000,
                     "rejection_rate_for_law_1.5x_worse": rejects_worse / 4000,
                     "archived_pooled_ratio": statistics.mean(ratios), "archived_attempts": len(ratios)},
        "planted_control": {"pairs": POINTS * K_PLANTED, "modelled_index_build_factor": PLANT,
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
    print(json.dumps({k: out[k] for k in ("expected_ratio_at_prior_means", "expected_index_build_ratio",
                                          "expected_selftest_ratio", "expected_rank_stage_ratio", "expected_online_ratio",
                                          "power_at_min_delta", "type_i_at_1.00", "aa_control", "law_gate",
                                          "planted_control")}, sort_keys=True))
    print(json.dumps(out["runtime"], sort_keys=True))
    print(json.dumps(cells, sort_keys=True))


if __name__ == "__main__":
    main()
