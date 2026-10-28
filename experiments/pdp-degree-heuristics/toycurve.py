"""Exact toy instances of the ECC2K-130 curve family, E: y^2 + xy = x^3 + a2 x^2 + 1 over F_2^n.

The group order comes from the Frobenius trace (Lucas sequence), the DLP subgroup
is the largest prime factor r of #E, and the curve ID follows AGENTS.md: SHA-256
over the canonical `field` and `curve` records, excluding the ID itself.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "pdp-scaling"))

import gf2n  # noqa: E402

import kernel  # noqa: E402

INF = (kernel.INF_X, 0)


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(value: object) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def is_probable_prime(n: int) -> bool:
    if n < 2:
        return False
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for p in small:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in small:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _pollard_rho(n: int) -> int:
    if n % 2 == 0:
        return 2
    rng = random.Random(n)
    while True:
        c = rng.randrange(1, n)
        x = y = rng.randrange(2, n)
        d = 1
        while d == 1:
            x = (x * x + c) % n
            y = (y * y + c) % n
            y = (y * y + c) % n
            d = math.gcd(abs(x - y), n)
        if d != n:
            return d


def factor(n: int) -> dict[int, int]:
    out: dict[int, int] = {}
    for p in range(2, 1000):
        while n % p == 0:
            out[p] = out.get(p, 0) + 1
            n //= p
    stack = [n] if n > 1 else []
    while stack:
        k = stack.pop()
        if is_probable_prime(k):
            out[k] = out.get(k, 0) + 1
        else:
            d = _pollard_rho(k)
            stack += [d, k // d]
    return dict(sorted(out.items()))


def koblitz_order(n: int, a2: int) -> int:
    """#E(F_2^n) for y^2 + xy = x^3 + a2 x^2 + 1, from tau^2 - mu tau + 2 = 0, mu = (-1)^(1 - a2)."""
    mu = 1 if a2 == 1 else -1
    v0, v1 = 2, mu
    for _ in range(n - 1):
        v0, v1 = v1, mu * v1 - 2 * v0
    return 2**n + 1 - v1


def _trace_mask(K: kernel.Field) -> int:
    """Bit mask t with Tr(v) = parity(popcount(v & t)) (Tr is F_2-linear)."""
    return sum(K.trace(1 << i) << i for i in range(K.n))


def _parity64(v: np.ndarray) -> np.ndarray:
    v = v.copy()
    for sh in (32, 16, 8, 4, 2, 1):
        v ^= v >> np.uint64(sh)
    return (v & np.uint64(1)).astype(np.uint8)


def trace_count_order(K: kernel.Field, chunk: int = 1 << 21) -> int:
    """#E(F_2^n) for y^2 + xy = x^3 + a2 x^2 + a6 by the trace count.

    For x != 0 put y = x t: t^2 + t = x + a2 + a6/x^2, which has two roots when
    Tr(x + a2 + a6/x^2) = 0 and none otherwise.  x = 0 gives the single point (0, sqrt(a6)), plus the
    point at infinity: #E = 2 + 2 #{x != 0 : Tr(x + a2 + a6/x^2) = 0}.  The count is vectorised (all
    inverses by Montgomery's batch trick over independent streams), so n = 23 takes a few seconds.
    """
    n, tmask = K.n, np.uint64(_trace_mask(K))
    tr_a2 = K.trace(K.a2)
    zeros = 0
    for lo in range(1, 1 << n, chunk):
        x = np.arange(lo, min(lo + chunk, 1 << n), dtype=np.uint64)
        inv = _batch_inverse(K, x)
        w2 = K.mul_vec(inv, inv)
        z = K.mul_const(w2, K.b)
        t = _parity64(x & tmask) ^ _parity64(z & tmask) ^ np.uint8(tr_a2)
        zeros += int((t == 0).sum())
    return 2 + 2 * zeros


