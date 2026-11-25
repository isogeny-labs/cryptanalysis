#!/usr/bin/env python3
"""
membership.py — the sieve inner loop at production scale: how do you decide
whether a *given* x is in the factor base, when the base cannot be stored?

At production (alpha = 0.2, p = 2^256) the base has ~2^51 elements, so no
implementation materialises it; the relation search must decide membership
from the defining data alone.  For the two shapes:

  interval  x in [1, X]                     -> one integer comparison
  a/b       x = a/b, |a|,|b| <= B, gcd = 1  -> rational reconstruction (EEA)

Rational reconstruction is exact when 2*B^2 < p (Wang): the unique solution
appears among the EEA remainders on (p, x).  At alpha = 0.2, B = p^{0.1}, so
2B^2 = p^{0.2} << p and the hypothesis holds with enormous margin.

This is the mirror image of abgen.py: there the base is enumerated (cost per
element), here it is *tested* (cost per candidate).  The MITM inner loop is
the second.

Usage: python3 membership.py
"""
import json
import os
import random
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "raw")
os.makedirs(RAW, exist_ok=True)

SECP_P = 2 ** 256 - 2 ** 32 - 977


# ---------------------------------------------------------------- the test
def rat_in_base(x, p, B, stats=None):
    """Is x = a/b (mod p) with gcd(a,b)=1, |a| <= B, 0 < b <= B, b != 0?

    Runs the EEA on (p, x) and checks every remainder pair (r_i, t_i) against
    the box.  Under 2*B^2 < p the answer is unique and appears as one of them.
    """
    if x == 0:
        return True                       # 0/1, with |0| <= B and 1 <= B
    r0, r1 = p, x
    t0, t1 = 0, 1
    steps = 0
    # |t_i| is non-decreasing in the EEA, so the first step with r_i <= B is
    # the only possible witness: if it fails the box, no later step can pass.
    while r1 > B:
        q = r0 // r1
        r0, r1 = r1, r0 - q * r1
        t0, t1 = t1, t0 - q * t1
        steps += 1
    steps += 1
    if stats is not None:
        stats.append(steps)
    if r1 == 0 or t1 == 0 or abs(t1) > B:
        return False
    return (r1 - t1 * x) % p == 0


# ---------------------------------------------------------------- correctness
def brute_base(p, B):
    """The set, by definition: dedupe is unnecessary under 2B^2 < p."""
    out = {0}
    for b in range(1, B + 1):
        ib = pow(b, p - 2, p)
        for a in range(-B, B + 1):
            if a != 0 and _gcd(abs(a), b) == 1:
                out.add(a * ib % p)
    return out


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def check():
    rows = []
    for p in (1019, 4093, 10007, 40009, 100003):
        if p % 2 == 0:
            continue
        # every B with 2B^2 < p, exhaustively over all x
        for B in (1, 2, 3, 5, 8, 13, 21, 34, 55, 89):
            if 2 * B * B >= p:
                break
            base = brute_base(p, B)
            bad = [x for x in range(p) if rat_in_base(x, p, B) != (x in base)]
            rows.append({"p": p, "B": B, "base_size": len(base),
                         "mismatches": len(bad),
                         "first_bad": bad[:3]})
            if bad:
                print("MISMATCH", p, B, bad[:5])
    ok = all(r["mismatches"] == 0 for r in rows)
    print(f"exhaustive correctness over all x: {len(rows)} (p,B) pairs, "
          f"all exact: {ok}")
    return rows


