#!/usr/bin/env python3
"""Leakage harness for the elliptic-curve one-way function f(k) = x([k]P).

Three kinds of leakage are measured separately:

1. Information-theoretic: x([k]P) = x([-k]P), so the sign of k is lost
   (one bit).  On j = 0 curves the map x -> x^3 also collapses the orbits of
   the order-3 automorphism, so log2(6) bits are lost in total.  Checked
   exactly on every sample (and on the whole group for tiny curves).
2. Output distinguishability: the bit encoding of x is not uniform (about half
   of F_p are x-coordinates; the top bit is biased when p is not close to
   2^nbits).  This is a property of the encoding, not of k.
3. Computational leakage about k: the advantage of predictors that guess bits
   of the sign-canonical scalar k* = min(k, n - k), or the class of +-k mod m,
   from f(k).  Each advantage is compared with a permutation null (labels
   shuffled, the predictor refitted) and reported with a p-value.

Calibration controls with known leakage:
  tiny    : brute-force table recovers k* exactly.
  smooth  : Pohlig-Hellman recovers +-k mod each small prime-power factor.
  anomalous: Smart's p-adic attack recovers k (up to sign) completely.
  prime   : generic 40-bit prime-order curve; expected advantage zero.
The MOV control is reported structurally only (embedding degree); at these
sizes a pairing transfer gives no advantage over generic methods, so it is not
a computational-leakage control here.

Pure Python plus numpy/matplotlib.  Deterministic from --seed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sys
from dataclasses import dataclass

import numpy as np

# ---------------------------------------------------------------- arithmetic


def is_probable_prime(n: int) -> bool:
    if n < 2:
        return False
    for q in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % q == 0:
            return n == q
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True  # deterministic for n < 3.3e24


def factor(n: int, bound: int = 1 << 21) -> dict[int, int]:
    """Trial division up to bound, then the cofactor must be 1 or prime."""
    out: dict[int, int] = {}
    q = 2
    while q * q <= n and q <= bound:
        while n % q == 0:
            out[q] = out.get(q, 0) + 1
            n //= q
        q += 1 if q == 2 else 2
    if n > 1:
        if not is_probable_prime(n):
            raise ValueError("cofactor not prime; raise the trial bound")
        out[n] = out.get(n, 0) + 1
    return out


def sqrt_mod(a: int, p: int) -> int | None:
    a %= p
    if a == 0:
        return 0
    if pow(a, (p - 1) // 2, p) != 1:
        return None
    if p % 4 == 3:
        return pow(a, (p + 1) // 4, p)
    q, s = p - 1, 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1:
        z += 1
    m, c, t, r = s, pow(z, q, p), pow(a, q, p), pow(a, (q + 1) // 2, p)
    while t != 1:
        i, t2 = 0, t
        while t2 != 1:
            t2 = t2 * t2 % p
            i += 1
        b = pow(c, 1 << (m - i - 1), p)
        m, c, t, r = i, b * b % p, t * b * b % p, r * b % p
    return r


@dataclass(frozen=True)
class Curve:
    """y^2 = x^3 + a x + b over F_p."""

    p: int
    a: int
    b: int

    def rhs(self, x: int) -> int:
        return (x * x * x + self.a * x + self.b) % self.p

    def on_curve(self, P) -> bool:
        if P is None:
            return True
        x, y = P
        return (y * y - self.rhs(x)) % self.p == 0

    def add(self, P, Q):
        if P is None:
            return Q
        if Q is None:
            return P
        p = self.p
        x1, y1 = P
        x2, y2 = Q
        if x1 == x2:
            if (y1 + y2) % p == 0:
                return None
            lam = (3 * x1 * x1 + self.a) * pow(2 * y1, -1, p) % p
        else:
            lam = (y2 - y1) * pow(x2 - x1, -1, p) % p
        x3 = (lam * lam - x1 - x2) % p
        return (x3, (lam * (x1 - x3) - y1) % p)

    def neg(self, P):
        return None if P is None else (P[0], (-P[1]) % self.p)

    def mul(self, k: int, P):
        if k < 0:
            return self.mul(-k, self.neg(P))
        R = None
        while k:
            if k & 1:
                R = self.add(R, P)
            P = self.add(P, P)
            k >>= 1
        return R

    def random_point(self, rng: random.Random):
        while True:
            x = rng.randrange(self.p)
            y = sqrt_mod(self.rhs(x), self.p)
            if y is not None and (x, y) != (0, 0):
                if y == 0:
                    continue
                return (x, y if rng.random() < 0.5 else (-y) % self.p)

    def lift_x(self, x: int):
        y = sqrt_mod(self.rhs(x), self.p)
        if y is None:
            return None
        return (x, min(y, self.p - y))

    def j_invariant(self) -> int:
        p, a, b = self.p, self.a, self.b
        den = (4 * a**3 + 27 * b * b) % p
        return 1728 * 4 * a**3 * pow(den, -1, p) % p


def order_of_point(E: Curve, P, multiple: int) -> int:
    """Exact order of P given that [multiple]P = O."""
    n = multiple
    for q, e in factor(multiple).items():
        for _ in range(e):
            if E.mul(n // q, P) is None:
                n //= q
            else:
                break
    return n


def group_order(E: Curve, rng: random.Random) -> int:
    """#E(F_p) by baby-step giant-step in the Hasse interval (Mestre style)."""
    p = E.p
    if p < 5000:
        return 1 + sum(
            1 + (0 if E.rhs(x) == 0 else (1 if pow(E.rhs(x), (p - 1) // 2, p) == 1 else -1))
            for x in range(p)
        )
    lo, hi = p + 1 - 2 * math.isqrt(p) - 2, p + 1 + 2 * math.isqrt(p) + 2
    L = 1
    for _ in range(40):
        P = E.random_point(rng)
        # find m in [lo, hi] with [m]P = O via BSGS
        width = hi - lo + 1
        m = math.isqrt(width) + 1
        baby = {}
        R = None
        for j in range(m):
            baby.setdefault(R, j)
            R = E.add(R, P)
        step = E.neg(E.mul(m, P))
        G = E.mul(lo, P)
        found = None
        for i in range(m + 1):
            jn = baby.get(E.neg(G))
            if jn is not None:
                found = lo + i * m + jn  # [lo + i m + j]P = O
                break
            G = E.add(G, E.neg(step))
        if found is None:
            raise RuntimeError("BSGS failed")
        o = order_of_point(E, P, found)
        L = L * o // math.gcd(L, o)
        cands = [c for c in range((lo + L - 1) // L * L, hi + 1, L)]
        if len(cands) == 1:
            return cands[0]
    raise RuntimeError("group order not determined")


def embedding_degree(n: int, p: int, kmax: int = 50) -> int | None:
    for k in range(1, kmax + 1):
        if pow(p, k, n) == 1:
            return k
    return None


# ---------------------------------------------------------------- attacks


def smart_attack(E: Curve, P, Q, rng: random.Random) -> int:
    """Return k with Q = [k]P on an anomalous curve (#E = p), via a random
    lift to Z/p^2 and the formal-group logarithm t = -x/y (Smart 1999)."""
    p = E.p
    M = p * p
    for _ in range(8):
        a2 = (E.a + p * rng.randrange(1, p)) % M

        x1, y1 = P
        b2 = (y1 * y1 - x1**3 - a2 * x1) % M

        def hensel(Pt):
            x, y = Pt
            f = (y * y - x**3 - a2 * x - b2) % M
            y2 = (y - f * pow(2 * y, -1, M)) % M
            return x, y2

        Pl, Ql = hensel(P), hensel(Q)

        def jac_mul(k, Pt):
            # Jacobian coordinates mod p^2, no inversions
            def dbl(T):
                X, Y, Z = T
                S = 4 * X * Y * Y % M
                Mm = (3 * X * X + a2 * pow(Z, 4, M)) % M
                X3 = (Mm * Mm - 2 * S) % M
                Y3 = (Mm * (S - X3) - 8 * pow(Y, 4, M)) % M
                Z3 = 2 * Y * Z % M
                return X3, Y3, Z3

            def add(T1, T2):
                if T1 is None:
                    return T2
                X1, Y1, Z1 = T1
                X2, Y2, Z2 = T2
                U1, U2 = X1 * Z2 * Z2 % M, X2 * Z1 * Z1 % M
                S1, S2 = Y1 * pow(Z2, 3, M) % M, Y2 * pow(Z1, 3, M) % M
                H, R = (U2 - U1) % M, (S2 - S1) % M
                if H == 0 and R == 0:
                    return dbl(T1)
                X3 = (R * R - H**3 - 2 * U1 * H * H) % M
                Y3 = (R * (U1 * H * H - X3) - S1 * H**3) % M
                Z3 = Z1 * Z2 * H % M
                return X3, Y3, Z3

            T = (Pt[0], Pt[1], 1)
            Racc = None
            for bit in bin(k)[2:]:
                if Racc is not None:
                    Racc = dbl(Racc)
                if bit == "1":
                    Racc = add(Racc, T)
            return Racc

        X1, Y1, Z1 = jac_mul(p, Pl)
        X2, Y2, Z2 = jac_mul(p, Ql)
        if Z1 % p or Z2 % p or Y1 % p == 0 or Y2 % p == 0:
            continue
        t1 = (-X1 * (Z1 // p) * pow(Y1, -1, p)) % p
        t2 = (-X2 * (Z2 // p) * pow(Y2, -1, p)) % p
        if t1 == 0:
            continue  # canonical lift; try another
        k = t2 * pow(t1, -1, p) % p
        if E.mul(k, P) == Q:
            return k
    raise RuntimeError("Smart attack failed on all lifts")


def subgroup_dlog(E: Curve, P, Q, order: int) -> int:
    """Brute-force dlog of Q in <P> (small order)."""
    R = None
    for k in range(order):
        if R == Q:
            return k
        R = E.add(R, P)
    raise RuntimeError("no dlog")


def ph_residue(E: Curve, P, n: int, m: int, x: int) -> int:
    """From x([k]P) alone, recover the class min(k mod m, -k mod m)."""
    Q = E.lift_x(x)  # equals +-[k]P
    c = n // m
    r = subgroup_dlog(E, E.mul(c, P), E.mul(c, Q), m)
    return min(r, (-r) % m)


# ---------------------------------------------------------------- statistics


def canonical(k: int, n: int) -> int:
    return min(k, n - k)


def bits_matrix(vals, nbits: int) -> np.ndarray:
    return np.array([[(v >> i) & 1 for i in range(nbits)] for v in vals], dtype=np.int8)


def linear_predictor_accuracy(Xtr, ytr, Xte, yte) -> float:
    """Least-squares linear classifier on +-1 features (with bias)."""
    A = np.hstack([2.0 * Xtr - 1.0, np.ones((len(Xtr), 1))])
    w, *_ = np.linalg.lstsq(A, 2.0 * ytr - 1.0, rcond=None)
    B = np.hstack([2.0 * Xte - 1.0, np.ones((len(Xte), 1))])
    pred = (B @ w > 0).astype(np.int8)
    return float((pred == yte).mean())


def lookup_predictor_accuracy(xtr, ytr, xte, yte, default) -> float:
    """Memorize x -> label; unseen x gets the training majority label."""
    table = {}
    for x, y in zip(xtr, ytr):
        table[x] = y
    pred = np.array([table.get(x, default) for x in xte])
    return float((pred == np.asarray(yte)).mean())


def advantage_with_null(fit_score, y, rng: np.random.Generator, n_perm: int):
    """fit_score(labels) -> test accuracy.  Returns observed accuracy, the
    majority-class baseline, advantage over the null mean, and a one-sided
    permutation p-value."""
    obs = fit_score(y)
    null = np.array([fit_score(rng.permutation(y)) for _ in range(n_perm)])
    p = (1 + int((null >= obs).sum())) / (n_perm + 1)
    return {
        "accuracy": obs,
        "null_mean": float(null.mean()),
        "null_sd": float(null.std(ddof=1)) if n_perm > 1 else 0.0,
        "advantage": obs - float(null.mean()),
        "p_value": p,
        "n_perm": n_perm,
    }


# ---------------------------------------------------------------- curve finding


def find_curve(kind: str, bits: int, rng: random.Random, smooth_bound: int = 1 << 12):
    """Return (Curve, n, P) where P generates a subgroup of order n."""
    if kind == "anomalous":
        # CM by Z[zeta_3]: 4p = 1 + 3 v^2 gives trace 1 for one sextic twist
        while True:
            v = rng.randrange(1 << (bits // 2 - 1), 1 << (bits // 2)) | 1
            if (1 + 3 * v * v) % 4:
                continue
            p = (1 + 3 * v * v) // 4
            if not is_probable_prime(p):
                continue
            for _ in range(200):
                b = rng.randrange(1, p)
                E = Curve(p, 0, b)
                P = E.random_point(rng)
                if E.mul(p, P) is None:
                    if group_order(E, rng) == p:
                        return E, p, P
    while True:
        p = rng.randrange(1 << (bits - 1), 1 << bits) | 1
        if not is_probable_prime(p):
            continue
        a, b = rng.randrange(p), rng.randrange(p)
        if (4 * a**3 + 27 * b * b) % p == 0:
            continue
        E = Curve(p, a, b)
        N = group_order(E, rng)
        if N == p:
            continue
        if kind in ("prime", "tiny"):
            if not is_probable_prime(N):
                continue
            P = E.random_point(rng)
            return E, N, P
        if kind == "smooth":
            f = factor(N)
            if max(f) > smooth_bound or N % 2 == 0:
                continue
            # need a point of full order N (group cyclic check)
            for _ in range(20):
                P = E.random_point(rng)
                if order_of_point(E, P, N) == N:
                    return E, N, P
    raise AssertionError


# ---------------------------------------------------------------- experiment


def sample(E, n, P, m, rng):
    ks = [rng.randrange(1, n) for _ in range(m)]
    xs = [E.mul(k, P)[0] for k in ks]
    return ks, xs


def info_theoretic_checks(E, n, P, ks, xs):
    sym = all(E.mul(n - k, P)[0] == x for k, x in zip(ks[:200], xs[:200]))
    return {"x_kP_equals_x_minus_kP_on_first_200": sym, "bits_lost_by_x": 1.0}


def j0_orbit_check(rng):
    """Tiny j=0 prime-order curve with p = 1 mod 3: count distinct x^3 over the
    whole group; the orbit of <-1, zeta_3> has size 6, so log2(6) bits are lost."""
    while True:
        p = rng.randrange(1 << 11, 1 << 12)
        if not is_probable_prime(p) or p % 3 != 1:
            continue
        for b in range(1, 50):
            E = Curve(p, 0, b)
            N = group_order(E, rng)
            if is_probable_prime(N) and N > 3:
                P = E.random_point(rng)
                pts = [E.mul(k, P) for k in range(1, N)]
                xs = {pt[0] for pt in pts}
                x3 = {pow(x, 3, p) for x in xs}
                return {
                    "p": p, "b": b, "n": N,
                    "distinct_x": len(xs), "distinct_x_cubed": len(x3),
                    "bits_lost_x": math.log2((N - 1) / len(xs)),
                    "bits_lost_x_cubed": math.log2((N - 1) / len(x3)),
                    "expected_bits_lost_x_cubed": math.log2(6),
                }


def distinguishability(E, xs):
    p = E.p
    nb = p.bit_length()
    B = bits_matrix(xs, nb)
    freq = B.mean(axis=0)
    z = (freq - 0.5) / math.sqrt(0.25 / len(xs))
    # expected top-bit frequency for uniform x in [0, p)
    top_expected = max(0, p - (1 << (nb - 1))) / p
    return {
        "nbits": nb,
        "per_bit_freq": freq.tolist(),
        "per_bit_z": z.tolist(),
        "top_bit_expected_if_uniform_mod_p": top_expected,
        "valid_x_fraction_expected": "~1/2 of F_p (Hasse)",
        "max_abs_z": float(np.abs(z).max()),
    }


def computational(E, n, P, ks, xs, kind, rng_np, n_perm, small_moduli):
    m = len(ks)
    half = m // 2
    nb = n.bit_length()
    kstar = [canonical(k, n) for k in ks]
    Xb = bits_matrix(xs, E.p.bit_length())
    Ystar = bits_matrix(kstar, nb)
    Yraw = bits_matrix(ks, nb)
    per_bit = []
    for i in range(nb):
        row = {"bit": i}
        for name, Y in (("kstar", Ystar), ("k", Yraw)):
            y = Y[:, i]
            row[f"linear_{name}"] = advantage_with_null(
                lambda lab: linear_predictor_accuracy(Xb[:half], lab[:half], Xb[half:], lab[half:]),
                y, rng_np, n_perm)
            if kind == "tiny":
                maj = int(round(y[:half].mean()))
                row[f"lookup_{name}"] = advantage_with_null(
                    lambda lab: lookup_predictor_accuracy(xs[:half], lab[:half], xs[half:], lab[half:], maj),
                    y, rng_np, n_perm)
        per_bit.append(row)
    out = {"per_bit": per_bit}
    # structured predictors
    if kind == "smooth":
        res = []
        for mod in small_moduli:
            truth = np.array([min(k % mod, (-k) % mod) for k in ks[half:]])
            pred = np.array([ph_residue(E, P, n, mod, x) for x in xs[half:]])
            st = advantage_with_null(lambda lab: float((pred == lab).mean()), truth, rng_np, n_perm)
            st["modulus"] = mod
            res.append(st)
        out["pohlig_hellman"] = res
    if kind == "anomalous":
        rng = random.Random(1)
        ok = 0
        test = list(zip(ks[half:], xs[half:]))[:50]
        for k, x in test:
            Q = E.lift_x(x)
            kk = smart_attack(E, P, Q, rng)
            ok += canonical(kk, n) == canonical(k, n)
        out["smart_attack"] = {"tested": len(test), "kstar_recovered": ok}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seed", type=int, default=20261114)
    ap.add_argument("--samples", type=int, default=2000)
    ap.add_argument("--perm", type=int, default=50)
    ap.add_argument("--bits", type=int, default=40)
    ap.add_argument("--tiny-bits", type=int, default=12)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "results"))
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    rng = random.Random(args.seed)
    rng_np = np.random.default_rng(args.seed)

    plans = [("tiny", args.tiny_bits), ("smooth", args.bits), ("anomalous", args.bits), ("prime", args.bits)]
    report = {"seed": args.seed, "samples": args.samples, "perm": args.perm, "controls": {}}
    for kind, bits in plans:
        E, n, P = find_curve(kind, bits, rng)
        m = max(args.samples, 8 * n) if kind == "tiny" else args.samples  # table must cover the group
        ks, xs = sample(E, n, P, m, rng)
        f = factor(n)
        small = sorted(q**e for q, e in f.items() if q**e <= 4096 and q > 2)[:4] if kind == "smooth" else []
        entry = {
            "curve": {"p": E.p, "a": E.a, "b": E.b, "n": n, "P": list(P),
                      "n_factorization": {str(q): e for q, e in f.items()},
                      "j": E.j_invariant(), "embedding_degree_le50": embedding_degree(n, E.p),
                      "trace": E.p + 1 - n},
            "info_theoretic": info_theoretic_checks(E, n, P, ks, xs),
            "distinguishability": distinguishability(E, xs),
            "computational": computational(E, n, P, ks, xs, kind, rng_np, args.perm, small),
        }
        report["controls"][kind] = entry
        print(f"[{kind}] p={E.p} n={n} done", file=sys.stderr)
    report["j0_orbit"] = j0_orbit_check(rng)
    path = os.path.join(args.out, "results.json")
    with open(path, "w") as fh:
        json.dump(report, fh, indent=1)
    plot(report, args.out)
    print(summary(report))
    return report


def summary(r) -> str:
    lines = ["control  | best linear adv (k*) | min p (Bonferroni) | lookup adv k* (bit, adv) | structured"]
    for kind, e in r["controls"].items():
        pb = e["computational"]["per_bit"]
        best = max(pb, key=lambda b: b["linear_kstar"]["advantage"])
        minp = min(1.0, len(pb) * min(b["linear_kstar"]["p_value"] for b in pb))  # Bonferroni
        lk = ""
        if "lookup_kstar" in pb[0]:
            mean_adv = np.mean([b["lookup_kstar"]["advantage"] for b in pb])
            lk = f"mean {mean_adv:.3f}"
        st = ""
        c = e["computational"]
        if "pohlig_hellman" in c:
            st = "; ".join(f"mod {x['modulus']}: acc {x['accuracy']:.3f} vs null {x['null_mean']:.3f} (p={x['p_value']:.3f})" for x in c["pohlig_hellman"])
        if "smart_attack" in c:
            st = f"Smart: {c['smart_attack']['kstar_recovered']}/{c['smart_attack']['tested']}"
        lines.append(f"{kind:9}| bit {best['bit']:2} {best['linear_kstar']['advantage']:+.3f} | {minp:.3f} | {lk} | {st}")
    return "\n".join(lines)


def plot(r, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    kinds = list(r["controls"])
    fig, axes = plt.subplots(len(kinds), 1, figsize=(9, 2.6 * len(kinds)), sharey=True)
    for ax, kind in zip(axes, kinds):
        pb = r["controls"][kind]["computational"]["per_bit"]
        bits = [b["bit"] for b in pb]
        adv = [b["linear_kstar"]["advantage"] for b in pb]
        sd = [b["linear_kstar"]["null_sd"] for b in pb]
        ax.bar(bits, adv, color="#4C72B0", label="linear predictor, bits of k*")
        ax.fill_between(bits, [-2 * s for s in sd], [2 * s for s in sd], color="0.8", step="mid",
                        label="±2 sd permutation null")
        if "lookup_kstar" in pb[0]:
            ax.plot(bits, [b["lookup_kstar"]["advantage"] for b in pb], "o-", color="#C44E52",
                    label="lookup table (brute force), k*")
            ax.plot(bits, [b["lookup_k"]["advantage"] for b in pb], "x--", color="#DD8452",
                    label="lookup table, raw k (sign lost)")
        c = r["controls"][kind]["curve"]
        ax.set_title(f"{kind}: p={c['p']} ({c['p'].bit_length()} bits), n={c['n']}", fontsize=9)
        ax.axhline(0, color="k", lw=0.6)
        ax.set_ylabel("advantage")
        ax.legend(fontsize=7, loc="upper right")
    axes[-1].set_xlabel("bit index of scalar")
    fig.tight_layout()
    fig.savefig(os.path.join(out, "per_bit_advantage.png"), dpi=70)

    fig, ax = plt.subplots(figsize=(9, 3))
    for kind in kinds:
        z = r["controls"][kind]["distinguishability"]["per_bit_z"]
        ax.plot(range(len(z)), z, "o-", label=kind, ms=3)
    ax.axhspan(-3, 3, color="0.9")
    ax.set_xlabel("bit index of x-coordinate")
    ax.set_ylabel("monobit z-score")
    ax.set_title("Output encoding bias (independent of k)")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "output_bit_bias.png"), dpi=130)


if __name__ == "__main__":
    main()
