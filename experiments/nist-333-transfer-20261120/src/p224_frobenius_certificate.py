#!/usr/bin/env python3
"""Expected E^3 Frobenius polynomial and independent evidence ledger."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("nist_333", ROOT / "src" / "nist_333.py")
nist = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["nist_333"] = nist
SPEC.loader.exec_module(nist)

PREREQ_SPEC = importlib.util.spec_from_file_location(
    "p224_jacobian_prerequisites", ROOT / "src" / "p224_jacobian_prerequisites.py"
)
prereq = importlib.util.module_from_spec(PREREQ_SPEC)
assert PREREQ_SPEC.loader is not None
sys.modules["p224_jacobian_prerequisites"] = prereq
PREREQ_SPEC.loader.exec_module(prereq)


def cube_quadratic_coefficients(p: int, trace: int):
    """Coefficients low-to-high of (1-trace*T+p*T^2)^3."""
    t = trace
    return [
        1,
        -3 * t,
        3 * (p + t * t),
        -(t**3 + 6 * p * t),
        3 * p * (p + t * t),
        -3 * t * p * p,
        p**3,
    ]


def build_certificate():
    curve = nist.CURVES["P-224"]
    p, n = curve["p"], curve["n"]
    trace = p + 1 - n
    coefficients = cube_quadratic_coefficients(p, trace)
    base = prereq.build_certificate()
    rational_bitangents_observed = int(base["rational_bitangent"]["factorization_verified"])
    return {
        "format": "nist-p224-frobenius-certificate-v1",
        "elliptic_curve": {
            "p": str(p),
            "group_order": str(n),
            "trace_t": str(trace),
            "frobenius_polynomial_coefficients_low_to_high": ["1", str(-trace), str(p)],
        },
        "expected_jacobian": {
            "isogeny_class": "E^3",
            "l_polynomial_formula": "(1 - t*T + p*T^2)^3",
            "l_polynomial_coefficients_low_to_high": [str(x) for x in coefficients],
            "predicted_curve_point_count_Fp": str(p + 1 - 3 * trace),
            "predicted_jacobian_order_Fp": str(n**3),
            "functional_equation_checks": {
                "c6_equals_p_cubed": coefficients[6] == p**3,
                "c5_equals_p_squared_c1": coefficients[5] == p * p * coefficients[1],
                "c4_equals_p_c2": coefficients[4] == p * coefficients[2],
            },
        },
        "independent_quartic_evidence": {
            "rational_bitangents_explicitly_certified": rational_bitangents_observed,
            "certified_line": "X=0",
            "certified_contact_divisor": "2*P1 + 2*P2",
            "strength": "geometric consistency check only; it does not determine the L-polynomial",
        },
        "certification_status": {
            "expected_polynomial_exact": True,
            "expected_polynomial_basis": "the verified source E^3 and the candidate (3,3,3) quotient isogeny class",
            "independent_full_point_count_completed": False,
            "full_independent_certification": False,
            "open_obligation": "compute the quartic L-polynomial independently of the quotient construction (or certify it on enough prime-power torsion) and compare every coefficient",
            "nonclaim": "nonsingularity, matching moduli, and one rational bitangent do not by themselves prove the E^3 L-polynomial",
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    encoded = json.dumps(build_certificate(), indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
