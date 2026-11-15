#!/usr/bin/env python3
"""Twist-leakage / invalid-point attack on an x-only Montgomery ladder.

f(k) = x([k]P) via the standard Montgomery x-only ladder (RFC 7748 style)
takes ANY field element x1 as input -- it never checks that x1 is the
x-coordinate of a point actually on E. The ladder's xDBL/xADD recursion
depends only on the curve parameter A (from y^2 = x^3 + A x^2 + x), never on
the curve's "B" (quadratic-twist-distinguishing) parameter -- so the same
ladder code computes correctly whether x1 lies on E or on E's quadratic
twist E'. If E' has smooth order, feeding the ladder x-coordinates of small-
order twist points lets Pohlig-Hellman recover k modulo each small twist
factor, even when E itself has (near-)prime order.

Everything here is done purely in terms of x-coordinates and the Legendre
symbol -- no square roots, no y-coordinates, no affine group law -- because
that is exactly what both the victim ladder and the attack need.
"""
from __future__ import annotations
import json, math, os, random, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))


def legendre(a: int, p: int) -> int:
    a %= p
    if a == 0:
        return 0
    r = pow(a, (p - 1) // 2, p)
    return 1 if r == 1 else -1


def rhs_E(x: int, A: int, p: int) -> int:
    """RHS of y^2 = x^3 + A x^2 + x (B=1)."""
    return (x * x * x + A * x * x + x) % p


def on_E(x: int, A: int, p: int) -> bool:
    r = rhs_E(x, A, p)
    return r == 0 or legendre(r, p) == 1


def ladder(k: int, x1: int, A: int, p: int) -> int | None:
    """RFC7748-style x-only Montgomery ladder. Returns x([k]P) given only
    x1 = x(P), or None if the result is the point at infinity. Does NOT
    check that x1 is on E -- this is the vulnerable, unvalidated ladder."""
    if k == 0:
        return None
    x1 %= p
    a24 = (A - 2) * pow(4, -1, p) % p
    x2, z2 = 1, 0
    x3, z3 = x1, 1
    swap = 0
    nbits = k.bit_length()
    for t in range(nbits - 1, -1, -1):
        kt = (k >> t) & 1
        swap ^= kt
        if swap:
            x2, x3 = x3, x2
            z2, z3 = z3, z2
        swap = kt
        AA = (x2 + z2) % p
        BBv = (x2 - z2) % p
        AA2 = AA * AA % p
        BB2 = BBv * BBv % p
        Ediff = (AA2 - BB2) % p
        Cc = (x3 + z3) % p
        Dd = (x3 - z3) % p
        DA = Dd * AA % p
        CB = Cc * BBv % p
        x3 = (DA + CB) % p
        x3 = x3 * x3 % p
        z3 = (DA - CB) % p
        z3 = z3 * z3 % p
        z3 = x1 * z3 % p
        x2 = AA2 * BB2 % p
        z2 = Ediff * (AA2 + a24 * Ediff % p) % p
    if swap:
        x2, x3 = x3, x2
        z2, z3 = z3, z2
    if z2 % p == 0:
        return None
    return x2 * pow(z2, -1, p) % p


def find_twist_point_of_order(q: int, A: int, d: int, p: int, t: int, rng: random.Random, max_tries=200):
    """Find an x-coordinate on the twist E' of exact order q | t, using only
    Legendre symbol + the ladder (no affine arithmetic, no sqrt)."""
    for _ in range(max_tries):
        x = rng.randrange(2, p)
        if on_E(x, A, p):
            continue  # on E, not the twist -- skip
        cofac = t // q
        cand = ladder(cofac, x, A, p)
        if cand is None:
            continue  # x had order dividing cofac, not giving order q
        return cand  # x-coordinate of the actual order-q point [cofac]x
    return None


def small_dlog(q: int, x_i: int, A: int, p: int, target):
    """Brute-force r in [0,q) with ladder(r, x_i, A, p) == target."""
    if target is None:
        return 0
    for r in range(1, q):
        if ladder(r, x_i, A, p) == target:
            return r
    raise RuntimeError("small dlog not found (implementation bug)")


def crt_pair(r1, m1, r2, m2):
    g = math.gcd(m1, m2)
    assert g == 1
    inv = pow(m1, -1, m2)
    x = (r1 + m1 * ((r2 - r1) * inv % m2)) % (m1 * m2)
    return x, m1 * m2


def crt_combine(residues_mods):
    r, m = residues_mods[0]
    for ri, mi in residues_mods[1:]:
        r, m = crt_pair(r, m, ri, mi)
    return r, m


def run_attack_on_curve(curve: dict, B: int, k: int, rng: random.Random, verbose=False,
                         max_search_tries: int = 200_000):
    """Full invalid-point attack. curve must have p, A, d, n, twist_order,
    twist_factors (as produced by search_curves.py). Returns a result dict."""
    p, A, d, n, t = curve["p"], curve["A"], curve["d"], curve["n"], curve["twist_order"]
    factors = {int(q): e for q, e in curve["twist_factors"].items()}
    odd_small_factors = sorted(q for q, e in factors.items() if q != 2 and q <= B)

    # genuine base point on E, and the real ladder output the attacker observes
    x0 = rng.randrange(2, p)
    while not on_E(x0, A, p) or rhs_E(x0, A, p) == 0:
        x0 = rng.randrange(2, p)
    real_output = ladder(k, x0, A, p)

    recovered = {}
    used_factors = []
    for q in odd_small_factors:
        x_i = find_twist_point_of_order(q, A, d, p, t, rng)
        if x_i is None:
            continue
        victim_output = ladder(k, x_i, A, p)
        r = small_dlog(q, x_i, A, p, victim_output)
        c = min(r, (q - r) % q)
        recovered[q] = c
        used_factors.append(q)
        if verbose:
            true_c = min(k % q, (-k) % q)
            print(f"    q={q}: recovered canonical residue {c}, true {true_c}, match={c==true_c}")

    if not used_factors:
        return dict(success=False, reason="no usable small twist factors", used_factors=[], M=1,
                    k_true=k, k_recovered=None, exhausted=True, search_tries=0,
                    n_candidates=0, search_space_n_over_M=None)

    M = 1
    for q in used_factors:
        M *= q

    # Each small-order point P_i was built with no y-coordinate information,
    # so there is no canonical "positive" direction correlating the sign
    # ambiguity across different factors: the +-k mod q_i ambiguity is
    # independent per factor (not a single global sign bit). Enumerate all
    # 2^nfac sign assignments.
    nfac = len(used_factors)
    candidates = set()
    for signmask in range(1 << nfac):
        residues_mods = []
        for j in range(nfac):
            q = used_factors[j]
            bit = (signmask >> j) & 1
            r = recovered[q] if bit == 0 else (-recovered[q]) % q
            residues_mods.append((r, q))
        v, _ = crt_combine(residues_mods)
        candidates.add(v)

    # Short search: extend each v mod M by multiples of M up to n, verify
    # against the real exchange output. Capped at max_search_tries total --
    # on a twist-secure curve M is tiny (only the few small factors below B
    # are usable) and n/M is astronomically large, so the search is a
    # negative-result ("infeasible with this M"), not an infinite loop.
    found_k = None
    tries = 0
    exhausted = False
    for v in candidates:
        j = 0
        while v + j * M < n + M:
            if tries >= max_search_tries:
                exhausted = True
                break
            cand_k = v + j * M
            tries += 1
            if cand_k != 0 and ladder(cand_k, x0, A, p) == real_output:
                found_k = cand_k
                break
            j += 1
        if found_k is not None or exhausted:
            break

    success = found_k is not None and found_k == k
    return dict(success=success, used_factors=used_factors, M=M, search_tries=tries,
                exhausted=exhausted, k_true=k, k_recovered=found_k,
                n_candidates=len(candidates), search_space_n_over_M=n // M if M else None)


if __name__ == "__main__":
    with open(os.path.join(HERE, "curves_found.json")) as f:
        curves = json.load(f)
    B = curves["smooth_bound"]
    rng = random.Random(777)

    print("=== Positive control: weak-twist curve ===")
    weak = curves["weak"]
    weak_results = []
    for trial in range(5):
        k = rng.randrange(1, weak["n"])
        t0 = time.time()
        res = run_attack_on_curve(weak, B, k, rng, verbose=(trial == 0))
        res["time_s"] = time.time() - t0
        weak_results.append(res)
        print(f"  trial {trial}: k={k} success={res['success']} "
              f"recovered={res.get('k_recovered')} time={res['time_s']:.2f}s "
              f"used_factors={res['used_factors']}")

    print("=== Negative control: twist-secure curve ===")
    secure = curves["secure"]
    secure_results = []
    for trial in range(5):
        k = rng.randrange(1, secure["n"])
        t0 = time.time()
        res = run_attack_on_curve(secure, B, k, rng, verbose=(trial == 0))
        res["time_s"] = time.time() - t0
        secure_results.append(res)
        print(f"  trial {trial}: k={k} success={res['success']} "
              f"used_factors={res['used_factors']} M={res['M']}")

    out = dict(
        smooth_bound=B,
        weak_curve=weak,
        secure_curve=secure,
        weak_results=weak_results,
        secure_results=secure_results,
    )
    with open(os.path.join(HERE, "attack_results.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("wrote attack_results.json")
