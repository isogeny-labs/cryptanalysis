#!/usr/bin/env python3
"""CT150: exact scope audit for reported q223 cubic-field ECDLP transfer.

Source constants: cryptanalysis fixed-jacobian-chain-01/src/lib.rs and
root crypto #3877 literal-complete-outcome.json. All claims [pcc:unverified].
No actual map or prime-field DLP is certified by this arithmetic audit.
"""
from __future__ import annotations
import json
from math import gcd, isqrt

P = 223
EXT_DEGREE = 3
QUOTIENT_DEGREE = 8
ISOGENY_EDGE = 13
MODELS = (
    ("original_fixed", 2_773_073, 11_092_292),
    ("fixed_nu12", 2_771_711, 11_086_844),
)


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("CT150 rejected: " + why)


def trace_cube(t: int, p: int) -> int:
    return t*t*t - 3*p*t


def examine(p: int, ell: int, order: int) -> dict:
    require(p >= 2 and all(p % d for d in range(2, isqrt(p)+1)), "prime base field")
    require(order == 4*ell and ell > 1, "original recorded group-order contract")
    q = p**EXT_DEGREE
    t3 = q + 1 - order
    bound1 = isqrt(4*p)
    bound3 = isqrt(4*q)
    require(abs(t3) <= bound3, "extension-field Hasse bound")
    candidates = [(t, trace_cube(t,p)) for t in range(-bound1,bound1+1)]
    # Every curve defined over F_p has an integral Frobenius trace t in this list.
    can_basechange = any(u == t3 for _,u in candidates)
    closest = min(candidates, key=lambda item:(abs(item[1]-t3),abs(item[0]),item[0]))
    # A degree-8 quotient of a 3-dim Weil restriction followed by a
    # degree-169 elliptic map (which induces degree 169^3 on the restriction).
    jac_degree = ISOGENY_EDGE**(2*EXT_DEGREE)
    total_degree = QUOTIENT_DEGREE*jac_degree
    return {
        "p": p, "q": q, "ell": ell, "source_group_order": order,
        "trace_over_cubic": t3, "prime_base_trace_bound": bound1,
        "possible_prime_base_traces_tested": len(candidates),
        "could_be_cubic_base_change_from_prime_field": can_basechange,
        "closest_base_trace": closest[0],
        "closest_cubic_trace": closest[1],
        "minimum_trace_gap": abs(closest[1]-t3),
        "prime_base_elliptic_group_max": p+1+bound1,
        "ell_exceeds_prime_base_elliptic_max": ell > p+1+bound1,
        "conditional_degree_of_direct_jacobian_chain": jac_degree,
        "conditional_quotient_degree": QUOTIENT_DEGREE,
        "conditional_total_degree": total_degree,
        "gcd_ell_with_total_degree": gcd(ell,total_degree),
        "gcd_full_group_with_total_degree": gcd(order,total_degree),
    }


def self_test() -> None:
    a, b = [examine(P,ell,order) for _,ell,order in MODELS]
    for x in (a,b):
        require(not x["could_be_cubic_base_change_from_prime_field"], "false prime-base descent")
        require(x["minimum_trace_gap"] == 112, "closest trace gap")
        require(x["possible_prime_base_traces_tested"] == 59, "complete base trace census")
        require(x["gcd_ell_with_total_degree"] == 1, "prime-order injection criterion")
        require(x["gcd_full_group_with_total_degree"] == 4, "2-primary qualification")
        require(x["ell_exceeds_prime_base_elliptic_max"], "source order too large for Fp elliptic group")
    # Positive control: F_223^3 order of a hypothetical F_223 elliptic
    # curve with trace 4. This is a polynomial check, not a constructed curve.
    t=4
    basechanged_order=P**3+1-trace_cube(t,P)
    require(basechanged_order % 4 == 0, "positive-control cofactor")
    candidate=examine(P,basechanged_order//4,basechanged_order)
    require(candidate["could_be_cubic_base_change_from_prime_field"], "positive basechange control")
    for mutated in ((P, MODELS[0][1], MODELS[0][2]+1), (221, MODELS[0][1], MODELS[0][2])):
        try:
            examine(*mutated)
        except ValueError:
            continue
        raise ValueError("negative control accepted")


def main() -> dict:
    self_test()
    return {
        "status": "[pcc:unverified]", "scope": "reported cubic-field group orders and conditional quotient/isogeny degrees only",
        "source_prime": P, "extension_degree": EXT_DEGREE,
        "models": [{"model": name, **examine(P,ell,order)} for name,ell,order in MODELS],
        "proof_obligation": "certify actual source group orders, Weil-restriction/degree-eight diagram, rational isogenies and point-map semantics; no arbitrary E(Fp) transfer or ECDLP speedup inferred",
    }


if __name__ == "__main__":
    print(json.dumps(main(), sort_keys=True, separators=(",", ":")))
