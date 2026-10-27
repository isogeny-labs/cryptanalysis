"""Independent integer point and sparse-rank replay of recovered Hecke rows."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "ecdlp-hecke-floor-rank-20261012" / "data"
EXPECTED = {
    42: "f4a8b964dad70fc8d697d1163f2fa8a963a44882731ae18518e1ace2951c311d",
    70: "efe387fe31c22001b9eeaabe72d920835f80a2300b1aaa4d151015b05d2357ef",
    150: "49e33851a0ed64e470f1693001664c6f76f58aea9e2e65b6974d1618dfa15e06",
    210: "616c4583ac761e9eb965c9ce36b366e3a67b104b881d9eb8a8cee47f2799844e",
}


def add(A, B, p):
    if A is None:
        return B
    if B is None:
        return A
    x1, y1 = A
    x2, y2 = B
    if x1 == x2 and (y1 + y2 + 1) % p == 0:
        return None
    if x1 == x2:
        slope = (3 * x1 * x1 - 2 * x1 - 10) * pow(2 * y1 + 1, -1, p) % p
    else:
        slope = (y2 - y1) * pow(x2 - x1, -1, p) % p
    x3 = (slope * slope + 1 - x1 - x2) % p
    y3 = (-slope * (x3 - x1) - y1 - 1) % p
    return x3, y3


def neg(A, p):
    return None if A is None else (A[0], (-A[1] - 1) % p)


def multiply(k, A, p):
    if k < 0:
        return multiply(-k, neg(A, p), p)
    result = None
    base = A
    while k:
        if k & 1:
            result = add(result, base, p)
        base = add(base, base, p)
        k >>= 1
    return result


def on_curve(A, p):
    x, y = A
    return (y*y + y - x*x*x + x*x + 10*x + 20) % p == 0


def rank_mod(rows, prime):
    pivots = {}
    for source in rows:
        row = {int(k): int(v) % prime for k, v in source.items() if int(v) % prime}
        while row:
            lead = min(row)
            pivot = pivots.get(lead)
            if pivot is None:
                inv = pow(row[lead], -1, prime)
                pivots[lead] = {j: v * inv % prime for j, v in row.items()}
                break
            factor = row[lead]
            for j, v in pivot.items():
                value = (row.get(j, 0) - factor * v) % prime
                if value:
                    row[j] = value
                else:
                    row.pop(j, None)
    return len(pivots)


def one_case(saved):
    conductor = saved["conductor"]
    source = BASE / f"exp11_class_walk_D7_f{conductor}.json"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == EXPECTED[conductor]
    data = json.loads(source.read_text())
    p = int(data["p"])
    points = []
    for encoded in data["column_points"]:
        a, b = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded).groups()
        points.append((int(a), int(b)))
    assert all(on_curve(P, p) for P in points)
    old_rows = [{int(k): int(v) for k, v in r.items()} for r in data["relation_rows"]]
    added = []
    for entry in saved["repeated_fibers"]:
        if not entry["all_in_class"]:
            continue
        assert entry["modular_verified"]
        row = {int(k): int(v) for k, v in entry["row"].items()}
        ell = int(entry["degree"])
        source_index = int(entry["source"])
        a_ell = ell + 1 - sum(row.values())
        assert (ell, a_ell) in ((2, -2), (7, -2))
        neighbors = dict(row)
        neighbors[source_index] = neighbors.get(source_index, 0) + a_ell
        assert all(v >= 0 for v in neighbors.values())
        assert sum(neighbors.values()) == ell + 1
        x_counts = Counter(points[i][0] for i, count in neighbors.items()
                           for _ in range(count))
        assert sorted(x_counts.values()) == sorted(entry["root_multiplicities"])
        acc = None
        for i, count in neighbors.items():
            for _ in range(count):
                acc = add(acc, points[i], p)
        assert acc == multiply(a_ell, points[source_index], p)
        added.append(row)
    assert len(added) == saved["new_rows"]
    ranks = {}
    for prime in (23, 1000000007):
        before = rank_mod(old_rows, prime)
        after = rank_mod(old_rows + added, prime)
        expected = saved["ranks"][f"mod_{prime}"]
        assert (before, after) == (expected["before"], expected["after"])
        ranks[str(prime)] = {"before": before, "after": after}
    return {"conductor": conductor, "new_rows": len(added),
            "group_sums_verified": len(added), "ranks": ranks}


def main():
    replay = json.loads((HERE / "replay.json").read_text())
    cases = [one_case(saved) for saved in replay["cases"]]
    output = {"status": "INDEPENDENT_INTEGER_REPLAY_PASS",
              "total_new_rows": sum(case["new_rows"] for case in cases),
              "cases": cases}
    (HERE / "validation.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
