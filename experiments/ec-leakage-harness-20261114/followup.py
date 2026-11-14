#!/usr/bin/env python3
"""Follow-ups 1-4 to the f(k) = x([k]P) leakage harness (ec_leakage.py).

  tiny        1. Is the ~0.05 linear advantage on the 12-bit curve real structure?
              Compares three nulls: sample-level label permutation (as in the
              base run, 5000 permutations), an x-consistent null (a random
              relabelling of the distinct x-values, which keeps "same x, same
              label" and so measures what a linear fit can memorise on a finite
              group), and a split whose test x-values never occur in training.
  population  2. 20 curves per class (smooth, anomalous, prime) at 40 bits.
              Per-bit z-scores of the linear predictor against a permutation
              null, pooled per class, plus the structured attacks per curve.
  generic     3. Stronger generic predictors on the same population: the plug-in
              mutual information between x mod m and the class c = min(k* mod q,
              -k* mod q), and gradient boosting on bits of x, x mod m and the
              Legendre symbol of x, both against permutation nulls.
  mov         4. MOV positive control with embedding degree 1: y^2 = x^3 + A x over
              F_p with Frobenius pi = 1 + r(c + d i), so all of E[r] is rational
              and r | p - 1 (r about 2^60, p about 2^122).  The Weil pairing with a
              second independent r-torsion point moves x([k]P) into F_p*, where
              PARI's znlog (index calculus) recovers k*.  Negative control: an
              ordinary curve with a prime subgroup of the same size, where PARI's
              generic elllog gets a fixed time budget.  (Embedding degree 2 into
              F_{p^2} was tried first: PARI's fflog on a prime-order subgroup there
              scaled like a generic method, 4 s at r ~ 2^48 and 68 s at 2^56, so
              that transfer gave no advantage at these sizes.)

Results go to results/followup_<name>.json and .png.  Deterministic from seeds.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from multiprocessing import Pool

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ec_leakage as L  # noqa: E402

_PARI = None


def pari_group_order(E, rng=None):
    """#E(F_p) by PARI's SEA (ellcard).  Replaces L.group_order in the
    follow-ups for speed; cross-checked against L.group_order (BSGS) on the
    first curve of each population job.  Consumes no randomness."""
    global _PARI
    if _PARI is None:
        import cypari2
        _PARI = cypari2.Pari()
    return int(_PARI(f"ellcard(ellinit([{E.a},{E.b}],{E.p}))"))


_BSGS_ORDER = L.group_order
L.group_order = pari_group_order

OUT = os.path.join(HERE, "results")
SEED = 20261114


def dump(name, obj):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"followup_{name}.json"), "w") as fh:
        json.dump(obj, fh, indent=1)


def savefig(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f"followup_{name}.png"), dpi=70)


def plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as p
    return p


# ------------------------------------------------------------------ 1. tiny


def lin_acc(Xtr, ytr, Xte, yte):
    return L.linear_predictor_accuracy(Xtr, ytr, Xte, yte)


def cmd_tiny(args):
    base = json.load(open(os.path.join(OUT, "results.json")))["controls"]["tiny"]["curve"]
    E = L.Curve(base["p"], base["a"], base["b"])
    n, P = base["n"], tuple(base["P"])
    rng = random.Random(SEED + 1)
    rnp = np.random.default_rng(SEED + 1)
    m = 8 * n
    ks = [rng.randrange(1, n) for _ in range(m)]
    xs = np.array([E.mul(k, P)[0] for k in ks])
    nb = n.bit_length()
    Y = L.bits_matrix([L.canonical(k, n) for k in ks], nb)
    Xb = L.bits_matrix(xs.tolist(), E.p.bit_length())
    half = m // 2
    distinct = np.unique(xs)
    # the whole-group optimum: every distinct x once, label = that x's k* bit
    rows = []
    for bit in range(nb):
        y = Y[:, bit]
        obs = lin_acc(Xb[:half], y[:half], Xb[half:], y[half:])
        # (a) sample-level permutation null
        perm = np.array([lin_acc(Xb[:half], yy[:half], Xb[half:], yy[half:])
                         for yy in (rnp.permutation(y) for _ in range(args.perm))])
        # (b) x-consistent null: random bijection of the distinct x-values, so the
        # labels stay a function of x but lose any curve structure
        xcons = []
        for _ in range(args.xperm):
            pi = dict(zip(distinct.tolist(), rnp.permutation(distinct).tolist()))
            Xp = L.bits_matrix([pi[x] for x in xs.tolist()], E.p.bit_length())
            xcons.append(lin_acc(Xp[:half], y[:half], Xp[half:], y[half:]))
        xcons = np.array(xcons)
        # (c) disjoint split on distinct x (k* is a function of x, so duplicates
        # carry no information): train on half of the distinct x-values, test on
        # the rest, averaged over 50 random splits; null = labels permuted across
        # distinct x-values (1000 times), scored on the same 50 splits.
        lab = {x: yy for x, yy in zip(xs.tolist(), y.tolist())}
        Xd = L.bits_matrix(distinct.tolist(), E.p.bit_length())
        yd = np.array([lab[x] for x in distinct.tolist()])
        splits = [rnp.permutation(len(distinct)) for _ in range(50)]
        def split_acc(lbl):
            accs = []
            for s_ in splits:
                tr, te = s_[: len(s_) // 2], s_[len(s_) // 2:]
                accs.append(lin_acc(Xd[tr], lbl[tr], Xd[te], lbl[te]))
            return float(np.mean(accs))
        disj = split_acc(yd)
        disj_null = np.array([split_acc(rnp.permutation(yd)) for _ in range(1000)])
        rows.append({
            "bit": bit, "accuracy": obs,
            "perm_null_mean": float(perm.mean()), "perm_null_sd": float(perm.std(ddof=1)),
            "perm_p": (1 + int((perm >= obs).sum())) / (args.perm + 1),
            "xconsistent_null_mean": float(xcons.mean()), "xconsistent_null_sd": float(xcons.std(ddof=1)),
            "xconsistent_p": (1 + int((xcons >= obs).sum())) / (args.xperm + 1),
            "disjoint_accuracy": disj, "disjoint_null_mean": float(disj_null.mean()),
            "disjoint_null_sd": float(disj_null.std(ddof=1)),
            "disjoint_p": (1 + int((disj_null >= disj).sum())) / 1001,
        })
        print(f"bit {bit}: acc {obs:.3f} perm {perm.mean():.3f} xcons {xcons.mean():.3f} "
              f"(p={rows[-1]['xconsistent_p']:.3f}) disjoint {disj:.3f} vs {disj_null.mean():.3f}",
              file=sys.stderr)
    out = {"curve": base, "samples": m, "distinct_x": int(len(distinct)),
           "perm": args.perm, "xperm": args.xperm, "rows": rows}
    dump("tiny", out)
    p = plt()
    fig, ax = p.subplots(figsize=(8, 3.2))
    b = [r["bit"] for r in rows]
    ax.plot(b, [r["accuracy"] - 0.5 for r in rows], "o-", label="observed (shared x, train/test)")
    ax.plot(b, [r["perm_null_mean"] - 0.5 for r in rows], "s--", label="sample-permutation null")
    ax.errorbar(b, [r["xconsistent_null_mean"] - 0.5 for r in rows],
                yerr=[2 * r["xconsistent_null_sd"] for r in rows], fmt="^-", capsize=2,
                label="x-consistent null (random relabel of x), ±2 sd")
    ax.plot(b, [r["disjoint_accuracy"] - 0.5 for r in rows], "x:", label="disjoint-x test split")
    ax.axhline(0, color="k", lw=0.6)
    ax.set_xlabel("bit of k*")
    ax.set_ylabel("accuracy − 0.5")
    ax.set_title(f"12-bit curve: where the linear 'advantage' comes from (p={base['p']})", fontsize=9)
    ax.legend(fontsize=7)
    savefig(fig, "tiny")
    return out


# ------------------------------------------------------------------ 2+3. population


def mutual_info(a, b):
    a = np.asarray(a)
    b = np.asarray(b)
    _, ai = np.unique(a, return_inverse=True)
    _, bi = np.unique(b, return_inverse=True)
    J = np.zeros((ai.max() + 1, bi.max() + 1))
    np.add.at(J, (ai, bi), 1)
    J /= J.sum()
    pa, pb = J.sum(1, keepdims=True), J.sum(0, keepdims=True)
    nz = J > 0
    return float((J[nz] * np.log2(J[nz] / (pa @ pb)[nz])).sum())


def features(E, xs):
    p = E.p
    nb = p.bit_length()
    X = L.bits_matrix(xs, nb).astype(np.float32)
    mods = np.array([[x % m for m in range(2, 17)] for x in xs], dtype=np.float32)
    leg = np.array([[1.0 if pow(x, (p - 1) // 2, p) == 1 else -1.0] for x in xs], dtype=np.float32)
    frac = np.array([[x / p] for x in xs], dtype=np.float32)
    return np.hstack([X, mods, leg, frac])


def hgb_acc(F, y, half, seed):
    from sklearn.ensemble import HistGradientBoostingClassifier
    clf = HistGradientBoostingClassifier(max_iter=150, learning_rate=0.1, max_leaf_nodes=31,
                                         random_state=seed)
    clf.fit(F[:half], y[:half])
    return float((clf.predict(F[half:]) == y[half:]).mean())


def one_curve(job):
    kind, idx, samples, perm, gperm = job
    seed = SEED + 7919 * idx + {"smooth": 1, "anomalous": 2, "prime": 3}[kind]
    rng = random.Random(seed)
    rnp = np.random.default_rng(seed)
    E, n, P = L.find_curve(kind, 40, rng)
    N_sea = pari_group_order(E)
    N_bsgs = _BSGS_ORDER(E, random.Random(seed)) if idx == 0 else None
    assert N_bsgs in (None, N_sea), (N_bsgs, N_sea)
    assert E.mul(n, P) is None
    ks, xs = L.sample(E, n, P, samples, rng)
    half = samples // 2
    nb = n.bit_length()
    kstar = [L.canonical(k, n) for k in ks]
    Xb = L.bits_matrix(xs, E.p.bit_length())
    Y = L.bits_matrix(kstar, nb)
    z = []
    for i in range(nb):
        y = Y[:, i]
        if y.min() == y.max():  # top bit of k* < n/2 is constant: nothing to predict
            continue
        obs = lin_acc(Xb[:half], y[:half], Xb[half:], y[half:])
        null = np.array([lin_acc(Xb[:half], yy[:half], Xb[half:], yy[half:])
                         for yy in (rnp.permutation(y) for _ in range(perm))])
        z.append((obs - null.mean()) / null.std(ddof=1))
    f = L.factor(n)
    q = min((q for q in f if q > 2), default=3) if kind == "smooth" else 3
    c = np.array([min(k % q, (-k) % q) for k in kstar])
    res = {"kind": kind, "idx": idx, "seed": seed, "order_sea": N_sea, "order_bsgs_check": N_bsgs, "p": E.p, "a": E.a, "b": E.b, "n": n,
           "P": list(P), "q": q, "q_divides_n": n % q == 0,
           "embedding_degree_le50": L.embedding_degree(n, E.p), "linear_z": [float(v) for v in z]}
    # structured attacks
    if kind == "smooth":
        pred = np.array([L.ph_residue(E, P, n, q, x) for x in xs[half:]])
        res["ph_accuracy"] = float((pred == c[half:]).mean())
        res["ph_accuracy_c_mod_2"] = float((pred % 2 == c[half:] % 2).mean())
    if kind == "anomalous":
        r2 = random.Random(seed)
        test = list(zip(kstar[half:], xs[half:]))[:20]
        res["smart_recovered"] = sum(L.canonical(L.smart_attack(E, P, E.lift_x(x), r2), n) == ks_
                                     for ks_, x in test)
        res["smart_tested"] = len(test)
    # 3. generic predictors
    mi = {}
    for m in (2, 3, 4, 5, 7, 8, 16, q):
        xm = [x % m for x in xs]
        obs = mutual_info(xm, c)
        null = np.array([mutual_info(xm, rnp.permutation(c)) for _ in range(200)])
        mi[str(m)] = {"mi_bits": obs, "null_mean": float(null.mean()),
                      "p": (1 + int((null >= obs).sum())) / 201}
    res["mi_xmod_vs_class"] = mi
    F = features(E, xs)
    # binary target c mod 2: a function of c, so Pohlig-Hellman (where q | n)
    # determines it exactly; one tree per round instead of one per class.
    c2 = c % 2
    chance = float(max(c2[half:].mean(), 1 - c2[half:].mean()))
    obs_c = hgb_acc(F, c2, half, seed)
    null_c = [hgb_acc(F, rnp.permutation(c2), half, seed) for _ in range(gperm)]
    obs_b = hgb_acc(F, Y[:, 0], half, seed)
    null_b = [hgb_acc(F, rnp.permutation(Y[:, 0]), half, seed) for _ in range(gperm)]
    res["hgb_class"] = {"accuracy": obs_c, "null_mean": float(np.mean(null_c)),
                        "null_sd": float(np.std(null_c, ddof=1)), "majority": chance,
                        "p": (1 + sum(v >= obs_c for v in null_c)) / (gperm + 1)}
    res["hgb_bit0"] = {"accuracy": obs_b, "null_mean": float(np.mean(null_b)),
                       "null_sd": float(np.std(null_b, ddof=1)),
                       "p": (1 + sum(v >= obs_b for v in null_b)) / (gperm + 1)}
    print(f"[{kind} {idx}] n={n} q={q} maxz={max(z):.2f} hgb_c={obs_c:.3f}/{np.mean(null_c):.3f}",
          file=sys.stderr, flush=True)
    return res


def cmd_population(args):
    jobs = [(k, i, args.samples, args.perm, args.gperm)
            for i in range(args.curves) for k in ("smooth", "anomalous", "prime")]
    with Pool(args.procs) as pool:
        rows = pool.map(one_curve, jobs, chunksize=1)
    summ = {}
    for kind in ("smooth", "anomalous", "prime"):
        R = [r for r in rows if r["kind"] == kind]
        Z = np.concatenate([r["linear_z"] for r in R])
        s = {
            "curves": len(R), "bits_total": int(len(Z)),
            "linear_z_mean": float(Z.mean()), "linear_z_sd": float(Z.std(ddof=1)),
            "linear_frac_abs_z_gt_3": float((np.abs(Z) > 3).mean()),
            "linear_max_z": float(Z.max()),
            # one-sided normal tail of the max over all bits of the class
            "linear_max_z_familywise_p": float(min(1.0, len(Z) * 0.5 * math.erfc(Z.max() / math.sqrt(2)))),
            "hgb_class_adv": [r["hgb_class"]["accuracy"] - r["hgb_class"]["null_mean"] for r in R],
            "hgb_class_min_p": min(r["hgb_class"]["p"] for r in R),
            "hgb_bit0_adv": [r["hgb_bit0"]["accuracy"] - r["hgb_bit0"]["null_mean"] for r in R],
            "hgb_bit0_min_p": min(r["hgb_bit0"]["p"] for r in R),
            "mi_min_p": min(v["p"] for r in R for v in r["mi_xmod_vs_class"].values()),
            "mi_tests": sum(len(r["mi_xmod_vs_class"]) for r in R),
        }
        if kind == "smooth":
            s["ph_accuracy"] = [r["ph_accuracy"] for r in R]
        if kind == "anomalous":
            s["smart"] = f"{sum(r['smart_recovered'] for r in R)}/{sum(r['smart_tested'] for r in R)}"
        summ[kind] = s
    out = {"samples": args.samples, "perm": args.perm, "gperm": args.gperm, "summary": summ, "curves": rows}
    dump("population", out)
    p = plt()
    fig, axes = p.subplots(1, 2, figsize=(9, 3.2))
    grid = np.linspace(-4, 4, 200)
    for kind, col in zip(summ, ("#4C72B0", "#C44E52", "#55A868")):
        Z = np.concatenate([r["linear_z"] for r in rows if r["kind"] == kind])
        axes[0].hist(Z, bins=40, range=(-4, 4), density=True, histtype="step", color=col,
                     label=f"{kind} ({len(Z)} bits)")
    axes[0].plot(grid, np.exp(-grid**2 / 2) / math.sqrt(2 * math.pi), "k:", label="N(0,1)")
    axes[0].set_xlabel("linear predictor z (per bit of k*)")
    axes[0].legend(fontsize=7)
    axes[0].set_title("Blind linear predictor, 20 curves/class", fontsize=9)
    data = [[r["hgb_class"]["accuracy"] - r["hgb_class"]["null_mean"] for r in rows if r["kind"] == k]
            for k in summ]
    axes[1].boxplot(data, tick_labels=list(summ))
    sm = [r["ph_accuracy_c_mod_2"] - r["hgb_class"]["null_mean"] for r in rows if r["kind"] == "smooth"]
    axes[1].scatter([1] * len(sm), sm, marker="*", color="#C44E52", zorder=3,
                    label="Pohlig–Hellman (smooth)")
    axes[1].axhline(0, color="k", lw=0.6)
    axes[1].set_ylabel("accuracy − null mean")
    axes[1].set_title("(±k* mod q) mod 2: gradient boosting vs Pohlig–Hellman", fontsize=9)
    axes[1].legend(fontsize=7)
    savefig(fig, "population")
    print(json.dumps(summ, indent=1, default=lambda v: round(v, 4) if isinstance(v, float) else v))
    return out


# ------------------------------------------------------------------ 4. MOV


def cmd_mov(args):
    import cypari2
    pari = cypari2.Pari()
    pari.allocatemem(1 << 31)
    rng = random.Random(SEED + 4)
    # Embedding degree 1 with full rational r-torsion: CM by Z[i], Frobenius
    # pi = 1 + r(c + d i), so r | pi - 1, E[r] is in E(F_p), and r | p - 1.
    # p = N(pi); one quartic twist of y^2 = x^3 + A x has trace 2(1 + r c).
    while True:
        r = rng.randrange(1 << (args.rbits - 1), 1 << args.rbits) | 1
        if not L.is_probable_prime(r):
            continue
        c, d = rng.randrange(1, 1 << 4), rng.randrange(1, 1 << 4)
        p = (1 + r * c) ** 2 + (r * d) ** 2
        if L.is_probable_prime(p):
            break
    want = p + 1 - 2 * (1 + r * c)
    while True:
        A = rng.randrange(1, p)
        N = int(pari(f"ellcard(ellinit([{A},0],{p}))"))
        if N == want:
            break
    grp = [int(v) for v in pari(f"ellgroup(ellinit([{A},0],{p}))")]
    assert N % (r * r) == 0 and len(grp) == 2 and grp[1] % r == 0, (N, grp)
    E = L.Curve(p, A, 0)
    cof = grp[0] // r
    while True:
        P = E.mul(cof, E.random_point(rng))
        R = E.mul(cof, E.random_point(rng))
        if P is None or R is None:
            continue
        pari(f"EE=ellinit([{A},0],{p}); P=[{P[0]},{P[1]}]; R=[{R[0]},{R[1]}]; r={r};"
             f"e1=ellweilpairing(EE,P,R,r);")
        if not int(pari("e1==1")):
            break
    assert E.mul(r, P) is None and int(pari("e1^r==1"))
    k_emb = L.embedding_degree(r, p)
    trials = []
    for t in range(args.trials):
        k = rng.randrange(1, r)
        Q = E.mul(k, P)
        Ql = E.lift_x(Q[0])  # only x([k]P) is used
        t0 = time.time()
        kk = int(pari(f"znlog(ellweilpairing(EE,[{Ql[0]},{Ql[1]}],R,r),e1,r)"))
        dt = time.time() - t0
        ok = L.canonical(kk % r, r) == L.canonical(k, r) and E.mul(kk, P)[0] == Q[0]
        trials.append({"k": k, "recovered": kk, "ok": bool(ok), "seconds": dt})
        print(f"MOV trial {t}: ok={ok} {dt:.2f}s", file=sys.stderr, flush=True)
    # negative control: ordinary curve over a prime of the same size with a prime
    # subgroup of the same size; PARI ellog (generic) gets the same time budget.
    while True:
        q = rng.randrange(1 << (args.rbits + 3), 1 << (args.rbits + 6)) | 1
        if not L.is_probable_prime(q):
            continue
        a, b = rng.randrange(q), rng.randrange(q)
        N = int(pari(f"ellcard(ellinit([{a},{b}],{q}))"))
        if N == q + 1 or N == q:
            continue
        rr = max(int(v) for v in pari(f"factor({N})[,1]"))
        if abs(rr.bit_length() - args.rbits) <= 1:
            break
    ord_emb = L.embedding_degree(rr, q, 200)
    budget = args.budget
    pari(f"E2=ellinit([{a},{b}],{q}); G=ellmul(E2,random(E2),{N // rr}); K=random({rr}); H=ellmul(E2,G,K);")
    t0 = time.time()
    from cysignals.signals import AlarmInterrupt
    try:
        kk = int(pari(f"alarm({int(math.ceil(budget))}, elllog(E2,H,G,{rr}))"))
        neg = {"finished": True, "seconds": time.time() - t0, "ok": bool(int(pari(f"{kk}==K")))}
    except AlarmInterrupt:
        neg = {"finished": False, "seconds": time.time() - t0}
    out = {
        "mov_curve": {"p": p, "pbits": p.bit_length(), "A": A, "B": 0, "N": N, "group": grp,
                      "r": r, "rbits": r.bit_length(), "c": c, "d": d, "P": list(P), "R": list(R),
                      "embedding_degree": k_emb},
        "trials": trials, "recovered": sum(t["ok"] for t in trials),
        "median_seconds": float(np.median([t["seconds"] for t in trials])),
        "rho_expected_group_ops": math.sqrt(math.pi * r / 4),
        "ordinary_control": {"q": q, "a": a, "b": b, "N": N, "r": rr, "rbits": rr.bit_length(),
                             "embedding_degree_le200": ord_emb, "budget_seconds": budget, **neg},
    }
    dump("mov", out)
    p_ = plt()
    fig, ax = p_.subplots(figsize=(6, 2.8))
    ax.bar(["MOV, embedding degree 1\nmedian per k", "generic ellog\n(ordinary, same r)"],
           [out["median_seconds"], neg["seconds"]], color=["#55A868", "#C44E52"])
    ax.set_ylabel("seconds")
    ax.set_title(f"r ≈ 2^{args.rbits}: MOV {out['recovered']}/{len(trials)} k* recovered; "
                 f"generic {'finished' if neg['finished'] else 'stopped at budget'}", fontsize=9)
    savefig(fig, "mov")
    print(json.dumps({k: v for k, v in out.items() if k != "trials"}, indent=1))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sp = ap.add_subparsers(dest="cmd", required=True)
    t = sp.add_parser("tiny")
    t.add_argument("--perm", type=int, default=5000)
    t.add_argument("--xperm", type=int, default=200)
    po = sp.add_parser("population")
    po.add_argument("--curves", type=int, default=20)
    po.add_argument("--samples", type=int, default=2000)
    po.add_argument("--perm", type=int, default=100)
    po.add_argument("--gperm", type=int, default=20)
    po.add_argument("--procs", type=int, default=os.cpu_count())
    mv = sp.add_parser("mov")
    mv.add_argument("--rbits", type=int, default=60)
    mv.add_argument("--trials", type=int, default=10)
    mv.add_argument("--budget", type=float, default=600.0, help="seconds for generic ellog")
    a = ap.parse_args()
    {"tiny": cmd_tiny, "population": cmd_population, "mov": cmd_mov}[a.cmd](a)


if __name__ == "__main__":
    main()
