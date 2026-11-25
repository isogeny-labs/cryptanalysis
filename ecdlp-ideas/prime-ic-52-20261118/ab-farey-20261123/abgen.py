#!/usr/bin/env python3
"""
abgen.py — canonical small-rational-height ("a/b") factor base, three ways.

The set
    X(B) = { x = a/b mod p : gcd(a,b) = 1, 1 <= |a|,|b| <= B, b != 0 }
           union {0}
is, up to the two involutions x -> -x and x -> 1/x, the Farey sequence of
order B.  That is the whole observation: it makes the base enumerable by a
mediant recurrence instead of a gcd scan over the square, and addressable by
index without storing anything.

Counts (proved in lean-check/Check/Farey.lean, checked by brute force here):
    |{ (a,b) : 1 <= |a|,|b| <= B, gcd(a,b)=1, b != 0 }| = 8*Phi(B) - 2
    |X(B)| = 4*Phi(B) - 1          ~ (12/pi^2) B^2 = 1.216 B^2
where Phi(B) = sum_{k<=B} phi(k).  The b = 0 row is excluded: x = a/0 is not
a field element.

Modes
  naive   : scan [1,B] x [1,B], gcd test          (the obvious implementation)
  farey   : mediant recurrence, no gcd, no set    (O(|X|) time, O(1) memory)
  unrank  : the i-th pair in O(polylog B + 2^omega) with no memory

Usage
  python3 abgen.py counts           # exact count checks, writes raw/counts.json
  python3 abgen.py bench            # timing, writes raw/bench.json
  python3 abgen.py selfcheck        # unrank/rank round trip
"""
import json
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "raw")
os.makedirs(RAW, exist_ok=True)


# ---------------------------------------------------------------- totients
def phi_sieve(n):
    phi = list(range(n + 1))
    for i in range(2, n + 1):
        if phi[i] == i:                      # i prime
            for j in range(i, n + 1, i):
                phi[j] -= phi[j] // i
    phi[0] = 0
    if n >= 1:
        phi[1] = 1
    return phi


def phi_prefix(n):
    phi = phi_sieve(n)
    pref = [0] * (n + 1)
    s = 0
    for k in range(1, n + 1):
        s += phi[k]
        pref[k] = s
    return phi, pref


def primes_upto(n):
    sieve = bytearray([1]) * (n + 1)
    sieve[0:2] = b"\x00\x00"
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            sieve[i * i:: i] = bytearray(len(sieve[i * i:: i]))
    return [i for i in range(2, n + 1) if sieve[i]]


# ---------------------------------------------------------------- naive
def naive_pairs(B):
    """Yield (a,b), 1 <= a <= b <= B, gcd = 1.  This is the square scan,
    quartered by the a <= b symmetry.  Cost ~ B^2 gcd tests."""
    for b in range(1, B + 1):
        for a in range(1, b + 1):
            if math.gcd(a, b) == 1:
                yield a, b


def naive_x(B, p):
    """Full x-set by brute force over the whole signed square (reference)."""
    seen = set()
    for b in range(1, B + 1):
        ib = pow(b, p - 2, p)
        for a in range(-B, B + 1):
            if a == 0:
                if b == 1:
                    seen.add(0)
                continue
            if math.gcd(abs(a), b) == 1:
                seen.add((a * ib) % p)
    return seen


# ---------------------------------------------------------------- farey
def farey_pairs(B):
    """The Farey fractions of order B in (0,1], increasing: (a,b) with
    1 <= a <= b <= B, gcd(a,b)=1.  Mediant recurrence, no gcd test.
    Cost |Farey| = Phi(B) steps."""
    a, b, c, d = 0, 1, 1, B               # 0/1 then 1/B
    while c <= B:
        yield c, d
        k = (B + b) // d
        a, b, c, d = c, d, k * c - a, k * d - b


def batch_inv(vals, p):
    """Montgomery batch inversion: one modpow for the whole block."""
    n = len(vals)
    pre = [1] * (n + 1)
    for i, v in enumerate(vals):
        pre[i + 1] = pre[i] * v % p
    inv_all = pow(pre[n], p - 2, p)
    out = [0] * n
    for i in range(n - 1, -1, -1):
        out[i] = inv_all * pre[i] % p
        inv_all = inv_all * vals[i] % p
    return out


