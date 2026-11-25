"""GF(2) cut ranks and dense tensor-train cost for the Torus7 label table."""
from collections import Counter
from itertools import permutations

from branch_diagram import coordinates


def deposit(value, bits):
    return sum(((value >> j) & 1) << bit for j, bit in enumerate(bits))


def unfolding(table, subset):
    left = [i for i in range(7) if subset >> i & 1]
    right = [i for i in range(7) if i not in left]
    cols = [deposit(j, right) for j in range(1 << len(right))]
    return [sum(((table >> (deposit(i, left) | k)) & 1) << j for j, k in enumerate(cols))
            for i in range(1 << len(left))]


def rank(rows):
    pivots = {}
    for row in rows:
        while row:
            k = row.bit_length() - 1
            if k not in pivots:
                pivots[k] = row
                break
            row ^= pivots[k]
    return len(pivots)


def profile(table):
    ranks = [rank(unfolding(table, s)) for s in range(128)]
    assert all(ranks[s] == ranks[127 ^ s] for s in range(128))
    results = Counter()
    best = None
    for order in permutations(range(7)):
        s, dims = 0, [1]
        for bit in order:
            s |= 1 << bit
            dims.append(ranks[s])
        bits = sum(2*a*b for a, b in zip(dims, dims[1:]))
        results[max(dims), bits] += 1
        best = min(best or (bits, order, dims), (bits, order, dims))
    return ranks, results, best


def distance_to_rank_drop(rows):
    # To acquire a dependence, some nonempty XOR of rows must become zero.
    # Each set bit needs one edit; flipping it in a chosen row achieves this.
    span = [0]
    for row in rows:
        span.extend([v ^ row for v in span])
    return min(v.bit_count() for v in span[1:])



if __name__ == "__main__":
    # AND of all inputs is a nonzero product of seven one-bit functions.
    assert profile(1 << 127)[1] == {(1, 14): 5040}
    _, coordinates_by_key = coordinates()
    table = sum(label << key for key, _, label, _ in coordinates_by_key)
    assert table == 0x5ec55aed5ec7a5051ebd2a65e6d923ee
    ranks, results, best = profile(table)
    for k in range(4):
        print("cut size", k, sorted(Counter(r for s,r in enumerate(ranks) if s.bit_count()==k).items()))
    print("peak rank and dense bits", sorted(results.items()))
    print("best", best)
    distances = Counter(distance_to_rank_drop(unfolding(table, s))
                        for s in range(128) if s.bit_count() == 3)
    print("edits to drop balanced cut rank by one", sorted(distances.items()))
