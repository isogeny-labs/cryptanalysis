#!/usr/bin/env python3
"""Paired summary, as 11.11: python3 summarize.py A.json B.json [A2.json]
Statistic: per seed, end-to-end total-ops exponent (least squares of log2 total_ops on
log2 n over the sizes present for that seed) and S per size; mean of B-A with SE and sign split."""
import json, sys, math, collections
def load(f):
    d = collections.defaultdict(dict)
    for r in json.load(open(f)):
        g = r['gaudry']; d[g['p']][g['n']] = g  # n differs per seed; key by order
    return d
def rows(f):
    out = {}
    cnt = collections.Counter()
    for r in json.load(open(f)):
        g = r['gaudry']; cnt[g['p']] += 1
        out[(g['p'], cnt[g['p']])] = g  # seed index = order within size
    return out
def fit(xs, ys):
    mx = sum(xs)/len(xs); my = sum(ys)/len(ys)
    return sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / sum((x-mx)**2 for x in xs)
def ms(v):
    m = sum(v)/len(v)
    sd = math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1)) if len(v) > 1 else float('nan')
    return m, sd/math.sqrt(len(v)) if len(v) > 1 else float('nan')
def per(g, key):
    if key == 'res_per_full': return g['residuals']/max(g['lp_full_relations'] + (g['lp_histogram'][0]), 1)
    if key == 'lp_ops': return g['la_ops'] - g['lp_merge_ops']
    return g[key]
def main():
    files = sys.argv[1:]
    R = [rows(f) for f in files]
    names = ['A', 'B', 'A2'][:len(R)]
    sizes = sorted({k[0] for k in R[0]})
    seeds = {p: sorted(k[1] for k in R[0] if k[0] == p) for p in sizes}
    for g in [g for r in R for g in r.values()]:
        assert g['correct'] is True, ('unchecked/incorrect run', g['p'], g['correct'])
    def exps(r):
        out = {}
        for s in range(1, 7):
            pts = [(math.log2(r[(p, s)]['n']), math.log2(r[(p, s)]['total_ops'])) for p in sizes if (p, s) in r]
            if len(pts) >= 3: out[s] = fit(*zip(*pts))
        return out
    E = [exps(r) for r in R]
    for i in range(1, len(R)):
        print(f"\n== {names[i]} vs {names[0]} (paired; difference = {names[i]} - {names[0]}) ==")
        common = sorted(set(E[0]) & set(E[i]))
        d = [E[i][s]-E[0][s] for s in common]
        m, se = ms(d)
        print(f"exponent: {names[0]} {ms([E[0][s] for s in common])[0]:.3f}  {names[i]} {ms([E[i][s] for s in common])[0]:.3f}  "
              f"paired diff {m:+.3f} +- {se:.3f}  (n={len(d)} seeds; worse/better {sum(x>0 for x in d)}/{sum(x<0 for x in d)})")
        print("size | S_A | S_B | diff +- SE | diff/SE | B lower/higher | n")
        npass = 0
        for p in sizes:
            ss = [s for s in seeds[p] if (p, s) in R[i]]
            d = [R[i][(p, s)]['s'] - R[0][(p, s)]['s'] for s in ss]
            m, se = ms(d)
            a = sum(R[0][(p, s)]['s'] for s in ss)/len(ss); b = sum(R[i][(p, s)]['s'] for s in ss)/len(ss)
            z = m/se if se == se and se > 0 else float('nan')
            if m < 0 and z < -2: npass += 1
            print(f"{p} | {a:.0f} | {b:.0f} | {m:+.0f} +- {se:.0f} | {z:+.1f} | {sum(x<0 for x in d)}/{sum(x>0 for x in d)} | {len(ss)}")
        print(f"sizes with B lower by >2 SE: {npass}")
    print("\n== per-size means by arm ==")
    keys = ['residuals', 'res_per_full', 'la_avg_weight', 'lp_ops', 'lp_merge_ops', 'la_ops', 'lp_full_relations', 'total_ops', 's']
    print("p arm n | " + " | ".join(keys))
    for p in sizes:
        for nm, r in zip(names, R):
            ss = [s for s in seeds[p] if (p, s) in r]
            print(p, nm, len(ss), "| " + " | ".join(f"{sum(per(r[(p,s)], k) for s in ss)/len(ss):.4g}" for k in keys))
    print("\n== exponents per seed ==")
    for nm, e in zip(names, E): print(nm, {s: round(v, 3) for s, v in e.items()})
main()
