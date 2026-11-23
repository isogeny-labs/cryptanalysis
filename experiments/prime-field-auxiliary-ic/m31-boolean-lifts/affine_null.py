"""Count affine fits for uniformly placed positive labels on fixed coordinates."""
import json
import sys
from collections import defaultdict
from math import comb


def fits(rows):
    size = len(rows)
    positives = sum(y for _, y in rows)
    assert size == 32 and len({x for x, _ in rows}) == size and positives == 17
    pivots = {}
    checks = []
    for i, (x, y) in enumerate(rows):
        assert 0 <= x < 2**31 and y in (0, 1)
        row, support = x | (1 << 31), 1 << i
        while row:
            pivot = row.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = row, support
                break
            r, s = pivots[pivot]
            row ^= r
            support ^= s
        else:
            checks.append(support)

    # Each left-kernel relation imposes an even parity on its label subset.
    # dp[w][s] counts w chosen positions whose check values XOR to s.
    states = 1 << len(checks)
    dp = [[0] * states for _ in range(positives + 1)]
    dp[0][0] = 1
    actual = 0
    for i, (_, label) in enumerate(rows):
        column = sum(((s >> i) & 1) << j for j, s in enumerate(checks))
        if label:
            actual ^= column
        for w in range(min(i + 1, positives), 0, -1):
            for s, n in enumerate(dp[w-1]):
                dp[w][s ^ column] += n
    assert sum(dp[positives]) == comb(size, positives)
    return len(pivots), int(actual == 0), dp[positives][0]


def main():
    groups = defaultdict(lambda: [0, 0, 0])
    for line in sys.stdin:
        rank, exact, eligible = fits(json.loads(line))
        group = groups[rank]
        group[0] += 1
        group[1] += exact
        group[2] += eligible
    assert sum(group[0] for group in groups.values()) == 256
    print(json.dumps({"labelings_per_fiber": comb(32, 17),
                      "groups": [{"rank": rank, "fibers": n, "actual_fits": real,
                                  "sum_of_fitting_labeling_counts": total}
                                 for rank, (n, real, total) in sorted(groups.items())]}, indent=2))


if __name__ == "__main__":
    main()
