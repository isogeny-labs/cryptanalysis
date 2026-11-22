"""Checked-Sage rational-curve control for the torsion-kernel packing bridge."""
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, QQ

root = Path(__file__).resolve().parent
curve = EllipticCurve(QQ, [0, 0, 0, -1, -2])
point = curve(2, 2)
rank = int(curve.rank(proof=True))
gens = list(curve.gens())
torsion_order = int(curve.torsion_subgroup().order())
generator_match = len(gens) == 1 and (point == gens[0] or point == -gens[0])
assert rank == 1 and generator_match and torsion_order == 1

height = point.height()
height2 = (2 * point).height()
height3 = (3 * point).height()
assert abs(float(height2 / height) - 4) < 1e-9
assert abs(float(height3 / height) - 9) < 1e-9

rows = []
for k in range(5):
    sums = {
        a * point + b * (2 * point) + c * (3 * point)
        for a, b, c in itertools.product(range(-k, k + 1), repeat=3)
    }
    box = (2 * k + 1) ** 3
    count = len(sums)
    assert count == 12 * k + 1
    bound = 1 + 18 * k  # d=1, T=1, B=3 sqrt(mu), delta=sqrt(mu), r=3.
    assert count <= bound
    rows.append({"K": k, "coefficient_box": box,
                 "distinct_rational_sums": count,
                 "euclidean_packing_upper": bound,
                 "packing_certifies_collision": bound < box,
                 "direct_collision": count < box})
assert rows[1]["packing_certifies_collision"]
result = {
    "schema": "xedni-elliptic-torsion-curve-control-v1",
    "curve_a_invariants": [str(x) for x in curve.a_invariants()],
    "point": [str(point[0]), str(point[1])],
    "rank": rank,
    "torsion_order": torsion_order,
    "point_is_generator_up_to_sign": generator_match,
    "canonical_height": str(height),
    "double_height_ratio": str(height2 / height),
    "triple_height_ratio": str(height3 / height),
    "rows": rows,
}
(root / "curve-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": "PASS", "rank": rank,
                  "torsion_order": torsion_order, "rows": len(rows)}))
