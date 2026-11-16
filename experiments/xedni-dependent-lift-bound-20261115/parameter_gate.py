"""Exact admission audit for the Lean uniform-cover contradiction.

The eight subgroup orders are frozen by the xedni coefficient-family lift
panel.  `arity` is the number of lifted points, not the subgroup order.
"""

import json


SUBGROUP_ORDERS = (43, 53, 53, 79, 61, 73, 47, 71)


def box_size(radius: int, arity: int) -> int:
    return (4 * radius + 1) ** arity - 1


def max_admitted_radius(q: int, arity: int) -> int:
    lo, hi = 0, q
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if box_size(mid, arity) < q and 2 * mid < q:
            lo = mid
        else:
            hi = mid
    assert box_size(lo, arity) < q and 2 * lo < q
    assert box_size(lo + 1, arity) >= q or 2 * (lo + 1) >= q
    return lo


def main() -> None:
    rows = []
    for q in SUBGROUP_ORDERS:
        for arity in (2, 3):
            radius = max_admitted_radius(q, arity)
            # A representation needs a nonempty torsion label set, so its
            # rank-gap left side T(2c+1)^d is at least one.
            rank_gap_possible = radius > 1
            rows.append({
                "subgroup_order": q,
                "arity": arity,
                "max_radius": radius,
                "short_relation_box_size": box_size(radius, arity),
                "rank_gap_numerically_possible_with_nonempty_torsion": rank_gap_possible,
            })
    print(json.dumps({"schema": "xedni-dependent-lift-parameter-gate-v1",
                      "rows": rows}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
