#!/usr/bin/env python3
"""Census: how often is the quadratic twist order smooth, over the 60
40-bit curves in results/followup_population.json (short Weierstrass
y^2=x^3+ax+b, smooth/anomalous/prime populations) and a fresh sample of
random 40-bit curves? t = 2p+2-n is the standard quadratic-twist-order
identity; it holds for ANY Weierstrass model, so this census does not need
Montgomery form -- only the attack demo (attack.py) does."""
from __future__ import annotations
import json, os, random, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from ec_leakage import is_probable_prime

import cypari2
pari = cypari2.Pari()


def pari_factor(n: int) -> dict:
    if n <= 1:
        return {}
    f = pari.factor(n)
    return {int(f[i, 0]): int(f[i, 1]) for i in range(f.nrows())}


def smooth_bound_reached(fac: dict, B: int) -> bool:
    return all(q <= B for q in fac)


def classify_twist(p: int, a: int, b: int, n: int, bounds):
    t = 2 * p + 2 - n
    fac = pari_factor(t)
    largest = max(fac) if fac else 1
    row = dict(p=p, n=n, twist_order=t, twist_largest_factor=largest,
               twist_factorization={str(k): v for k, v in fac.items()})
    for B in bounds:
        row[f"smooth_le_{B}"] = smooth_bound_reached(fac, B)
    return row


def random_curve(bits: int, rng: random.Random):
    """A fresh random 40-bit curve (not selected for any twist property),
    for an independent baseline sample alongside the 60-curve population."""
    lo, hi = 1 << (bits - 1), 1 << bits
    while True:
        p = rng.randrange(lo, hi) | 1
        if is_probable_prime(p):
            break
    while True:
        a = rng.randrange(1, p)
        b = rng.randrange(1, p)
        if (4 * a**3 + 27 * b * b) % p != 0:
            break
    E = pari.ellinit([a, b], p)
    n = int(pari.ellcard(E))
    return p, a, b, n


if __name__ == "__main__":
    pop_path = os.path.join(os.path.dirname(os.path.dirname(HERE)), "results", "followup_population.json")
    with open(pop_path) as f:
        pop = json.load(f)
    bounds = [1 << 12, 1 << 16, 1 << 20]

    t0 = time.time()
    rows = []
    for c in pop["curves"]:
        row = classify_twist(c["p"], c["a"], c["b"], c["n"], bounds)
        row["kind"] = c["kind"]
        row["idx"] = c["idx"]
        rows.append(row)
    print(f"classified {len(rows)} population curves in {time.time()-t0:.1f}s")

    # fresh independent sample of random 40-bit curves (not drawn from the
    # population's smooth/anomalous/prime selection procedure)
    rng = random.Random(20261115)
    fresh_rows = []
    t0 = time.time()
    for i in range(60):
        p, a, b, n = random_curve(40, rng)
        row = classify_twist(p, a, b, n, bounds)
        row["kind"] = "fresh_random"
        row["idx"] = i
        fresh_rows.append(row)
    print(f"classified {len(fresh_rows)} fresh random curves in {time.time()-t0:.1f}s")

    def tabulate(rows, label):
        print(f"\n=== {label} (n={len(rows)}) ===")
        for B in bounds:
            cnt = sum(1 for r in rows if r[f"smooth_le_{B}"])
            print(f"  twist order fully {B}-smooth: {cnt}/{len(rows)} ({100*cnt/len(rows):.1f}%)")
        by_kind = {}
        for r in rows:
            by_kind.setdefault(r["kind"], []).append(r)
        if len(by_kind) > 1:
            for kind, krows in by_kind.items():
                print(f"  -- kind={kind} (n={len(krows)}):")
                for B in bounds:
                    cnt = sum(1 for r in krows if r[f"smooth_le_{B}"])
                    print(f"      {B}-smooth: {cnt}/{len(krows)} ({100*cnt/len(krows):.1f}%)")

    tabulate(rows, "followup_population.json (60 curves)")
    tabulate(fresh_rows, "fresh random 40-bit curves (60 curves)")

    out = dict(bounds=bounds, population_rows=rows, fresh_rows=fresh_rows)
    with open(os.path.join(HERE, "census_results.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote census_results.json")
