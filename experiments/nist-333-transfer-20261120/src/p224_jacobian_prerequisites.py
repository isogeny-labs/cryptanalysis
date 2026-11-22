#!/usr/bin/env python3
"""Certify rational base data for divisor arithmetic on the P-224 quartic.

This does not implement the general plane-quartic Jacobian group law.  It
certifies the concrete rational points and canonical divisor needed to choose
a Picard/Jacobian encoding without an unspecified rational-basepoint oracle.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
CURVE_PATH = ROOT / "artifacts" / "p224_descended_quartic.json"

# The two contact points of the rational bitangent X=0.  They are retained as
# explicit regression values; all geometric claims below are recomputed from
# the quartic coefficients rather than trusted from these constants.
CONTACT_Y = (
    22787173778508524698301357359670643493480311217601617318077615795862,
    13535062028274435351443631403241021304881425966529312421607570796382,
)


def load_curve(path: Path = CURVE_PATH):
    data = json.loads(path.read_text())
    p = int(data["field"]["p"])
    terms = {
        tuple(row["exponents_xyz"]): int(row["coefficient"]) % p
        for row in data["terms"]
    }
    return data, p, terms


def evaluate(terms, point, p):
    x, y, z = point
    return sum(
        coefficient * pow(x, i, p) * pow(y, j, p) * pow(z, k, p)
        for (i, j, k), coefficient in terms.items()
    ) % p


def gradient(terms, point, p):
    x, y, z = point
    variables = (x, y, z)
    result = []
    for coordinate in range(3):
        total = 0
        for exponents, coefficient in terms.items():
            exponent = exponents[coordinate]
            if not exponent:
                continue
            value = coefficient * exponent
            for index, power in enumerate(exponents):
                value *= pow(variables[index], power - int(index == coordinate), p)
            total += value
        result.append(total % p)
    return tuple(result)


def multiply(left, right, p):
    result = [0] * (len(left) + len(right) - 1)
    for i, x in enumerate(left):
        for j, y in enumerate(right):
            result[i + j] = (result[i + j] + x * y) % p
    return result


def line_restriction(terms, p):
    """Return coefficients low-to-high for F(0,Y,1)."""
    return [terms.get((0, degree, 4 - degree), 0) for degree in range(5)]


def build_certificate(path: Path = CURVE_PATH):
    data, p, terms = load_curve(path)
    restriction = line_restriction(terms, p)
    leading = restriction[4]
    expected = [leading]
    for root in CONTACT_Y:
        expected = multiply(expected, [root * root % p, (-2 * root) % p, 1], p)
    factorization_valid = expected == restriction

    points = []
    for index, y in enumerate(CONTACT_Y, start=1):
        point = (0, y, 1)
        value = evaluate(terms, point, p)
        derivatives = gradient(terms, point, p)
        smooth = any(derivatives)
        tangent_is_x_zero = derivatives[0] != 0 and derivatives[1:] == (0, 0)
        points.append(
            {
                "name": f"P{index}",
                "projective_xyz": [str(coordinate) for coordinate in point],
                "quartic_value_mod_p": str(value),
                "gradient_mod_p": [str(coordinate) for coordinate in derivatives],
                "smooth": smooth,
                "tangent_line": "X=0" if tangent_is_x_zero else None,
                "contact_multiplicity": 2 if factorization_valid else None,
            }
        )

    passed = factorization_valid and all(
        row["quartic_value_mod_p"] == "0" and row["smooth"] and row["tangent_line"] == "X=0"
        for row in points
    )
    return {
        "format": "nist-p224-jacobian-prerequisites-v1",
        "curve_artifact": str(path.relative_to(ROOT)),
        "field_prime": str(p),
        "rational_bitangent": {
            "line": "X=0",
            "restriction_coefficients_low_to_high": [str(x) for x in restriction],
            "factorization": "c*(Y-y1*Z)^2*(Y-y2*Z)^2",
            "leading_coefficient_c": str(leading),
            "factorization_verified": factorization_valid,
            "intersection_divisor": "2*P1 + 2*P2",
            "canonical_divisor_verified": factorization_valid,
        },
        "points": points,
        "jacobian_representation": {
            "chosen_rational_basepoint": "P1",
            "degree_zero_encoding": "[D - deg(D)*P1] for an F_p-rational divisor D",
            "generic_genus_three_encoding": "[D3 - 3*P1] with D3 an effective degree-3 divisor, away from exceptional loci",
            "rational_canonical_divisor": "K = 2*P1 + 2*P2",
            "field_of_definition": "F_p; no extension-field base divisor is required",
        },
        "verification": {
            "all_checks_pass": passed,
            "checks": [
                "F(P1)=F(P2)=0",
                "P1 and P2 are smooth",
                "the tangent at each point is X=0",
                "F(0,Y,Z)=c*(Y-y1*Z)^2*(Y-y2*Z)^2",
            ],
        },
        "scope_boundary": {
            "completed": "rational basepoint, divisor encoding, and canonical-divisor prerequisites",
            "not_completed": "general plane-quartic Jacobian addition/reduction and the source isogeny point map",
        },
        "source_curve_normalization": data["normalization"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--curve", type=Path, default=CURVE_PATH)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = build_certificate(args.curve)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
