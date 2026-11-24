"""Verify the fixed public holdout from source with Python 3 and NumPy."""
import ast
import csv
import hashlib
import itertools
import statistics
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
P = 2**31 - 1
Q = 2147505293
WIDTH = 544


def source_points(seed, count):
    seen = set()
    points = []
    for i in itertools.count():
        message = f"m31-smooth-census/{seed}/{i}".encode()
        x = int.from_bytes(hashlib.sha256(message).digest()[:4], "big") & P
        if x == P or x in seen:
            continue
        seen.add(x)
        rhs = (x**3 + 2*x + 14) % P
        y = pow(rhs, (P+1)//4, P)
        if y*y % P == rhs:
            points.append((x, min(y, P-y)))
            if len(points) == count:
                return np.array(points, dtype=np.int64)


def point_sums(points, left, right):
    x, y = points[left].T
    u, v = points[right].T
    double = left == right
    denominator = np.where(double, 2*y, u-x) % P
    numerator = np.where(double, 3*(x*x % P)+2, v-y) % P
    if np.any(denominator == 0):
        raise ValueError("unexpected exceptional chord in fixed panel")
    # Reference powering uses only products of reduced 31-bit field elements.
    inv = np.ones_like(x)
    for bit in bin(P-2)[2:]:
        inv = inv*inv % P
        if bit == "1":
            inv = inv*denominator % P
    slope = numerator*inv % P
    xx = (slope*slope-x-u) % P
    yy = (slope*(x-xx)-y) % P
    return np.column_stack((xx, yy))


def equation_rank(keys, pairs, edges, dimension):
    # Group by complete coordinates before forming differences of source indices.
    order = np.argsort(keys, kind="stable")
    values = keys[order]
    hits = np.flatnonzero(values[1:] == values[:-1])+1
    rows = []
    for end in hits:
        # Consecutive differences span all differences within the group.
        lhs, rhs = pairs[order[end-1]], pairs[order[end]]
        if edges is not None:
            lhs, rhs = edges[lhs].ravel(), edges[rhs].ravel()
        rows.append(np.bincount(lhs, minlength=dimension) -
                    np.bincount(rhs, minlength=dimension))
    if not rows:
        return 0
    matrix = np.array(rows, dtype=np.int64) % Q
    rank = 0
    for col in range(dimension):
        candidates = np.flatnonzero(matrix[rank:, col])
        if not len(candidates):
            continue
        pivot = rank + candidates[0]
        matrix[[rank, pivot]] = matrix[[pivot, rank]]
        matrix[rank] = matrix[rank]*pow(int(matrix[rank,col]), -1, Q) % Q
        tail = matrix[rank+1:]
        tail[:] = (tail-tail[:,col,None]*matrix[rank]) % Q
        rank += 1
        if rank == len(matrix):
            break
    return rank


def main():
    lean = (HERE.parent / "RectangleFree.lean").read_text()
    table = ast.literal_eval(lean.split(":= #", 1)[1].split("def points", 1)[0].strip())
    edges = np.array([(x,64+j) for j,line in enumerate(table) for x in line])
    pairs = np.column_stack(np.triu_indices(WIDTH))
    with (HERE / "timings.csv").open() as file:
        rows = list(csv.DictReader(file))
    records = {(int(r["seed"]), r["sparse"], r["method"]): r for r in rows}
    seeds = range(80000,81024)
    expected = set(itertools.product(seeds, ("False","True"), ("radix","filtered")))
    if set(records) != expected or len(rows) != len(expected):
        raise ValueError("holdout case identity mismatch")
    for seed in seeds:
        sources = source_points(seed, WIDTH)
        for sparse in (False, True):
            basis = point_sums(sources[:132], *edges.T) if sparse else sources
            digest = hashlib.sha256(basis.astype("<u4").tobytes()).hexdigest()
            x,y = point_sums(basis, *pairs.T).T
            rank = equation_rank((x << 31) | y, pairs, edges if sparse else None,
                                 132 if sparse else WIDTH)
            for method in ("radix", "filtered"):
                r = records[seed,str(sparse),method]
                if (digest,rank) != (r["basis_sha256"],int(r["rank"])):
                    raise ValueError(f"mismatch at {seed} {sparse} {method}")
    for sparse in ("False", "True"):
        for method in ("radix", "filtered"):
            arm = [records[s,sparse,method] for s in seeds]
            times = [float(r["wall_ms"]) for r in arm]
            rank = sum(int(r["rank"]) for r in arm)
            print(sparse, method, rank, statistics.median(times), sum(times)/rank)


if __name__ == "__main__":
    main()
