"""Exact degree-3 projection kernel after the frozen rank forecast failed."""
from functools import reduce
from math import gcd, lcm
import hashlib
import json
from pathlib import Path

from sage.all import BinaryQF, QQ, matrix, pari

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def sha(name):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()


def primitive(vector):
    denominator = reduce(lcm, (int(q.denominator()) for q in vector), 1)
    values = [int(q * denominator) for q in vector]
    divisor = reduce(gcd, (abs(x) for x in values if x), 0)
    assert divisor
    values = [x // divisor for x in values]
    if next(x for x in values if x) < 0:
        values = [-x for x in values]
    return values


def main():
    protocol = read("diagnostic_protocol.json")
    assert protocol["status"] == "FROZEN_AFTER_HOLDOUT_MISMATCH_BEFORE_DIAGNOSIS"
    for name, digest in protocol["source_sha256"].items():
        assert sha(name) == digest, name
    data, audit = read("data/exp11_class_walk_D431_f6.json"), read("audit.json")
    floor = {r["column"] for r in audit["point_records"] if r["endomorphism_conductor"] == 6}
    nonfloor = sorted(set(range(data["class_size"])) - floor)
    c2 = [i for i, r in enumerate(audit["row_records"])
          if r["degree"] == 3 and r["source_conductor"] == 2]
    assert len(c2) == 42
    rows = data["relation_rows"]
    projected = matrix(QQ, [[int(rows[i].get(str(j), 0)) for j in nonfloor] for i in c2])
    full = matrix(QQ, [[int(rows[i].get(str(j), 0)) for j in range(data["class_size"])] for i in c2])
    kernel = projected.left_kernel()
    basis = []
    for vector in kernel.basis():
        coeffs = primitive(vector)
        combined = {j: sum(coeffs[k] * int(rows[i].get(str(j), 0)) for k, i in enumerate(c2))
                    for j in range(data["class_size"])}
        combined = {j: value for j, value in combined.items() if value}
        assert set(combined) <= floor
        basis.append({"rows": {str(c2[k]): v for k, v in enumerate(coeffs) if v},
                      "floor_vector": {str(j): v for j, v in sorted(combined.items())},
                      "row_support": sum(bool(v) for v in coeffs),
                      "floor_support": len(combined)})
    assert len(basis) == 4
    assert int(full.rank()) == 42 and int(projected.rank()) == 38
    norm3_f1 = BinaryQF(3, 1, 36)
    norm3_f2 = BinaryQF(3, 2, 144)
    assert int(norm3_f1.discriminant()) == -431
    assert int(norm3_f2.discriminant()) == -1724
    orders = {"f1": int(norm3_f1.form_class().order()),
              "f2": int(norm3_f2.form_class().order())}
    result = {"status": "VERIFIED_FOUR_DEGREE3_FLOOR_DIRECTIONS",
              "protocol_sha256": sha("diagnostic_protocol.json"),
              "source_sha256": protocol["source_sha256"],
              "class_number_f2": int(pari.qfbclassno(-1724)),
              "norm3_orders": orders,
              "conductor2_degree3_rows": len(c2),
              "full_QQ_rank": int(full.rank()),
              "nonfloor_QQ_rank": int(projected.rank()),
              "floor_kernel_dimension": len(basis),
              "basis": basis,
              "candidate_id": None, "timing_claim": None}
    (HERE / "degree3_diagnostic.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("basis", "source_sha256")}, sort_keys=True))


if __name__ == "__main__":
    main()
