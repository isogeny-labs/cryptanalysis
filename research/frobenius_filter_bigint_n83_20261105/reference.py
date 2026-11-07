#!/usr/bin/env python3
"""Independent Python-integer reference for frobenius_filter at q = 2^83.

Prints, for each product surface, the exact quotient/remainder by
T^2 - t*T + q and the filter booleans, using Python arbitrary-precision
integers only; the --coeffs/--trace arguments for the Rust tool go to stderr.
tools/ecdlp-surfaces/tests/math.rs hard-codes the coefficient strings from this
script and compares every field of the Rust result against them.
"""
import json, sys

q = 2**83
T0 = -6151469093347  # a = 0 Frobenius trace
T1 = 6151469093347   # a = 1 Frobenius trace


def mul(p, r):
    out = [0] * (len(p) + len(r) - 1)
    for i, x in enumerate(p):
        for j, y in enumerate(r):
            out[i + j] += x * y
    return out


def quad(t):  # T^2 - t T + q, high degree first
    return [1, -t, q]


def divmod_quartic(f, t):
    c1, c2, c3, c4 = f[1:]
    u = c1 + t
    v = c2 + t * u - q
    return [1, u, v], [c3 + t * v - q * u, c4 - q * v]


def report(f, t):
    quo, rem = divmod_quartic(f, t)
    divides = rem == [0, 0]
    recip = f[3] == q * f[1] and f[4] == q * q
    shape = quo[2] == q
    hasse = quo[1] ** 2 <= 4 * q
    return {
        "field_size": q,
        "source_polynomial_coefficients": quad(t),
        "surface_polynomial_coefficients": f,
        "quotient_coefficients": quo,
        "remainder_coefficients": rem,
        "source_polynomial_divides": divides,
        "surface_reciprocal_conditions_pass": recip,
        "quotient_elliptic_shape": shape,
        "quotient_hasse_bound_pass": hasse,
        "passes_necessary_conditions": divides and recip and shape and hasse,
    }


CASES = {
    "a0_ExE": (mul(quad(T0), quad(T0)), T0),
    "a1_ExE": (mul(quad(T1), quad(T1)), T1),
    "a0_E0xE1": (mul(quad(T0), quad(T1)), T0),
    "a1_E0xE1": (mul(quad(T0), quad(T1)), T1),
    # negative: E0 x E0 tested against the a=1 source factor
    "neg_E0xE0_source_a1": (mul(quad(T0), quad(T0)), T1),
}

if __name__ == "__main__":
    out = {k: report(*v) for k, v in CASES.items()}
    for k, (f, t) in CASES.items():
        print(k, "--coeffs", ",".join(map(str, f[1:])), "--trace", t, file=sys.stderr)
    json.dump(out, sys.stdout, indent=1)
    print()
