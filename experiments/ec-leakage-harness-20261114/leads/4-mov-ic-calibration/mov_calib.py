#!/usr/bin/env python3
"""Lead 4: MOV (embedding degree 1) known-answer calibration. WEAK-CURVE row, not an improvement.
usage: mov_calib.py --bits 40,48,56,60 --trials 5 --budget 60 --out results.json
"""
import sys, os, json, math, time, random, argparse
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import ec_leakage as L
import cypari2
from cysignals.signals import AlarmInterrupt

pari = cypari2.Pari(); pari.allocatemem(1 << 30)

def build_mov(rbits, rng):
    while True:
        r = rng.randrange(1 << (rbits - 1), 1 << rbits) | 1
        if not L.is_probable_prime(r): continue
        c, d = rng.randrange(1, 16), rng.randrange(1, 16)
        p = (1 + r * c) ** 2 + (r * d) ** 2
        if L.is_probable_prime(p): break
    want = p + 1 - 2 * (1 + r * c)
    while True:
        A = rng.randrange(1, p)
        N = int(pari(f"ellcard(ellinit([{A},0],{p}))"))
        if N == want: break
    grp = [int(v) for v in pari(f"ellgroup(ellinit([{A},0],{p}))")]
    assert N % (r * r) == 0 and len(grp) == 2 and grp[1] % r == 0
    E = L.Curve(p, A, 0); cof = grp[0] // r
    while True:
        P = E.mul(cof, E.random_point(rng)); R = E.mul(cof, E.random_point(rng))
        if P is None or R is None: continue
        pari(f"EE=ellinit([{A},0],{p}); P=[{P[0]},{P[1]}]; R=[{R[0]},{R[1]}]; r={r}; e1=ellweilpairing(EE,P,R,r);")
        if not int(pari("e1==1")): break
    assert E.mul(r, P) is None and int(pari("e1^r==1"))
    return dict(E=E, p=p, A=A, r=r, P=P, R=R, N=N, c=c, d=d, emb=L.embedding_degree(r, p))

def mov_trials(m, trials, rng):
    E, P, r = m["E"], m["P"], m["r"]; out = []
    for t in range(trials):
        k = rng.randrange(2, r - 1); Q = E.mul(k, P); xq = Q[0]   # only x is used below
        Ql = E.lift_x(xq)  # sign unknown from x; either +-Q gives k or -k
        t0 = time.time()
        e2 = pari(f"ellweilpairing(EE,[{Ql[0]},{Ql[1]}],R,r)")
        t1 = time.time()
        kk = int(pari(f"znlog({e2},e1,r)"))
        t2 = time.time()
        # against-secret check: x([kk]P) == x([k]P), and kk == +-k mod r
        ok = (E.mul(kk % r, P)[0] == xq) and (kk % r in (k % r, (-k) % r))
        out.append(dict(k=k, recovered=kk % r, ok=bool(ok), sec_total=t2 - t0, sec_pairing=t1 - t0, sec_znlog=t2 - t1))
    return out

def ordinary(rbits, rng):
    while True:
        q = rng.randrange(1 << (rbits + 3), 1 << (rbits + 6)) | 1
        if not L.is_probable_prime(q): continue
        a, b = rng.randrange(q), rng.randrange(q)
        N = int(pari(f"ellcard(ellinit([{a},{b}],{q}))"))
        if N in (q, q + 1): continue
        rr = max(int(v) for v in pari(f"factor({N})[,1]"))
        if rr.bit_length() == rbits: return q, a, b, N, rr

def generic(rbits, ntr, budget, rng):
    q, a, b, N, rr = ordinary(rbits, rng); res = []
    for _ in range(ntr):
        pari(f"E2=ellinit([{a},{b}],{q}); G=ellmul(E2,random(E2),{N // rr}); while(G==[0],G=ellmul(E2,random(E2),{N // rr})); K=random({rr}); H=ellmul(E2,G,K);")
        t0 = time.time()
        try:
            kk = int(pari(f"alarm({int(budget)}, elllog(E2,H,G,{rr}))"))
            res.append(dict(finished=True, seconds=time.time() - t0, ok=bool(int(pari(f"{kk}==K")))))
        except AlarmInterrupt:
            res.append(dict(finished=False, seconds=time.time() - t0))
    return dict(q=q, qbits=q.bit_length(), r=rr, rbits=rr.bit_length(), N=N, trials=res)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bits", default="40,48,56,60"); ap.add_argument("--trials", type=int, default=5)
    ap.add_argument("--gtrials", default="2,2,1,1,1"); ap.add_argument("--budget", type=int, default=60)
    ap.add_argument("--seed", type=int, default=20261115); ap.add_argument("--out", default="results.json")
    a = ap.parse_args(); bits = [int(x) for x in a.bits.split(",")]
    gt = [int(x) for x in a.gtrials.split(",")]
    rows = []
    for i, rb in enumerate(bits):
        rng = random.Random(a.seed + rb)
        m = build_mov(rb, rng)
        tr = mov_trials(m, a.trials, rng)
        row = dict(rbits=m["r"].bit_length(), r=m["r"], p=m["p"], pbits=m["p"].bit_length(), A=m["A"], N=m["N"],
                   embedding_degree=m["emb"], mov_trials=tr, mov_all_ok=all(t["ok"] for t in tr),
                   mov_median_total=float(sorted(t["sec_total"] for t in tr)[len(tr)//2]) if tr else None,
                   mov_median_pairing=float(sorted(t["sec_pairing"] for t in tr)[len(tr)//2]),
                   mov_median_znlog=float(sorted(t["sec_znlog"] for t in tr)[len(tr)//2]),
                   rho_expected_ops=math.sqrt(math.pi * m["r"] / 4))
        row["generic"] = generic(rb, gt[min(i, len(gt)-1)], a.budget, rng); row["generic_budget"] = a.budget
        rows.append(row)
        print(rb, "MOV", row["mov_median_total"], row["mov_all_ok"], "generic", [(g["finished"], round(g["seconds"],1)) for g in row["generic"]["trials"]], file=sys.stderr, flush=True)
        json.dump(dict(label="[pcc:unverified]", rows=rows, args=vars(a)), open(a.out, "w"), indent=1, default=str)

main()
