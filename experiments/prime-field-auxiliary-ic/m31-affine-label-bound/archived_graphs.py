"""Check signed-graph ranks and decompose stopping counts on the six saved traces."""
from collections import Counter
from fractions import Fraction

from archived_loops import observations


def signed_rank(rows):
    adjacency = [[] for _ in range(17)]
    for row in rows:
        i, j = row["i"], row["j"]
        parity = -row["si"] * row["sj"]
        adjacency[i].append((j, parity))
        adjacency[j].append((i, parity))

    # In a connected component one column value determines the others.
    # An inconsistent sign around a cycle forces that value to zero in odd characteristic.
    values = {}
    nullity = 0
    for start in range(len(adjacency)):
        if start in values:
            continue
        values[start] = 1
        stack = [start]
        balanced = True
        while stack:
            i = stack.pop()
            for j, parity in adjacency[i]:
                value = parity * values[i]
                if j in values:
                    balanced &= values[j] == value
                else:
                    values[j] = value
                    stack.append(j)
        nullity += balanced
    return len(adjacency) - nullity


def trace(seed, arm):
    data, rows = observations(arm, seed)
    ranks = [signed_rank(rows[:k]) for k in range(1, len(rows) + 1)]
    assert ranks == [*range(1, len(rows)), len(rows) - 1]
    assert ranks[-1] == data["rank"]
    # A row belongs to the unique dependency iff deleting it preserves rank.
    support = [r for i, r in enumerate(rows) if signed_rank(rows[:i] + rows[i+1:]) == ranks[-1]]
    assert support == [r for r, w in zip(rows, data["weights"], strict=True) if w % 2147505293]
    degree = Counter(r[c] for r in support for c in ("i", "j"))
    print(seed, arm, "rows", len(rows), "support", len(support), "vertex_degrees", sorted(degree.values()))
    return len(rows), Fraction(data["queries"], len(rows)), data["queries"]


if __name__ == "__main__":
    for seed in range(3):
        nr, nq, nt = trace(seed, "v2_chain")
        br, bq, bt = trace(seed, "v2_batch")
        row_ratio = Fraction(nr, br)
        spacing_ratio = nq / bq
        assert row_ratio * spacing_ratio == Fraction(nt, bt)
        print("accepted-row ratio", float(row_ratio), "queries/accepted-row ratio", float(spacing_ratio))
