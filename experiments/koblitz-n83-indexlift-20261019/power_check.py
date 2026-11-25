#!/usr/bin/env python3
"""Power of the frozen primary rule (before any timing).

The primary statistic is R = E2E(cP) / E2E(cPI) with the SHARED rank stage:
E2E(c) = K + mean cold(c), where K is the mean rank stage over the rank
blocks, each block's value the mean of its rank processes (kP and kPI, the
same rank code over the same index). The frozen bootstrap
(`verify_receipt.py`): rank blocks resampled; within each drawn block the
attempt indices resampled and used for both rank processes; the cold points
resampled, paired across cP and cPI.

Simulation from the prior `inputs/power_prior.json` (run 39214027289):

* a simulated block draws one archived block (seeds 301-304); its two rank
  processes are the archived kP and kPaa (the same attempts with the same
  probes, two processes of the same rank code, as kP and kPI are here);
* cold: 20 points resampled from the archived 20; the baseline cP = the
  archived cR, the candidate cPI = the archived cP / e (cR and cP are two
  processes of the same cold code, so e = 1 is a real A/A null), with e set
  so that the END-TO-END ratio at the prior's means equals the effect of
  interest.

Power = share of simulations whose 95% lower bound exceeds 1. The chosen
block count is the smallest of BLOCKS whose power at MIN_DELTA minus two
Monte Carlo standard errors is at least 0.80, and at least MIN_BLOCKS
(three: the shared rank stage K enters every S and gap to rho directly).
The expected effect is reported from the archived cPI, never used as an
input. `--quick` is for development only.
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
BLOCKS = (2, 3, 4)
MIN_BLOCKS = 3  # K enters S and the gaps to rho directly, so three blocks even if two have the power
EFFECTS = (1.0, 1.002, 1.005, 1.01, 1.02, 1.035)
MIN_DELTA = 1.01
SIMULATIONS = 200
DRAWS = 300
POINTS = 20
SEED = 2026101991


def e2e_shared_bootstrap(blocks, cold, rng, draws):
    """blocks: [(rest_mean, [per-attempt mean of the block's rank processes])]; cold: [(cb, cc)]."""
    def value(block_values, cold_draw):
        k = statistics.mean(block_values)
        return (k + statistics.mean(c[0] for c in cold_draw)) / (k + statistics.mean(c[1] for c in cold_draw))

    point = value([rest + sum(att) for rest, att in blocks], cold)
    values = []
    for _ in range(draws):
        bv = []
        for _ in blocks:
            rest, att = blocks[rng.randrange(len(blocks))]
            bv.append(rest + sum(rng.choices(att, k=len(att))))
        cd = [cold[rng.randrange(len(cold))] for _ in cold]
        values.append(value(bv, cd))
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
        rest = (b["kP_non_attempt_ms"] + b["kPaa_non_attempt_ms"]) / 2
        att = [(x + y) / 2e6 for x, y in zip(b["kP_attempt_ns"], b["kPaa_attempt_ns"])]
        archived.append((rest, att))
    cold = [(v["cR"], v["cP"]) for _, v in sorted(prior["cold_ms"].items())]
    mean_rank = statistics.mean(rest + sum(att) for rest, att in archived)
    mean_cold = statistics.mean(c[0] for c in cold)

    def cold_effect(e2e_effect):
        # (K + C) / (K + C / e) = E  ->  e = C / ((K + C) / E - K)
        return mean_cold / ((mean_rank + mean_cold) / e2e_effect - mean_rank)

    rng = random.Random(SEED)
    table = {}
    for effect in EFFECTS:
        e = cold_effect(effect)
        row = {}
        for k in BLOCKS:
            hits = 0
            for _ in range(sims):
                blocks = []
                for _ in range(k):
                    rest, att = archived[rng.randrange(len(archived))]
                    blocks.append((rest, rng.choices(att, k=len(att))))
                pts = [cold[rng.randrange(len(cold))] for _ in range(POINTS)]
                pts = [(cb, cc / e) for cb, cc in pts]
                _, lo, _ = e2e_shared_bootstrap(blocks, pts, rng, DRAWS)
                hits += lo > 1.0
            power = hits / sims
            row[str(k)] = {"power": power, "mc_se": math.sqrt(max(power * (1 - power), 1e-12) / sims)}
        table["%.3f" % effect] = {"cold_effect": e, "by_blocks": row}
    at_min = table["%.3f" % MIN_DELTA]["by_blocks"]
    passing = [k for k in BLOCKS if at_min[str(k)]["power"] - 2 * at_min[str(k)]["mc_se"] >= 0.80]
    chosen = max(MIN_BLOCKS, min(passing)) if passing else None
    archived_cpi = statistics.mean(v["cPI"] for v in prior["cold_ms"].values())
    archived_cp = statistics.mean(v["cP"] for v in prior["cold_ms"].values())
    expected = (mean_rank + archived_cp) / (mean_rank + archived_cpi)
    result = {"schema": 1, "prior": "inputs/power_prior.json", "prior_source": prior["source"],
              "statistic": ("R = E2E(cP) / E2E(cPI), E2E(c) = K + mean cold(c), K the shared mean rank stage "
                            "(each block the mean of its rank processes); 95% lower bound > 1"),
              "bootstrap": ("rank blocks resampled; attempt indices resampled within each drawn block, shared by "
                            "the block's rank processes; cold points resampled, paired; %d draws per simulation "
                            "(10,000 in the frozen verifier)" % DRAWS),
              "null": "e = 1: the archived cR / cP cold pairs, two processes of the same cold code",
              "simulations": sims, "points": POINTS, "min_delta": MIN_DELTA, "min_blocks": MIN_BLOCKS,
              "mean_rank_stage_ms_prior": mean_rank, "mean_cold_ms_prior": mean_cold,
              "power": table, "chosen_rank_blocks": chosen,
              "type_i_at_1.000": {k: v["power"] for k, v in table["1.000"]["by_blocks"].items()},
              "expected_e2e_ratio_from_archived_cPI": expected,
              "expected_note": ("(K + mean cP) / (K + mean cPI) with run 39214027289's kP/kPaa rank stage and "
                                "cP / cPI cold means: an estimate from another run, not a claim and not an input "
                                "of this check"),
              "quick": args.quick}
    if not args.quick:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"chosen_rank_blocks": chosen, "expected": expected,
                      "power": {e: {k: round(v["power"], 3) for k, v in t["by_blocks"].items()}
                                for e, t in table.items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
