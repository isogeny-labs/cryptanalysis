#!/usr/bin/env python3
"""Analyze GT-02 optimal-base runs. usage: analyze.py ladder|confirm|prime DIR"""
import sys, json, glob, os, re, random, math
def load(p):
    j = json.load(open(p)); return j
def rows(j):
    return j["rows"]
def S(j): return [r["s"] for r in rows(j)]
def ok(j, nrep=12):
    return j["all_verified"] and len(rows(j)) == nrep and all(r["verified"] and not r["exhausted"] for r in rows(j))
def gm(x): return math.exp(sum(math.log(v) for v in x)/len(x))
def boot(ratios, B=10000, seed=1):
    rnd = random.Random(seed); n = len(ratios); g = []
    for _ in range(B): g.append(gm([ratios[rnd.randrange(n)] for _ in range(n)]))
    g.sort(); return g[int(.025*B)], g[int(.975*B)]
def pair(jb, jl):
    # pair per repeat; require identical instance and planted target (recovered log)
    rb, rl = rows(jb), rows(jl)
    same = jb["instance"] == jl["instance"] and [r["recovered"] for r in rb] == [r["recovered"] for r in rl]
    rat = [b["s"]/l["s"] for b, l in zip(rb, rl)]
    return same, rat
def mean(x): return sum(x)/len(x)
def setup(j): return mean([r["decomposition"]["setup"]["gae"] for r in rows(j)]) if "setup" in rows(j)[0]["decomposition"] else None
def ladder(D):
    res = {}
    for pb in sorted(glob.glob(f"{D}/A_c2_*_base.json")):
        m_ = re.match(r".*A_c2_n(\d+)_m(\d)_d(\d+)_base", pb); n, m, d = map(int, m_.groups())
        pl = pb.replace("_base", "_lead")
        if not os.path.exists(pl): continue
        jb, jl = load(pb), load(pl)
        cell = dict(n=n, m=m, d=d, ok_b=ok(jb), ok_l=ok(jl), Sb=mean(S(jb)), Sl=mean(S(jl)),
                    cols=rows(jb)[0]["factor_base"].get("columns"), h=None)
        if cell["ok_b"] and cell["ok_l"]:
            same, rat = pair(jb, jl); cell["same"] = same; cell["ratio"] = gm(rat); cell["lo"], cell["hi"] = boot(rat)
        res.setdefault((n, m), []).append(cell)
    return res
if __name__ == "__main__":
    mode, D = sys.argv[1], sys.argv[2]
    if mode == "ladder":
        res = ladder(D); sel = []
        print("| n | m | d | cols | S base | S lead | ratio [95% CI] | usable b/l |\n|--|--|--|--|--|--|--|--|")
        for (n, m), cs in sorted(res.items()):
            cs.sort(key=lambda c: c["d"])
            for c in cs:
                r = f"{c['ratio']:.3f} [{c['lo']:.3f},{c['hi']:.3f}]" if "ratio" in c else "-"
                print(f"| {n} | {m} | {c['d']} | {c['cols']} | {c['Sb']:.2f} | {c['Sl']:.2f} | {r} | {c['ok_b']}/{c['ok_l']} |")
            ub = [c for c in cs if c["ok_b"]]; ul = [c for c in cs if c["ok_l"]]
            db = min(ub, key=lambda c: c["Sb"]); dl = min(ul, key=lambda c: c["Sl"])
            sel.append(dict(n=n, m=m, d=db["d"], dl=dl["d"], best_b=db["Sb"], best_l=dl["Sl"]))
        json.dump(sel, open(f"{D}/selection.json", "w"), indent=1)
        print("\nselection (argmin baseline d, argmin lead dl):"); [print(s) for s in sel]
    if mode in ("confirm", "prime"):
        pat = "B_c2_*_base.json" if mode == "confirm" else "P_*_base.json"
        print("| cell | r | h | cols | S base | S lead | paired ratio [95% CI] | identical+verified | rho S | base/rho | lead/rho | setup base->lead GAE |\n|--|--|--|--|--|--|--|--|--|--|--|--|")
        for pb in sorted(glob.glob(f"{D}/{pat}"), key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))]):
            pl = pb.replace("_base", "_lead"); 
            if not os.path.exists(pl): continue
            jb, jl = load(pb), load(pl); nm = os.path.basename(pb)[:-10]
            if not (ok(jb) and ok(jl)): print(f"| {nm} | unusable (resource limit / unverified) |"); continue
            same, rat = pair(jb, jl); lo, hi = boot(rat); r0 = rows(jb)[0]
            rho = [x["rho_s"] for x in rows(jb) if x.get("rho_s")]
            rs = mean(rho) if rho else (jb.get("rho_reference") or {}).get("s") if isinstance(jb.get("rho_reference"), dict) else None
            h = round((r0["group_order"]) / r0["r"])
            sb, sl = setup(jb), setup(jl)
            print(f"| {nm} | {r0['r']} | {h} | {r0['factor_base'].get('columns')} | {mean(S(jb)):.2f} | {mean(S(jl)):.2f} | {gm(rat):.3f} [{lo:.3f},{hi:.3f}] | {same and ok(jb) and ok(jl)} | {rs if rs is None else round(rs,2)} | {'' if not rs else round(mean(S(jb))/rs,2)} | {'' if not rs else round(mean(S(jl))/rs,2)} | {sb if sb is None else round(sb)}->{sl if sl is None else round(sl)} |")
