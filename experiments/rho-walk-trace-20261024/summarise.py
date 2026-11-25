#!/usr/bin/env python3
"""Summarise trace.jsonl: shares of group_ops by component, per size.

Components (disjoint, sum to group_ops):
  table, walk starts, restarts (by reason), look-ahead retries (batch slots whose
  step was rejected), unprocessed slots (final round), cycle escapes (scan + doubling),
  steps in fruitless cycles (committed steps booked to a detected cycle), abandoned
  segments, and the remaining committed steps (productive).
dup_steps is reported separately: committed steps after the walk met a point another
trail had visited (they overlap the productive share)."""
import gzip, json, math, sys
from collections import defaultdict
from pathlib import Path

here = Path(__file__).parent
rows = [json.loads(l) for l in gzip.open(here / "trace.jsonl.gz", "rt")] if (here / "trace.jsonl.gz").exists() else \
    [json.loads(l) for l in open(sys.argv[1])]
by = defaultdict(list)
for r in rows:
    by[r["r_bits"]].append(r)
out = {}
for bits, rs in sorted(by.items()):
    tot = sum(r["total_ops"] for r in rs)
    f = lambda k: sum(r[k] for r in rs)
    fl = lambda k, i: sum(r[k][i] for r in rs)
    cyc = f("escape_cycle_steps")
    ab = f("abandon_wasted")
    prod = f("committed") - cyc - ab
    comp = {
        "table": f("table_ops"), "starts": f("start_ops"),
        "restart_selfmerge": fl("restart_ops", 0), "restart_useless": fl("restart_ops", 1),
        "restart_abandon": fl("restart_ops", 2),
        "retry_slots": f("retry_slots"), "unprocessed": f("unprocessed"), "escape_ops": f("escape_ops"),
        "cycle_steps": cyc, "abandon_steps": ab, "productive": prod,
    }
    assert sum(comp.values()) == tot, (bits, sum(comp.values()), tot)
    steps = f("committed")
    lens = defaultdict(int)
    for r in rs:
        for L, c in r["cycle_len"].items():
            lens[int(L)] += c
    S = [r["total_ops"] / math.sqrt(r["order"]) for r in rs]
    out[bits] = {
        "solves": len(rs), "mean_S": sum(S) / len(S), "mean_ops": tot / len(rs),
        "table_r": sorted({r["table_r"] for r in rs}), "W": sorted({r["W"] for r in rs}),
        "dp_bits": sorted({r["dp_bits"] for r in rs}),
        "share": {k: v / tot for k, v in comp.items()},
        "ops": comp,
        "per_1e4_steps": {"escapes": 1e4 * f("escapes") / steps, "abandons": 1e4 * f("abandons") / steps,
                          "retries": 1e4 * f("retry_slots") / f("step_ops")},
        "dup_step_share_of_steps": f("dup_steps") / steps,
        "restarts": [fl("restarts", i) for i in range(3)],
        "cycle_len": dict(sorted(lens.items())),
        "escape_unclosed": f("escape_unclosed"),
        "pre_solve_share": f("first_cross_at") and sum((r["solve_at"] - r["first_cross_at"]) for r in rs) / steps,
    }
json.dump(out, open(here / "summary.json", "w"), indent=1)
hdr = "| bits | solves | mean S | table r | walks W | table | starts | restarts | retries | escapes | cycle steps | abandon | productive | escapes /1e4 steps |"
print(hdr); print("|" + "---|" * 14)
for b, o in out.items():
    s = o["share"]
    print(f"| {b} | {o['solves']} | {o['mean_S']:.3f} | {o['table_r'][0]}-{o['table_r'][-1]} | {o['W'][0]}-{o['W'][-1]} | "
          f"{100*s['table']:.1f}% | {100*s['starts']:.1f}% | "
          f"{100*(s['restart_selfmerge']+s['restart_useless']+s['restart_abandon']):.1f}% | {100*(s['retry_slots']):.1f}% | "
          f"{100*s['escape_ops']:.1f}% | {100*s['cycle_steps']:.1f}% | {100*(s['abandon_steps']+s['unprocessed']):.1f}% | "
          f"{100*s['productive']:.1f}% | {o['per_1e4_steps']['escapes']:.1f} |")

print()
print("| bits | restarts / solve | of which same (a,b) | cycles escaped / solve | 2-cycles | 4-cycles | 6-cycles | >= 8 | steps per escaped cycle | retries / 1e4 slots | first cross-trail repeat to solve (share of steps) |")
print("|" + "---|" * 11)
for b, o in out.items():
    L = o["cycle_len"]; tot = sum(L.values())
    big = sum(v for k, v in L.items() if int(k) >= 8)
    n = o["solves"]
    cyc_steps = o["ops"]["cycle_steps"]
    print(f"| {b} | {sum(o['restarts'])/n:.1f} | {100*o['restarts'][0]/max(1,sum(o['restarts'])):.0f}% | {tot/n:.1f} | "
          f"{100*L.get(2,0)/tot:.0f}% | {100*L.get(4,0)/tot:.0f}% | {100*L.get(6,0)/tot:.0f}% | {100*big/tot:.0f}% | "
          f"{cyc_steps/tot:.1f} | {o['per_1e4_steps']['retries']:.0f} | {100*o['pre_solve_share']:.1f}% |")
