#!/usr/bin/env python3
"""Power (precision) check for the frozen primary, before freezing (`analysis/power.json`).

The primary is an estimate, not a test against a baseline: the gap
G = mean E2E(cL_opt) / mean cold(rT) over the cold points, with the frozen
paired point bootstrap (95%). The power question is how many points make
its interval narrow enough to say where the known-log reference sits
relative to the tuned rho.

Simulation, per cell (points N, cost model A or B of `cost_model.py`):

* rT cold: resampled with replacement from the 20 archived rT770 cold times
  of run 39214027289 (`inputs/power_prior.json`), so the "true" rho mean is
  that sample's mean;
* cL_opt end to end: the model's non-online cost at K_opt, times a setup
  jitter drawn from the archived cP setup's relative spread, plus an online
  interval of P probes times the model's ns per probe, with P exponential
  with mean r / (166 * 83 * K^2) times the archived law ratio (0.9785 over
  2,400 rank attempts; their coefficient of variation is 0.97, an
  exponential's is 1);
* the frozen estimator and bootstrap (1,000 draws here, 10,000 in the run).

Reported per cell: the median relative half-width of the 95% interval,
the probability that its lower bound exceeds 1 (the interval puts the
reference above rho), the probability that it is below 1, and the coverage
of the true G. The chosen N is the smallest grid value with median relative
half-width <= 0.20 and P(lower bound > 1) >= 0.90 under both models.
The secondary ratio E2E(kP+cP) / E2E(cL_opt) is reported at the chosen N.
"""

import json
import math
import random
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "inputs" / "power_prior.json"
MODEL = HERE / "analysis" / "cost_model.json"
OUT = HERE / "analysis" / "power.json"
GRID = (20, 30, 40, 60)
SIMS = 400
DRAWS = 1000
SEED = 2026101983
R = 8569786107849059


def ci(pairs, rng):
    n = len(pairs)
    values = []
    for _ in range(DRAWS):
        draw = [pairs[rng.randrange(n)] for _ in range(n)]
        values.append(sum(a for a, _ in draw) / sum(b for _, b in draw))
    values.sort()
    return values[int(0.025 * DRAWS)], values[int(0.975 * DRAWS) - 1]


def main():
    prior = json.loads(PRIOR.read_text())
    model = json.loads(MODEL.read_text())
    k = model["K_opt"]
    c = model["constants"]
    rho = [r["cold_ms"] for r in prior["rho_rT"]]
    rho_mean = statistics.mean(rho)
    setups = [x["setup_complete_ms"] for x in prior["cold_cP"]]
    jitter = statistics.stdev(setups) / statistics.mean(setups)
    mean_probes = R / (166 * 83 * k * k) * c["probe_law_ratio_rank_attempts"]
    rank = statistics.mean(b["rank_stage_ms"] for b in prior["rank_kP"])
    cold_cp = statistics.mean(x["cold_ms"] for x in prior["cold_cP"])
    out = {"schema": 1, "K_opt": k, "sims_per_cell": SIMS, "bootstrap_draws": DRAWS, "seed": SEED,
           "rho_prior": {"n": len(rho), "mean_cold_ms": rho_mean, "cv": statistics.stdev(rho) / rho_mean},
           "setup_relative_sd": jitter, "online_mean_probes_at_K_opt": mean_probes, "cells": {}}
    rng = random.Random(SEED)
    for name in ("A", "B"):
        parts = model["models"][name]["parts_ms_at_K_opt"]
        fixed = sum(v for key, v in parts.items() if key != "online")
        x = k / c["K0"]
        ns = c["ns_per_probe_online"] * (x ** c["local_probe_cost_exponent"] if name == "B" else 1.0)
        true_cl = fixed + mean_probes * ns / 1e6
        truth = true_cl / rho_mean
        for n in GRID:
            widths, above, below, covered, ratios = [], 0, 0, 0, []
            for _ in range(SIMS):
                pairs = []
                for _ in range(n):
                    cl = fixed * (1 + jitter * rng.gauss(0, 1)) + rng.expovariate(1 / mean_probes) * ns / 1e6
                    pairs.append((cl, rho[rng.randrange(len(rho))]))
                est = sum(a for a, _ in pairs) / sum(b for _, b in pairs)
                lo, hi = ci(pairs, rng)
                widths.append((hi - lo) / 2 / est)
                above += lo > 1
                below += hi < 1
                covered += lo <= truth <= hi
                ratios.append((rank + cold_cp) / statistics.mean(a for a, _ in pairs))
            out["cells"]["%s/N%d" % (name, n)] = {
                "model": name, "points": n, "true_gap": truth, "true_e2e_ms": true_cl,
                "median_relative_half_width": statistics.median(widths),
                "p_lower_bound_above_1": above / SIMS, "p_upper_bound_below_1": below / SIMS,
                "coverage": covered / SIMS,
                "secondary_ratio_kP_cP_over_cL_median": statistics.median(ratios),
                "secondary_ratio_relative_spread_sd": statistics.stdev(ratios) / statistics.mean(ratios)}
    ok = [n for n in GRID if all(out["cells"]["%s/N%d" % (m, n)]["median_relative_half_width"] <= 0.20 and
                                 out["cells"]["%s/N%d" % (m, n)]["p_lower_bound_above_1"] >= 0.90
                                 for m in ("A", "B"))]
    out["chosen_points"] = min(ok) if ok else max(GRID)
    out["rule"] = ("smallest N in %s with median relative half-width <= 0.20 and P(lower bound > 1) >= 0.90 "
                   "under both cost models" % (GRID,))
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"chosen_points": out["chosen_points"],
                      "cells": {key: {f: round(v, 4) if isinstance(v, float) else v for f, v in cell.items()
                                      if f in ("true_gap", "median_relative_half_width", "p_lower_bound_above_1",
                                               "coverage", "secondary_ratio_kP_cP_over_cL_median")}
                                for key, cell in out["cells"].items()}}, indent=1))


if __name__ == "__main__":
    main()
