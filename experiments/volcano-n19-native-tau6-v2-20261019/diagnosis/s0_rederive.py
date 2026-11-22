#!/usr/bin/env python3
"""Re-derive the 300 S0 systems of run 39307409409 and find the mismatches.

No timing. Pure Python plus the native library through ctypes.

S0 (arm.sage selftest_row) drew, for t = 0..299,
    xR = F.from_integer(rng.randrange(1, 2**19)),  j = t % 19,
with rng = random.Random('volcano-n19-native-tau6-20261019:selftest'),
and compared Sage's variety of TauField.system(j, xR, 1) with
Native(lib, N_BITS, MODULUS, 6).solve(enc(xR), j).

Evaluators (none shares code with another):
  third     pure-Python S3 over all 4,096 (u, w), field F_2[z]/(m), m the
            run.sage modulus (Sage's field: GF(2^19, modulus=R(MODULUS)));
  third_rec the same evaluator over the reciprocal modulus (the polynomial
            arm.sage's Native.__init__ actually passed to tau6_new);
  native    tau6_solve / tau6_solve_bruteforce with the modulus passed as
            arm.sage computed it (arm_mod), and as it should be (good_mod).
"""
import argparse
import ctypes
import json
import random

N, K = 19, 6
# run.sage line 19, verbatim.
MODULUS = list(reversed([1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1]))


def arm_mod(bits):
    """arm.sage Native.__init__ (protocol v1), verbatim: reads the list as highest first."""
    mod = 0
    for i, c in enumerate(bits):
        if c:
            mod |= 1 << (len(bits) - 1 - i)
    return mod


def good_mod(bits):
    """What Sage's PolynomialRing(GF(2))(MODULUS) is: the list is lowest degree first."""
    return sum(1 << i for i, c in enumerate(bits) if c)


def pymul(a, b, m):
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a <<= 1
        if a >> N & 1:
            a ^= m
    return r


def third(xr, j, m):
    """Direct S3 evaluation; x2 = (sum w_l z^l)^(2^j) by j squarings."""
    xr2 = pymul(xr, xr, m)
    out = []
    for u in range(1 << K):
        for w in range(1 << K):
            x2 = w
            for _ in range(j):
                x2 = pymul(x2, x2, m)
            p = pymul(u, x2, m)
            f = pymul(p, p, m) ^ pymul(xr2, pymul(u, u, m) ^ pymul(x2, x2, m), m) ^ pymul(xr, p, m) ^ 1
            if f == 0:
                out.append((u, w))
    return out


class Lib:
    def __init__(self, path, mod):
        self.lib = ctypes.CDLL(path)
        self.lib.tau6_new.restype = ctypes.c_void_p
        self.lib.tau6_new.argtypes = [ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint64]
        for f in (self.lib.tau6_solve, self.lib.tau6_solve_bruteforce):
            f.restype = ctypes.c_int64
            f.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
        self.ctx = self.lib.tau6_new(mod, N, K, 1)
        assert self.ctx
        self.buf = (ctypes.c_uint32 * 4096)()

    def _run(self, f, xr, j):
        c = f(self.ctx, xr, j, self.buf, 4096)
        return [(self.buf[i] & 63, self.buf[i] >> 6) for i in range(c)]

    def solve(self, xr, j):
        return self._run(self.lib.tau6_solve, xr, j)

    def bf(self, xr, j):
        return self._run(self.lib.tau6_solve_bruteforce, xr, j)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lib', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    am, gm = arm_mod(MODULUS), good_mod(MODULUS)
    nat_arm, nat_good = Lib(a.lib, am), Lib(a.lib, gm)
    rng = random.Random('volcano-n19-native-tau6-20261019:selftest')
    rows = []
    for t in range(300):
        xr = rng.randrange(1, 2 ** N)          # F.from_integer: bit i = coefficient of z^i
        j = t % N
        th, thr = third(xr, j, gm), third(xr, j, am)
        na, nab = nat_arm.solve(xr, j), nat_arm.bf(xr, j)
        ng, ngb = nat_good.solve(xr, j), nat_good.bf(xr, j)
        rows.append({'t': t, 'xR': xr, 'j': j, 'third': th, 'third_reciprocal': thr,
                     'native_v1_modulus': na, 'native_v1_modulus_bruteforce': nab,
                     'native_fixed_modulus': ng, 'native_fixed_modulus_bruteforce': ngb})
    mism = [r for r in rows if sorted(r['native_v1_modulus']) != sorted(r['third'])]
    summary = {
        'modulus_sage': gm, 'modulus_sage_bin': bin(gm),
        'modulus_passed_by_arm_sage_v1': am, 'modulus_passed_by_arm_sage_v1_bin': bin(am),
        'reciprocal': am == int(bin(gm)[2:][::-1], 2),
        'systems': len(rows),
        # Reproduces the receipt's fields if Sage == third:
        'v1_set_equal_vs_third': len(rows) - len(mism),
        'v1_bruteforce_equal': sum(r['native_v1_modulus'] == r['native_v1_modulus_bruteforce'] for r in rows),
        'third_nonempty': sum(bool(r['third']) for r in rows),
        'third_multi': sum(len(r['third']) > 1 for r in rows),
        'v1_native_equals_third_reciprocal': sum(r['native_v1_modulus'] == r['third_reciprocal'] for r in rows),
        'fixed_equals_third': sum(r['native_fixed_modulus'] == r['third'] for r in rows),
        'fixed_bruteforce_equals_third': sum(r['native_fixed_modulus_bruteforce'] == r['third'] for r in rows),
        'mismatching_systems': [{k: r[k] for k in ('t', 'xR', 'j', 'third', 'native_v1_modulus')} for r in mism],
    }
    json.dump({'summary': summary, 'rows': rows}, open(a.out, 'w'), indent=1)
    s = dict(summary)
    print(json.dumps(s, indent=1))


if __name__ == '__main__':
    main()
