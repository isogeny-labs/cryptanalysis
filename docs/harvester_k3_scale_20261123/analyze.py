#!/usr/bin/env python3
"""Analyse ladder cells: python3 analyze.py DIR [DIR...]  -> prints tables, writes summary.json next to first DIR."""
import glob, json, math, random, sys, os
cells = {}
for d in sys.argv[1:]:
    for f in sorted(glob.glob(d + "/p*_s*.json")):
        b = os.path.basename(f)[:-5]; p, arm, s = b.split("_"); p = int(p[1:]); s = int(s[1:])
        r = json.load(open(f))[0]; cells[(p, arm, s)] = r
sizes = sorted({k[0] for k in cells})
def ok(r): return r["gaudry"]["solved"] and r["gaudry"]["correct"] is True
bad = [k for k, r in cells.items() if not ok(r)]
def lg(x): return math.log2(x)
def slope(xs, ys):
    mx = sum(xs)/len(xs); my = sum(ys)/len(ys)
    return sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / sum((x-mx)**2 for x in xs)
random.seed(20261123)
def boot(vals, B=10000):
    if len(vals) < 2: return (float("nan"),)*2
    ms = sorted(sum(random.choice(vals) for _ in vals)/len(vals) for _ in range(B))
    return ms[int(.025*B)], ms[int(.975*B)]
def ms(v): m = sum(v)/len(v); lo, hi = boot(v); return m, lo, hi
out = {"unsolved_or_wrong": [list(k) for k in bad], "sizes": sizes}
print("failures:", bad)
# per size table
print("\n p     n_bits  seedsA seedsB | S_A mean | S_B mean | S_B/S_A paired mean [95% CI] | S_rho mean | S_A/rho | S_B/rho | wall A s | wall B s")
rows = []
for p in sizes:
    sa = {s: cells[(p, "A", s)] for (pp, a, s) in cells if pp == p and a == "A"}
    sb = {s: cells[(p, "B", s)] for (pp, a, s) in cells if pp == p and a == "B"}
    both = sorted(set(sa) & set(sb))
    ratios = [sb[s]["gaudry"]["s"]/sa[s]["gaudry"]["s"] for s in both]
    rho = [r["rho"]["s"] for r in list(sa.values()) + list(sb.values())]
    rho_by = {}
    for s, r in list(sa.items()) + list(sb.items()): rho_by[s] = r["rho"]["s"]
    rm = sum(rho_by.values())/len(rho_by)
    mA = sum(r["gaudry"]["s"] for r in sa.values())/max(1, len(sa)); mB = sum(r["gaudry"]["s"] for r in sb.values())/max(1, len(sb))
    # distance to rho: per-seed ratio S/S_rho of the same instance
    dA = [r["gaudry"]["s"]/r["rho"]["s"] for r in sa.values()]; dB = [r["gaudry"]["s"]/r["rho"]["s"] for r in sb.values()]
    rr = ms(ratios) if ratios else (float("nan"),)*3
    nb = list(sb.values())[0]["gaudry"]["bits"] if sb else list(sa.values())[0]["gaudry"]["bits"]
    wa = sum(r["gaudry"]["wall_ms"] for r in sa.values())/max(1, len(sa))/1e3; wb = sum(r["gaudry"]["wall_ms"] for r in sb.values())/max(1, len(sb))/1e3
    print(f"{p:6d} {nb:6.1f}  {len(sa):2d}     {len(sb):2d}    | {mA:8.0f} | {mB:8.0f} | {rr[0]:.3f} [{rr[1]:.3f},{rr[2]:.3f}] (n={len(both)}) | {rm:.2f} | {sum(dA)/max(1,len(dA)):8.0f} | {sum(dB)/max(1,len(dB)):8.0f} | {wa:7.0f} | {wb:7.0f}")
    rows.append(dict(p=p, bits=nb, nA=len(sa), nB=len(sb), S_A=mA, S_B=mB, ratio=rr, rho=rm, dA=sum(dA)/max(1,len(dA)), dB=sum(dB)/max(1,len(dB))))
