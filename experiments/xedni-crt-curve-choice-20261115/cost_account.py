"""Exact candidate-probe accounting for the frozen fixed-target CRT replay."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_rows(filename, expected_hash):
    raw = gzip.open(HERE / filename, "rb").read()
    assert digest(raw) == expected_hash, filename
    return [json.loads(line) for line in raw.splitlines()]


def point_key(row):
    return tuple(tuple(point) for point in row["reduced_points"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    protocol_path = HERE / "cost-protocol.json"
    protocol = json.loads(protocol_path.read_text())
    assert protocol["schema"] == "xedni-crt-search-probe-accounting-v1"
    inputs = protocol["inputs"]
    parent = load_rows(inputs["parent_rows"], inputs["parent_rows_uncompressed_sha256"])
    target = load_rows(inputs["target_rows"], inputs["target_rows_uncompressed_sha256"])
    assert len(parent) == 1722 and len(target) == 1849
    parent_by_point = {point_key(row): row for row in parent}
    assert len(parent_by_point) == len(parent)

    names = protocol["counters"]
    counts = {name: 0 for name in names}
    first = None
    visited = set()
    for index, row in enumerate(target, start=1):
        assert row["t"] == [(index - 1) // 43, (index - 1) % 43]
        counts["target_queries"] += 1
        if row["status"] in ("identity", "duplicate"):
            assert not row.get("accepted") and not row.get("rational_relation")
            continue

        key = point_key(row)
        assert key in parent_by_point and key not in visited
        visited.add(key)
        counterpart = parent_by_point[key]
        for field in ("status", "accepted", "reduced_relation", "rational_relation"):
            assert row[field] == counterpart[field], (index, field)
        counts["admissible_pairs"] += 1
        for field, source in (("attempts_7", "attempts_7"),
                              ("attempts_11_strict", "attempts_11_strict"),
                              ("attempts_11_weak", "attempts_11_weak")):
            counts[field] += counterpart.get(source, 0)
        counts["accepted_pairs"] += int(row["accepted"])
        counts["accepted_reduced_relations"] += int(row["accepted"] and row["reduced_relation"])
        counts["accepted_rational_relations"] += int(row["accepted"] and row["rational_relation"])
        if first is None and row["accepted"] and row["rational_relation"]:
            first = {"query_index_one_based": index, "t": row["t"],
                     "recovered_scalar": row["recovered_scalar"],
                     "counters": counts.copy()}

    assert len(visited) == len(parent)
    summary = json.loads((HERE / "result-v2.json").read_text())
    target_summary = json.loads((HERE / "result-target.json").read_text())
    assert counts["attempts_7"] == summary["coefficient_search_attempts"]["at_7"]
    assert counts["attempts_11_strict"] == summary["coefficient_search_attempts"]["at_11_strict"]
    assert counts["attempts_11_weak"] == summary["coefficient_search_attempts"]["at_11_weak"]
    assert counts["accepted_pairs"] == summary["accepted_pairs"]
    assert counts["accepted_rational_relations"] == target_summary["accepted_rational_relations"]
    assert counts["target_queries"] == target_summary["target_queries"]
    assert first is not None and first["recovered_scalar"] == 17

    result = {"schema": "xedni-crt-search-probe-accounting-result-v1", "status": "PASS",
              "protocol_sha256": digest(protocol_path.read_bytes()),
              "source_sha256": digest(Path(__file__).read_bytes()),
              "first_accepted_rational_relation": first,
              "complete_scan": counts}
    output = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.verify:
        assert (HERE / "cost-result.json").read_text() == output
        print("cost accounting PASS")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
