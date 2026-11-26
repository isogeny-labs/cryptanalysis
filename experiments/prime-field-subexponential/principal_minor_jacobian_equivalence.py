#!/usr/bin/env python3
"""Certify that deficient branch matrices are norm/Jacobian solutions."""

from itertools import product
import json
from pathlib import Path
from random import Random

from binary_split_norm_control import null_vector, product_from_roots
from interpolation_projection_control import determinant
from multisection_span_control import section_basis
from paired_arrangement_mobius import candidate_rows
from paired_span_state_control import SEED, extended_panel
from toy_jacobian import GenusTwo


PRIME = 101


def section_polynomials(curve, panel, kernel):
    dimension = panel["projective_section_dimension"]
    b_count = (dimension - 1) // 2 + 1
    return (
        curve.poly.canonical(kernel[:b_count]),
        curve.poly.canonical(kernel[b_count:]),
    )


def norm_polynomial(curve, panel, b_poly, c_poly):
    poly = curve.poly
    u = panel["target_u"]
    v = panel["target_v"]
    w = poly.exact_quotient(
        poly.sub(curve.coefficients, poly.mul(v, v)),
        u,
    )
    return poly.sub(
        poly.sub(poly.mul(w, poly.mul(b_poly, b_poly)),
                 poly.mul((2,), poly.mul(v, poly.mul(b_poly, c_poly)))),
        poly.mul(u, poly.mul(c_poly, c_poly)),
    )


def selected_sum(curve, xs, bits):
    total = curve.identity
    for x, bit in zip(xs, bits, strict=True):
        y = curve.roots(x)[bit]
        total = curve.add(total, curve.point_divisor(x, y))
    return total


def residual_points(curve, panel, b_poly, c_poly, cofactor):
    """Recover candidate residual zeros (the control is genus two)."""
    if len(cofactor) == 1:
        return [None]
    assert len(cofactor) == 2 and cofactor[1]
    x = -cofactor[0] * pow(cofactor[1], -1, curve.p) % curve.p
    result = []
    for y in curve.roots(x):
        value = (
            curve.poly.evaluate(b_poly, x)
            * (y - curve.poly.evaluate(panel["target_v"], x))
            - curve.poly.evaluate(panel["target_u"], x)
            * curve.poly.evaluate(c_poly, x)
        ) % curve.p
        if value == 0:
            result.append((x, y))
    assert result
    return result


def analyze(curve, panel):
    dimension = panel["projective_section_dimension"]
    size = dimension + 1
    xs = panel["split_abscissae"][:size]
    reduced = dict(panel)
    reduced["split_abscissae"] = xs
    paired_rows = candidate_rows(curve, reduced)
    u_poly = product_from_roots(curve.poly, xs)
    target_inverse = curve.neg((tuple(panel["target_u"]), tuple(panel["target_v"])))

    determinant_solutions = 0
    residual_completions = 0
    supplied_tail_extensions = 0
    norm_certificates = 0
    cofactor_degrees = []
    for bits in product((0, 1), repeat=size):
        rows = [paired_rows[2 * index + bit] for index, bit in enumerate(bits)]
        deficient = determinant(rows, curve.p) == 0
        determinant_solutions += deficient
        if not deficient:
            continue
        kernel = null_vector(rows, curve.p)
        assert kernel is not None
        b_poly, c_poly = section_polynomials(curve, reduced, kernel)
        norm = norm_polynomial(curve, reduced, b_poly, c_poly)
        cofactor = curve.poly.exact_quotient(norm, u_poly)
        assert cofactor
        cofactor_degrees.append(len(cofactor) - 1)
        partial = selected_sum(curve, xs, bits)
        residual = next(
            point for point in residual_points(
                curve, reduced, b_poly, c_poly, cofactor
            )
            if curve.add(
                partial,
                curve.identity if point is None else curve.point_divisor(*point),
            ) == target_inverse
        )
        residual_completions += 1
        remaining_xs = panel["split_abscissae"][size:]
        supplied_tail_extensions += (
            residual is not None and residual[0] in remaining_xs
        )
        norm_certificates += 1

    assert determinant_solutions == residual_completions == norm_certificates
    return {
        "projective_section_dimension": dimension,
        "square_slots": size,
        "sign_assignments": 1 << size,
        "deficient_determinants": determinant_solutions,
        "deficient_density_scaled_by_prime": (
            determinant_solutions * curve.p / (1 << size)
        ),
        "jacobian_residual_completions": residual_completions,
        "extensions_using_supplied_remaining_slots": supplied_tail_extensions,
        "norm_certificates": norm_certificates,
        "every_deficient_kernel_completes_to_jacobian_target": True,
        "every_kernel_norm_is_selected_product_times_residual": True,
        "residual_cofactor_degrees": cofactor_degrees,
    }


def main():
    source = json.loads(
        Path(__file__).with_name("binary_split_norm_control.json").read_text()
    )
    curve = GenusTwo(PRIME)
    panels = list(source["panels"])
    rng = Random(SEED)
    for dimension in range(8, 11):
        panel, _, _ = extended_panel(curve, dimension, rng)
        panels.append(panel)
    result = {
        "prime": PRIME,
        "genus": 2,
        "statement": (
            "At square saturation, each deficient branch determinant gives a "
            "norm cofactor of degree g-1 and a residual divisor completing the "
            "selected points to the Jacobian target."
        ),
        "panels": [analyze(curve, panel) for panel in panels],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
