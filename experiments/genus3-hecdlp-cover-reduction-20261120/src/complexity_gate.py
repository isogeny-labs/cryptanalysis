#!/usr/bin/env python3
"""Exact structural and exponent gate for proposed NIST cover attacks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


NIST_BITS = {"P-224": 224, "P-256": 256}


def certificate(label: str, prime_bits: int):
    rho_exponent = 0.5
    plane_quartic_exponent = 1.0
    return {
        "curve": label,
        "native_field": "F_p with p prime",
        "subfield_lattice_certificate": {
            "theorem": "The subfields of F_(p^m) are exactly F_(p^d) for d dividing m.",
            "application": "m=1 has only d=1, so F_p has no proper finite subfield.",
            "proper_same_characteristic_subfield_exists": False,
            "cubic_descent_equation": "p=q^3",
            "cubic_descent_possible_for_prime_p": False,
            "reason": "a prime cannot be a nontrivial perfect cube",
        },
        "same_field_costs": {
            "elliptic_pollard_rho_exponent_in_p": rho_exponent,
            "plane_quartic_index_calculus_soft_exponent_in_p": plane_quartic_exponent,
            "destination_minus_rho_log2_at_nominal_size": prime_bits
            * (plane_quartic_exponent - rho_exponent),
            "winner": "elliptic Pollard rho",
        },
        "complexity_changing_gate": {
            "same_field_cover_or_isogeny_passes": False,
            "required_evidence_for_a_pass": [
                "a representation over a genuinely smaller field F_q with quantified q versus p, or",
                "a rigorously analyzed destination algorithm with exponent below 1/2 in p, or",
                "a separate exploitable group-order/endomorphism weakness with full subgroup accounting",
            ],
            "excluded_as_non_speedups": [
                "dimension reduction that retracts to the original ECDLP",
                "a same-field genus-3 Jacobian followed by soft-O(p) index calculus",
                "constant-factor GLV/GLS decompositions marketed as exponent changes",
            ],
        },
        "conclusion": "The standard (3,3,3) quotient over the native NIST prime field is not a drastic ECDLP reduction.",
    }


def build_bundle():
    return {
        "format": "nist-cover-complexity-gate-v1",
        "curves": {label: certificate(label, bits) for label, bits in NIST_BITS.items()},
        "research_filter": {
            "continue": "only mechanisms satisfying one of the explicit pass conditions",
            "stop": "additional same-field covers or isogenies without a sub-rho destination algorithm",
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    encoded = json.dumps(build_bundle(), indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
