#!/usr/bin/env python3
"""Rank each saved Hecke-degree subset, with and without floor columns."""
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from validate import sparse_rank

HERE = Path(__file__).resolve().parent
MODULUS = 1_000_000_007
CASES = [(60, "conductor_validation.json"),
         (90, "conductor_validation90.json"),
         (210, "conductor_validation210.json")]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_degree(row):
    coefficient_sum = sum(row.values())
    if coefficient_sum == 10:
        return 7
    assert coefficient_sum == 5
    return {4: 2, 5: 3, 7: 5}[len(row)]


def main():
    cases = []
    for f, receipt_name in CASES:
        source = HERE / f"data/exp11_class_walk_D7_f{f}.json"
        receipt_path = HERE / receipt_name
        data = json.loads(source.read_text())
        receipt = json.loads(receipt_path.read_text())
        assert receipt["status"] == "verified" and receipt["source_sha256"] == digest(source)
        degrees = [row_degree(row) for row in data["relation_rows"]]
        assert dict(Counter(degrees)) == {int(k): v for k, v in data["relations_per_l"].items()}
        nonfloor = [i for i, d in enumerate(receipt["column_conductors"]) if d != f]
        remap = {column: index for index, column in enumerate(nonfloor)}
        rows = []
        for size in range(1, len(data["hecke_primes"]) + 1):
            for subset in itertools.combinations(data["hecke_primes"], size):
                selected = [row for row, degree in zip(data["relation_rows"], degrees) if degree in subset]
                projected = [{remap[int(k)]: int(v) for k, v in row.items() if int(k) in remap}
                             for row in selected]
                full_rank = sparse_rank(selected, MODULUS, data["class_size"])
                projected_rank = sparse_rank(projected, MODULUS, len(nonfloor))
                rows.append({"degrees": list(subset), "rows": len(selected),
                             "full_rank": full_rank, "nonfloor_projection_rank": projected_rank,
                             "floor_supported_rowspace_dimension": full_rank - projected_rank})
        assert rows[-1]["full_rank"] == data["rank"]
        cases.append({"f": f, "source_sha256": digest(source),
                      "conductor_receipt_sha256": digest(receipt_path), "subsets": rows})
    result = {"status": "verified", "modulus": MODULUS, "cases": cases}
    (HERE / "degree_subset_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "verified", "subset_counts": {str(c["f"]): len(c["subsets"]) for c in cases}}))


if __name__ == "__main__":
    main()
