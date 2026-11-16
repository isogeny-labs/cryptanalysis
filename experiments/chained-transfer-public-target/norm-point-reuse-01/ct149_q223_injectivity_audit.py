#!/usr/bin/env python3
"""CT149: deterministic integer audit of reported q223 isogeny subgroup orders.

Not a source-curve point count, map-isogeny certificate, or ECDLP benchmark.
[pcc:unverified]
"""
from __future__ import annotations
import json
from math import gcd, isqrt

MODELS = (
    ("original_fixed", 2773073, 11092292),
    ("alternative_fixed_nu12", 2771711, 11086844),
)
DEGREES = (13, 169)


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError("CT149 rejected: " + message)


def certify_prime(n: int) -> int:
    require(n >= 2, "nonpositive subgroup order")
    # Inspect every candidate divisor, including every composite divisor,
    # through floor(sqrt(n)); this is a finite exact primality proof.
    bound = isqrt(n)
    for d in range(2, bound + 1):
        require(n % d != 0, "composite subgroup order")
    return max(0, bound - 1)


def audit(name: str, ell: int, full: int) -> dict:
    require(full == 4 * ell, "full-group order does not match model")
    divisions = certify_prime(ell)
    result = {"model": name, "ell": ell, "full_group_order": full,
              "prime_trial_divisors_checked": divisions, "degree_checks": []}
    for degree in DEGREES:
        require(degree > 0 and degree in (13, 13 * 13), "wrong isogeny degree")
        require(gcd(ell, degree) == 1, "subgroup kernel collision possible")
        require(gcd(full, degree) == 1, "full-group kernel collision possible")
        inv_ell = pow(degree, -1, ell)
        inv_full = pow(degree, -1, full)
        require(degree * inv_ell % ell == 1, "bad subgroup inverse")
        require(degree * inv_full % full == 1, "bad full-group inverse")
        result["degree_checks"].append({"degree": degree, "gcd_subgroup": 1,
              "gcd_full": 1, "inverse_mod_ell": inv_ell,
              "inverse_mod_full": inv_full})
    return result


def self_test() -> None:
    # These controls deliberately make a true source field claim false.
    failures = 0
    for bad in (("toy_104_has_13_torsion", 104, 416),
                ("mismatched_full_order", 2773073, 11092293),
                ("composite_claim", 2773073 * 3, 4 * 2773073 * 3)):
        try:
            audit(*bad)
        except ValueError:
            failures += 1
    require(failures == 3, "negative control escaped")


def main() -> dict:
    self_test()
    models = [audit(*entry) for entry in MODELS]
    require(len({x["ell"] for x in models}) == 2, "source-model collision")
    return {"status": "[pcc:unverified]", "scope": "source-reported q223 integer subgroup orders; conditional on actual degree-13/169 isogenies",
            "negative_controls_rejected": 3, "models": models,
            "conclusion": "no 13-primary source subgroup/kernel collision on either reported rational group, if group orders and isogeny degrees are certified"}


if __name__ == "__main__":
    print(json.dumps(main(), sort_keys=True, separators=(",", ":")))
