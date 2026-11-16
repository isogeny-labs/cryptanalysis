"""Independent checked-Sage replay of the rational-curve control."""
import json
from pathlib import Path

from sage.all import EllipticCurve, QQ

root = Path(__file__).resolve().parent
data = json.loads((root / "curve-result.json").read_text())
assert data["schema"] == "xedni-elliptic-torsion-curve-control-v1"
curve = EllipticCurve(QQ, [0, 0, 0, -1, -2])
point = curve(2, 2)
assert [str(x) for x in curve.a_invariants()] == data["curve_a_invariants"]
assert [str(point[0]), str(point[1])] == data["point"]
assert int(curve.rank(proof=True)) == data["rank"] == 1
assert int(curve.torsion_subgroup().order()) == data["torsion_order"] == 1
assert any(point == g or point == -g for g in curve.gens())

for row in data["rows"]:
    k = row["K"]
    # Independent scalar-interval route: the coefficients of P,2P,3P
    # produce every integer between -6K and 6K, checked by a direct set.
    coefficients = {a + 2 * b + 3 * c
                    for a in range(-k, k + 1)
                    for b in range(-k, k + 1)
                    for c in range(-k, k + 1)}
    assert coefficients == set(range(-6 * k, 6 * k + 1))
    points = {n * point for n in coefficients}
    assert len(points) == len(coefficients) == row["distinct_rational_sums"]
    assert row["coefficient_box"] == (2 * k + 1) ** 3
    assert row["euclidean_packing_upper"] == 1 + 18 * k
    assert row["packing_certifies_collision"] == (
        row["euclidean_packing_upper"] < row["coefficient_box"])
    assert row["direct_collision"] == (
        row["distinct_rational_sums"] < row["coefficient_box"])

print(json.dumps({"status": "PASS", "rows": len(data["rows"]),
                  "curve": "y^2=x^3-x-2"}))
