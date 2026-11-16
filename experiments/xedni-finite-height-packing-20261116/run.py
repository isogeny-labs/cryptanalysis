"""Exact finite lattice controls for the projected height-ball count."""
import itertools
import json
from pathlib import Path

root = Path(__file__).resolve().parent
rows = []
for torsion_order in (1, 2):
    for k in range(17):
        box_size = (2 * k + 1) ** 3
        values = {
            (a + c, b + c, c % torsion_order)
            for a, b, c in itertools.product(range(-k, k + 1), repeat=3)
        }
        # For P=(1,0),(0,1),(1,1), sum ||P_i||=2+sqrt(2)<7/2.
        # The Euclidean packing ratio 2R/delta is thus <7k (delta=1).
        bound = torsion_order * (1 + 7 * k) ** 2
        rows.append({
            "torsion_order": torsion_order,
            "K": k,
            "coefficient_box": box_size,
            "distinct_values": len(values),
            "packing_integer_upper": bound,
            "packing_certifies_collision": bound < box_size,
            "direct_collision": len(values) < box_size,
            "count_within_packing_bound": len(values) <= bound,
        })
assert all(row["count_within_packing_bound"] for row in rows)
assert all(not row["packing_certifies_collision"] or row["direct_collision"] for row in rows)
result = {"schema": "xedni-finite-height-packing-control-v1", "rows": rows}
(root / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"rows": len(rows), "first_certified_K": {
    str(t): min(row["K"] for row in rows if row["torsion_order"] == t
                and row["packing_certifies_collision"])
    for t in (1, 2)}}))
