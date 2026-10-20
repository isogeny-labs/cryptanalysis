#!/usr/bin/env python3
"""Power and runtime of the replication design (before any timing).

Prior: `inputs/power_prior.json` (`make_power_prior.py`), the parent's
archived Tier 1 run 39335956567. It holds 20 cold points (cPI, cM38I and
cM38Iaa) and 16 rank blocks (kPI in 4 of them, kM38I and kM38Iaa in all 16,
kM38IX in 4).

The design (`make_protocol.py`) has POINTS points. Each point gets K
alternating primary pairs. A pair has two sides, run back to back:
A = (kPI, cPI) and B = (kM38I, cM38I). Each side's E2E is the rank stage of
its rank process plus the cold time of its cold process. The primary is
R = sum over pairs of E2E_A / sum over pairs of E2E_B. Its 95% interval is
a two-stage paired bootstrap: draw the points with replacement, then the
pairs within each drawn point with replacement. A and B of a pair are always
drawn together. This is the statistic and bootstrap of `verify_receipt.py`.

Each simulated observation is drawn from the prior:

* kPI: one archived kPI block, its 600 attempts resampled, its non-attempt
  time, times a rank process factor;
* kM38I: a non-attempt time from an archived kM38I block, 16 attempts drawn
  from the pooled 256 archived kM38I attempts, times f and a rank process
  factor;
* cPI and cM38I: one archived point's cPI and cM38I cold times. Each is
  multiplied by its own cold process factor. A point keeps its archived
  point across its K pairs.

The rank process factors are the archived kM38Iaa / kM38I rank-stage ratios
(16 blocks). The cold factors are the archived cM38Iaa / cM38I cold ratios
(20 points). A ratio of two processes carries the noise of both, so using it
as one process's factor overstates the per-process noise by about sqrt(2).
That makes the power figures conservative.

f is chosen so that the E2E ratio at the prior's means equals the effect E.
E = 1.00 means no gain, so its rejection rate is the type I error. The
`modelled` cell sets f = 1, the parent's measured costs (about 7.6x). Power
is the share of simulations whose lower 95% bound exceeds 1.

The script also simulates three controls:

* the A/A control: K_AA alternating pairs per point of B against B', with
  the same rank seed and so the same attempts, each process with its own
  factor. It reports the rate at which the point estimate is inside
  [0.97, 1.03] for E2E and for cold;
* the probe-law gate: the pooled kM38I probes per relation over its
  POINTS * K distinct blocks (16 attempts each), divided by the law
  r / (166 E_M38). It reports the pass rate of [0.80, 1.20] at the archived
  law, and the rejection rate for a law 1.5x worse;
* the planted control: kM38IX / kM38I per attempt over POINTS planted pairs,
  resampled from the archived paired blocks. It reports the rate at which
  the lower bound exceeds 1.

Runtime: the archived mean process wall of each arm times its count in the
design, plus the parent job's fixed cost before the schedule (11.7 min) and
after it (about 2 min). The estimate is also scaled to a host 1.5x slower.

`--quick` is for development only.
"""

import argparse
import json
import math
import random
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "inputs" / "power_prior.json"
OUT = HERE / "analysis" / "power.json"
R = 8569786107849059
ENTRIES_M38 = 30366551
COLUMNS = 16
POINTS = 10
K = 3
K_AA = 2
K_PLANTED = 1
EFFECTS = (1.0, 1.10, 1.25, 1.50, 2.00, 4.00)
MIN_DELTA = 1.50
BAND = (0.80, 1.20)
AA_BAND = (0.97, 1.03)
SIMULATIONS = 400
DRAWS = 500
SEED = 2026102011
FIXED_BEFORE_MIN = 11.7   # parent run: job start to runner start (restore, build, tests, table checks)
FIXED_AFTER_MIN = 2.0     # verifier and upload
DEADLINE_MIN = 285
JOB_LIMIT_MIN = 300


