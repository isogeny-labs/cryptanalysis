#!/usr/bin/env python3
"""Power of the frozen primary rule and of the probe-law gate (before any timing).

Prior: `inputs/power_prior.json` (`make_power_prior.py`): the closure run
39305259093's rank blocks (kP, kM38, kM38aa, kM10) and cold times (cP,
cM38, cM10), and the index-lift run 39290913632's cP / cPI cold times.

Primary statistic R = E2E(kPI, cPI) / E2E(kM38I, cM38I) with the frozen
bootstrap of `verify_receipt.py`: for each rank arm its blocks are
resampled, then the attempts within each drawn block (the baseline's and
the candidate's attempts are different targets on different bases, so the
two arms are resampled independently); the cold points are resampled,
paired across cPI and cM38I.

Simulation, per cell (effect E, candidate C):

* baseline kPI: BASE_BLOCKS blocks, each an archived kP block (the rank
  stage does not depend on the index canonicalizer: the layout gate makes
  the index byte identical) with its 600 attempts resampled and a process
  factor drawn from the archived kM38aa / kM38 per-block ratios; the
  archived non-attempt time;
* candidate kC I: the design's blocks for C, each with K'(C) attempts drawn
  from the pooled archived kC attempts (the closure run's own candidate
  loop), times a cost factor f and a process factor, and a non-attempt time
  drawn from the archived kC blocks;
* cold: the 20 archived closure-run points, resampled; cPI = archived cP x L
  and cC I = archived cC x L, with L = mean cPI / mean cP of the index-lift
  run (the index-lift cold factor; the closure's cold path builds an index
  of the same size).

f is set so that the END-TO-END ratio at the prior's means equals E (E =
1.00 is no gain). `modelled` sets f = 1 (the two changes stack as their own
runs measured them). Power = share of simulations whose 95% lower bound
exceeds 1.

Probe-law gate: the pooled mean probes per relation of kM38I's distinct
attempts over law = r / (166 E_M38) must lie in [0.80, 1.20] (the closure
run's band). Its pass rate is simulated by resampling the closure run's
kM38 attempts' probes over their law, and its rejection rate for a law 1.5x
worse.

MIN_DELTA = 1.50 end to end (the closure's): the mechanism divides the
relations needed by M = 38. `--quick` is for development only.
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
ENTRIES = {"M38": 30366551, "M10": 29821794}
CANDIDATES = {"M38": {"columns": 16, "blocks": 16, "arm": "kM38", "cold": "cM38"},
              "M10": {"columns": 60, "blocks": 8, "arm": "kM10", "cold": "cM10"}}  # primary first
BASE_BLOCKS = 4
EFFECTS = (1.0, 1.10, 1.50, 2.00, 4.00)
MIN_DELTA = 1.50
BANDS = {"M38": (0.80, 1.20), "M10": (0.85, 1.15)}
SIMULATIONS = 200
DRAWS = 300
POINTS = 20
SEED = 2026101911


def e2e_bootstrap(base, cand, cold, rng, draws):
    """base/cand: [(rest, [attempt ms])]; cold: [(c_base, c_cand)]. (estimate, lo, hi)."""
    def stage(blocks, resample):
        return statistics.mean(rest + (sum(rng.choices(att, k=len(att))) if resample else sum(att))
                               for rest, att in blocks)

    def value(bb, cb, pts, resample):
        return ((stage(bb, resample) + statistics.mean(c[0] for c in pts)) /
                (stage(cb, resample) + statistics.mean(c[1] for c in pts)))

    point = value(base, cand, cold, False)
    values = []
    for _ in range(draws):
        bb = rng.choices(base, k=len(base))
        cb = rng.choices(cand, k=len(cand))
        pts = rng.choices(cold, k=len(cold))
        values.append(value(bb, cb, pts, True))
    values.sort()
    return point, values[int(0.025 * draws)], values[int(0.975 * draws) - 1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    sims = 40 if args.quick else SIMULATIONS
    prior = json.loads(PRIOR.read_text())
    blocks = prior["rank_blocks"]
    base = [{"rest": b["kP"]["non_attempt_ms"], "ms": [a / 1e6 for a in b["kP"]["attempt_ns"]]}
            for _, b in sorted(blocks.items()) if "kP" in b]
    factors = [sum(b["kM38aa"]["attempt_ns"]) / sum(b["kM38"]["attempt_ns"])
               for _, b in sorted(blocks.items()) if "kM38aa" in b]
    lift = prior["indexlift_cold_ms"]
    L = statistics.mean(v["cPI"] for v in lift.values()) / statistics.mean(v["cP"] for v in lift.values())
    mean_base_rank = statistics.mean(b["rest"] + sum(b["ms"]) for b in base)
    rng = random.Random(SEED)
    table = {}
    for name, spec in CANDIDATES.items():
        k, arm = spec["columns"], spec["arm"]
        cand_blocks = [b[arm] for _, b in sorted(blocks.items()) if arm in b]
        pooled = [a / 1e6 for b in cand_blocks for a in b["attempt_ns"]]
        rests = [b["non_attempt_ms"] for b in cand_blocks]
        cold = [(v["cP"] * L, v[spec["cold"]] * L) for _, v in sorted(prior["cold_ms"].items())]
        mean_cold_base = statistics.mean(c[0] for c in cold)
        mean_cold_cand = statistics.mean(c[1] for c in cold)
        mean_attempt = statistics.mean(pooled)
        e2e_base = mean_base_rank + mean_cold_base
        e2e_cand_modelled = statistics.mean(rests) + k * mean_attempt + mean_cold_cand
        cells = {}
        for effect in EFFECTS + ("modelled",):
            if effect == "modelled":
                f = 1.0
            else:
                f = (e2e_base / effect - mean_cold_cand - statistics.mean(rests)) / (k * mean_attempt)
            hits, estimates = 0, []
            for _ in range(sims):
                sb = []
                for _ in range(BASE_BLOCKS):
                    blk = base[rng.randrange(len(base))]
                    g = factors[rng.randrange(len(factors))]
                    sb.append((blk["rest"], [x * g for x in rng.choices(blk["ms"], k=600)]))
                sc = []
                for _ in range(spec["blocks"]):
                    g = factors[rng.randrange(len(factors))]
                    sc.append((rests[rng.randrange(len(rests))], [x * f * g for x in rng.choices(pooled, k=k)]))
                pts = [cold[rng.randrange(len(cold))] for _ in range(POINTS)]
                est, lo, _ = e2e_bootstrap(sb, sc, pts, rng, DRAWS)
                hits += lo > 1.0
                estimates.append(est)
            power = hits / sims
            cells[effect if effect == "modelled" else "%.2f" % effect] = {
                "attempt_cost_factor": f, "power": power,
                "mc_se": math.sqrt(max(power * (1 - power), 1e-12) / sims),
                "median_estimate": statistics.median(estimates)}
        law = R / (166 * ENTRIES[name])
        ratios = [p / law for b in cand_blocks for p in b["attempt_probes"]]
        n = k * spec["blocks"]
        lo_band, hi_band = BANDS[name]
        passes = fails_worse = 0
        for _ in range(2000):
            m = statistics.mean(ratios[rng.randrange(len(ratios))] for _ in range(n))
            passes += lo_band <= m <= hi_band
            fails_worse += not (lo_band <= 1.5 * m <= hi_band)
        cells["law_gate"] = {"band": [lo_band, hi_band], "attempts": n,
                             "pass_rate_true_law": passes / 2000,
                             "reject_rate_law_1.5x_worse": fails_worse / 2000,
                             "archived_ratio_mean": statistics.mean(ratios),
                             "archived_ratio_cv": statistics.stdev(ratios) / statistics.mean(ratios),
                             "archived_attempts": len(ratios)}
        table[name] = {"columns": k, "blocks": spec["blocks"], "cells": cells,
                       "mean_cold_ms_modelled": {"cPI": mean_cold_base, name: mean_cold_cand},
                       "mean_attempt_ms_prior": mean_attempt,
                       "e2e_ms_modelled": {"baseline": e2e_base, "candidate": e2e_cand_modelled},
                       "expected_ratio_at_prior_means": e2e_base / e2e_cand_modelled}
    result = {"schema": 1, "prior": "inputs/power_prior.json", "prior_sources": prior["sources"],
              "statistic": "R = E2E(kPI, cPI) / E2E(kM38I, cM38I), 95% lower bound > 1",
              "bootstrap": ("each rank arm's blocks resampled, then its attempts within each drawn block "
                            "(independently across arms); cold points resampled, paired; %d draws per simulation "
                            "(10,000 in the frozen verifier)" % DRAWS),
              "simulations": sims, "points": POINTS, "baseline_blocks": BASE_BLOCKS,
              "indexlift_cold_factor_L": L, "aa_process_factors": len(factors),
              "min_delta": MIN_DELTA, "mean_rank_stage_ms_prior_kP": mean_base_rank, "candidates": table,
              "type_i_at_1.00": {c: t["cells"]["1.00"]["power"] for c, t in table.items()},
              "power_at_min_delta": {c: t["cells"]["%.2f" % MIN_DELTA]["power"] for c, t in table.items()},
              "quick": args.quick}
    if not args.quick:
        OUT.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({c: {"expected": round(t["expected_ratio_at_prior_means"], 3),
                          **{e: (round(v["power"], 3) if "power" in v else v) for e, v in t["cells"].items()}}
                      for c, t in table.items()}, sort_keys=True))


if __name__ == "__main__":
    main()
