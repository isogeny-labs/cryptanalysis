#!/usr/bin/env python3
"""Power of the frozen primary rule and of the probe-law gate (before any timing).

Prior: `inputs/power_prior.json` (run 39214027289, the baseline kP / kPaa
attempts of rank seeds 301-304 and the cP / cR cold A/A pairs).

Primary statistic R = E2E(kP, cP) / E2E(kC, cC) with the frozen bootstrap of
`verify_receipt.py`: for each rank arm its blocks are resampled, then the
attempts within each drawn block (the baseline's and the candidate's
attempts are different targets, so the two arms are resampled
independently); the cold points are resampled, paired across cP and cC.

Simulation, per cell (effect E, candidate C):

* baseline: BASE_BLOCKS blocks, each an archived kP block with its 600
  attempts resampled and a process factor drawn from the archived per-process
  A/A ratios (kPaa / kP); the archived non-attempt time;
* candidate: the design's blocks for C, each with K'(C) attempts drawn from
  the pooled archived kP attempts (the closure keeps the root index and the
  probe law, so an attempt costs what a baseline attempt costs), times a
  cost factor f and a process factor; non-attempt time 10 ms;
* cold: the 20 archived points, resampled; cP = archived cP, cC = archived
  cR (two processes of the same cold code: the closure keeps the index size).

f is set so that the END-TO-END ratio equals E (E = 1.00 is no gain: f is
then the factor by which the candidate's attempts would have to cost more,
e.g. a probe law about 10x worse at M = 10). `modelled` sets f = 1 (the
closure keeps the law). Power = share of simulations whose 95% lower bound
exceeds 1.

Probe-law gate: the pooled mean probes per relation of the candidate's
distinct attempts over law = r / (166 E) must lie in the frozen band. Its
pass rate is simulated by resampling the archived kP attempts' probes over
their own law (K600, ratio 0.978 measured), and its rejection rate for a
law 1.5x worse, for each candidate's attempt count.

MIN_DELTA = 1.50 end to end: the mechanism divides the relations needed by
M (38 or 10), so the hypothesis is a several-fold change of the rank stage
(modelled R about 6 at M = 38, 4.5 at M = 10); an end-to-end effect below
1.5 would mean the closure lost most of its mechanism (a probe law several
times worse), which the law gate reports on its own. Power at 1.10 is
reported, not required.

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
K600_ENTRIES = 29878182
CANDIDATES = {"M38": {"columns": 16, "blocks": 16}, "M10": {"columns": 60, "blocks": 8}}  # primary first
BASE_BLOCKS = 4
EFFECTS = (1.0, 1.10, 1.50, 2.00)
MIN_DELTA = 1.50
BANDS = {"M10": (0.85, 1.15), "M38": (0.80, 1.20)}
SIMULATIONS = 200
DRAWS = 300
POINTS = 20
SEED = 2026101977


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
    archived = []
    for _, b in sorted(prior["rank_blocks"].items()):
        ms = [a / 1e6 for a in b["kP_attempt_ns"]]
        aa = sum(b["kPaa_attempt_ns"]) / sum(b["kP_attempt_ns"])
        archived.append({"rest": b["kP_non_attempt_ms"], "ms": ms, "aa": aa, "probes": b["kP_attempt_probes"]})
    pooled = [x for blk in archived for x in blk["ms"]]
    factors = [blk["aa"] for blk in archived]
    cold = [(v["cP"], v["cR"]) for _, v in sorted(prior["cold_ms"].items())]
    mean_cold = statistics.mean(c[0] for c in cold)
    mean_attempt = statistics.mean(pooled)
    mean_base_rank = statistics.mean(blk["rest"] + sum(blk["ms"]) for blk in archived)
    e2e_base = mean_base_rank + mean_cold
    rng = random.Random(SEED)
    table = {}
    for name, spec in CANDIDATES.items():
        k = spec["columns"]
        cells = {}
        for effect in EFFECTS + ("modelled",):
            if effect == "modelled":
                f = 1.0
            else:
                f = (e2e_base / effect - mean_cold - 10.0) / (k * mean_attempt)
            hits, estimates = 0, []
            for _ in range(sims):
                base = []
                for _ in range(BASE_BLOCKS):
                    blk = archived[rng.randrange(len(archived))]
                    g = factors[rng.randrange(len(factors))]
                    base.append((blk["rest"], [x * g for x in rng.choices(blk["ms"], k=600)]))
                cand = []
                for _ in range(spec["blocks"]):
                    g = factors[rng.randrange(len(factors))]
                    cand.append((10.0, [x * f * g for x in rng.choices(pooled, k=k)]))
                pts = [cold[rng.randrange(len(cold))] for _ in range(POINTS)]
                est, lo, _ = e2e_bootstrap(base, cand, pts, rng, DRAWS)
                hits += lo > 1.0
                estimates.append(est)
            power = hits / sims
            cells[effect if effect == "modelled" else "%.2f" % effect] = {
                "attempt_cost_factor": f, "power": power,
                "mc_se": math.sqrt(max(power * (1 - power), 1e-12) / sims),
                "median_estimate": statistics.median(estimates)}
        # Probe-law gate.
        law = R / (166 * K600_ENTRIES)
        ratios = [p / law for blk in archived for p in blk["probes"]]
        n = spec["columns"] * spec["blocks"]
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
                             "archived_ratio_cv": statistics.stdev(ratios) / statistics.mean(ratios)}
        table[name] = {"columns": k, "blocks": spec["blocks"], "cells": cells}
    result = {"schema": 1, "prior": "inputs/power_prior.json", "prior_source": prior["source"],
              "statistic": "R = E2E(kP, cP) / E2E(kC, cC), 95% lower bound > 1",
              "bootstrap": ("each rank arm's blocks resampled, then its attempts within each drawn block "
                            "(independently across arms); cold points resampled, paired; %d draws per simulation "
                            "(10,000 in the frozen verifier)" % DRAWS),
              "simulations": sims, "points": POINTS, "baseline_blocks": BASE_BLOCKS,
              "min_delta": MIN_DELTA, "mean_rank_stage_ms_prior": mean_base_rank, "mean_cold_ms_prior": mean_cold,
              "mean_attempt_ms_prior": mean_attempt, "candidates": table,
              "type_i_at_1.00": {c: t["cells"]["1.00"]["power"] for c, t in table.items()},
              "power_at_min_delta": {c: t["cells"]["%.2f" % MIN_DELTA]["power"] for c, t in table.items()},
              "quick": args.quick}
    if not args.quick:
        OUT.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({c: {e: (round(v["power"], 3) if "power" in v else v) for e, v in t["cells"].items()}
                      for c, t in table.items()}, sort_keys=True))


if __name__ == "__main__":
    main()
