"""Independent affine and integer-row replay of the conductor-6 census."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TRACE = {2: -2, 3: -1}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(row):
    return tuple(sorted((int(i), int(v)) for i, v in row.items() if v))


def neg(point, p):
    return None if point is None else (point[0], (-point[1] - 1) % p)


def add(a, b, p):
    if a is None:
        return b
    if b is None:
        return a
    x1, y1 = a
    x2, y2 = b
    if x1 == x2 and (y1 + y2 + 1) % p == 0:
        return None
    if x1 == x2:
        slope = (3*x1*x1 - 2*x1 - 10) * pow(2*y1 + 1, -1, p) % p
    else:
        slope = (y2-y1) * pow(x2-x1, -1, p) % p
    x3 = (slope*slope + 1 - x1 - x2) % p
    y3 = (-slope*(x3-x1) - y1 - 1) % p
    return x3, y3


def inspect(entry):
    source = ROOT / entry["path"]
    assert digest(source) == entry["sha256"]
    data = json.loads(source.read_text())
    p = int(entry["p"])
    slug = source.stem + "_p" + str(p)
    receipt_path = HERE / "cases" / (slug + ".json")
    ledger_path = HERE / "cases" / (slug + "_ledger.json")
    receipt = json.loads(receipt_path.read_text())
    ledger = json.loads(ledger_path.read_text())
    assert receipt["input"] == entry and receipt["status"] == "PASS"
    assert not receipt["added_rows"] and not receipt["removed_rows"]
    assert not receipt["old_neighbor_mismatches"] and not receipt["bad_complete_rows"]
    assert len(ledger) == receipt["archived_rows"] == receipt["reconstructed_rows"]
    assert Counter(key(row["row"]) for row in ledger) == Counter(
        key(row) for row in data["relation_rows"])
    points = []
    for encoded in data["column_points"]:
        match = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded)
        assert match is not None
        x, y = map(int, match.groups())
        assert (y*y + y - x*x*x + x*x + 10*x + 20) % p == 0
        points.append((x, y))
    assert len(points) == entry["points"]
    by_source_degree = {}
    for item in ledger:
        source_index = int(item["source"])
        degree = int(item["degree"])
        assert (source_index, degree) not in by_source_degree
        assert degree in TRACE and 0 <= source_index < len(points)
        by_source_degree[source_index, degree] = item
        counts = {int(i): int(v) for i, v in item["row"].items()}
        counts[source_index] = counts.get(source_index, 0) + TRACE[degree]
        assert all(count >= 0 for count in counts.values())
        assert sum(counts.values()) == degree + 1
        total = None
        for i, count in counts.items():
            assert 0 <= i < len(points)
            for _ in range(count):
                total = add(total, points[i], p)
        target = neg(points[source_index], p)
        if degree == 2:
            target = add(target, target, p)
        assert total == target, (slug, source_index, degree)
    for record in receipt["repeated_records"]:
        assert record["status"] == "RECOVERED_REPEATED"
        assert record["old_complete"] and record["new_complete"]
        item = by_source_degree[record["source"], record["degree"]]
        counts = {int(i): int(v) for i, v in item["row"].items()}
        counts[record["source"]] = counts.get(record["source"], 0) + TRACE[record["degree"]]
        x_counts = Counter(points[i][0] for i, count in counts.items() for _ in range(count))
        assert sorted(x_counts.values()) == record["root_multiplicities"]
    return {"input": entry["path"], "p": p, "rows": len(ledger),
            "group_sums_verified": len(ledger),
            "repeated_fibers_verified": len(receipt["repeated_records"]),
            "ledger_sha256": digest(ledger_path)}


def main():
    inputs_path = HERE / "inputs.json"
    inputs = json.loads(inputs_path.read_text())
    summary = json.loads((HERE / "summary.json").read_text())
    assert summary["status"] == "PASS" and summary["inputs_sha256"] == digest(inputs_path)
    for source_entry in inputs["sources"]:
        assert digest(ROOT / source_entry["path"]) == source_entry["sha256"]
    results = [inspect(entry) for entry in inputs["matrices"]]
    assert len(results) == summary["case_count"] == 11
    assert sum(row["repeated_fibers_verified"] for row in results) == summary["repeated_fibers"] == 3
    assert sum(row["rows"] for row in results) == sum(row["group_sums_verified"] for row in results)
    output = {"status": "INDEPENDENT_INTEGER_CENSUS_PASS",
              "case_count": len(results), "total_rows": sum(row["rows"] for row in results),
              "repeated_fibers": 3, "cases": results,
              "inputs_sha256": digest(inputs_path)}
    (HERE / "validation.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
