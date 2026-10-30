"""Independent integer row, group, and modular-rank replay."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "hecke-new-quotient-holdout-20261026" / "data" / "exp11_class_walk_D2631_f6.json"
EXPECTED = "3ea1440f009ad62e135f6211d56d366fda476f84e82e8bb714f4a7962629c193"
P = 23743


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
        slope = (3*x1*x1 - 2*x1 - 10) * pow(2*y1 + 1, -1, P) % P
    else:
        slope = (y2-y1) * pow(x2-x1, -1, P) % P
    x3 = (slope*slope + 1 - x1 - x2) % P
    y3 = (-slope*(x3-x1) - y1 - 1) % P
    return x3, y3


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
                updated = (row.get(j, 0) - factor*v) % prime
                if updated:
                    row[j] = updated
                else:
                    row.pop(j, None)
    return len(pivots)


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    data = json.loads(SOURCE.read_text())
    replay = json.loads((HERE / "replay.json").read_text())
    rebuilt = json.loads((HERE / "reconstructed_rows.json").read_text())
    assert replay["status"] == "D2631_MULTIPLICITY_CROSS_REPLAY_PASS"
    assert len(rebuilt) == len(data["relation_rows"]) == 576
    key = lambda row: tuple(sorted((int(i), int(v)) for i, v in row.items() if v))
    assert Counter(map(key, rebuilt)) == Counter(map(key, data["relation_rows"]))
    pts = []
    for encoded in data["column_points"]:
        a, b = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded).groups()
        pts.append((int(a), int(b)))
    assert len(pts) == 768
    assert len(replay["repeated_records"]) == 1
    record = replay["repeated_records"][0]
    assert record["source"] == 247 and record["degree"] == 3
    assert record["root_multiplicities"] == [1, 1, 2]
    row = {int(i): int(v) for i, v in record["row"].items()}
    counts = dict(row)
    counts[247] = counts.get(247, 0) - 1  # a_3=-1, source term adds one.
    assert all(v >= 0 for v in counts.values()) and sum(counts.values()) == 4
    x_counts = Counter(pts[i][0] for i, count in counts.items() for _ in range(count))
    assert sorted(x_counts.values()) == [1, 1, 2]
    total = None
    for i, count in counts.items():
        for _ in range(count):
            total = add(total, pts[i])
    assert total == neg(pts[247])
    ranks = {}
    for prime in (23, 1000000007):
        old = rank_mod(data["relation_rows"], prime)
        new = rank_mod(rebuilt, prime)
        assert old == new == 480
        ranks[str(prime)] = {"archived": old, "reconstructed": new}
    output = {"status": "INDEPENDENT_INTEGER_REPLAY_PASS",
              "rows": len(rebuilt), "repeated_source": 247,
              "repeated_group_sum_verified": True, "ranks": ranks,
              "reconstructed_rows_sha256": hashlib.sha256((HERE / "reconstructed_rows.json").read_bytes()).hexdigest()}
    (HERE / "validation.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
