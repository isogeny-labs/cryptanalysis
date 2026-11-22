#!/usr/bin/env python3
"""Power of the frozen primary rule for the panel size (before any timing).

Simulates the primary statistic R_on = mean online(cS) / mean online(cF)
with the frozen bootstrap (`verify_receipt.py`: the points resampled with
replacement, paired across cS and cF) from the prior
`inputs/power_prior.json` (run 39214027289):

* a simulated panel of N points draws N archived points (20 available)
  with replacement; cS = the archived cR online time, and the candidate is
  cF = the archived cP online time / e. cR and cP are two processes of the
  same online code on the same point with the same probes, so cP / cR is
  the paired A/A noise of one point, and e is the online effect;
* at e = 1 the simulation is the null (the A/A pair itself).

Power = share of simulations whose 95% lower bound exceeds 1. The chosen
panel is the smallest of SIZES whose power at the minimal effect of
interest (MIN_DELTA, online) minus two Monte Carlo standard errors is at
least 0.80 and whose null rejection rate is at most 0.05, and at least
MIN_POINTS. The end-to-end secondary is reported with its expected value
only (a 0.1 s change on about 166 s), not powered.
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
SIZES = (16, 32, 64, 128)
MIN_POINTS = 64
EFFECTS = (1.0, 1.01, 1.02, 1.05, 1.10, 1.30, 1.50)
MIN_DELTA = 1.05
SIMULATIONS = 400
DRAWS = 1000
SEED = 2026101977


def ratio_of_means(pairs):
    return sum(a for a, _ in pairs) / sum(b for _, b in pairs)


def lower_upper(pairs, rng, draws):
    n = len(pairs)
    values = sorted(ratio_of_means([pairs[rng.randrange(n)] for _ in range(n)]) for _ in range(draws))
    return values[int(0.025 * draws)], values[int(0.975 * draws) - 1]


def simulate(prior, size, effect, rng, simulations, draws):
    base = [(p["cR"]["online_ms"], p["cP"]["online_ms"]) for p in prior["points"].values()]
    hits = upper_misses = 0
    estimates = []
    for _ in range(simulations):
        pairs = [base[rng.randrange(len(base))] for _ in range(size)]
        pairs = [(s, f / effect) for s, f in pairs]
        lo, hi = lower_upper(pairs, rng, draws)
        hits += lo > 1.0
        upper_misses += hi < 1.0
        estimates.append(ratio_of_means(pairs))
    return {"power": hits / simulations, "rejection_below": upper_misses / simulations,
            "mc_se": math.sqrt(max(hits / simulations * (1 - hits / simulations), 1e-12) / simulations),
            "mean_estimate": statistics.mean(estimates)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="development only")
    args = parser.parse_args()
    prior = json.loads(PRIOR.read_text())
    simulations, draws = (50, 200) if args.quick else (SIMULATIONS, DRAWS)
    rng = random.Random(SEED)
    table = {}
    for effect in EFFECTS:
        table["%.2f" % effect] = {"by_points": {str(n): simulate(prior, n, effect, rng, simulations, draws)
                                                for n in SIZES}}
    chosen = None
    for n in SIZES:
        cell = table["%.2f" % MIN_DELTA]["by_points"][str(n)]
        null = table["1.00"]["by_points"][str(n)]
        if n >= MIN_POINTS and cell["power"] - 2 * cell["mc_se"] >= 0.80 and null["power"] <= 0.05:
            chosen = n
            break
    aa = [p["cP"]["online_ms"] / p["cR"]["online_ms"] for p in prior["points"].values()]
    online = statistics.mean(p["cR"]["online_ms"] for p in prior["points"].values())
    cold = statistics.mean(p["cR"]["cold_ms"] for p in prior["points"].values())
    rank = statistics.mean(prior["kP_rank_stage_ms"])
    out = {"schema": 1, "prior": str(PRIOR.relative_to(HERE)), "prior_runs_jsonl_sha256": prior["runs_jsonl_sha256"],
           "simulations": simulations, "bootstrap_draws": draws, "seed": SEED, "sizes": list(SIZES),
           "min_points": MIN_POINTS, "min_delta": MIN_DELTA, "effects": list(EFFECTS),
           "power": {k: {"by_points": {n: v["power"] for n, v in cell["by_points"].items()}}
                     for k, cell in table.items()},
           "detail": table, "type_i_at_1.00": {n: v["power"] for n, v in table["1.00"]["by_points"].items()},
           "chosen_points": chosen,
           "prior_summary": {"points": len(prior["points"]), "aa_online_cP_over_cR_per_point": {
               "min": min(aa), "max": max(aa), "mean": statistics.mean(aa), "sd": statistics.stdev(aa)},
               "mean_online_ms": online, "mean_cold_ms": cold, "mean_rank_stage_ms": rank},
           "expected": {"note": ("not an input: the local per-probe ratio of the S3 online loop over the frame "
                                 "loop (smoke/) and the archived 221.4 against 141.5 ns per probe give an "
                                 "online effect of about 1.4-1.6"),
                        "e2e_change_ms_at_online_1.5": online * (1 - 1 / 1.5),
                        "e2e_ratio_at_online_1.5": (rank + cold) / (rank + cold - online * (1 - 1 / 1.5))}}
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"chosen_points": chosen, "power_at_min_delta": out["power"]["%.2f" % MIN_DELTA],
                      "type_i": out["type_i_at_1.00"], "prior_summary": out["prior_summary"],
                      "expected": out["expected"]}, indent=1))


if __name__ == "__main__":
    main()
