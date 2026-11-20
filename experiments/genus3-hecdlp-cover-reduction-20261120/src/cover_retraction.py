#!/usr/bin/env python3
"""Certificates for retracting cover-lifted Jacobian DLPs to an elliptic DLP.

No logarithm is solved here.  The output records the pullback/pushforward
identity and, optionally, its composition with a polarized isogeny.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


NIST_ORDERS = {
    "P-224": int("FFFFFFFFFFFFFFFFFFFFFFFFFFFF16A2E0B8F03E13DD29455C5C2A3D", 16),
    "P-256": int("FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551", 16),
}


def certificate(subgroup_order: int, cover_degree: int, isogeny_multiplier: int = 1):
    if subgroup_order <= 1:
        raise ValueError("subgroup order must exceed one")
    if cover_degree <= 0 or isogeny_multiplier <= 0:
        raise ValueError("degrees and multipliers must be positive")
    multiplier = cover_degree * isogeny_multiplier
    coprime = math.gcd(subgroup_order, multiplier) == 1
    return {
        "subgroup_order": subgroup_order,
        "cover_degree": cover_degree,
        "isogeny_multiplier": isogeny_multiplier,
        "composed_multiplier": multiplier,
        "coprime_to_subgroup_order": coprime,
        "typed_path": [
            "E[n] --f^*--> J_H[n]",
            "J_H[n] --phi--> A[n]" if isogeny_multiplier != 1 else "no additional isogeny",
            "A[n] --phi^dagger--> J_H[n]" if isogeny_multiplier != 1 else "identity on J_H[n]",
            "J_H[n] --f_*--> E[n]",
        ],
        "identity": (
            "f_* o f^* = [d]"
            if isogeny_multiplier == 1
            else "f_* o phi^dagger o phi o f^* = [m*d]"
        ),
        "symbol_assignment": {
            "d": cover_degree,
            "m": isogeny_multiplier,
            "phi_dual_phi": f"[{isogeny_multiplier}]",
        },
        "kernel_intersection": (
            "trivial on E[n] because the composed multiplier is invertible modulo n"
            if coprime
            else "not certified: the composed multiplier is not invertible modulo n"
        ),
        "recovery_scalar_mod_n": pow(multiplier, -1, subgroup_order) if coprime else None,
        "recovery_map": (
            f"[{pow(multiplier, -1, subgroup_order)}] o f_*"
            if coprime and isogeny_multiplier == 1
            else (
                f"[{pow(multiplier, -1, subgroup_order)}] o f_* o phi^dagger"
                if coprime
                else None
            )
        ),
        "scope": "only the transported subgroup image; arbitrary classes in the full Jacobian or Prym component are not covered",
        "complexity_interpretation": "dimension reduction to the original ECDLP, not a speedup over the original ECDLP",
    }


def build_bundle():
    return {
        "format": "cover-retraction-certificates-v1",
        "general": {
            "cover_only": "f_* f^*=[d]",
            "after_polarized_isogeny": "f_* phi^dagger phi f^*=[m*d] when phi^dagger phi=[m]",
            "dlog_consequence": "Q=[k]P in E[n] iff the corresponding nonzero transported images have the same k modulo n, provided gcd(m*d,n)=1",
        },
        "smith_222_composition": {
            "isogeny_multiplier": 2,
            "identity": "f_* phi^dagger phi f^*=[2d]",
            "condition": "gcd(2d,n)=1",
        },
        "nist_333_diagonal_composition": {
            label: certificate(n, cover_degree=3, isogeny_multiplier=3)
            for label, n in NIST_ORDERS.items()
        },
        "limitations": [
            "requires explicit executable pullback/pushforward (or diagonal/summation) maps",
            "requires the polarized dual of any composed isogeny",
            "does not solve arbitrary HECDLP instances outside the transported elliptic subgroup",
            "does not improve the asymptotic hardness of the original elliptic DLP",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subgroup-order", type=int)
    parser.add_argument("--cover-degree", type=int)
    parser.add_argument("--isogeny-multiplier", type=int, default=1)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if (args.subgroup_order is None) != (args.cover_degree is None):
        parser.error("--subgroup-order and --cover-degree must be supplied together")
    result = (
        build_bundle()
        if args.subgroup_order is None
        else certificate(args.subgroup_order, args.cover_degree, args.isogeny_multiplier)
    )
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
