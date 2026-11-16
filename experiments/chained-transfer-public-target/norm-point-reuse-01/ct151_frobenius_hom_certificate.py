#!/usr/bin/env python3
"""CT151: conditional prime-field E -> Res(K/k) E' Hom obstruction.

Integer-only certificate, no original q223 curve or DLP verification.
Standing [pcc:unverified]. Precommitted CT151_FROBENIUS_HOM_PROTOCOL.md.
"""
from __future__ import annotations

import hashlib
import json
from math import isqrt

P = 223
MODELS = (
    ("original_fixed", 11_092_292),
    ("fixed_nu12", 11_086_844),
)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError("CT151 rejected: " + reason)


def trim(poly: list[int]) -> list[int]:
    a = list(poly)
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    return a or [0]


def sub(a: list[int], b: list[int]) -> list[int]:
    return trim([(a[i] if i < len(a) else 0) -
                 (b[i] if i < len(b) else 0)
                 for i in range(max(len(a), len(b)))])


def add(a: list[int], b: list[int]) -> list[int]:
    return trim([(a[i] if i < len(a) else 0) +
                 (b[i] if i < len(b) else 0)
                 for i in range(max(len(a), len(b)))])


def mul(a: list[int], b: list[int]) -> list[int]:
    out = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            out[i+j] += ai * bj
    return trim(out)


def div_monic(numerator: list[int], denominator: list[int]) -> tuple[list[int], list[int]]:
    d = trim(denominator)
    require(d[-1] == 1, "nonmonic divisor")
    rem = trim(numerator)
    quotient = [0] * max(1, len(rem) - len(d) + 1)
    while rem != [0] and len(rem) >= len(d):
        shift = len(rem) - len(d)
        factor = rem[-1]
        quotient[shift] += factor
        for i, di in enumerate(d):
            rem[shift+i] -= factor*di
        rem = trim(rem)
    return trim(quotient), rem


def pair_mul(a: tuple[int, int], b: tuple[int, int], t: int, p: int) -> tuple[int, int]:
    # Independent quadratic-basis route: X^2=tX-p.
    return (a[0]*b[0] - p*a[1]*b[1],
            a[0]*b[1] + a[1]*b[0] + t*a[1]*b[1])


def eval_pair(poly: list[int], t: int, p: int) -> tuple[int, int]:
    value = (0, 0)
    for coefficient in reversed(poly):
        value = pair_mul(value, (0, 1), t, p)
        value = (value[0]+coefficient, value[1])
    return value


def trace_cube(t: int, p: int) -> int:
    return t*t*t - 3*p*t


def setup(p: int, t: int, T: int) -> tuple[list[int], list[int], list[int], int]:
    return ([p, -t, 1], [p**3, 0, 0, -T, 0, 0, 1],
            [t**3, -3*t*t, 3*t, -1], trace_cube(t,p)-T)


def verify(p: int, t: int, T: int, R: list[int], delta: int) -> None:
    polynomial, frobenius, v, actual_delta = setup(p, t, T)
    require(delta == actual_delta, "delta tampering")
    require(add(mul(R, polynomial), [delta*p**3]) == mul(v, frobenius),
            "Bezout coefficient tampering")
    # This is not the long-division route: reduce each polynomial directly
    # in the rank-2 quotient Z[X]/(X^2-tX+p).
    require(pair_mul(eval_pair(v, t, p), eval_pair(frobenius, t, p), t, p)
            == (delta*p**3, 0), "independent quadratic quotient check")


def certificate(p: int, t: int, T: int) -> tuple[list[int], int]:
    polynomial, frobenius, v, delta = setup(p, t, T)
    quotient, rem = div_monic(sub(mul(v, frobenius), [delta*p**3]), polynomial)
    require(rem == [0], "nonzero polynomial remainder")
    verify(p, t, T, quotient, delta)
    require(len(quotient) == 8, "unexpected witness degree")
    return quotient, delta


def audit(p: int, models: tuple[tuple[str, int], ...]) -> dict:
    require(p >= 2 and all(p % d for d in range(2, isqrt(p)+1)), "composite base characteristic")
    require(p == P, "unfrozen prime characteristic")
    require(models == MODELS, "changed frozen source group orders")
    bound = isqrt(4*p)
    all_rows: list[dict] = []
    for name, group_order in models:
        T = p**3+1-group_order
        require(abs(T) <= isqrt(4*p**3), "K-Hasse bound")
        witnesses: list[list[int]] = []
        gaps: list[tuple[int, int]] = []
        for t in range(-bound, bound+1):
            R, delta = certificate(p, t, T)
            require(delta != 0, "Frobenius match; cannot exclude hom")
            witnesses.append([t, delta, *R])
            gaps.append((abs(delta), t))
        minimum = min(gaps)
        encoded = json.dumps(witnesses, separators=(",", ":")).encode("ascii")
        all_rows.append({
            "model": name, "reported_group_order": group_order,
            "predicted_cubic_trace": T, "candidate_traces_tested": len(witnesses),
            "certificate_degree": 7,
            "all_delta_nonzero": True, "minimum_abs_delta": minimum[0],
            "minimizing_prime_trace": minimum[1],
            "integer_witness_roster_sha256": hashlib.sha256(encoded).hexdigest(),
        })
    return {"standing": "[pcc:unverified]", "prime": p, "extension_degree": 3,
            "scope": "conditional k-defined Hom(E/Fp,Res(Fp3/Fp)E')=0 for both reported cubic-source orders; not a complete prime-field ECDLP transfer",
            "models": all_rows, "total_bezout_witnesses": sum(r["candidate_traces_tested"] for r in all_rows)}


def self_test() -> None:
    # A positive base-change trace must *not* be certified as an obstruction.
    t = 4
    _, delta = certificate(P, t, trace_cube(t, P))
    require(delta == 0, "positive boundary matched trace")
    R, delta = certificate(P, t, -2724)
    require(delta == 112, "fixed negative-trace witness")
    for corrupted_R, corrupted_delta in (([R[0]+1, *R[1:]], delta),
                                         (R, delta+1)):
        try:
            verify(P, t, -2724, corrupted_R, corrupted_delta)
        except ValueError:
            continue
        raise ValueError("CT151 accepted a corrupted certificate")
    for bad_prime, bad_models in ((221, MODELS), (P, (("original_fixed", MODELS[0][1]+1), MODELS[1]))):
        try:
            audit(bad_prime, bad_models)
        except ValueError:
            continue
        raise ValueError("CT151 accepted corrupted frozen inputs")


def main() -> dict:
    self_test()
    result = audit(P, MODELS)
    require(result["total_bezout_witnesses"] == 118, "unexpected trace census")
    require(all(r["minimum_abs_delta"] == 112 for r in result["models"]), "minimum separation")
    return result


if __name__ == "__main__":
    print(json.dumps(main(), sort_keys=True, separators=(",", ":")))
