"""Amended exact scalar-image panel with checked rational-curve premises."""
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, QQ

root = Path(__file__).resolve().parent
protocol = json.loads((root / "PROTOCOL-v2.json").read_text())
curve = EllipticCurve(QQ, [0, 0, 0, -1, -2])
point = curve(2, 2)
rank = int(curve.rank(proof=True))
torsion = int(curve.torsion_subgroup().order())
generator_match = len(curve.gens()) == 1 and (
    point == curve.gens()[0] or point == -curve.gens()[0])
assert rank == torsion == 1 and generator_match
height = point.height()

panel = []
for n in protocol["n_panel"]:
    multiple = n * point
    assert multiple != curve(0)
    assert -n * point + multiple == curve(0)
    height_ratio = multiple.height() / height
    assert abs(float(height_ratio) - n * n) < 1e-8
    rows = []
    for k in range(n + 1):
        scalars = {a + n * b for a, b in
                   itertools.product(range(-k, k + 1), repeat=2)}
        box = (2 * k + 1) ** 2
        packing_upper = 1 + 4 * n * k
        row = {"K": k, "coefficient_box": box,
               "distinct_scalar_sums": len(scalars),
               "derived_distinct_rational_sums": len(scalars),
               "packing_upper": packing_upper,
               "direct_collision": len(scalars) < box,
               "packing_certifies_collision": packing_upper < box}
        assert not row["direct_collision"] or 2 * k >= n
        assert row["packing_certifies_collision"] == (k > 0 and n <= k)
        rows.append(row)
    first_collision = next(row["K"] for row in rows if row["direct_collision"])
    first_packing = next(row["K"] for row in rows
                         if row["packing_certifies_collision"])
    assert first_collision == (n + 1) // 2
    assert first_packing == n
    panel.append({"n": n, "height_ratio": str(height_ratio),
                  "minimum_nonzero_relation_max_coefficient": n,
                  "first_collision_K": first_collision,
                  "first_packing_K": first_packing,
                  "rows": rows})

result = {"schema": "xedni-height-growth-obstruction-result-v2",
          "curve_a_invariants": [str(x) for x in curve.a_invariants()],
          "generator": [str(point[0]), str(point[1])],
          "rank": rank, "torsion_order": torsion,
          "generator_match_up_to_sign": generator_match,
          "generator_canonical_height": str(height),
          "panel": panel}
(root / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": "PASS", "n_cases": len(panel),
                  "rows": sum(len(case["rows"]) for case in panel)}))
