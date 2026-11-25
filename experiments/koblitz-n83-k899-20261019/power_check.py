#!/usr/bin/env python3
"""Power of the frozen primary rule for four rank blocks (before any timing).

Simulates R = E2E(kP600, cP600) / E2E(kP899, cP899) with the frozen
bootstrap of `verify_receipt.py` (rank blocks resampled with the same ids
for both arms; attempts resampled within each drawn block independently per
arm; cold points resampled, paired) from the prior `inputs/power_prior.json`
(run 39214027289, K600) and the diagnostic's K899/K600 cost ratios
(`inputs/k899_identity.json` `diagnostic`):

* a simulated K600 block resamples the 600 attempts of one archived kP block
  (seeds 301-304), times a process factor drawn from the archived
  per-process A/A ratios (kPaa / kP);
* a simulated K899 block draws 899 attempts from the pooled 2,400 archived
  K600 attempts, each times s (the per-attempt cost ratio K899 / K600), and
  its own process factor. The probes until the first root-table hit are
  geometric with mean the law r / (166 E), so a K899 attempt is a K600
  attempt rescaled: the per-attempt distribution keeps its shape (CV 0.97)
  and only its mean moves (by the law ratio times the per-probe ratio);
* cold: 20 points resampled from the archived 20; cP600 = archived cP,
  cP899 = archived cR (another process of the same cold code) times the
  diagnostic's cold ratio K899 / K600.

The end-to-end effect E is set through s, holding the cold ratio at the
diagnostic's value. Power = share of simulations whose 95% lower bound
exceeds 1; at E = 1.00 it is the rejection rate at no effect. The block
count is fixed at four (the design); the check reports the power at
MIN_DELTA and the effect the diagnostic predicts.
"""

import argparse
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "inputs" / "power_prior.json"
IDENTITY = HERE / "inputs" / "k899_identity.json"
OUT = HERE / "analysis" / "power.json"
BLOCKS = 4
INFO_BLOCKS = (8, 12)  # reported for information only; the design runs BLOCKS
EFFECTS = (1.00, 1.03, 1.05, 1.07, 1.10)
MIN_DELTA = 1.05
SIMULATIONS = 400
DRAWS = 400
POINTS = 20
SEED = 2026101989


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    sims = 60 if args.quick else SIMULATIONS
    prior = json.loads(PRIOR.read_text())
    diag = json.loads(IDENTITY.read_text())["diagnostic"]
    cold_ratio = diag["cold_ratio_K899_over_K600"]
    archived = []
    for _, b in sorted(prior["rank_blocks"].items()):
        a = np.array(b["kP_attempt_ns"], dtype=float) / 1e6
        aa = np.array(b["kPaa_attempt_ns"], dtype=float) / 1e6
        archived.append({"rest": b["kP_non_attempt_ms"], "att": a, "aa": aa.sum() / a.sum()})
    pool = np.concatenate([blk["att"] for blk in archived])
    factors = np.array([blk["aa"] for blk in archived])
    cold6 = np.array([v["cP"] for _, v in sorted(prior["cold_ms"].items())])
    cold9 = np.array([v["cR"] for _, v in sorted(prior["cold_ms"].items())]) * cold_ratio
    mean_rank6 = float(np.mean([blk["rest"] + blk["att"].sum() for blk in archived]))
    mean_rest = float(np.mean([blk["rest"] for blk in archived]))
    mean_cold6 = float(cold6.mean())

    def scale_for(effect):
        # (rank6 + cold6) / (rest + 899 s mean_att + cold6 * ratio) = E
        target = (mean_rank6 + mean_cold6) / effect - mean_cold6 * cold_ratio - mean_rest
        return target / (899 * pool.mean())

    rng = np.random.default_rng(SEED)

    def simulate(effect, nblocks):
        s = scale_for(effect)
        hits = 0
        estimates = []
        for _ in range(sims):
            b6, b9 = [], []
            for _ in range(nblocks):
                blk = archived[rng.integers(len(archived))]
                f6, f9 = factors[rng.integers(len(factors))], factors[rng.integers(len(factors))]
                b6.append((blk["rest"], blk["att"][rng.integers(600, size=600)] * f6))
                b9.append((blk["rest"], pool[rng.integers(len(pool), size=899)] * s * f9))
            pts = rng.integers(len(cold6), size=POINTS)
            c6, c9 = cold6[pts], cold9[pts]
            estimates.append((np.mean([r + x.sum() for r, x in b6]) + c6.mean()) /
                             (np.mean([r + x.sum() for r, x in b9]) + c9.mean()))
            # the frozen bootstrap: blocks (same ids for both arms), attempts per arm, points paired
            bd = rng.integers(nblocks, size=(DRAWS, nblocks))
            rank6 = np.zeros(DRAWS)
            rank9 = np.zeros(DRAWS)
            for j in range(nblocks):
                for i in range(nblocks):
                    mask = bd[:, j] == i
                    n = int(mask.sum())
                    if n:
                        rank6[mask] += b6[i][0] + b6[i][1][rng.integers(600, size=(n, 600))].sum(axis=1)
                        rank9[mask] += b9[i][0] + b9[i][1][rng.integers(899, size=(n, 899))].sum(axis=1)
            pd = rng.integers(POINTS, size=(DRAWS, POINTS))
            values = np.sort((rank6 / nblocks + c6[pd].mean(axis=1)) / (rank9 / nblocks + c9[pd].mean(axis=1)))
            hits += values[int(0.025 * DRAWS)] > 1.0
        power = hits / sims
        return power, math.sqrt(max(power * (1 - power), 1e-12) / sims), float(np.median(estimates)), s

    predicted = diag.get("predicted_e2e_ratio")
    effects = sorted(set(EFFECTS) | ({round(predicted, 3)} if predicted else set()))
    table, info = {}, {}
    for effect in effects:
        power, se, med, s = simulate(effect, BLOCKS)
        table["%.3f" % effect] = {"per_attempt_cost_ratio_K899_over_K600": s, "power": power, "mc_se": se,
                                  "median_point_estimate": med}
    for nblocks in INFO_BLOCKS:
        info[str(nblocks)] = {}
        for effect in sorted({1.00, 1.05} | ({round(predicted, 3)} if predicted else set())):
            power, se, _, _ = simulate(effect, nblocks)
            info[str(nblocks)]["%.3f" % effect] = {"power": power, "mc_se": se}
    result = {"schema": 1, "prior": "inputs/power_prior.json", "prior_source": prior["source"],
              "diagnostic_inputs": {"cold_ratio_K899_over_K600": cold_ratio,
                                    "predicted_e2e_ratio": predicted, "source": diag.get("run_url")},
              "statistic": "R = E2E(kP600, cP600) / E2E(kP899, cP899), 95% lower bound > 1",
              "bootstrap": ("rank blocks resampled (same ids for both arms); attempts resampled within each drawn "
                            "block independently per arm; cold points resampled, paired; %d draws per simulation "
                            "(10,000 in the frozen verifier)" % DRAWS),
              "simulations": sims, "points": POINTS, "blocks": BLOCKS, "min_delta": MIN_DELTA,
              "mean_rank_stage_ms_prior_K600": mean_rank6, "mean_cold_ms_prior_K600": mean_cold6,
              "power": table, "chosen_rank_blocks": BLOCKS,
              "information_only_other_block_counts": info,
              "type_i_at_1.00": table["1.000"]["power"], "quick": args.quick}
    if not args.quick:
        OUT.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"4": {e: (round(t["power"], 3), round(t["median_point_estimate"], 4)) for e, t in table.items()},
                      "info": info}))


if __name__ == "__main__":
    main()
