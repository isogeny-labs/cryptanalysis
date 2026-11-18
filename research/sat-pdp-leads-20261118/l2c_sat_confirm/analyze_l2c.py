#!/usr/bin/env python3
"""L2c analysis exactly as PROTOCOL.md fixes it. Primary: l = 4, all base CNFs
(decomposable targets only), rho = conflicts_C / conflicts_A, geometric mean,
95% bootstrap over base CNFs (10,000 resamples, seed 'l2-boot'); A/A band
A(k)/A(0), k in {1,2}, same subset and bootstrap. Prints a table and the
decision, writes summary.json."""
import json, math, random, collections, sys

rows = [json.loads(l) for l in open(sys.argv[1] if len(sys.argv) > 1 else "rows.jsonl")]
bad = [r for r in rows if not r["answer_ok"] or r["answer"] != "SAT" or r.get("model_ok") is False]
cens = [r for r in rows if r["censored"]]
by = collections.defaultdict(dict)
for r in rows:
    by[(r["file"], r["k"])][r["arm"]] = r


def per_file(sel):
    out = collections.defaultdict(lambda: ([], [], []))
    for (f, k), d in by.items():
        if "A" not in d or "C" not in d:
            continue
        l, enc = int(f[1]), f.split("_")[1]
        if not sel(l, enc):
            continue
        a, c = d["A"], d["C"]
        out[f][0].append(math.log(max(c["conflicts"], 1) / max(a["conflicts"], 1)))
        out[f][1].append(math.log(c["wall"] / a["wall"]))
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


cells = [("l4 SAT (primary)", lambda l, e: l == 4), ("l4 plain", lambda l, e: l == 4 and e == "plain"),
         ("l4 dual", lambda l, e: l == 4 and e == "dual"), ("l3 SAT", lambda l, e: l == 3)]
summary = {"rows": len(rows), "invalid": len(bad), "censored": len(cens), "cells": {}}
fmt = lambda s: f"{s[0]:.3f} [{s[1]:.3f}, {s[2]:.3f}]" if s else "n/a"
print("| subset | files | pairs | conflicts C/A (95% CI) | A/A conflicts (95% CI) | wall C/A (95% CI) |")
print("|---|--:|--:|--|--|--|")
for name, sel in cells:
    pf = per_file(sel)
    r, w, aa = stat(pf, 0), stat(pf, 1), stat(pf, 2)
    if not r:
        continue
    print(f"| {name} | {r[3]} | {r[4]} | {fmt(r)} | {fmt(aa)} | {fmt(w)} |")
    summary["cells"][name] = {"rho": r, "aa": aa, "omega": w}
p = summary["cells"].get("l4 SAT (primary)")
if bad:
    decision = "INVALID"
elif not p:
    decision = "INCOMPLETE"
else:
    rho, aa = p["rho"], p["aa"]
    no_overlap = rho[2] < aa[1] or rho[1] > aa[2]
    if rho[0] <= 1 / 1.3 and rho[2] < 1 and no_overlap:
        decision = "CONFIRMED"
    elif rho[1] <= 1 <= rho[2] or rho[0] > 1 / 1.3:
        decision = "REFUTED"
    else:
        decision = "INCONCLUSIVE"
summary["decision"] = decision
print(f"\ninvalid rows: {len(bad)}; censored: {len(cens)}; rows: {len(rows)}")
print("decision (PROTOCOL.md rule):", decision)
json.dump(summary, open("summary.json", "w"), indent=1)