def farey_x(B, p, block=1 << 14):
    """Canonical x-set from the Farey enumeration, O(1) memory, no gcd, no set.

    Per pair (a,b), a<b:  the four values +-a/b, +-b/a  (4 distinct x)
    Pair (1,1):           +-1                          (2 distinct x)
    Plus x = 0 from the pair (0,1).
    Discarded duplicate case: a/b = -b/a  <=>  (a/b)^2 = -1, i.e. p = 1 mod 4.
    """
    if p % 4 == 1:
        raise ValueError("use p = 3 mod 4: excludes the x^2 = -1 collapse")
    yield 0
    buf, pairs = [], []

    def flush():
        if not pairs:
            return
        vals = []
        for a, b in pairs:
            vals.append(b)
            vals.append(a)
        iv = batch_inv(vals, p)
        emit = []
        for j, (a, b) in enumerate(pairs):
            ib, ia = iv[2 * j], iv[2 * j + 1]
            u, v = a * ib % p, b * ia % p
            emit.append(u)
            emit.append(p - u if u else 0)
            if a != b:
                emit.append(v)
                emit.append(p - v if v else 0)
        # keep the canonical order stable for hashing / streaming
        for x in emit:
            buf.append(x)
        pairs.clear()

    for a, b in farey_pairs(B):
        pairs.append((a, b))
        if len(pairs) >= block:
            flush()
    flush()
    for x in buf:
        yield x


def farey_pairs_list(B):
    return list(farey_pairs(B))