def two_stage(points, rng, draws):
    """points: [[(a, b), ...] per point]. (estimate, lo, hi) of sum a / sum b."""
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
    """Processes per arm in the design (per point, and the Q0 segment)."""
    per_point = {"kPI": K, "cPI": K, "kM38I": K + K_AA + K_PLANTED, "cM38I": K + K_AA,
                 "kM38Iaa": K_AA, "cM38Iaa": K_AA, "kM38IX": K_PLANTED, "rT": 1}
    return per_point, {"cPI": 1, "cM38I": 1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    sims = 40 if args.quick else SIMULATIONS
    prior = json.loads(PRIOR.read_text())
    blocks = prior["rank_blocks"]
    kpi = [{"rest": b["kPI"]["non_attempt_ms"], "ms": [a / 1e6 for a in b["kPI"]["attempt_ns"]]}
           for _, b in sorted(blocks.items()) if "kPI" in b]
    m38 = [b["kM38I"] for _, b in sorted(blocks.items())]
    pooled = [a / 1e6 for b in m38 for a in b["attempt_ns"]]
    rests = [b["non_attempt_ms"] for b in m38]
    rank_factors = [b["kM38Iaa"]["rank_stage_ms"] / b["kM38I"]["rank_stage_ms"] for _, b in sorted(blocks.items())]
    cold = [(v["cPI"], v["cM38I"]) for _, v in sorted(prior["cold_ms"].items())]
    cold_factors = [v["cM38Iaa"] / v["cM38I"] for _, v in sorted(prior["cold_ms"].items())]
    mean_kpi = statistics.mean(b["rest"] + sum(b["ms"]) for b in kpi)
    mean_attempt = statistics.mean(pooled)
    mean_rest = statistics.mean(rests)
    mean_cpi = statistics.mean(c[0] for c in cold)
    mean_cm38 = statistics.mean(c[1] for c in cold)
    e2e_a = mean_kpi + mean_cpi
    e2e_b = mean_rest + COLUMNS * mean_attempt + mean_cm38
    rng = random.Random(SEED)

    def side_a(q):
        blk = kpi[rng.randrange(len(kpi))]
        g = rank_factors[rng.randrange(len(rank_factors))]
        rank = blk["rest"] + g * sum(rng.choices(blk["ms"], k=len(blk["ms"])))
        return rank + cold[q][0] * cold_factors[rng.randrange(len(cold_factors))]

    def side_b(q, f, attempts=None, rest=None):
        g = rank_factors[rng.randrange(len(rank_factors))]
        attempts = attempts if attempts is not None else rng.choices(pooled, k=COLUMNS)
        rest = rest if rest is not None else rests[rng.randrange(len(rests))]
        return rest + g * f * sum(attempts) + cold[q][1] * cold_factors[rng.randrange(len(cold_factors))]

    cells = {}
    for effect in EFFECTS + ("modelled",):
        f = 1.0 if effect == "modelled" else (e2e_a / effect - mean_cm38 - mean_rest) / (COLUMNS * mean_attempt)
        hits, estimates, widths = 0, [], []
        for _ in range(sims):
            points = []
            for _ in range(POINTS):
                q = rng.randrange(len(cold))
                points.append([(side_a(q), side_b(q, f)) for _ in range(K)])
            est, lo, hi = two_stage(points, rng, DRAWS)
            hits += lo > 1.0
            estimates.append(est)
            widths.append(hi / lo)
        power = hits / sims
        cells["modelled" if effect == "modelled" else "%.2f" % effect] = {
            "attempt_cost_factor": f, "power": power, "mc_se": math.sqrt(max(power * (1 - power), 1e-12) / sims),
            "median_estimate": statistics.median(estimates), "median_ci_hi_over_lo": statistics.median(widths)}

    aa_e2e_in = aa_cold_in = 0
    aa_estimates = []
    for _ in range(sims):
        e2e_pairs, cold_pairs = [], []
        for _ in range(POINTS):
            q = rng.randrange(len(cold))
            for _ in range(K_AA):
                attempts, rest = rng.choices(pooled, k=COLUMNS), rests[rng.randrange(len(rests))]
                b1, b2 = side_b(q, 1.0, attempts, rest), side_b(q, 1.0, attempts, rest)
                e2e_pairs.append((b1, b2))
                c1 = cold[q][1] * cold_factors[rng.randrange(len(cold_factors))]
                c2 = cold[q][1] * cold_factors[rng.randrange(len(cold_factors))]
                cold_pairs.append((c1, c2))
        e = sum(a for a, _ in e2e_pairs) / sum(b for _, b in e2e_pairs)
        c = sum(a for a, _ in cold_pairs) / sum(b for _, b in cold_pairs)
        aa_estimates.append(e)
        aa_e2e_in += AA_BAND[0] <= e <= AA_BAND[1]
        aa_cold_in += AA_BAND[0] <= c <= AA_BAND[1]

    law = R / (166 * ENTRIES_M38)
    ratios = [p / law for b in m38 for p in b["attempt_probes"]]
    n_law = POINTS * K * COLUMNS
    passes = rejects_worse = 0
    for _ in range(4000):
        m = statistics.mean(ratios[rng.randrange(len(ratios))] for _ in range(n_law))
        passes += BAND[0] <= m <= BAND[1]
        rejects_worse += not (BAND[0] <= 1.5 * m <= BAND[1])
    planted = [list(zip(b["kM38IX"]["attempt_ns"], b["kM38I"]["attempt_ns"])) for _, b in sorted(blocks.items())
               if "kM38IX" in b]
    planted_hits = 0
    for _ in range(sims):
        sample = [planted[rng.randrange(len(planted))] for _ in range(POINTS * K_PLANTED)]
        sample = [[blk[rng.randrange(len(blk))] for _ in blk] for blk in sample]
        values = []
        for _ in range(DRAWS):
            draw = [sample[rng.randrange(len(sample))] for _ in sample]
            draw = [[blk[rng.randrange(len(blk))] for _ in blk] for blk in draw]
            values.append(sum(x for blk in draw for x, _ in blk) / sum(y for blk in draw for _, y in blk))
        values.sort()
        planted_hits += values[int(0.025 * DRAWS)] > 1.0

    walls = {arm: statistics.mean(v) / 1000 for arm, v in prior["process_wall_ms"].items()}
    per_point, q0 = counts()
    point_s = sum(n * walls[arm] for arm, n in per_point.items())
    schedule_s = POINTS * point_s + sum(n * walls[arm] for arm, n in q0.items())
    total_min = FIXED_BEFORE_MIN + schedule_s / 60 + FIXED_AFTER_MIN
    slow_min = FIXED_BEFORE_MIN * 1.5 + 1.5 * schedule_s / 60 + FIXED_AFTER_MIN
    out = {
        "schema": 1,
        "prior": "inputs/power_prior.json (run 39335956567, the parent's archived Tier 1 run)",
        "design": {"points": POINTS, "primary_pairs_per_point": K, "aa_pairs_per_point": K_AA,
                   "planted_pairs_per_point": K_PLANTED, "attempts_per_kM38I_block": COLUMNS,
                   "primary_pairs": POINTS * K, "rank_blocks_kPI": POINTS * K,
                   "distinct_kM38I_blocks": POINTS * K},
        "method": ("simulated receipts drawn from the prior; primary statistic and two-stage paired bootstrap of "
                   "verify_receipt.py (%d simulations per cell, %d bootstrap draws each)" % (sims, DRAWS)),
        "prior_means_ms": {"kPI_rank_stage": mean_kpi, "kM38I_rank_stage": mean_rest + COLUMNS * mean_attempt,
                           "cPI_cold": mean_cpi, "cM38I_cold": mean_cm38, "E2E_A": e2e_a, "E2E_B": e2e_b},
        "expected_ratio_at_prior_means": e2e_a / e2e_b,
        "min_delta": MIN_DELTA,
        "cells": cells,
        "power_at_min_delta": cells["%.2f" % MIN_DELTA]["power"],
        "type_i_at_1.00": cells["1.00"]["power"],
        "aa_control": {"pairs": POINTS * K_AA, "e2e_point_estimate_inside_band_rate": aa_e2e_in / sims,
                       "cold_point_estimate_inside_band_rate": aa_cold_in / sims,
                       "median_e2e_estimate": statistics.median(aa_estimates), "band": list(AA_BAND)},
        "law_gate": {"attempts": n_law, "band": list(BAND), "pass_rate_at_archived_law": passes / 4000,
                     "rejection_rate_for_law_1.5x_worse": rejects_worse / 4000,
                     "archived_pooled_ratio": statistics.mean(ratios)},
        "planted_control": {"pairs": POINTS * K_PLANTED, "lower_bound_above_1_rate": planted_hits / sims,
                            "archived_attempt_ratio": sum(x for b in planted for x, _ in b) /
                                                      sum(y for b in planted for _, y in b)},
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
    print(json.dumps({k: out[k] for k in ("expected_ratio_at_prior_means", "power_at_min_delta", "type_i_at_1.00",
                                          "aa_control", "law_gate", "planted_control")}, sort_keys=True))
    print(json.dumps(out["runtime"], sort_keys=True))
    print(json.dumps(cells, sort_keys=True))


if __name__ == "__main__":
    main()
