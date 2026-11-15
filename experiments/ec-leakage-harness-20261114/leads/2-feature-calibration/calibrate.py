#!/usr/bin/env python3
"""Lead 2: positive-control calibration of the generic-learner feature family.

For each of the 60 curves in results/followup_population.json draw samples
k uniform in [1,n-1], x = x([k]P).  Target (as in scale.py): cmod2 = c mod 2,
c = min(k* mod q, -k* mod q).  Feature sets:
  default : bits of x, x mod 2..32, Legendre(x), x/p            (scale.py)
  struct  : default + bits of xs, xs/p, where xs = x([m]Q), Q = lift_x(x),
            m = n/q on smooth curves (q | n).  On non-smooth curves q does not
            divide n and m = n//q (floor): same code path, no subgroup.
Learners: least-squares linear and HistGradientBoosting (scale.py settings).
Statistic: z vs no-leakage null (scale.py null_z).
Controls: planted default-expressible leak (y = [x mod 7 < 3], k-independent),
shuffled-label null, bit0 of k* as negative target, A/A (two training sets +
two learner seeds, same test set).
"""
import json, math, os, random, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
H = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, H)
import ec_leakage as L
import scale as S

NTR, NTE = int(os.environ.get("NTR", 3000)), int(os.environ.get("NTE", 3000))
LIMIT = int(os.environ.get("PER_CLASS", 20))


def draw(pari, c, m, n_total, seed):
    pari(f"setrand({seed}); E=ellinit([{c['a']},{c['b']}],{c['p']}); G=[{c['P'][0]},{c['P'][1]}];")
    v = pari(f"my(n={c['n']}); vector({n_total},i,my(k=1+random(n-1)); my(x=lift(ellmul(E,G,k)[1]));"
             f" my(y=ellordinate(E,x)[1]); [k, x, lift(ellmul(E,[x,y],{m})[1])])")
    a = np.array([[int(t[0]), int(t[1]), int(t[2])] for t in v], dtype=np.int64)
    return a[:, 0], a[:, 1], a[:, 2]


def struct_feats(xs, p):
    nb = p.bit_length()
    bits = ((xs[:, None] >> np.arange(nb)) & 1).astype(np.float32)
    return np.hstack([bits, (xs / p).astype(np.float32)[:, None]])


def fit(lname, F, y, Ft, seed):
    if y.min() == y.max():
        return np.full(len(Ft), int(y[0]), dtype=np.int64)
    return S.fit_linear(F, y, Ft) if lname == "linear" else S.fit_hgb(F, y, Ft, seed)


def main():
    import cypari2
    pari = cypari2.Pari(); pari.allocatemem(1 << 29)
    pop = json.load(open(os.path.join(H, "results", "followup_population.json")))
    rows, curves_meta = [], []
    rng = np.random.default_rng(20261115)
    for kind in ("smooth", "anomalous", "prime"):
        for c in [c for c in pop["curves"] if c["kind"] == kind][:LIMIT]:
            t0 = time.time()
            n, p, q = c["n"], c["p"], c["q"]
            m = n // q
            tot = 2 * NTR + NTE
            k, x, xs = draw(pari, c, m, tot, c["seed"] + 77)
            E = L.Curve(p, c["a"], c["b"])
            for i in random.Random(1).sample(range(tot), 30):   # re-derive with harness arithmetic
                Q = E.lift_x(int(x[i]))
                assert E.mul(int(k[i]), tuple(c["P"]))[0] == int(x[i])
                assert E.mul(m, Q)[0] == int(xs[i]) if E.mul(m, Q) else True
            ks = np.minimum(k, n - k)
            cls = np.minimum(ks % q, (-ks) % q)
            nd = len(set(xs[:2000].tolist()))
            tg = {"cmod2": cls % 2, "bit0": ks & 1, "planted_xmod7": (x % 7 < 3).astype(np.int64)}
            tg["shuffled"] = rng.permutation(tg["cmod2"])
            Fd = S.features(x, p)
            Fs = np.hstack([Fd, struct_feats(xs, p)])
            te = slice(2 * NTR, tot)
            sets = {"A": slice(0, NTR), "B": slice(NTR, 2 * NTR)}
            for tname, y in tg.items():
                for fname, F in (("default", Fd), ("struct", Fs)):
                    for lname in ("linear", "hgb"):
                        for rep, sl in sets.items():
                            seed = c["seed"] + (1 if rep == "A" else 2)
                            pred = fit(lname, F[sl], y[sl], F[te], seed)
                            acc, mu, z = S.null_z(pred, y[te])
                            rows.append(dict(kind=kind, idx=c["idx"], q=q, target=tname, feat=fname,
                                             learner=lname, rep=rep, acc=acc, null_mean=mu, z=z,
                                             majority=float(max(y[te].mean(), 1 - y[te].mean()))))
            curves_meta.append(dict(kind=kind, idx=c["idx"], q=q, q_divides_n=c["q_divides_n"], distinct_xs_2000=nd))
            r = [w for w in rows if w["kind"] == kind and w["idx"] == c["idx"] and w["target"] == "cmod2" and w["rep"] == "A" and w["learner"] == "hgb"]
            print(f"[{kind} {c['idx']}] q={q} distinct xs={nd} " + " ".join(f"{w['feat']}:{w['acc']:.3f}(z{w['z']:+.1f})" for w in r)
                  + f" {time.time()-t0:.0f}s", file=sys.stderr, flush=True)
    summ = summarize(rows)
    json.dump(dict(params=dict(NTR=NTR, NTE=NTE, per_class=LIMIT), curves=curves_meta, summary=summ, rows=rows),
              open(os.path.join(HERE, "results.json"), "w"), indent=1)
    plot(rows)
    print(json.dumps(summ, indent=1))


