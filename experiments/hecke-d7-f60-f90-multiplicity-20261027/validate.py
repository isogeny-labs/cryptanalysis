"""Independent affine, Fricke, and modular-rank replay of four added rows."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "ecdlp-hecke-floor-rank-20261012" / "data"
KERNEL = HERE.parent / "ecdlp-hecke-floor-rank-20261012" / "tools" / "hecke11.py"
COLLECTOR = HERE.parent / "hecke-multiplicity-collector-20261026" / "multiplicity.py"
EXPECTED = {
    60: "39faa7734979733b3035fb6c25c39b1c0a5e389bd4c54a6c65965da1d8cce434",
    90: "4cb80fb8f8a10a138455dbf6be0c3fb229af6d6367f255000bf06ab9010f38b8",
}
TRACE = {2: -2, 3: -1, 5: 1}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def neg(point, p):
    return None if point is None else (point[0], (-point[1] - 1) % p)


def add(a, b, p):
    if a is None:
        return b
    if b is None:
        return a
    x1, y1 = a
    x2, y2 = b
    if x1 == x2 and (y1+y2+1) % p == 0:
        return None
    if x1 == x2:
        slope = (3*x1*x1 - 2*x1 - 10) * pow(2*y1+1, -1, p) % p
    else:
        slope = (y2-y1) * pow(x2-x1, -1, p) % p
    x3 = (slope*slope + 1 - x1 - x2) % p
    y3 = (-slope*(x3-x1) - y1 - 1) % p
    return x3, y3


def mul(k, point, p):
    if k < 0:
        return mul(-k, neg(point, p), p)
    result = None
    while k:
        if k & 1:
            result = add(result, point, p)
        point = add(point, point, p)
        k >>= 1
    return result


def key(row):
    return tuple(sorted((int(i), int(v)) for i, v in row.items() if v))


def rank_mod(rows, prime):
    pivots = {}
    for source in rows:
        row = {int(i): int(v) % prime for i, v in source.items() if int(v) % prime}
        while row:
            lead = min(row)
            pivot = pivots.get(lead)
            if pivot is None:
                inverse = pow(row[lead], -1, prime)
                pivots[lead] = {i: v * inverse % prime for i, v in row.items()}
                break
            factor = row[lead]
            for i, v in pivot.items():
                updated = (row.get(i, 0) - factor*v) % prime
                if updated:
                    row[i] = updated
                else:
                    row.pop(i, None)
    return len(pivots)


def inspect(case):
    f = case["conductor"]
    path = DATA / f"exp11_class_walk_D7_f{f}.json"
    assert digest(path) == EXPECTED[f] == case["source_sha256"]
    data = json.loads(path.read_text())
    p = int(data["p"])
    ledger_path = HERE / f"ledger_f{f}.json"
    ledger = json.loads(ledger_path.read_text())
    old_rows = data["relation_rows"]
    new_rows = [item["row"] for item in ledger]
    assert len(old_rows) == case["old_rows"]
    assert len(new_rows) == case["reconstructed_rows"]
    old_count = Counter(map(key, old_rows))
    new_count = Counter(map(key, new_rows))
    assert not (old_count - new_count)
    added = list((new_count - old_count).elements())
    assert len(added) == case["new_rows"] == 2
    assert Counter(added) == Counter(key(row) for row in case["additions"])
    points = []
    for encoded in data["column_points"]:
        match = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded)
        assert match is not None
        x, y = map(int, match.groups())
        assert (y*y + y - x*x*x + x*x + 10*x + 20) % p == 0
        points.append((x, y))
    assert len(points) == case["points"]
    by_source_degree = {}
    for item in ledger:
        src, degree = int(item["source"]), int(item["degree"])
        assert (src, degree) not in by_source_degree
        by_source_degree[src, degree] = item
        counts = {int(i): int(v) for i, v in item["row"].items()}
        counts[src] = counts.get(src, 0) + TRACE[degree]
        assert all(v >= 0 for v in counts.values()) and sum(counts.values()) == degree + 1
        total = None
        for i, count in counts.items():
            assert 0 <= i < len(points)
            for _ in range(count):
                total = add(total, points[i], p)
        assert total == mul(TRACE[degree], points[src], p)
    for record in case["repeated_fibers"]:
        assert record["degree"] == 2 and record["status"] == "RECOVERED_REPEATED"
        assert not record["old_complete"] and record["new_complete"]
        assert record["modular_verified"] and record["group_sum_verified"]
        item = by_source_degree[record["source"], record["degree"]]
        assert key(item["row"]) == key(record["row"])
        counts = {int(i): int(v) for i, v in item["row"].items()}
        counts[record["source"]] += TRACE[2]
        x_counts = Counter(points[i][0] for i, count in counts.items() for _ in range(count))
        assert sorted(x_counts.values()) == record["root_multiplicities"] == [1, 2]
    assert len(case["repeated_fibers"]) == 2
    torsion = (16 % p, (-61) % p)
    index = {point: i for i, point in enumerate(points)}
    permutation = {i: index[add(torsion, neg(point, p), p)]
                   for i, point in enumerate(points)}
    reflected = Counter(tuple(sorted((permutation[int(i)], int(v))
                                     for i, v in row.items() if v))
                        for row in new_rows)
    reflected_old = Counter(tuple(sorted((permutation[int(i)], int(v))
                                         for i, v in row.items() if v))
                            for row in old_rows)
    assert reflected_old == old_count
    assert reflected == new_count
    ranks = {}
    for prime in (23, 1000000007):
        before = rank_mod(old_rows, prime)
        after = rank_mod(new_rows, prime)
        assert before == after == case["ranks"][f"mod_{prime}"]["after"]
        ranks[str(prime)] = {"before": before, "after": after}
    return {"conductor": f, "p": p, "old_rows": len(old_rows),
            "reconstructed_rows": len(new_rows), "new_rows": len(added),
            "group_sums_verified": len(new_rows),
            "fricke_closed_before": True, "fricke_closed_after": True,
            "ranks": ranks, "ledger_sha256": digest(ledger_path)}


def main():
    assert digest(KERNEL) == "7e66144e76bf62f7e645d87cc58be2bb0f7cc5e52601665650ef0706a6f715fb"
    assert digest(COLLECTOR) == "89a6cfd5951666587589834d8b8e288aaf0dfc48d9e310df62ef44c48f5bca1e"
    cases = json.loads((HERE / "replay.json").read_text())["cases"]
    assert [case["conductor"] for case in cases] == [60, 90]
    assert all(case["status"] == "REPLAY_PASS" for case in cases)
    results = [inspect(case) for case in cases]
    output = {"status": "INDEPENDENT_D7_F60_F90_PASS", "cases": results,
              "new_rows": sum(item["new_rows"] for item in results),
              "group_sums_verified": sum(item["group_sums_verified"] for item in results)}
    (HERE / "validation.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
