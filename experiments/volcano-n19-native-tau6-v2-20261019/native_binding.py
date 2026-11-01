"""ctypes binding of native/src/lib.rs, in plain Python (protocol v2).

v1 kept this class inside arm.sage, which only Sage can load, so the local
checks (smoke/, no Sage) used their own copy of it and never ran the one the
runner used. That copy passed the modulus correctly; arm.sage's did not: it
read run.sage's MODULUS (coefficients lowest degree first, the order
PolynomialRing(GF(2))(MODULUS) uses) as highest degree first, so the native
context worked over the reciprocal polynomial. Run 39307409409's S0 failed on
exactly that (diagnosis/README.md).

In v2 arm.sage and every local check import this module, and the binding
checks the field before use: `check_field` compares the context's modulus
with the one Sage reports, and products against a reference multiplication.
"""
import ctypes
import random


def modulus_int(coeffs):
    """run.sage MODULUS (lowest degree first) as an integer, bit i = coefficient of z^i."""
    return sum(1 << i for i, c in enumerate(coeffs) if int(c))


class Native:
    """tau6_new / tau6_solve / tau6_solve_bruteforce / tau6_mul / tau6_modulus."""

    def __init__(self, path, n, modulus, k):
        if not isinstance(modulus, int) or modulus >> n != 1:
            raise ValueError('modulus must be the integer of a degree-n polynomial (bit i = z^i)')
        self.lib = ctypes.CDLL(path)
        self.lib.tau6_new.restype = ctypes.c_void_p
        self.lib.tau6_new.argtypes = [ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint64]
        for f in (self.lib.tau6_solve, self.lib.tau6_solve_bruteforce):
            f.restype = ctypes.c_int64
            f.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_uint32,
                          ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
        self.lib.tau6_mul.restype = ctypes.c_uint64
        self.lib.tau6_mul.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_uint64]
        self.lib.tau6_modulus.restype = ctypes.c_uint64
        self.lib.tau6_modulus.argtypes = [ctypes.c_void_p]
        self.n, self.k, self.mask = int(n), int(k), (1 << int(k)) - 1
        self.ctx = self.lib.tau6_new(int(modulus), int(n), int(k), int(1))
        if not self.ctx:
            raise RuntimeError('tau6_new rejected its arguments')
        self.cap = int(1 << (2 * int(k)))
        self.buf = (ctypes.c_uint32 * self.cap)()
        self._solve = self.lib.tau6_solve

    def modulus(self):
        return int(self.lib.tau6_modulus(self.ctx))

    def mul(self, a, b):
        return int(self.lib.tau6_mul(self.ctx, int(a), int(b)))

    def solve(self, xr, j):
        c = self._solve(self.ctx, int(xr), int(j), self.buf, self.cap)
        if c < 0 or c > self.cap:
            raise RuntimeError('tau6_solve failed')
        b, k, m = self.buf, self.k, self.mask
        return [(b[i] & m, b[i] >> k) for i in range(c)]

    def bruteforce(self, xr, j):
        c = self.lib.tau6_solve_bruteforce(self.ctx, int(xr), int(j), self.buf, self.cap)
        b, k, m = self.buf, self.k, self.mask
        return [(b[i] & m, b[i] >> k) for i in range(c)]


def check_field(nat, expected_modulus, ref_mul, samples=256, seed='native_binding.check_field'):
    """The context's field is the expected one: same modulus, and `samples` random
    products equal ref_mul(a, b) (integers, bit i = z^i). Returns a record."""
    rng = random.Random(seed)
    bad = 0
    for _ in range(samples):
        a, b = rng.randrange(1 << nat.n), rng.randrange(1 << nat.n)
        bad += int(nat.mul(a, b) != int(ref_mul(a, b)))
    rec = {'native_modulus': nat.modulus(), 'expected_modulus': int(expected_modulus),
           'products_checked': samples, 'products_wrong': bad}
    rec['ok'] = rec['native_modulus'] == rec['expected_modulus'] and bad == 0
    return rec


def pymul(a, b, n, m):
    """Reference product in F_2[z]/(m), shift-and-add (no code shared with lib.rs)."""
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a <<= 1
        if a >> n & 1:
            a ^= m
    return r