# ---------------------------------------------------------------- benchmarks
def bench():
    p = SECP_P
    rng = random.Random(20261124)
    out = {}

    # --- the a/b membership test at production height (alpha = 0.2)
    for log2B in (26,):                          # B = p^{0.1} ~ 2^25.6
        B = 2 ** log2B
        assert 2 * B * B < p
        xs = [rng.randrange(1, p) for _ in range(20000)]
        stats = []
        t0 = time.perf_counter()
        hits = sum(1 for x in xs if rat_in_base(x, p, B, stats))
        dt = time.perf_counter() - t0
        stats.sort()
        out[f"ab_B_2^{log2B}"] = {
            "us_per_test_python": round(dt / len(xs) * 1e6, 3),
            "hits": hits,
            "eea_steps_median": stats[len(stats) // 2],
            "eea_steps_p95": stats[int(len(stats) * 0.95)],
            "eea_steps_max": stats[-1],
            "note": "python big-int; each step is one 256/256-bit division",
        }
        # recall: planted elements must be found
        planted = []
        for _ in range(200):
            b = rng.randrange(1, B + 1)
            a = rng.randrange(-B, B + 1)
            if a == 0 or _gcd(abs(a), b) != 1:
                continue
            planted.append(a * pow(b, p - 2, p) % p)
        found = sum(1 for x in planted if rat_in_base(x, p, B))
        out[f"ab_B_2^{log2B}"]["recall_on_planted"] = f"{found}/{len(planted)}"

    # --- the interval predicate, same x's
    xs = [rng.randrange(1, p) for _ in range(20000)]
    X = 2 ** 51
    t0 = time.perf_counter()
    _ = sum(1 for x in xs if x <= X)
    dt = time.perf_counter() - t0
    out["interval"] = {"us_per_test_python": round(dt / len(xs) * 1e6, 3)}

    # --- a materialised hash table of 2^20 elements, for reference only
    tab = set(rng.randrange(1, p) for _ in range(2 ** 20))
    t0 = time.perf_counter()
    _ = sum(1 for x in xs[:5000] if x in tab)
    dt = time.perf_counter() - t0
    out["hash_2^20_materialised"] = {
        "us_per_test_python": round(dt / 5000 * 1e6, 3),
        "note": "reference only: at production the base has 2^51 elements "
                "and cannot be materialised",
    }

    # --- enumeration rate: cost per base element when the base IS materialised
    from abgen import farey_pairs, batch_inv
    Bn = 4000
    t0 = time.perf_counter()
    pairs = list(farey_pairs(Bn))
    t_pairs = time.perf_counter() - t0
    block = 4096
    t0 = time.perf_counter()
    emitted = 0
    for i in range(0, len(pairs), block):
        chunk = pairs[i:i + block]
        vals = []
        for a, b in chunk:
            vals.append(b); vals.append(a)
        iv = batch_inv(vals, p)
        emitted += 4 * len(chunk)
    t_ab = time.perf_counter() - t0
    t0 = time.perf_counter()
    n_int = 0
    for a in range(1, 4 * len(pairs) + 1):
        n_int += 1
    t_int = time.perf_counter() - t0
    out["enumeration_per_element_ns"] = {
        "ab_python": round(t_ab / emitted * 1e9, 1),
        "ab_farey_enumeration_only": round(t_pairs / len(pairs) * 1e9, 1),
        "interval_python": round(t_int / n_int * 1e9, 1),
        "note": "python loop overhead dominates both; the structural cost is "
                "one batched inversion per (a,b) pair vs none for the interval",
    }

    # --- counted cost model (language-independent), 256-bit operands
    #     one 256/256-bit division ~ 4 limb divisions ~ 4*30 = 120 cycles
    #     one comparison ~ 1 cycle (branch)
    med = out["ab_B_2^26"]["eea_steps_median"]
    out["counted_cost_at_3GHz"] = {
        "ab_cycles": med * 120,
        "ab_ns": round(med * 120 / 3.0, 1),
        "interval_cycles": 1,
        "interval_ns": 0.3,
        "ratio": med * 120,
    }
    return out


if __name__ == "__main__":
    res = {"correctness": check(), "bench": bench()}
    with open(os.path.join(RAW, "membership.json"), "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res["bench"], indent=1))