def _batch_inverse(K: kernel.Field, x: np.ndarray, streams: int = 1024) -> np.ndarray:
    """Inverses of nonzero elements: Montgomery's trick along `streams` independent columns."""
    m = len(x)
    if m < 4 * streams:
        return _inverse_vec(K, x)
    steps = -(-m // streams)
    pad = steps * streams - m
    X = np.concatenate([x, np.ones(pad, dtype=np.uint64)]).reshape(streams, steps)
    P = np.empty_like(X)
    acc = np.ones(streams, dtype=np.uint64)
    for j in range(steps):
        acc = K.mul_vec(acc, np.ascontiguousarray(X[:, j]))
        P[:, j] = acc
    inv_acc = _inverse_vec(K, acc)
    out = np.empty_like(X)
    for j in range(steps - 1, 0, -1):
        out[:, j] = K.mul_vec(inv_acc, np.ascontiguousarray(P[:, j - 1]))
        inv_acc = K.mul_vec(inv_acc, np.ascontiguousarray(X[:, j]))
    out[:, 0] = inv_acc
    return out.reshape(-1)[:m]


def _inverse_vec(K: kernel.Field, x: np.ndarray) -> np.ndarray:
    """x^(2^n - 2) for a vector of nonzero field elements: a_k = x^(2^k - 1), then square once."""

    def frob(a: np.ndarray, k: int) -> np.ndarray:
        for _ in range(k):
            a = K.mul_vec(a, a)
        return a

    a, k = x, 1  # a = x^(2^k - 1)
    for bit in bin(K.n - 1)[3:]:
        a = K.mul_vec(frob(a, k), a)  # a_{2k}
        k *= 2
        if bit == "1":
            a = K.mul_vec(K.mul_vec(a, a), x)  # a_{k+1}
            k += 1
    assert k == K.n - 1
    return K.mul_vec(a, a)  # x^(2^n - 2)


def sqrt_mod(a: int, p: int) -> int | None:
    a %= p
    if a == 0:
        return 0
    if pow(a, (p - 1) // 2, p) != 1:
        return None
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


@dataclass
class ToyCurve:
    n: int
    a2: int = 0
    b: int = 1
    generator_seed: int = 8701
    K: kernel.Field = field(init=False, repr=False)

    def __post_init__(self):
        if not 0 <= self.b < (1 << self.n) or self.b == 0:
            raise ValueError("a6 must be a nonzero element of F_2^n")
        if not 0 <= self.a2 < (1 << self.n):
            raise ValueError("a2 must be an element of F_2^n")
        self.mod = gf2n.modulus(self.n)
        self.K = kernel.Field(self.n, self.mod, self.a2, self.b)
        # Frobenius is an endomorphism only when a2 and a6 lie in F_2.
        self.frobenius_endo = self.a2 in (0, 1) and self.b == 1
        # b = 1 keeps the closed form (byte-identical to earlier records); other a6 are counted.
        self.order = koblitz_order(self.n, self.a2) if self.b == 1 else trace_count_order(self.K)
        self.trace = 2**self.n + 1 - self.order
        fac = factor(self.order)
        self.factorization = fac
        self.r = max(fac)
        if fac[self.r] != 1:
            raise ValueError(f"r^2 divides #E for n={self.n}")
        self.h = self.order // self.r
        self.proj_scalar = self.h * pow(self.h, -1, self.r)
        rng = random.Random(self.generator_seed + self.n)
        while True:
            P = self.K.lift(rng.getrandbits(self.n))
            if P is None:
                continue
            G = self.K.smul(P, self.h)
            if G[0] != kernel.INF_X:
                assert self.K.smul(G, self.r)[0] == kernel.INF_X
                self.G = G
                break
        self.T4 = None
        if self.h == 4:
            while True:
                P = self.K.lift(rng.getrandbits(self.n))
                if P is None:
                    continue
                Q = self.K.smul(P, self.r)
                if self.K.add(Q, Q)[0] != kernel.INF_X:
                    self.T4 = Q
                    break
        self._lambda: int | None = None

    # --- identity -----------------------------------------------------------
    @property
    def tag(self) -> str:
        if self.b == 1:
            return "kb1" if self.a2 == 0 else "ka1"
        return f"o{self.a2:x}b{self.b:x}"

    def field_record(self) -> dict:
        exps = [i for i in range(self.n, -1, -1) if (self.mod >> i) & 1]
        return {
            "characteristic": 2,
            "degree": self.n,
            "representation": "polynomial_basis",
            "modulus_exponents": exps,
            "element_encoding": "unsigned integer; bit i is the coefficient of z^i",
        }

    def curve_record(self) -> dict:
        return {
            "model": "y^2 + x*y = x^3 + a2*x^2 + a6",
            "a2": self.a2,
            "a6": self.b,
            "order": self.order,
            "trace": self.trace,
            "subgroup_order": self.r,
            "cofactor": self.h,
            "generator": [self.G[0], self.G[1]],
            "target_group": "prime-order subgroup generated by G",
        }

    @property
    def curve_id(self) -> str:
        digest = sha256_hex({"field": self.field_record(), "curve": self.curve_record()})
        return f"EC1N{self.n}C{self.tag}h{digest[:12]}"

    # --- group helpers --------------------------------------------------------
    def in_subgroup(self, P: tuple[int, int]) -> bool:
        return P[0] != kernel.INF_X and self.K.smul(P, self.r)[0] == kernel.INF_X

    def project(self, xs, ys):
        """pi_r(P) = [h (h^-1 mod r)] P, the r-component of each point."""
        return self.K.smul_batch(xs, ys, self.proj_scalar)

    def psi(self, xs, ys):
        """[r] P, the image in E[h]; P is in <G> iff this is the identity."""
        return self.K.smul_batch(xs, ys, self.r)

    def z4_labels(self, xs, ys) -> list[int] | None:
        """For h = 4: k with [r]P = [k]T4, a homomorphism E -> Z/4."""
        if self.T4 is None:
            return None
        table = {INF: 0, self.T4: 1, self.K.add(self.T4, self.T4): 2, self.K.neg(self.T4): 3}
        px, py = self.psi(xs, ys)
        return [table[(int(x), int(y) if x != kernel.INF_X else 0)] for x, y in zip(px, py)]

    def frobenius_eigenvalue(self) -> int:
        """lambda with tau(G) = [lambda] G, tau(x, y) = (x^2, y^2)."""
        if not self.frobenius_endo:
            raise ValueError("Frobenius is not an endomorphism unless a2, a6 are in F_2 (a6 = 1 here)")
        if self._lambda is None:
            mu = 1 if self.a2 == 1 else -1
            root = sqrt_mod(mu * mu - 8, self.r)
            assert root is not None
            inv2 = pow(2, -1, self.r)
            tG = (self.K.sqr(self.G[0]), self.K.sqr(self.G[1]))
            for lam in ((mu + root) * inv2 % self.r, (mu - root) * inv2 % self.r):
                if self.K.smul(self.G, lam) == tG:
                    self._lambda = lam
                    break
            assert self._lambda is not None
        return self._lambda

    def random_subgroup_point(self, rng: random.Random) -> tuple[int, tuple[int, int]]:
        k = rng.randrange(1, self.r)
        return k, self.K.smul(self.G, k)

    def summary(self) -> dict:
        return {
            "curve_id": self.curve_id,
            "n": self.n,
            "order": self.order,
            "factorization": {str(p): e for p, e in self.factorization.items()},
            "subgroup_order": self.r,
            "subgroup_bits": self.r.bit_length(),
            "cofactor": self.h,
        }


def pick_ordinary_a6(n: int, a2: int, index: int, max_cofactor: int = 4, tries: int = 4000) -> int:
    """A deterministic 'random' a6 (not 0, 1) whose curve y^2+xy=x^3+a2 x^2+a6 has #E = h r, r prime, h in {2, 4}.

    The stream is seeded by (n, a2, index); earlier accepted a6 for lower indices are skipped, so the index-th
    curve is distinct.  h is always even (the point (0, sqrt(a6)) has order 2).
    """
    rng = random.Random(f"ordinary-a6|{n}|{a2}|{index}")
    seen: set[int] = set()
    while len(seen) < tries:
        a6 = rng.randrange(2, 1 << n)
        if a6 in seen:
            continue
        seen.add(a6)
        K = kernel.Field(n, gf2n.modulus(n), a2, a6)
        order = trace_count_order(K)
        for h in (2, 4):
            if h <= max_cofactor and order % h == 0 and is_probable_prime(order // h) and (order // h).bit_length() >= n - 1:
                return a6
    raise RuntimeError(f"no ordinary a6 found for n={n}, a2={a2}")
