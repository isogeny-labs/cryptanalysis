#!/usr/bin/env python3
"""Paired per-repeat S ratios (baseline / lead) and a percentile bootstrap.

usage: analyze_ratchet.py RAW_DIR OUT_DIR cell-id ...
Reads RAW_DIR/<cell>-baseline.json and -lead.json, pairs repeat i with repeat i
(same instance, same seed, checked), and writes OUT_DIR/ratchet_cells.{csv,json}
and ratchet_per_repeat.csv.  Bootstrap: 10,000 resamples of the 8 paired log
ratios, python random.Random(20261119), 2.5% / 97.5% percentiles of the mean.
Standard library only.
"""
import csv, json, math, os, random, sys

raw, out = sys.argv[1], sys.argv[2]
cells = sys.argv[3:]


def boot(vals, seed=20261119, B=10000):
    rng = random.Random(seed)
    n = len(vals)
    logs = [math.log(v) for v in vals]
    ms = sorted(sum(logs[rng.randrange(n)] for _ in range(n)) / n for _ in range(B))
    return math.exp(sum(logs) / n), math.exp(ms[int(0.025 * B)]), math.exp(ms[int(0.975 * B) - 1])


def status(c, arm):
    p = f"{raw}/{c}-{arm}.status.json"
    return json.load(open(p)) if os.path.exists(p) else {}


cells_out, rep_out = [], []
for c in cells:
    b = json.load(open(f"{raw}/{c}-baseline.json"))
    l = json.load(open(f"{raw}/{c}-lead.json"))
    br, lr = b["rows"], l["rows"]
    assert len(br) == len(lr), (c, len(br), len(lr))
    ok, ratios = True, []
    for i, (x, y) in enumerate(zip(br, lr)):
        same = (x["r"] == y["r"] and x["spec"]["seed"] == y["spec"]["seed"]
                and x["instance"] == y["instance"] and x["recovered"] == y["recovered"]
                and x["decomposition"]["relations_found"] == y["decomposition"]["relations_found"]
                and x["decomposition"]["targets_tried"] == y["decomposition"]["targets_tried"])
        ok &= bool(same and x["verified"] and y["verified"])
        ratios.append(x["s"] / y["s"])
        rep_out.append(dict(
            cell=c, repeat=i, seed=x["spec"]["seed"], r=x["r"], h=x["group_order"] // x["r"],
            columns=x["factor_base"]["columns"], trials=x["decomposition"]["targets_tried"],
            relations=x["decomposition"]["relations_found"], S_baseline=x["s"], S_lead=y["s"],
            ratio=x["s"] / y["s"], gae_baseline=x["total_gae"], gae_lead=y["total_gae"],
            setup_gae_baseline=x["decomposition"]["setup"]["gae"],
            setup_gae_lead=y["decomposition"]["setup"]["gae"],
            identical_relations_and_log=bool(same), verified_both=bool(x["verified"] and y["verified"])))
    gm, lo, hi = boot(ratios)
    rho = b.get("rho_reference") or {}
    rs = rho.get("mean_s")
    mb = sum(x["s"] for x in br) / len(br)
    ml = sum(y["s"] for y in lr) / len(lr)
    cells_out.append(dict(
        cell=c, instance=br[0]["instance"], r=br[0]["r"], h=br[0]["group_order"] // br[0]["r"],
        columns=br[0]["factor_base"]["columns"], repeats=len(br), all_identical_and_verified=ok,
        geomean_ratio=gm, ci_lo=lo, ci_hi=hi, min_ratio=min(ratios), max_ratio=max(ratios),
        S_baseline_mean=mb, S_lead_mean=ml, rho_S_mean=rs, rho_runs=rho.get("runs"),
        baseline_over_rho=(mb / rs if rs else None), lead_over_rho=(ml / rs if rs else None),
        baseline_arm_wall_s=status(c, "baseline").get("wall_seconds"),
        lead_arm_wall_s=status(c, "lead").get("wall_seconds")))
os.makedirs(out, exist_ok=True)
for name, rows in (("ratchet_cells", cells_out), ("ratchet_per_repeat", rep_out)):
    with open(f"{out}/{name}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
json.dump(cells_out, open(f"{out}/ratchet_cells.json", "w"), indent=1)
for r in cells_out:
    print(r["cell"], f'{r["geomean_ratio"]:.4f} [{r["ci_lo"]:.4f}, {r["ci_hi"]:.4f}]',
          "exact+verified" if r["all_identical_and_verified"] else "NOT EXACT")
