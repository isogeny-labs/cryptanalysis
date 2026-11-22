#!/usr/bin/env python3
"""Exact field-of-definition audit and external descent obstruction ledger."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("nist_333", ROOT / "src" / "nist_333.py")
nist = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["nist_333"] = nist
SPEC.loader.exec_module(nist)


def build_status():
    artifact = json.loads((ROOT / "artifacts" / "p256_finite_field_theta.json").read_text())
    aronhold = json.loads((ROOT / "artifacts" / "p256_aronhold_frobenius.json").read_text())
    bundle = nist.build_p256()
    field = bundle["basis_points"][0][0].ctx
    fp3 = field.base
    p = nist.CURVES["P-256"]["p"]

    coefficients = []
    for row in artifact["quartic"]:
        raw = row["coefficient"]
        a = fp3.e([int(value, 16) for value in raw["a"]])
        b = fp3.e([int(value, 16) for value in raw["b"]])
        coefficients.append(field.e(a, b))
    all_quadratic_components_zero = all(not value.b for value in coefficients)
    all_fixed_by_p3 = all(value ** (p**3) == value for value in coefficients)
    all_fixed_by_p = all(value**p == value for value in coefficients)
    return {
        "format": "nist-p256-descent-status-v1",
        "reconstruction": {
            "candidate_artifact": "artifacts/p256_finite_field_theta.json",
            "theta_pattern": {
                "odd_zero": artifact["odd_theta_zero_count"],
                "even_nonzero": artifact["even_theta_nonzero_count"],
                "violations": artifact["theta_pattern_violations"],
            },
            "quartic_term_count": artifact["quartic_term_count"],
            "aronhold_bitangent_checks": artifact["aronhold_bitangent_checks"],
            "candidate_constructed": True,
        },
        "exact_field_audit": {
            "ambient_torsion_field_degree": 6,
            "all_quadratic_extension_components_zero": all_quadratic_components_zero,
            "all_coefficients_fixed_by_p_cubed": all_fixed_by_p3,
            "all_coefficients_fixed_by_p": all_fixed_by_p,
            "minimal_field_conclusion": "the displayed candidate is over F_(p^3), not over F_p"
            if all_quadratic_components_zero and all_fixed_by_p3 and not all_fixed_by_p
            else "field audit did not establish the expected cubic-only state",
        },
        "descent_diagnostic": {
            "magma_input": "handoff/p256_descent_diagnostic.m",
            "required_checks": [
                "Dixmier-Ohno moduli are Frobenius-rational",
                "the quartic is isomorphic to its p-Frobenius conjugate",
                "an isomorphism satisfies the order-three projective cocycle",
                "Hilbert 90 yields a nonsingular F_p quartic with matching moduli",
            ],
            "local_magma_available": shutil.which("magma") is not None,
            "local_sage_available": shutil.which("sage") is not None,
            "public_calculator_http_status": 401,
            "browser_surface_status": "unavailable: gaas-browser sandbox could not be initialized",
            "external_validation_completed": False,
        },
        "local_frobenius_bitangent_audit": {
            "artifact": "artifacts/p256_aronhold_frobenius.json",
            "all_odd_characteristics": aronhold["all_odd_characteristics_count"],
            "orbit_histogram": aronhold["full_odd_frobenius_orbit_histogram"],
            "rational_bitangents_predicted": aronhold["rational_bitangent_count_predicted"],
            "known_aronhold_lines_preserved": aronhold["images_remaining_in_selected_aronhold_system"],
            "seven_line_shortcut_available": aronhold["selected_aronhold_stable"],
            "consequence": aronhold["descent_consequence"],
        },
        "obstruction_certificate": {
            "type": "computational validation obstruction, not a proven mathematical non-descent",
            "precise_missing_capability": "equations for the remaining 21 bitangents or a ternary-quartic isomorphism/Galois-descent computation over a 256-bit finite field",
            "preserved_reproducer": "run handoff/p256_descent_diagnostic.m in Magma 2.29 with the quartic package",
            "safe_claim": "P-256 reconstruction reaches an exact F_(p^3) candidate; F_p descent remains unverified",
            "forbidden_claim": "the P-256 quotient has been constructed over the NIST base field",
        },
        "status": "extension-field quotient candidate complete; base-field descent blocked on independent ternary-quartic tooling",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    encoded = json.dumps(build_status(), indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
