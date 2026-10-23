"""Independent point-identity comparison of the two saved relation matrices."""
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REG = "data/exp11_class_walk_D215_f6.json"
OLD = "legacy/data/exp11_class_walk_D215_f6.json"


def read(name):
    return json.loads((HERE / name).read_text())


def sha(name):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()


def labeled_rows(data):
    points = data["column_points"]
    return Counter(tuple(sorted((points[int(k)], int(v)) for k, v in row.items() if v))
                   for row in data["relation_rows"])


def rank_mod(rows, modulus):
    pivots = {}
    for row in rows:
        current = {int(k): int(v) % modulus for k, v in row.items() if int(v) % modulus}
        while current:
            col = min(current)
            if col not in pivots:
                inverse = pow(current[col], -1, modulus)
                pivots[col] = {k: v * inverse % modulus for k, v in current.items()}
                break
            a = current[col]
            for k, v in pivots[col].items():
                w = (current.get(k, 0) - a * v) % modulus
                if w:
                    current[k] = w
                else:
                    current.pop(k, None)
    return len(pivots)


def main():
    protocol = read("producer_protocol.json")
    for name, digest in protocol["input_sha256"].items():
        assert sha(name) == digest, name
    new, old = read(REG), read(OLD)
    assert all((d["DK"], d["f"], d["p"], d["u"], d["hecke_primes"]) ==
               (-215, 6, 2131, 28, [2, 3]) for d in (new, old))
    new_points, old_points = set(new["column_points"]), set(old["column_points"])
    added_points = sorted(new_points - old_points)
    removed_points = sorted(old_points - new_points)
    assert added_points == ["(16 : 60 : 1)"] and not removed_points
    new_rows, old_rows = labeled_rows(new), labeled_rows(old)
    added_rows, removed_rows = new_rows - old_rows, old_rows - new_rows
    assert not removed_rows and sum(added_rows.values()) == 2
    assert all(any(point == added_points[0] for point, _ in row) for row in added_rows)
    ranks = {str(q): {"regularized": rank_mod(new["relation_rows"], q),
                      "original": rank_mod(old["relation_rows"], q)}
             for q in (11, 23, 1000000007, 2147483647)}
    assert all(v == {"regularized": 112, "original": 111} for v in ranks.values())
    audit = read("audit.json")
    assert audit["status"] == "VERIFIED_D215_F6_BRANCH_MATRIX"
    nonfloor = {r["point"] for r in audit["point_records"]
                if r["endomorphism_conductor"] != 6}
    projected = {}
    for label, data in (("regularized", new), ("original", old)):
        keep = {i for i, point in enumerate(data["column_points"]) if point in nonfloor}
        projected[label] = [{k: v for k, v in row.items() if int(k) in keep}
                            for row in data["relation_rows"]]
    projected_ranks = {str(q): {label: rank_mod(rows, q) for label, rows in projected.items()}
                       for q in (11, 23, 1000000007, 2147483647)}
    assert all(v == {"regularized": 108, "original": 108} for v in projected_ranks.values())
    assert (new["class_size"], old["class_size"], new["relations"], old["relations"]) == (168, 167, 140, 138)
    result = {"status": "PASS_SECOND_CLASS_BRANCH_DELTA",
              "protocol_sha256": sha("producer_protocol.json"),
              "regularized_sha256": sha(REG), "original_sha256": sha(OLD),
              "added_points": added_points, "removed_points": removed_points,
              "preserved_original_rows": sum(old_rows.values()),
              "added_rows": [{"multiplicity": count, "terms": list(row)} for row, count in sorted(added_rows.items())],
              "removed_rows": [], "ranks": ranks,
              "projected_ranks": projected_ranks, "audit_sha256": sha("audit.json"),
              "candidate_id": None, "timing_claim": None}
    (HERE / "comparison.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "added_rows"}, sort_keys=True))


if __name__ == "__main__":
    main()
