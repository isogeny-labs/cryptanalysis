"""Independent integer row, group, rank, and two-sheet cycle replay."""
import hashlib
import json
import re
from collections import Counter, deque
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "hecke-two-sheet-small-order-20261023" / "data" / "exp11_class_walk_D1295_f6.json"
AUDIT = HERE.parent / "hecke-two-sheet-small-order-20261023" / "audit.json"
EXPECTED = "33854aefc3ba05b93917aa9b2dd0ebaa558c96ba3dd5d500bea3a2d3b7736baa"
P = 11719


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


def components(adj):
    unseen = set(adj)
    groups = []
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        seen = {first}
        queue = deque([first])
        while queue:
            source = queue.popleft()
            for neighbor in adj[source]:
                if neighbor not in seen:
                    unseen.remove(neighbor)
                    seen.add(neighbor)
                    queue.append(neighbor)
        groups.append(seen)
    return groups


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    data = json.loads(SOURCE.read_text())
    audit = json.loads(AUDIT.read_text())
    replay = json.loads((HERE / "replay.json").read_text())
    rebuilt = json.loads((HERE / "reconstructed_rows.json").read_text())
    ledger = json.loads((HERE / "ledger.json").read_text())
    assert replay["status"] == "D1295_MULTIPLICITY_CROSS_REPLAY_PASS"
    assert len(rebuilt) == len(ledger) == len(data["relation_rows"]) == 360
    key = lambda row: tuple(sorted((int(i), int(v)) for i, v in row.items() if v))
    assert Counter(map(key, rebuilt)) == Counter(map(key, data["relation_rows"]))
    assert [key(item["row"]) for item in ledger] == list(map(key, rebuilt))
    pts = []
    for encoded in data["column_points"]:
        a, b = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded).groups()
        pts.append((int(a), int(b)))
    assert len(pts) == 432
    assert len(replay["repeated_records"]) == 1
    record = replay["repeated_records"][0]
    assert record["source"] == 49 and record["degree"] == 2
    assert record["root_multiplicities"] == [1, 2]
    row = {int(i): int(v) for i, v in record["row"].items()}
    counts = dict(row)
    counts[49] = counts.get(49, 0) - 2  # a_2=-2, source term adds two.
    assert all(v >= 0 for v in counts.values()) and sum(counts.values()) == 3
    x_counts = Counter(pts[i][0] for i, count in counts.items() for _ in range(count))
    assert sorted(x_counts.values()) == [1, 2]
    total = None
    for i, count in counts.items():
        for _ in range(count):
            total = add(total, pts[i])
    assert total == neg(add(pts[49], pts[49]))
    ranks = {}
    for prime in (23, 1000000007):
        old = rank_mod(data["relation_rows"], prime)
        new = rank_mod(rebuilt, prime)
        assert old == new == 288
        ranks[str(prime)] = {"archived": old, "reconstructed": new}
    records = audit["point_records"]
    assert len(records) == len(pts)
    c2 = {r["column"] for r in records if r["conductor"] == 2}
    floor = {r["column"] for r in records if r["conductor"] == 6}
    j_by_col = {r["column"]: r["j"] for r in records}
    assert len(c2) == 72 and len(floor) == 144
    d3 = [item for item in ledger if item["degree"] == 3]
    assert len(d3) == 144
    c2rows = {item["source"]: item["row"] for item in d3 if item["source"] in c2}
    assert set(c2rows) == c2
    adj = {}
    for src, raw in c2rows.items():
        projected = {int(i): int(v) for i, v in raw.items() if int(i) not in floor and v}
        assert projected.get(src) == 1 and len(projected) == 3
        assert set(projected.values()) == {1} and set(projected) <= c2
        adj[src] = set(projected) - {src}
    assert all(len(ns) == 2 and all(src in adj[dst] for dst in ns) for src, ns in adj.items())
    groups = components(adj)
    assert sorted(map(len, groups)) == [18] * 4
    jsets = []
    for group in groups:
        jcounts = Counter(j_by_col[i] for i in group)
        assert len(jcounts) == 18 and set(jcounts.values()) == {1}
        jsets.append(set(jcounts))
        rows = [{int(i): int(v) for i, v in c2rows[src].items() if int(i) in group}
                for src in group]
        assert rank_mod(rows, 1000000007) == 16
    matches = sorted((i, j) for i in range(4) for j in range(i + 1, 4) if jsets[i] == jsets[j])
    assert len(matches) == 2 and len({i for pair in matches for i in pair}) == 4
    assert rank_mod([item["row"] for item in d3], 1000000007) == 144
    assert rank_mod([{i: v for i, v in item["row"].items() if int(i) not in floor}
                     for item in d3], 1000000007) == 136
    output = {"status": "INDEPENDENT_INTEGER_SHEET_REPLAY_PASS",
              "rows": len(rebuilt), "repeated_source": 49,
              "repeated_group_sum_verified": True, "ranks": ranks,
              "cycle_lengths": sorted(map(len, groups)), "paired_j_cycle_indices": matches,
              "degree3_projected_kernel_dimension": 8,
              "reconstructed_rows_sha256": hashlib.sha256((HERE / "reconstructed_rows.json").read_bytes()).hexdigest()}
    (HERE / "validation.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
