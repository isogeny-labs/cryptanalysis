"""Check the frozen rational-curve cover with centers built before sampling."""

import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, RealField, ZZ

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    spec = json.loads((HERE / "protocol-v2.json").read_text())
    curve = spec["curve"]
    sample = spec["sample"]
    predictions = spec["frozen_predictions"]
    E = EllipticCurve(QQ, curve["weierstrass_a_invariants"])
    P = E(curve["point"])
    p = curve["reduction_prime"]
    assert ZZ(E.discriminant()) % p != 0
    Ered = E.change_ring(GF(p))

    def reduce(point):
        if point.is_zero():
            return Ered(0)
        assert ZZ(point[0].denominator()) % p != 0
        assert ZZ(point[1].denominator()) % p != 0
        return Ered([Ered.base_ring()(point[0]), Ered.base_ring()(point[1])])

    multipliers = sample["lifted_point_multipliers"]
    L = sample["coefficient_radius"]
    bound = L * sum(abs(m) for m in multipliers)
    assert bound == predictions["center_scalar_bound"]

    # The analytic range and centers are fixed before coefficient enumeration.
    center_scalars = range(-bound, bound + 1)
    centers = {k * P for k in center_scalars}
    assert len(centers) == predictions["center_count"]
    assert len(centers) == 2 * bound + 1
    assert E.torsion_order() == spec["cover"]["torsion_label_count"]

    points = [m * P for m in multipliers]
    red_points = [reduce(point) for point in points]
    relation = sample["known_relation"]
    assert len(relation) == len(points) and any(relation)
    assert sum((a * point for a, point in zip(relation, points)), E(0)).is_zero()

    box = itertools.product(range(-L, L + 1), repeat=len(points))
    observed = set()
    covered = 0
    reduction_checks = 0
    for coeff in box:
        k = sum(a * m for a, m in zip(coeff, multipliers))
        point = sum((a * q for a, q in zip(coeff, points)), E(0))
        assert point == k * P and point in centers
        assert reduce(point) == sum((a * q for a, q in zip(coeff, red_points)), Ered(0))
        observed.add(point)
        covered += 1
        reduction_checks += 1
    assert covered == predictions["coefficient_box_count"]
    assert reduction_checks == predictions["coefficient_box_count"]
    assert observed == centers
    assert len(centers) < covered

    RR = RealField(spec["height_precision_bits"])
    hP = RR(P.height(precision=RR.precision(), algorithm="pari"))
    assert hP > 0
    min_gap = min(RR((d * P).height(precision=RR.precision(), algorithm="pari"))
                  for d in range(1, 2 * bound + 1))
    assert min_gap > 0

    print(json.dumps({
        "schema": "xedni-rational-height-cover-result-v2",
        "status": "PASS",
        "protocol_sha256": digest(HERE / "protocol-v2.json"),
        "source_sha256": digest(HERE / "run_v2.py"),
        "sage_runtime_sha256": digest(HERE / "sage-runtime-info-v2.json"),
        "center_construction_order": "before_coefficient_enumeration",
        "center_scalar_bound": bound,
        "center_count": len(centers),
        "coefficient_box_count": covered,
        "distinct_sum_count": len(observed),
        "covered_sum_count": covered,
        "reduction_checks": reduction_checks,
        "known_relation": relation,
        "rational_torsion_order": int(E.torsion_order()),
        "metric_cover_radius": 0,
        "canonical_height_P": str(hP),
        "minimum_positive_center_difference_height": str(min_gap),
        "strict_count_condition": len(centers) < covered,
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
