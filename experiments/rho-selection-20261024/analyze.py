#!/usr/bin/env python3
"""Analysis frozen in PROTOCOL.md.  Usage: analyze.py rows.jsonl[.gz] [main_rows.jsonl[.gz]] [--out DIR].

Per size: ratio of sums arm/base over all (curve, target) pairs, bootstrap over
curves (curves resampled with replacement, the same resample for every arm).
Pooled: geometric mean over sizes of the per-size ratios.  Bonferroni: the
intervals are the (alpha/m, 1 - alpha/m) percentiles with alpha = 0.05 and m =
the number of arm-versus-base comparisons.  Winner rule: see PROTOCOL.md."""
import gzip, json, math, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

BOOT, ALPHA, SEED = 10000, 0.05, 20261025


def load(path):
    op = gzip.open if str(path).endswith(".gz") else open
    return [json.loads(l) for l in op(path, "rt")]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else Path(".")
    if "--out" in sys.argv:
        args.remove(str(out))
    rows = load(args[0])
    main_rows = load(args[1]) if len(args) > 1 else None
    sizes = sorted({r["bits"] for r in rows})
    arms = list(dict.fromkeys(r["arm"] for r in rows))
    curves = sorted({(r["bits"], r["curve"]) for r in rows})
    ops = defaultdict(dict)  # (arm) -> {(bits,curve,target): ops}
    ok = True
    for r in rows:
        ops[r["arm"]][(r["bits"], r["curve"], r["target"])] = r["ops"]
        ok &= bool(r["ok"])
    keys = sorted(ops["base"])
    # checks
    checks = {"all_solves_correct": ok, "n_solves_per_arm": len(keys)}
    checks["control_identical_to_base"] = all(ops["control"][k] == ops["base"][k] for k in keys)
    if main_rows is not None:
        mo = {(r["bits"], r["curve"], r["target"]): r["ops"] for r in main_rows}
        checks["unflagged_main_identical_to_base"] = all(mo[k] == ops["base"][k] for k in keys) and all(r["ok"] for r in main_rows)
    cmp_arms = [a for a in arms if a not in ("base", "control")]
    m = len(cmp_arms)
    per = {}  # arm -> size -> per-curve sums arrays
    ncur = {}
    for b in sizes:
        cs = sorted({c for (bb, c) in curves if bb == b})
        ncur[b] = len(cs)
        for arm in arms:
            per.setdefault(arm, {})[b] = np.array([sum(v for (bb, c, t), v in ops[arm].items() if bb == b and c == ci) for ci in cs], float)
    rng = np.random.default_rng(SEED)
    idx = {b: rng.integers(0, ncur[b], size=(BOOT, ncur[b])) for b in sizes}
    lo_q, hi_q = 100 * ALPHA / m, 100 * (1 - ALPHA / m)  # Bonferroni percentiles
    res = {}
    for arm in cmp_arms:
        cell, boots = {}, []
        for b in sizes:
            num, den = per[arm][b], per["base"][b]
            ratio = num.sum() / den.sum()
            bs = num[idx[b]].sum(1) / den[idx[b]].sum(1)
            cell[b] = {"ratio": ratio, "lo": float(np.percentile(bs, lo_q)), "hi": float(np.percentile(bs, hi_q))}
            boots.append(np.log(bs))
        pooled_bs = np.exp(np.mean(boots, axis=0))
        pooled = math.exp(np.mean([math.log(cell[b]["ratio"]) for b in sizes]))
        p_lo, p_hi = float(np.percentile(pooled_bs, lo_q)), float(np.percentile(pooled_bs, hi_q))
        regress = [b for b in sizes if cell[b]["lo"] > 1.0]
        win = bool(p_hi < 1.0 and not regress and ok)
        res[arm] = {"pooled": pooled, "pooled_lo": p_lo, "pooled_hi": p_hi, "cells": cell, "regress_sizes": regress, "winner_criteria_met": win}
    ranked = sorted([a for a in cmp_arms if res[a]["winner_criteria_met"]], key=lambda a: res[a]["pooled"])
    summary = {"checks": checks, "bootstrap": BOOT, "alpha": ALPHA, "comparisons": m, "sizes": sizes, "curves_per_size": ncur,
               "arms": res, "winner_ranking": ranked, "selected": ranked[0] if ranked else None}
    # mean S per size per arm (exact: ops / sqrt(order))
    S = {}
    orders = {(r["bits"], r["curve"]): r["order"] for r in rows}
    for arm in arms:
        S[arm] = {b: float(np.mean([v / math.sqrt(orders[(bb, c)]) for (bb, c, t), v in ops[arm].items() if bb == b])) for b in sizes}
    summary["mean_S"] = S
    (out / "results.json").write_text(json.dumps(summary, indent=1))
    lines = ["| arm | pooled ratio | Bonferroni interval | " + " | ".join(f"{b} bits" for b in sizes) + " | criteria met |", "|" + "---|" * (4 + len(sizes))]
    for a in cmp_arms:
        r = res[a]
        lines.append(f"| {a} | {r['pooled']:.4f} | [{r['pooled_lo']:.4f}, {r['pooled_hi']:.4f}] | " +
                     " | ".join(f"{r['cells'][b]['ratio']:.3f} [{r['cells'][b]['lo']:.3f}, {r['cells'][b]['hi']:.3f}]" for b in sizes) +
                     f" | {'yes' if r['winner_criteria_met'] else 'no'} |")
    lines += ["", "Mean S = group_ops / sqrt(order) per arm and size:", "",
              "| arm | " + " | ".join(f"{b} bits" for b in sizes) + " |", "|" + "---|" * (1 + len(sizes))]
    for a in arms:
        lines.append(f"| {a} | " + " | ".join(f"{S[a][b]:.3f}" for b in sizes) + " |")
    lines += ["", "Checks: " + json.dumps(checks), "", f"Selected: {summary['selected']} (ranking {ranked})"]
    (out / "results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


main()
