#!/usr/bin/env python3
"""Summarise trace.jsonl: share of operations per part of the walk, cycle
statistics, and the paired ratio of curve_solve to rho (mean over curves of
log(mean curve_solve ops / mean rho ops), same targets and seeds)."""
from __future__ import annotations

import collections
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def summary(R: list[dict]) -> dict:
    tot = sum(r["total_ops"] for r in R)
    sh = lambda k: sum(r[k] for r in R) / tot  # noqa: E731
    cyc = collections.Counter()
    for r in R:
        for L, c in r["cycle_len"].items():
            cyc[int(L)] += c
    by_curve = collections.defaultdict(lambda: [0, 0])
    for r in R:
        v = by_curve[(r["r_bits"], r["curve_index"])]
        v[0] += r["curve_solve_ops"]
        v[1] += r["rho_ops"]
    ratio = math.exp(sum(math.log(c / h) for c, h in by_curve.values()) / len(by_curve))
    ab = sum(r["abandons"] for r in R)
    steps = sum(r["useful_steps"] for r in R)
    c2 = cyc.get(2, 0)
    m = R[0]["m"]
    return {
        "solves": len(R), "curves": len(by_curve), "m": m, "ratio_curve_solve_vs_rho": ratio, "theory_ratio": math.sqrt(2 / m),
        "share_productive": (steps - sum(r["abandon_wasted"] for r in R)) / tot, "share_cycle_steps": sh("abandon_wasted"),
        "share_retries": sh("retry_steps"), "share_table_starts_restarts": sh("table_ops") + sh("start_ops") + sh("restart_ops"),
        "abandons_per_1e4_steps": 1e4 * ab / steps, "abandons_in_short_cycle": sum(r["abandon_cycle"] for r in R) / max(ab, 1),
        "cycle2_same_multiplier_after_retry": sum(r["cycle2_after_retry"] for r in R) / max(c2, 1),
        "cycle_len": dict(sorted(cyc.items())), "recover_failures": sum(r["coll_recover_fail"] for r in R),
    }


def main() -> int:
    import gzip
    rows = [json.loads(l) for l in gzip.open(HERE / "trace.jsonl.gz", "rt")]
    out = {}
    for fam in ("j1728", "j0"):
        for bits in (24, 28, 32, "all"):
            R = [r for r in rows if r["family"] == fam and (bits == "all" or r["r_bits"] == bits)]
            out[f"{fam} r={bits}"] = summary(R)
    (HERE / "summary.json").write_text(json.dumps(out, indent=1))
    print("| family | r bits | ratio vs rho | theory | productive | in cycles | retries | table+starts+restarts | abandons per 10^4 steps |")
    print("|---|---|---|---|---|---|---|---|---|")
    for k, s in out.items():
        fam, bits = k.split(" r=")
        print(f"| {fam} | {bits} | {s['ratio_curve_solve_vs_rho']:.3f} | {s['theory_ratio']:.3f} | {s['share_productive']:.1%} | {s['share_cycle_steps']:.1%} | "
              f"{s['share_retries']:.1%} | {s['share_table_starts_restarts']:.1%} | {s['abandons_per_1e4_steps']:.1f} |")
    for k in ("j1728 r=all", "j0 r=all"):
        s = out[k]
        print(f"{k}: abandoned walks in a short cycle {s['abandons_in_short_cycle']:.0%}; 2-cycles reusing a multiplier after a retry "
              f"{s['cycle2_same_multiplier_after_retry']:.0%}; recover failures {s['recover_failures']}; lengths {dict(list(s['cycle_len'].items())[:6])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
