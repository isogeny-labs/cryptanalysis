#!/usr/bin/env python3
"""Lead 5: PARI fflog timing on a prime-order-r subgroup of F_p^2*, r | p+1.
MEASURED part: timings + log-log fit. ANALYTIC part: L[1/3] crossover. [pcc:unverified]"""
import json, sys, time, random, math
import numpy as np
import cypari2
pari = cypari2.Pari(); pari.allocatemem(800_000_000)
SEED = 20261114
random.seed(SEED); pari.setrand(SEED)
BITS = [int(b) for b in sys.argv[1].split(',')] if len(sys.argv) > 1 else [40,44,48,52,56]
REPS = int(sys.argv[2]) if len(sys.argv) > 2 else 3
OUT = sys.argv[3] if len(sys.argv) > 3 else 'results.json'

def make(bits):
    r = pari.nextprime(random.getrandbits(bits) | (1 << (bits-1)))
    while True:  # p = r*h - 1, p = 3 mod 4 prime, so r | p+1 (embedding degree 2)
        h = random.randrange(2, 4000)
        p = r*h - 1
        if p % 4 == 3 and pari.isprime(p): return int(r), int(p)


print("start",flush=True)
rows = []
for bits in BITS:
    r, p = make(bits); print("made",r,p,flush=True)
    a = pari.ffgen(pari(p)**2, 'a')
    # element of order r: random^((p^2-1)/r), the subgroup lies in the norm-1 torus
    while True:
        g = pari.random(a) ** ((pari(p)**2 - 1)//pari(r))
        if g != 1: break
    ts = []
    for rep in range(REPS):
        k = random.randrange(2, r-1)
        h = g**k
        t0 = time.perf_counter()
        x = pari.fflog(h, g, pari(r))       # order given as r (prime): no factoring of p^2-1 needed
        dt = time.perf_counter() - t0
        assert g**x == h
        ts.append(dt)
    rows.append(dict(r_bits=bits, r=r, p=p, p_bits=int(p).bit_length(), cofactor=(p+1)//r,
                     times=ts, median=float(np.median(ts))))
    print(bits, p.bit_length(), rows[-1]['median'], flush=True)

# smooth control: full-group log in F_p^2* where p^2-1 is smooth -> Pohlig-Hellman, expect fast & non-sqrt
ctrl = None
fit = None
if len(rows) >= 3:
    x = np.log2([2.0**R['r_bits'] for R in rows]); y = np.log2([R['median'] for R in rows])
    A = np.vstack([x, np.ones_like(x)]).T
    (m, c), res, *_ = np.linalg.lstsq(A, y, rcond=None)
    # bootstrap over reps
    rng = np.random.default_rng(SEED); ms = []
    for _ in range(2000):
        yy = np.log2([rng.choice(R['times']) for R in rows])
        ms.append(np.linalg.lstsq(A, yy, rcond=None)[0][0])
    fit = dict(exponent=float(m), ci95=[float(np.percentile(ms,2.5)), float(np.percentile(ms,97.5))], intercept_log2=float(c))
    # exponent between endpoints
    fit['endpoint_exponent'] = float((y[-1]-y[0])/(x[-1]-x[0]))
json.dump(dict(label='MEASURED [pcc:unverified]', seed=SEED, reps=REPS, rows=rows, fit=fit), open(OUT,'w'), indent=1)
print(fit)
