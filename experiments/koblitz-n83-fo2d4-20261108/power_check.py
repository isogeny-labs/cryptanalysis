#!/usr/bin/env python3
"""Power, noise and runtime of the field-ops-2 on D4 design (before any timing).

A SIZING simulation. Nothing in it is a result of the run.

Both sides run the D4 base and do IDENTICAL work per (point, rank seed): same index, same
relations, same probe counts (the gates enforce it), so the pair ratio A / B has no
algorithmic noise, only timing noise. The k4c400 run (`inputs/power_prior.json`) measured
exactly that noise: its 40 A/A pairs are the same D4 arm run twice per (point, seed). Their
per-pair log ratios u (E2E, cold) are the noise of one A / B pair. The 60 primary D4 pairs
give the sizes (rank stage, cold) and heavy tails.

Simulated pair at true effect r (A is r times slower than B at every size):
  B = T (an archived primary pair's E2E, or cold), A = T * r * exp(s u), u drawn from the
  archived A/A log ratios, s = +-1 at random (removes the archived mean offset). Pairs of a
  point keep the archived point's pairs (its three pairs share a point). Primary rule of
  verify_receipt.py: R = sum A / sum B, two-stage paired bootstrap (points, then pairs;
  A and B of a pair drawn together), 95% interval, lower bound > 1.

Reported: power by effect and design; the same for a COLD-ONLY primary (cold process alone,
the stage that holds most of an index-build change) at equal compute; the A/A control pass
rates under the point-estimate rule; the modelled runtime. The design is chosen from it
and frozen in make_protocol.py.
"""
import json
import math
import random
import statistics
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / "analysis" / "power.json"
SIMS, DRAWS, SEED = 600, 1500, 20261108
EFFECTS = (1.000, 1.003, 1.005, 1.010, 1.015, 1.020, 1.030)
DESIGNS = {"8x3": (8, 3), "12x3": (12, 3), "16x3": (16, 3), "20x3": (20, 3)}
MIN_DELTA = 1.01  # smallest effect the frozen design must resolve with power >= 0.9; expected is 1.02-1.03


def lower_bound(a, b, rng):
    """a, b: (points, pairs) arrays of A and B times. Two-stage paired bootstrap, 95% lower and upper."""
    p, k = a.shape
    pts = rng.integers(0, p, size=(DRAWS, p))
    prs = rng.integers(0, k, size=(DRAWS, p, k))
    sa = a[pts[:, :, None], prs].sum(axis=(1, 2))
    sb = b[pts[:, :, None], prs].sum(axis=(1, 2))
    r = np.sort(sa / sb)
    return r[int(0.025 * DRAWS)], r[int(0.975 * DRAWS) - 1], a.sum() / b.sum()


def main():
    prior = json.loads((HERE / "inputs" / "power_prior.json").read_text())
    by_point = {}
    for key, s in prior["d4_primary_pairs"].items():
        unit = key.split("/")[0]
        by_point.setdefault(unit, []).append(s)
    aa = list(prior["d4_aa_pairs"].values())
    u_e2e = [math.log((v["B"]["rank_stage_ms"] + v["B"]["cold_ms"]) / (v["Baa"]["rank_stage_ms"] + v["Baa"]["cold_ms"]))
             for v in aa]
    u_cold = [math.log(v["B"]["cold_ms"] / v["Baa"]["cold_ms"]) for v in aa]
    noise = {"e2e": {"n": len(u_e2e), "mean": statistics.mean(u_e2e), "sd": statistics.stdev(u_e2e)},
             "cold": {"n": len(u_cold), "mean": statistics.mean(u_cold), "sd": statistics.stdev(u_cold)}}
    pts = sorted(by_point)
    walls = {a: statistics.mean(v) for a, v in prior["process_wall_ms"].items()}
    rank_wall, cold_wall, plant_wall, rho_wall = walls["kD4FO"], walls["cD4FO"], walls["cD4FOX"], walls["rT"]
    rng = np.random.default_rng(SEED)
    pyr = random.Random(SEED)

    def simulate(design, effect, kind, aa_null=False):
        p, k = design
        u = u_e2e if kind == "e2e" else u_cold
        a = np.zeros((p, k))
        b = np.zeros((p, k))
        for i in range(p):
            arch = by_point[pyr.choice(pts)]
            for j in range(k):
                s = arch[j % len(arch)]
                t = (s["rank_stage_ms"] + s["cold_ms"]) if kind == "e2e" else s["cold_ms"]
                b[i, j] = t
                a[i, j] = t * (1.0 if aa_null else effect) * math.exp(pyr.choice((-1, 1)) * pyr.choice(u))
        return a, b

    out = {"label": "sizing simulation, not a result", "noise_of_one_pair_log_ratio_from_k4c400_AA_pairs": noise,
           "effects": list(EFFECTS), "sims": SIMS, "draws": DRAWS, "designs": {}}
    for kind in ("e2e", "cold"):
        for name, design in DESIGNS.items():
            cells = {}
            for effect in EFFECTS:
                hit = 0
                for _ in range(SIMS):
                    lo, hi, est = lower_bound(*simulate(design, effect, kind), rng)
                    hit += lo > 1.0
                cells["%.3f" % effect] = {"power": hit / SIMS}
            out["designs"]["%s_%s" % (kind, name)] = cells
    # A/A point-estimate rule: share of null runs with the point estimate inside [0.97, 1.03]
    aa_rule = {}
    for kind in ("e2e", "cold"):
        ok = 0
        for _ in range(SIMS):
            a, b = simulate((12, 3), 1.0, kind, aa_null=True)
            ok += 0.97 <= a.sum() / b.sum() <= 1.03
        aa_rule[kind + "_point_inside_0.97_1.03_rate"] = ok / SIMS
    out["aa_control_12x3"] = aa_rule
    # cost per point (ms): primary 3 pairs x 2 sides x (rank + cold), A/A 2 pairs x 2 x (rank + cold), planted pair, rho
    def minutes(points, k=3, k_aa=2, cold_only=False):
        per_pair = (cold_wall if cold_only else rank_wall + cold_wall)
        per_point = 2 * k * per_pair + 2 * k_aa * per_pair + cold_wall + plant_wall + rho_wall
        return points * per_point / 6e4
    out["schedule_minutes_modelled"] = {"%s_e2e" % n: minutes(d[0], d[1]) for n, d in DESIGNS.items()}
    out["schedule_minutes_modelled"].update({"%s_cold_only" % n: minutes(d[0], d[1], cold_only=True)
                                             for n, d in DESIGNS.items()})
    out["mean_process_wall_ms"] = {"rank_kD4FO": rank_wall, "cold_cD4FO": cold_wall, "planted_cD4FOX": plant_wall,
                                   "rho_rT": rho_wall}
    out["min_delta"] = MIN_DELTA
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"noise": noise, "aa": aa_rule, "minutes": out["schedule_minutes_modelled"]}, indent=1))
    for key, cells in out["designs"].items():
        print(key, {e: c["power"] for e, c in cells.items()})


if __name__ == "__main__":
    main()
