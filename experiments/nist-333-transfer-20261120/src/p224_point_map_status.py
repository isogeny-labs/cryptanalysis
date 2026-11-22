#!/usr/bin/env python3
"""Executable Kummer-stage map certificate and remaining signed-map ledger."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "finite_field_theta", ROOT / "src" / "finite_field_theta.py"
)
theta = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["finite_field_theta"] = theta
SPEC.loader.exec_module(theta)


def image_digest(image):
    encoded = json.dumps(
        [coordinate.as_json() for coordinate in image],
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_certificate():
    started = time.time()
    engine = theta.P224ThetaEngine()
    quotient = engine.quotient_theta_data()
    base = engine.quotient_kummer_image(engine.generic, quotient)
    base_digest = image_digest(base)
    negative = engine.quotient_kummer_image(
        theta.negate_product(engine.generic), quotient
    )
    negative_digest = image_digest(negative)
    kernel_checks = []
    basis_coefficients = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    for coefficients in basis_coefficients:
        translated = theta.add_product(
            engine.generic, engine.kernel[coefficients], engine.a
        )
        image = engine.quotient_kummer_image(translated, quotient)
        kernel_checks.append(
            {
                "kernel_coefficients": list(coefficients),
                "image_sha256": image_digest(image),
                "exact_projective_equality": image == base,
            }
        )

    p_basis, _ = engine.data["three_basis"]
    outside = (p_basis, None, None)
    outside_argument = theta.add_product(engine.generic, outside, engine.a)
    outside_image = engine.quotient_kummer_image(outside_argument, quotient)
    outside_distinguished = outside_image != base
    n = theta.nist.CURVES["P-224"]["n"]
    return {
        "format": "nist-p224-point-map-status-v1",
        "implemented_map": {
            "domain": "E^3 over the exact degree-six working field",
            "codomain": "level-2 projective Kummer coordinates of E^3/Lambda",
            "coordinate_count": len(base),
            "formula": "scalar_i*g_i(P)^3*Theta(P+D_i)^2/Theta(P)^2",
            "base_image_sha256": base_digest,
            "negative_image_sha256": negative_digest,
            "exact_sign_pair_collision": negative == base,
            "sign_information": "lost: K(Q)=K(-Q), verified exactly on the test point",
            "executable_entry_point": "P224ThetaEngine.quotient_kummer_image",
        },
        "kernel_fiber_checks": {
            "selected_kernel_order": len(engine.kernel),
            "three_generators_exactly_collapsed": all(
                row["exact_projective_equality"] for row in kernel_checks
            ),
            "generator_checks": kernel_checks,
            "transverse_nonkernel_three_torsion_distinguished": outside_distinguished,
            "test_point": "generic source point translated by (P,0,0)",
            "interpretation": "exact function evaluation confirms the selected generators act trivially and one transverse 3-torsion direction does not",
        },
        "polarized_dual_certificate": {
            "theorem_identity": "pi^dagger o pi = [3] on E^3 for a polarized (3,3,3)-isogeny",
            "diagonal_then_sum_identity": "Sum o pi^dagger o pi o Diagonal = [9] on E",
            "subgroup_order_n": str(n),
            "gcd_9_n": 1,
            "recovery_scalar_9_inverse_mod_n": str(pow(9, -1, n)),
            "symbolic_certificate_complete": True,
            "executable_signed_dual_composition_complete": False,
        },
        "remaining_obstruction": {
            "missing_stage": "recover a signed degree-three divisor on the descended quartic from the Kummer coordinates",
            "required_construction": [
                "construct the codomain Jacobian level-2 Weil functions xi using Riemann-Roch",
                "interpolate Tian's eight low-degree symmetric zeta functions",
                "solve the resulting Groebner system for an effective degree-three divisor",
                "transport through the Hilbert-90 coordinate descent",
                "implement the polarized dual on the same divisor representation",
            ],
            "why_current_map_is_insufficient": "Kummer coordinates cannot distinguish Q from -Q, so they cannot by themselves support a homomorphism or dual-composition test",
            "available_software_gap": "no local Magma/Sage/general plane-quartic Jacobian implementation and no public Tian point-map implementation was found",
        },
        "status": {
            "source_to_kummer_map": "complete and exact on tested points",
            "source_to_signed_jacobian_divisor_map": "open",
            "kernel_test_at_kummer_stage": "complete for a generating set plus a transverse control",
            "end_to_end_dual_composition": "open",
        },
        "elapsed_seconds": time.time() - started,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = build_certificate()
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