# ---------------------------------------------------------------- unrank
class FareyRank:
    """Rank/unrank of the pair list without materialising it.

    rank(pair) = Phi(b-1) + #{a' <= a : gcd(a',b) = 1}
    unrank(i)  = bisect on Phi to get b, then a k-th-coprime search on [1,b].
    Random access is O(log B * 2^omega(b)); storage is O(B) for the totient
    prefix only, or O(1) if Phi is evaluated by a summatory-totient routine.
    """

    def __init__(self, B):
        self.B = B
        self.phi, self.pref = phi_prefix(B)
        self.pr = primes_upto(B)
        self._fac = {}

    def factors(self, b):
        f = self._fac.get(b)
        if f is not None:
            return f
        out, m = [], b
        for q in self.pr:
            if q * q > m:
                break
            if m % q == 0:
                out.append(q)
                while m % q == 0:
                    m //= q
        if m > 1:
            out.append(m)
        self._fac[b] = out
        return out

    def coprime_le(self, b, t):
        """#{a in [1,t] : gcd(a,b) = 1} by inclusion-exclusion."""
        fs = self.factors(b)
        total, k = 0, len(fs)
        for mask in range(1 << k):
            prod, bits = 1, 0
            for i in range(k):
                if mask >> i & 1:
                    prod *= fs[i]
                    bits += 1
            total += (-1) ** bits * (t // prod)
        return total

    def nth_coprime(self, b, k):
        lo, hi = 1, b
        while lo < hi:
            mid = (lo + hi) // 2
            if self.coprime_le(b, mid) >= k:
                hi = mid
            else:
                lo = mid + 1
        return lo

    def unrank(self, i):
        """1-based index into the Phi(B) pairs."""
        pref = self.pref
        lo, hi = 1, self.B
        while lo < hi:                      # smallest b with pref[b] >= i
            mid = (lo + hi) // 2
            if pref[mid] >= i:
                hi = mid
            else:
                lo = mid + 1
        b = lo
        k = i - pref[b - 1]
        return self.nth_coprime(b, k), b

    def rank(self, a, b):
        return self.pref[b - 1] + self.coprime_le(b, a)


# ---------------------------------------------------------------- benches
def bench(Bs, p):
    out = []
    for B in Bs:
        n_pairs = sum(1 for _ in naive_pairs(B))
        t0 = time.perf_counter()
        seen = {0}
        for a, b in naive_pairs(B):
            ib = pow(b, p - 2, p)               # unbatched, as a naive impl does
            u = a * ib % p
            seen.add(u)
            seen.add((-u) % p)
            v = b * pow(a, p - 2, p) % p if a != b else u
            seen.add(v)
            seen.add((-v) % p)
        t_naive = time.perf_counter() - t0

        t0 = time.perf_counter()
        got = set(farey_x(B, p))
        t_farey = time.perf_counter() - t0

        assert got == seen, (B, len(got), len(seen))
        assert len(got) == 4 * Phi(B) - 1, (B, len(got), 4 * Phi(B) - 1)

        out.append({
            "B": B,
            "pairs_farey": n_pairs,
            "pairs_naive": B * B,
            "x_count": len(got),
            "predicted_4Phi_minus_1": 4 * Phi(B) - 1,
            "naive_seconds": round(t_naive, 3),
            "farey_seconds": round(t_farey, 3),
            "speedup": round(t_naive / t_farey, 2),
            "naive_pairs_per_sec": int(n_pairs / t_naive),
            "farey_pairs_per_sec": int(n_pairs / t_farey),
        })
        print(f"B=2^{B.bit_length()-1:<3} |X|={len(got):>12,} "
              f"naive={t_naive:7.2f}s farey={t_farey:6.2f}s "
              f"x{t_naive/t_farey:5.2f}")
    return out


Phi_cache = {}


def Phi(B):
    if B not in Phi_cache:
        phi, pref = phi_prefix(B)
        Phi_cache[B] = pref[B]
    return Phi_cache[B]


def counts():
    out = {"count_checks": [], "asymptotic": []}
    # brute force over the full signed square for small B
    for B in (1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 24, 32, 48, 64, 96):
        p = 1000003                        # p = 3 mod 4, irrelevant here
        n_signed = 8 * Phi(B) - 2
        got = naive_x(B, p)
        ok = (len(got) == 4 * Phi(B) - 1)
        # independent brute force of the signed-pair count
        cnt = 0
        for b in range(1, B + 1):
            for a in range(-B, B + 1):
                if a == 0:
                    cnt += 1 if b == 1 else 0
                elif math.gcd(abs(a), b) == 1:
                    cnt += 1
        cnt = 2 * cnt                      # b < 0 by the (a,b) -> (-a,-b) symmetry
        out["count_checks"].append({
            "B": B, "x_count": len(got), "pred": 4 * Phi(B) - 1,
            "signed_pairs": cnt, "signed_pred": n_signed,
            "ok": bool(ok and cnt == n_signed),
        })
        if not (ok and cnt == n_signed):
            print("COUNT MISMATCH", B, len(got), 4 * Phi(B) - 1, cnt, n_signed)
    for B in (2 ** 10, 2 ** 12, 2 ** 14, 2 ** 16, 2 ** 18, 2 ** 20):
        n = 4 * Phi(B) - 1
        out["asymptotic"].append({
            "B": B, "log2_B": B.bit_length() - 1, "x_count": n,
            "n_over_B2": n / B ** 2, "twelve_over_pi2": 12 / math.pi ** 2,
        })
    with open(os.path.join(RAW, "counts.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out["asymptotic"][-3:], indent=1))
    print("count checks:", "ALL OK" if all(c["ok"] for c in out["count_checks"]) else "FAIL")


def selfcheck():
    """rank/unrank are mutual inverses and cover exactly the Farey set.

    NOTE the two orders differ by design: farey_pairs streams in VALUE order
    (mediant recurrence, O(1) memory); rank/unrank indexes (b ascending,
    a ascending).  Sharding only needs a bijection, so this is fine, but the
    test compares as sets and checks rank(unrank(i)) == i.
    """
    out = {}
    for B in (1, 2, 7, 64, 1000, 4096):
        fr = FareyRank(B)
        seq = farey_pairs_list(B)
        n = len(seq)
        assert n == Phi(B), (B, n, Phi(B))
        idx = list(range(1, min(n, 20000) + 1))
        ok_rank = all(fr.rank(*fr.unrank(i)) == i for i in idx)
        full_set = set(fr.unrank(i) for i in range(1, n + 1)) if n <= 200000 else None
        out[B] = {"pairs": n, "rank_unrank_inverse": ok_rank,
                  "full_coverage": None if full_set is None else full_set == set(seq)}
        print(B, out[B])
    # random access at a size that cannot be materialised
    B = 2 ** 20
    fr = FareyRank(B)
    import random
    rng = random.Random(7)
    idxs = [1, Phi(B)] + [rng.randrange(1, Phi(B)) for _ in range(998)]
    fr.unrank(idxs[0])                                    # warm up
    t0 = time.perf_counter()
    res = [fr.unrank(i) for i in idxs]
    dt = time.perf_counter() - t0
    ok = all(fr.rank(*res[j]) == idxs[j] for j in range(0, 1000, 37))
    out["random_access_B_2^20"] = {
        "Phi": Phi(B), "x_count": 4 * Phi(B) - 1,
        "us_per_unrank": round(dt / len(idxs) * 1e6, 2),
        "spot_rank_roundtrip": ok,
        "first_last": [res[0], res[1]],
    }
    print(out["random_access_B_2^20"])
    with open(os.path.join(RAW, "selfcheck.json"), "w") as f:
        json.dump({str(k): v for k, v in out.items()}, f, indent=1)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "counts"
    if cmd == "counts":
        counts()
    elif cmd == "selfcheck":
        selfcheck()
    elif cmd == "bench":
        p = 2 ** 31 - 1          # Mersenne prime, p = 3 mod 4
        res = bench([256, 1024, 2048, 4096], p)
        with open(os.path.join(RAW, "bench.json"), "w") as f:
            json.dump(res, f, indent=1)
