#!/usr/bin/env python3
"""L2 analysis exactly as PROTOCOL.md fixes it.

rho   = conflicts_B / conflicts_A per (file, k)       (candidate vs baseline)
omega = wall_B / wall_A per (file, k)                (wall_B includes SBVA)
A/A   = conflicts_A(k) / conflicts_A(0), k in {1, 2}  (shuffle noise floor)
Geometric means over the l = 4 UNSAT instances; 95% bootstrap intervals that
resample base CNFs (10,000 resamples, seed 'l2-boot'). Censored calls are kept
at their recorded conflict count and flagged. Writes summary.json and prints a
Markdown table plus the decision.
"""
import json, math, random, collections, sys

rows = [json.loads(l) for l in open(sys.argv[1] if len(sys.argv) > 1 else "rows.jsonl")]
# Deviation (RESULT.md): CaDiCaL HEAD omits eliminated variables from its printed
# model, so arm-A model checks can fail spuriously. A row with model_ok False is
# accepted only if model_recheck.json shows a full model (--elim=0, same shuffled
# CNF) that satisfies every clause.
import os
rechk = {}
if os.path.exists("model_recheck.json"):
    rechk = {(r["file"], r["k"]): r["sat"] and r["model_satisfies"] for r in json.load(open("model_recheck.json"))}
bad = [r for r in rows if not r["answer_ok"]
       or (r.get("model_ok") is False and not rechk.get((r["file"], r["k"]), False))]
cens = [r for r in rows if r["censored"]]
by = collections.defaultdict(dict)
for r in rows:
    by[(r["file"], r["k"])][r["arm"]] = r

def meta(f):
    l = int(f[1]); enc = f.split("_")[1]; idx = int(f.split("_t")[1][:2])
    return l, enc, idx

def gm(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))

def per_file(sel):
    """file -> (list of log rho, list of log omega, list of log aa)"""
    out = collections.defaultdict(lambda: ([], [], []))
    for (f, k), d in by.items():
        l, enc, idx = meta(f)
        if "A" not in d or "B" not in d or not sel(l, enc, d["A"]["decomposable"]):
            continue
        a, b = d["A"], d["B"]
        out[f][0].append(math.log(max(b["conflicts"], 1) / max(a["conflicts"], 1)))
        out[f][1].append(math.log(b["wall"] / a["wall"]))
        if k > 0 and (f, 0) in by:
            out[f][2].append(math.log(max(a["conflicts"], 1) / max(by[(f, 0)]["A"]["conflicts"], 1)))
    return out

def stat(pf, j, boot=10000):
    files = sorted(f for f in pf if pf[f][j])
    if not files:
        return None
    pt = math.exp(sum(sum(pf[f][j]) for f in files) / sum(len(pf[f][j]) for f in files))
    rng = random.Random("l2-boot")
    bs = []
    for _ in range(boot):
        s = [rng.choice(files) for _ in files]
        bs.append(math.exp(sum(sum(pf[f][j]) for f in s) / sum(len(pf[f][j]) for f in s)))
    bs.sort()
    return pt, bs[int(0.025 * boot)], bs[int(0.975 * boot)], len(files), sum(len(pf[f][j]) for f in files)

cells = [("l4 UNSAT (primary)", lambda l, e, d: l == 4 and not d),
         ("l4 UNSAT plain", lambda l, e, d: l == 4 and not d and e == "plain"),
         ("l4 UNSAT dual", lambda l, e, d: l == 4 and not d and e == "dual"),
         ("l4 SAT", lambda l, e, d: l == 4 and d),
         ("l3 UNSAT", lambda l, e, d: l == 3 and not d),
         ("l3 SAT", lambda l, e, d: l == 3 and d)]
summary = {"rows": len(rows), "invalid": len(bad), "censored": len(cens), "cells": {}}
print("| subset | files | pairs | conflicts B/A (95% CI) | A/A conflicts (95% CI) | wall B/A (95% CI) |")
print("|---|--:|--:|--|--|--|")
for name, sel in cells:
    pf = per_file(sel)
    r, w, aa = stat(pf, 0), stat(pf, 1), stat(pf, 2)
    if not r:
        continue
    fmt = lambda s: f"{s[0]:.3f} [{s[1]:.3f}, {s[2]:.3f}]" if s else "n/a"
    print(f"| {name} | {r[3]} | {r[4]} | {fmt(r)} | {fmt(aa)} | {fmt(w)} |")
    summary["cells"][name] = {"rho": r, "aa": aa, "omega": w}

p = summary["cells"].get("l4 UNSAT (primary)")
if bad:
    decision = "INVALID (answer or model mismatch)"
elif p:
    rho, aa, om = p["rho"], p["aa"], p["omega"]
    excl = rho[2] < aa[1] or rho[1] > aa[2]
    if rho[0] <= 1 / 1.3 and excl and om[0] < 1:
        decision = "SUCCESS (measured improvement)"
    elif (aa[1] <= rho[0] <= aa[2]) or rho[0] > 1 / 1.3:
        decision = "KILL"
    else:
        decision = "INCONCLUSIVE"
else:
    decision = "INCOMPLETE"
summary["decision"] = decision
print(f"\ninvalid rows: {len(bad)}; censored calls: {len(cens)}; total rows: {len(rows)}")
print("decision (PROTOCOL.md rule):", decision)
json.dump(summary, open("summary.json", "w"), indent=1)