def summarize(rows):
    out = {}
    for kind in ("smooth", "anomalous", "prime"):
        for tname in ("cmod2", "bit0", "planted_xmod7", "shuffled"):
            for fname in ("default", "struct"):
                for lname in ("linear", "hgb"):
                    R = [r for r in rows if (r["kind"], r["target"], r["feat"], r["learner"]) == (kind, tname, fname, lname)]
                    if not R: continue
                    A = {r["idx"]: r for r in R if r["rep"] == "A"}
                    B = {r["idx"]: r for r in R if r["rep"] == "B"}
                    za = np.array([A[i]["z"] for i in A]); zb = np.array([B[i]["z"] for i in A])
                    acc = np.array([r["acc"] for r in R]); mu = np.array([r["null_mean"] for r in R])
                    dd = np.array([A[i]["acc"] - B[i]["acc"] for i in A])
                    out[f"{kind}|{tname}|{fname}|{lname}"] = dict(
                        n_curves=len(A), mean_acc=float(acc.mean()), mean_null=float(mu.mean()),
                        min_acc_per_curve=float(acc.min()), frac_curves_z_gt_5=float(np.mean(np.maximum(za, zb) > 5)),
                        mean_z=float(np.r_[za, zb].mean()), max_z=float(np.r_[za, zb].max()),
                        min_z=float(np.r_[za, zb].min()), sd_z=float(np.r_[za, zb].std(ddof=1)),
                        AA_mean_acc_diff=float(dd.mean()), AA_sd_acc_diff=float(dd.std(ddof=1)),
                        AA_z_corr=float(np.corrcoef(za, zb)[0, 1]) if za.std() > 0 and zb.std() > 0 else None)
    return out


def plot(rows):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.2))
    for ax, lname in zip(axes, ("linear", "hgb")):
        for j, (feat, col) in enumerate((("default", "#888"), ("struct", "#C44E52"))):
            for i, kind in enumerate(("smooth", "anomalous", "prime")):
                v = [r["acc"] - r["null_mean"] for r in rows if (r["kind"], r["target"], r["feat"], r["learner"], r["rep"]) == (kind, "cmod2", feat, lname, "A")]
                ax.scatter(np.full(len(v), i + (j - .5) * .3) + np.random.default_rng(0).uniform(-.05, .05, len(v)), v, s=8, color=col, label=feat if i == 0 else None)
        ax.axhline(0, color="k", lw=.5); ax.set_xticks(range(3)); ax.set_xticklabels(["smooth", "anomalous", "prime"])
        ax.set_title(f"{lname}: cmod2 accuracy minus null mean", fontsize=8); ax.set_ylabel("acc - null")
    axes[0].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "calibration.png"), dpi=70)


if __name__ == "__main__":
    main()
