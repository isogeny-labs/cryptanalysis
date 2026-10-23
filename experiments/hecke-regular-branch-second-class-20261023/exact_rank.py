"""Exact rational ranks for both paired relation matrices and projections."""
import hashlib
import json
from pathlib import Path

from sage.all import QQ, matrix

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def sha(name):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()


def ranks(data, nonfloor):
    keep = {i for i, point in enumerate(data["column_points"]) if point in nonfloor}
    n = len(data["column_points"])
    rows = data["relation_rows"]
    full = matrix(QQ, [[int(row.get(str(j), 0)) for j in range(n)] for row in rows])
    projected = matrix(QQ, [[int(row.get(str(j), 0)) if j in keep else 0
                             for j in range(n)] for row in rows])
    return {"full_QQ": int(full.rank()), "nonfloor_QQ": int(projected.rank())}


def main():
    audit = read("audit.json")
    assert audit["status"] == "VERIFIED_D215_F6_BRANCH_MATRIX"
    nonfloor = {r["point"] for r in audit["point_records"] if r["endomorphism_conductor"] != 6}
    sources = {"regularized": "data/exp11_class_walk_D215_f6.json",
               "original": "legacy/data/exp11_class_walk_D215_f6.json"}
    result = {key: ranks(read(name), nonfloor) for key, name in sources.items()}
    assert result == {"regularized": {"full_QQ": 112, "nonfloor_QQ": 108},
                      "original": {"full_QQ": 111, "nonfloor_QQ": 108}}
    output = {"status": "PASS_PAIRED_EXACT_RANKS", "ranks": result,
              "source_sha256": {key: sha(name) for key, name in sources.items()},
              "audit_sha256": sha("audit.json"), "script_sha256": sha("exact_rank.py")}
    (HERE / "exact_rank.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
