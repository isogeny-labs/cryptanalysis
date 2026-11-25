#!/usr/bin/env sage -python
"""Exact four-summand supports of the frozen equal-size S4 bases."""

import itertools
import json

from mixed_equal_yield_cost import ARMS, inputs


def main():
    _, curve, _, bases, base_x, support3, _ = inputs()
    records = []
    for arm in ARMS:
        base = bases[arm]
        assert len(base) == 8 and len(set(base)) == 8
        sums = {sum(row, curve(0))
                for row in itertools.combinations_with_replacement(base, 4)}
        assert curve(0) in sums
        assert len(support3[arm]) == 96
        records.append({
            "arm": arm,
            "signed_base_size": len(base),
            "base_x": base_x[arm],
            "three_sum_nonidentity_support": len(support3[arm]),
            "four_sum_indexed_multisets": 330,
            "four_sum_nonidentity_support": len(sums) - 1,
            "four_sum_identity_present": True,
        })
    assert [row["four_sum_nonidentity_support"] for row in records] == [216, 216, 218, 220, 224]
    print(json.dumps({
        "schema": "four-sum-mixed-support/v1",
        "scope": "retrospective exact support census on existing fixed bases",
        "p": 1009, "r": 1069, "curve": "y^2=x^3+4x+10",
        "horizontal_degree": 5,
        "records": records,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
