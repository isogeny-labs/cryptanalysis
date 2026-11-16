"""Exact integer-lattice control of the Euclidean packing threshold."""
import itertools
import json
from pathlib import Path


def le_sqrt2(a: int, b: int) -> bool:
    """Decide a <= b sqrt(2) for nonnegative integers exactly."""
    assert a >= 0 and b >= 0
    return a * a <= 2 * b * b


def bound_dominates(count: int, torsion: int, k: int) -> bool:
    # T*(1+4 sqrt(2) K)^2 = T*(1+32K^2+8 sqrt(2) K).
    base = torsion * (1 + 32 * k * k)
    return count <= base or le_sqrt2(count - base, 8 * torsion * k)


def bound_below_box(box: int, torsion: int, k: int) -> bool:
    base = torsion * (1 + 32 * k * k)
    remainder = box - base
    return remainder > 0 and not le_sqrt2(remainder, 8 * torsion * k)


rows = []
for torsion in (1, 2):
    for k in range(21):
        vectors = {
            (a + c, b + c, c % torsion)
            for a, b, c in itertools.product(range(-k, k + 1), repeat=3)
        }
        count = len(vectors)
        box = (2 * k + 1) ** 3
        expected_count = (12 * k * k + 6 * k + 1) if torsion == 1 else (
            1 if k == 0 else 24 * k * k + 2)
        assert count == expected_count
        row = {
            "torsion_order": torsion,
            "K": k,
            "coefficient_box": box,
            "distinct_values": count,
            "independent_count_formula": expected_count,
            "radius_squared": 8 * k * k,
            "minimum_projected_norm_squared": 1,
            "euclidean_bound_holds": bound_dominates(count, torsion, k),
            "packing_certifies_collision": bound_below_box(box, torsion, k),
            "direct_collision": count < box,
            "integer_upper": torsion * (1 + 6 * k) ** 2,
        }
        assert row["euclidean_bound_holds"]
        assert count <= row["integer_upper"]
        assert not row["packing_certifies_collision"] or row["direct_collision"]
        rows.append(row)

result = {"schema": "xedni-euclidean-packing-control-v1", "rows": rows}
root = Path(__file__).resolve().parent
(root / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"rows": len(rows), "first_certified_K": {
    str(t): min(row["K"] for row in rows
                if row["torsion_order"] == t and row["packing_certifies_collision"])
    for t in (1, 2)}}))
