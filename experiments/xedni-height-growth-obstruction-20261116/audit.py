"""Independent interval-union replay of the height-growth panel."""
import json
from pathlib import Path

from sage.all import EllipticCurve, QQ

root = Path(__file__).resolve().parent
result = json.loads((root / "result.json").read_text())
protocol = json.loads((root / "PROTOCOL-v2.json").read_text())
assert result["schema"] == "xedni-height-growth-obstruction-result-v2"
curve = EllipticCurve(QQ, [0, 0, 0, -1, -2])
point = curve(2, 2)
assert int(curve.rank(proof=True)) == result["rank"] == 1
assert int(curve.torsion_subgroup().order()) == result["torsion_order"] == 1
assert any(point == g or point == -g for g in curve.gens())
assert [case["n"] for case in result["panel"]] == protocol["n_panel"]

rows_checked = 0
for case in result["panel"]:
    n = case["n"]
    multiple = n * point
    assert multiple != curve(0) and multiple - n * point == curve(0)
    assert abs(float(multiple.height() / point.height()) - n * n) < 1e-8
    assert len(case["rows"]) == n + 1
    for row in case["rows"]:
        k = row["K"]
        # Independent interval-union count of a+nb for |a|,|b|<=K.
        intervals = sorted((n * b - k, n * b + k)
                           for b in range(-k, k + 1))
        count = 0
        end = None
        for lo, hi in intervals:
            if end is None or lo > end + 1:
                count += hi - lo + 1
                end = hi
            elif hi > end:
                count += hi - end
                end = hi
        box = (2 * k + 1) ** 2
        assert count == row["distinct_scalar_sums"]
        assert count == row["derived_distinct_rational_sums"]
        assert box == row["coefficient_box"]
        assert 1 + 4 * n * k == row["packing_upper"]
        assert (count < box) == row["direct_collision"]
        assert (row["packing_upper"] < box) == row["packing_certifies_collision"]
        rows_checked += 1
    assert case["first_collision_K"] == (n + 1) // 2
    assert case["first_packing_K"] == n
    assert case["minimum_nonzero_relation_max_coefficient"] == n

assert rows_checked == 95
print(json.dumps({"status": "PASS", "n_cases": len(result["panel"]),
                  "rows_checked": rows_checked}))
