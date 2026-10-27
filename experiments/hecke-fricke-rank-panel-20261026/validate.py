"""Independent integer replay of the conductor-42 Fricke partner."""
import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "ecdlp-hecke-floor-rank-20261012" / "data" / "exp11_class_walk_D7_f42.json"
P = 3187
T = (16, -61 % P)


def neg(A):
    return None if A is None else (A[0], (-A[1] - 1) % P)


def add(A, B):
    if A is None:
        return B
    if B is None:
        return A
    x1, y1 = A
    x2, y2 = B
    if x1 == x2 and (y1 + y2 + 1) % P == 0:
        return None
    if x1 == x2:
        slope = ((3 * x1 * x1 - 2 * x1 - 10) * pow(2 * y1 + 1, -1, P)) % P
    else:
        slope = ((y2 - y1) * pow(x2 - x1, -1, P)) % P
    x3 = (slope * slope + 1 - x1 - x2) % P
    y3 = (-slope * (x3 - x1) - y1 - 1) % P
    return x3, y3


def on_curve(A):
    if A is None:
        return True
    x, y = A
    return (y * y + y - x * x * x + x * x + 10 * x + 20) % P == 0


def rank_mod(rows, prime):
    pivots = {}
    for source in rows:
        row = {j: v % prime for j, v in enumerate(source) if v % prime}
        while row:
            k = min(row)
            pivot = pivots.get(k)
            if pivot is None:
                inv = pow(row[k], -1, prime)
                pivots[k] = {j: v * inv % prime for j, v in row.items()}
                break
            scale = row[k]
            for j, v in pivot.items():
                updated = (row.get(j, 0) - scale * v) % prime
                if updated:
                    row[j] = updated
                else:
                    row.pop(j, None)
    return len(pivots)


def main():
    data = json.loads(DATA.read_text())
    diagnostic = json.loads((HERE / "diagnostic.json").read_text())
    augmented = json.loads((HERE / "augmented.json").read_text())
    pts = []
    for encoded in data["column_points"]:
        a, b = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded).groups()
        pts.append((int(a), int(b)))
    assert len(pts) == 160 and all(on_curve(A) for A in pts)
    index = {A: i for i, A in enumerate(pts)}
    perm = [index[add(T, neg(A))] for A in pts]
    assert all(perm[perm[i]] == i and perm[i] != i for i in range(160))
    assert perm[88] == 67
    source = {int(k): int(v) for k, v in data["relation_rows"][74].items()}
    # a_7=-2, so the source-row coefficient 3 contains one neighbor and
    # two copies of its source term.
    assert sum(source.values()) == 10 and source[88] == 3
    neighbor_counts = dict(source)
    neighbor_counts[88] -= 2
    assert sum(neighbor_counts.values()) == 8
    mapped_neighbors = [pts[perm[i]] for i, count in neighbor_counts.items()
                        for _ in range(count)]
    assert all(on_curve(A) for A in mapped_neighbors)
    acc = None
    for A in mapped_neighbors:
        acc = add(acc, A)
    assert acc == add(neg(pts[67]), neg(pts[67]))
    recovered = {}
    for A in mapped_neighbors:
        j = index[A]
        recovered[j] = recovered.get(j, 0) + 1
    recovered[67] = recovered.get(67, 0) + 2
    saved = {int(k): int(v) for k, v in diagnostic["recovered_row"].items()}
    assert recovered == saved
    rows = [{int(k): int(v) for k, v in r.items()} for r in data["relation_rows"]]
    rows.append(recovered)
    pairs = [(i, perm[i]) for i in range(160) if i < perm[i]]
    rank_results = {}
    for prime in (23, 1000000007):
        full = [[r.get(i, 0) for i in range(160)] for r in rows]
        plus = [[r.get(i, 0) + r.get(j, 0) for i, j in pairs] for r in rows]
        minus = [[r.get(i, 0) - r.get(j, 0) for i, j in pairs] for r in rows]
        got = {"full": rank_mod(full, prime), "plus": rank_mod(plus, prime),
               "minus": rank_mod(minus, prime)}
        assert got == augmented["ranks"][f"mod_{prime}"]
        rank_results[str(prime)] = got
    output = {"status": "INDEPENDENT_AFFINE_AND_RANK_REPLAY_PASS",
              "recovered_row": {str(k): v for k, v in sorted(recovered.items())},
              "group_sum_verified": True, "ranks": rank_results}
    (HERE / "validation.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
