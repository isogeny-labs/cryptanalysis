#!/usr/bin/env python3
"""Paired summary of the k=4 large-prime harvester run (plain arm vs lp arm).

usage: summarize_k4_paired.py paired_a.json [paired_b.json ...]
Rows come in (plain, lp) pairs per (p, seed); both arms share the curve, the
base, the residual stream and the 8 rho runs.  r = la_ops*16/(S_rho*sqrt(n)*c_add).
Registered: report whether r_lp falls below 0.518 by more than 2 SE.
"""
import json, math, sys, collections

R_INF = 0.518
rows = []
for f in sys.argv[1:]:
    rows += json.load(open(f))
pairs = collections.OrderedDict()
for r in rows:
    pairs.setdefault((r["p"], r["seed"]), {})[r["arm"]] = r

def ms(x):
    n = len(x)
    m = sum(x) / n
    sd = math.sqrt(sum((v - m) ** 2 for v in x) / (n - 1)) if n > 1 else float("nan")
    return m, sd / math.sqrt(n) if n > 1 else float("nan")

# pooled rho over every run in the file (both arms share the same runs; count once per pair)
pool = []
for (p, s), d in pairs.items():
    if "plain" in d:
        pool += [x["s"] for x in d["plain"]["rho"]]
S_pool = sum(pool) / len(pool)

def rr(r, S):
    return r["la_ops"] * 16 / (S * math.sqrt(r["n"]) * r["fp_muls_per_add"])

print(f"pairs: {len(pairs)}; pooled rho S = {S_pool:.3f} over {len(pool)} runs")
hdr = "p seed arm small unknowns rows_fed resid resid/row row_w core_w merge_ops wied_ops la_ops r_own r_pool correct"
print(hdr)
for (p, s), d in pairs.items():
    for arm in ("plain", "lp"):
        if arm not in d:
            continue
        r = d[arm]
        print(f"{p} {s} {arm} {r['small_base']} {r['unknowns']} {r['rows_fed']} {r['residuals']} "
              f"{r['residuals_per_row']:.1f} {r['row_weight']:.2f} {r['core_row_weight']:.2f} "
              f"{r['merge_ops']} {r['wiedemann_ops']} {r['la_ops']} {r['r']:.3f} {rr(r, S_pool):.3f} "
              f"{r['solved'] and r['correct']}")

complete = [(k, d) for k, d in pairs.items() if "plain" in d and "lp" in d]
def col(arm, f):
    return [f(d[arm]) for _, d in complete]
print()
for name, f in [("r (own rho)", lambda r: r["r"]), ("r (pooled rho)", lambda r: rr(r, S_pool)),
                ("LA ops (mod-n mults)", lambda r: r["la_ops"]), ("unknowns", lambda r: r["unknowns"]),
                ("rows fed", lambda r: r["rows_fed"]), ("row weight (fed)", lambda r: r["row_weight"]),
                ("row weight (core)", lambda r: r["core_row_weight"]),
                ("residuals", lambda r: r["residuals"]), ("residuals per row", lambda r: r["residuals_per_row"]),
                ("relation-phase group ops", lambda r: r["relation_group_ops"])]:
    a, b = col("plain", f), col("lp", f)
    ma, sa = ms(a); mb, sb = ms(b)
    dm, ds = ms([y - x for x, y in zip(a, b)])
    print(f"{name:26s} plain {ma:12.4g} +-{sa:9.3g}   lp {mb:12.4g} +-{sb:9.3g}   paired lp-plain {dm:11.4g} +-{ds:9.3g}"
          + (f" (z {dm/ds:.1f})" if ds == ds and ds > 0 else ""))

print()
for use, label in (("r", "own rho"), ("pool", "pooled rho")):
    f = (lambda r: r["r"]) if use == "r" else (lambda r: rr(r, S_pool))
    b = col("lp", f)
    mb, sb = ms(b)
    z = (mb - R_INF) / sb if sb == sb and sb > 0 else float("nan")
    print(f"registered check ({label}): mean r_lp = {mb:.3f} +- {sb:.3f} (N={len(b)}); "
          f"0.518 - r_lp = {R_INF - mb:.3f} = {(R_INF - mb)/sb:.2f} SE; below by more than 2 SE: {(R_INF - mb) > 2*sb}")
print()
by = collections.OrderedDict()
for (p, s), d in complete:
    by.setdefault(p, []).append(d)
for p, ds in by.items():
    a = [d["plain"]["r"] for d in ds]; b = [d["lp"]["r"] for d in ds]
    print(f"p={p}: r plain {['%.3f' % x for x in a]}  r lp {['%.3f' % x for x in b]}")
