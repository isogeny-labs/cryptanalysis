#!/usr/bin/env python3
"""Size the cold panel for the primary online gap, before freezing.

The primary is G = mean IC online (cP) / mean BL online over the panel's
points, with a bootstrap over points (pairs resampled together). It is a
measurement, not a test against 1, so the panel is sized for precision:

* a panel of n points is simulated by drawing n IC online times from the
  prior's 20 rank-probe cP rows and n BL online times from the prior's 20 BL
  rows rescaled to this budget (`inputs/power_prior.json`), 400 simulations
  per cell, each with a 1,000-draw percentile bootstrap of G;
* reported per cell: the median and 90th percentile of the interval's
  width ratio (upper / lower), the probability that the lower bound exceeds 1
  (reading `bl_online_faster_than_ic`), and the probability that the upper
  bound is below B's measured 235 (the older producer's figure);
* sensitivity: the BL rows are also scaled by 0.5x and 2x (B's measured /
  model step ratio was 1.56, and the run said the model could be off by
  2.4x); the width ratio does not depend on that scale, the probabilities may.

Rule (frozen here): COUNT is the smallest n in the grid whose median width
ratio at scale 1 is at most 2.0. Writes `analysis/power.json`.
"""

import json
import random
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
GRID = (20, 32, 48, 64, 80, 96)
SCALES = (0.5, 1.0, 2.0)
SIMS = 400
DRAWS = 1000
SEED = 2026101981
TARGET_WIDTH_RATIO = 2.0
B_GAP = 235.0


def cell(ic, bl, n, rng):
    widths, above_one, below_b, estimates = [], 0, 0, []
    for _ in range(SIMS):
        pairs = [(rng.choice(ic), rng.choice(bl)) for _ in range(n)]
        estimates.append(sum(a for a, _ in pairs) / sum(b for _, b in pairs))
        draws = []
        for _ in range(DRAWS):
            sample = [pairs[rng.randrange(n)] for _ in range(n)]
            draws.append(sum(a for a, _ in sample) / sum(b for _, b in sample))
        draws.sort()
        lo, hi = draws[int(0.025 * DRAWS)], draws[int(0.975 * DRAWS) - 1]
        widths.append(hi / lo)
        above_one += lo > 1
        below_b += hi < B_GAP
    widths.sort()
    return {"n": n, "median_width_ratio": statistics.median(widths),
            "p90_width_ratio": widths[int(0.9 * len(widths))],
            "p_lower_bound_above_1": above_one / SIMS, "p_upper_bound_below_B_235": below_b / SIMS,
            "median_estimate": statistics.median(estimates)}


def main():
    prior = json.loads((HERE / "inputs" / "power_prior.json").read_text())
    ic = prior["ic_online_ms"]
    out = {"schema": 1, "statistic": "G = mean cP online / mean BL online, percentile bootstrap over points",
           "sims_per_cell": SIMS, "bootstrap_draws": DRAWS, "seed": SEED, "grid": list(GRID),
           "rule": "smallest n with median width ratio (upper/lower) <= %.1f at BL scale 1" % TARGET_WIDTH_RATIO,
           "prior": "inputs/power_prior.json (model-based; see make_power_prior.py)", "cells": {}}
    for scale in SCALES:
        bl = [v * scale for v in prior["bl_online_ms_scaled"]]
        rng = random.Random(SEED + int(scale * 10))
        out["cells"]["bl_scale_%s" % scale] = [cell(ic, bl, n, rng) for n in GRID]
    chosen = next((c["n"] for c in out["cells"]["bl_scale_1.0"]
                   if c["median_width_ratio"] <= TARGET_WIDTH_RATIO), GRID[-1])
    out["chosen_points"] = chosen
    (HERE / "analysis" / "power.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"chosen_points": chosen,
                      "at_scale_1": [(c["n"], round(c["median_width_ratio"], 3), c["p_lower_bound_above_1"])
                                     for c in out["cells"]["bl_scale_1.0"]]}, sort_keys=True))


if __name__ == "__main__":
    main()