out["table"] = rows
# exponents
SEEDS = [int(x) for x in os.environ.get("SEEDS", "1,2,3,4,5,6").split(",")]
def fit(arm, szs, key="total_ops"):
    res = {}
    for s in SEEDS:
        pts = [(lg(cells[(p, arm, s)]["gaudry"]["n"]), lg(cells[(p, arm, s)]["gaudry"][key])) for p in szs if (p, arm, s) in cells and ok(cells[(p, arm, s)])]
        if len(pts) >= 3: res[s] = slope(*zip(*pts))
    return res
def report(name, szs):
    fa, fb = fit("A", szs), fit("B", szs)
    both = sorted(set(fa) & set(fb))
    d = [fb[s]-fa[s] for s in both]
    print(f"\n[{name}] sizes {szs}")
    for lab, f in (("A", fa), ("B", fb)):
        if f: m, lo, hi = ms(list(f.values())); print(f"  exponent {lab}: {m:.3f} [{lo:.3f},{hi:.3f}] seeds={sorted(f)}")
    if d:
        m, lo, hi = ms(d); print(f"  paired B-A: {m:.3f} [{lo:.3f},{hi:.3f}] seeds={both}, B lower on {sum(x<0 for x in d)}/{len(d)}")
    out[name] = dict(A=fa, B=fb, paired=d)
report("original4", [271, 523, 1039, 2083])
report("extended_all", sizes)
report("top4", sizes[-4:])
report("top3", sizes[-3:])
report("new_three_only", [p for p in sizes if p > 2083])
# local slopes between consecutive sizes
print("\nlocal slopes d log2 ops / d log2 n between consecutive sizes (mean over seeds with both cells)")
for arm in "AB":
    s_ = []
    for p0, p1 in zip(sizes, sizes[1:]):
        v = []
        for s in SEEDS:
            if (p0, arm, s) in cells and (p1, arm, s) in cells:
                a, b = cells[(p0, arm, s)]["gaudry"], cells[(p1, arm, s)]["gaudry"]
                v.append((lg(b["total_ops"])-lg(a["total_ops"]))/(lg(b["n"])-lg(a["n"])))
        s_.append((p0, p1, v))
    print(" ", arm, ["%d-%d: %.3f (n=%d)" % (a, b, sum(v)/len(v), len(v)) if v else f"{a}-{b}: -" for a, b, v in s_])
# S accounting audit
# pooled-rho distance (ratio of means) per size
print("\ndistance to rho, ratio of mean S over seeds / mean rho S (same seeds)")
for r in rows:
    print(f"  p={r['p']:6d}  A/rho {r['S_A']/r['rho']:8.0f}   B/rho {(r['S_B']/r['rho']) if r['S_B'] else float('nan'):8.0f}")
print("\nS-accounting audit (per size, arm B and A means)")
for arm in "AB":
    for p in sizes:
        rs = [r["gaudry"] for (pp, a, s), r in cells.items() if pp == p and a == arm]
        if not rs: continue
        n = len(rs)
        m = lambda f: sum(f(g) for g in rs)/n
        la_eq = lambda g: g["la_ops"]*g["la_fp_equiv"]/g["fp_muls_per_add"]
        rel_eq = lambda g: g["group_ops"] + (g["oracle_fp_muls"] + g["precompute_fp_muls"])/g["fp_muls_per_add"]
        la_share = m(lambda g: la_eq(g)/g["total_ops"])
        mg_share = m(lambda g: g["lp_merge_ops"]*g["la_fp_equiv"]/g["fp_muls_per_add"]/g["total_ops"])
        w_la = m(lambda g: g["linear_algebra_ms"]/max(1e-9, la_eq(g)))*1e3  # us per charged op
        w_rel = m(lambda g: (g["wall_ms"]-g["linear_algebra_ms"])/rel_eq(g))*1e3
        print(f"  {arm} p={p:6d} LA share of total_ops {la_share*100:5.2f}% (merge {mg_share*100:5.2f}%)  wall us/charged-op: LA+harvest {w_la:8.3f}  relation-phase {w_rel:8.3f}  ratio {w_la/w_rel:6.2f}")
json.dump(out, open(os.path.join(sys.argv[1], "summary.json"), "w"), indent=1, default=str)
