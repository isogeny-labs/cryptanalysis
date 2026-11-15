"""Check canonical heights, finite cover, and reduction on a frozen E/Q panel."""

import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, RealField, ZZ

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def point_record(point):
    if point.is_zero():
        return {"identity": True}
    return {"x": str(point[0]), "y": str(point[1])}


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    curve_spec = protocol["curve"]
    sample_spec = protocol["sample"]
    height_spec = protocol["height"]
    precision = height_spec["precision_bits"]
    RR = RealField(precision)
    E = EllipticCurve(QQ, curve_spec["weierstrass_a_invariants"])
    P = E(curve_spec["point"])
    p = curve_spec["reduction_prime"]
    assert ZZ(E.discriminant()) % p != 0
    F = GF(p)
    Ered = E.change_ring(F)

    def reduce_point(point):
        if point.is_zero():
            return Ered(0)
        assert ZZ(point[0].denominator()) % p != 0
        assert ZZ(point[1].denominator()) % p != 0
        return Ered([F(point[0]), F(point[1])])

    multipliers = sample_spec["lifted_point_multipliers"]
    points = [m * P for m in multipliers]
    reduced_points = [reduce_point(point) for point in points]
    radius = sample_spec["coefficient_radius"]
    box = list(itertools.product(range(-radius, radius + 1), repeat=len(points)))
    assert len(box) == protocol["frozen_controls"]["coefficient_box_count"]

    relation = sample_spec["known_relation"]
    assert any(relation)
    assert sum((a * point for a, point in zip(relation, points)), E(0)).is_zero()

    scalar_values = set()
    reduction_checks = 0
    for coeff in box:
        scalar = sum(a * m for a, m in zip(coeff, multipliers))
        lifted = sum((a * point for a, point in zip(coeff, points)), E(0))
        assert lifted == scalar * P
        reduced = reduce_point(lifted)
        from_reduced = sum((a * point for a, point in zip(coeff, reduced_points)), Ered(0))
        assert reduced == from_reduced
        scalar_values.add(scalar)
        reduction_checks += 1
    assert len(scalar_values) == protocol["frozen_controls"]["distinct_sum_count"]
    assert reduction_checks == len(box)

    hP = RR(P.height(precision=precision, algorithm=height_spec["primary_algorithm"]))
    hP_sage = RR(P.height(precision=precision, algorithm=height_spec["crosscheck_algorithm"]))
    cross_residual = abs(hP - hP_sage)
    assert hP > 0
    assert cross_residual < RR(height_spec["crosscheck_absolute_cap"])
    heights = {k: RR((k * P).height(precision=precision,
                                    algorithm=height_spec["primary_algorithm"]))
               for k in scalar_values}
    quadratic_residual = max(abs(heights[k] - k * k * hP) for k in scalar_values)
    assert quadratic_residual < RR(height_spec["quadratic_residual_cap"])

    pairing_residual = RR(0)
    for i, mi in enumerate(multipliers):
        for j, mj in enumerate(multipliers):
            hi = RR(points[i].height(precision=precision))
            hj = RR(points[j].height(precision=precision))
            hij = RR((points[i] + points[j]).height(precision=precision))
            pairing = (hij - hi - hj) / 2
            pairing_residual = max(pairing_residual, abs(pairing - mi * mj * hP))
    assert pairing_residual < RR(height_spec["quadratic_residual_cap"])

    max_input_height = max(RR(point.height(precision=precision)) for point in points)
    max_sum_height = max(heights.values())
    paper_triangle_bound = len(points) ** 2 * radius ** 2 * max_input_height
    assert max_sum_height <= paper_triangle_bound + RR(height_spec["quadratic_residual_cap"])

    torsion_order = int(E.torsion_order())
    center_count = len(scalar_values)
    assert center_count * torsion_order < len(box)
    # Radius zero: each distinct sum itself is a center. Positive minimum
    # canonical height of a difference checks metric separation on this set.
    differences = {abs(a - b) for a in scalar_values for b in scalar_values if a != b}
    min_difference_height = min(RR((d * P).height(precision=precision)) for d in differences)
    assert min_difference_height > 0

    result = {
        "schema": "xedni-rational-height-cover-result-v1",
        "status": "PASS",
        "protocol_sha256": sha(HERE / "protocol.json"),
        "source_sha256": sha(HERE / "run.py"),
        "sage_runtime_sha256": sha(HERE / "sage-runtime-info.json"),
        "curve_discriminant": str(E.discriminant()),
        "generator": point_record(P),
        "reduction_prime": p,
        "reduced_curve_order": int(Ered.cardinality()),
        "reduced_point_order": int(reduce_point(P).order()),
        "rational_torsion_order": torsion_order,
        "coefficient_box_count": len(box),
        "distinct_rational_sum_count": center_count,
        "distinct_scalar_range": [min(scalar_values), max(scalar_values)],
        "reduction_checks": reduction_checks,
        "known_relation": relation,
        "metric_cover_radius": 0,
        "metric_center_count": center_count,
        "label_count": torsion_order,
        "strict_count_condition": center_count * torsion_order < len(box),
        "canonical_height_P": str(hP),
        "canonical_height_P_sage": str(hP_sage),
        "height_crosscheck_residual": str(cross_residual),
        "quadratic_height_max_residual": str(quadratic_residual),
        "pairing_max_residual": str(pairing_residual),
        "max_input_height": str(max_input_height),
        "max_sum_height": str(max_sum_height),
        "triangle_height_bound": str(paper_triangle_bound),
        "minimum_nonzero_difference_height": str(min_difference_height),
        "points": [point_record(point) for point in points],
    }
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
