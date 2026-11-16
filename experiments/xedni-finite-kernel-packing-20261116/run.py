"""Exact finite-kernel and omitted-kernel packing controls."""
from collections import defaultdict
import itertools
import json
from pathlib import Path


def le_sqrt2(a: int, b: int) -> bool:
    assert a >= 0 and b >= 0
    return a * a <= 2 * b * b


def within_bound(count: int, torsion: int, k: int) -> bool:
    # T * (1 + 4 sqrt(2) K)^2 = T * (1 + 32 K^2 + 8 sqrt(2) K).
    base = torsion * (1 + 32 * k * k)
    return count <= base or le_sqrt2(count - base, 8 * torsion * k)


def bound_below_box(box: int, torsion: int, k: int) -> bool:
    base = torsion * (1 + 32 * k * k)
    remainder = box - base
    return remainder > 0 and not le_sqrt2(remainder, 8 * torsion * k)


rows = []
for torsion in (1, 2, 3, 4):
    for k in range(17):
        values = {
            (a + c, b + c, c % torsion)
            for a, b, c in itertools.product(range(-k, k + 1), repeat=3)
        }
        fibers = defaultdict(set)
        for x, y, residue in values:
            fibers[(x, y)].add(residue)
        projected_count = len(fibers)
        assert projected_count == 12 * k * k + 6 * k + 1
        max_fiber = max(map(len, fibers.values()))
        box = (2 * k + 1) ** 3
        row = {
            "K": k,
            "kernel_card": torsion,
            "coefficient_box": box,
            "distinct_values": len(values),
            "projected_values": projected_count,
            "maximum_observed_fiber": max_fiber,
            "fiber_bound_holds": len(values) <= torsion * projected_count,
            "euclidean_bound_holds": within_bound(len(values), torsion, k),
            "packing_certifies_collision": bound_below_box(box, torsion, k),
            "direct_collision": len(values) < box,
        }
        assert max_fiber <= torsion
        assert row["fiber_bound_holds"] and row["euclidean_bound_holds"]
        assert not row["packing_certifies_collision"] or row["direct_collision"]
        rows.append(row)

# Omitting a kernel bound fails already for a one-dimensional projection of Z^2.
omitted_kernel = []
for k in range(1, 17):
    values = {(0, n) for n in range(-k, k + 1)}
    projected = {x for x, _ in values}
    row = {"K": k, "distinct_values": len(values),
           "projected_values": len(projected),
           "claimed_kernel_card": 1,
           "false_fiber_bound": len(values) <= len(projected)}
    assert not row["false_fiber_bound"]
    omitted_kernel.append(row)

root = Path(__file__).resolve().parent
result = {"schema": "xedni-finite-kernel-packing-control-v1",
          "finite_kernel_rows": rows,
          "omitted_kernel_counterexamples": omitted_kernel}
(root / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"finite_rows": len(rows), "counterexamples": len(omitted_kernel),
                  "first_certified_K": {
                      str(t): min(row["K"] for row in rows if row["kernel_card"] == t
                                  and row["packing_certifies_collision"])
                      for t in (1, 2, 3, 4)}}))
