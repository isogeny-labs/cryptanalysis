"""Coupled Monte Carlo for first row dependence under iid uniform group points."""
import math
import random
from statistics import mean, stdev

ORDER = 2147505293
WIDTH = 17
TRIALS = 8192
ROWS = [(i, i, 1) for i in range(2 * WIDTH)] + [
    (i, j, sign)
    for j in range(2 * WIDTH) for i in range(j) for sign in (-1, 1)
]


def dependent(pivots, label):
    i, j, sign = label
    row = {i: 1}
    row[j] = row.get(j, 0) + sign
    while row:
        col = min(row)
        value = row[col]
        if col not in pivots:
            inverse = pow(value, -1, ORDER)
            pivots[col] = {k: v * inverse % ORDER for k, v in row.items()}
            return False
        for k, v in pivots[col].items():
            rem = (row.get(k, 0) - value * v) % ORDER
            if rem:
                row[k] = rem
            else:
                row.pop(k, None)
    return True


def trial(rng):
    # Sampling the order of first visits integrates out repeated and missed points.
    labels = ROWS.copy()
    rng.shuffle(labels)
    pivots = [{}, {}, {}]
    clocks = [None] * 3
    time = 0.0
    for seen, label in enumerate(labels):
        time += ORDER / (2 * (len(labels) - seen))
        i, j, _ = label
        for arm, eligible in enumerate((j < WIDTH, j < WIDTH or i >= WIDTH, True)):
            if eligible and clocks[arm] is None and dependent(pivots[arm], label):
                clocks[arm] = time
        if all(t is not None for t in clocks):
            assert clocks[2] <= clocks[1] <= clocks[0]
            return clocks
    raise AssertionError("missing dependence")


def main():
    assert len(ROWS) == len(set(ROWS)) == 1156
    rng = random.Random(2026112403)
    results = [trial(rng) for _ in range(TRIALS)]
    for name, times in zip(("one", "pooled", "mixed"), zip(*results)):
        print(name, "mean queries", round(mean(times)), "MC SE", round(stdev(times) / math.sqrt(TRIALS)))
    savings = [b - c for _, b, c in results]
    print("mixed earlier", sum(s > 0 for s in savings), "/", TRIALS)
    print("paired mean savings", round(mean(savings)), "MC SE", round(stdev(savings) / math.sqrt(TRIALS)))


if __name__ == "__main__":
    main()
