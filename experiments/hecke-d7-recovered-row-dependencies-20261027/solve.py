"""Produce exact archived-row span certificates for recovered Hecke rows."""
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from sage.all import GF, QQ, matrix, vector


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
Q = 1000000007
EXPECTED_NEW = {42: 3, 60: 2, 70: 2, 90: 2, 150: 2, 210: 2}


def load(path):
    entry = next(item for item in INPUTS["inputs"] if item["path"] == str(path))
    full = ROOT / path
    assert hashlib.sha256(full.read_bytes()).hexdigest() == entry["sha256"]
    return json.loads(full.read_text())


def row_key(row):
    return tuple(sorted((int(i), int(v)) for i, v in row.items() if v))


def targets(f):
    prior = load(Path("experiments/hecke-multiplicity-collector-20261026/replay.json"))
    later = load(Path("experiments/hecke-d7-f60-f90-multiplicity-20261027/replay.json"))
    cases = {case["conductor"]: case for case in prior["cases"] + later["cases"]}
    case = cases[f]
    assert case["new_rows"] == EXPECTED_NEW[f]
    rows = []
    for entry in case["repeated_fibers"]:
        if "row" not in entry:
            continue
        assert entry.get("status", "RECOVERED_REPEATED") == "RECOVERED_REPEATED"
        assert entry["modular_verified"]
        rows.append({"source": entry["source"], "degree": entry["degree"],
                     "row": {int(i): int(v) for i, v in entry["row"].items()}})
    assert len(rows) == EXPECTED_NEW[f]
    return rows


def integer_check(rows, target, coefficients, denominator):
    accumulated = Counter()
    for item in coefficients:
        for i, value in rows[item["row_index"]].items():
            accumulated[int(i)] += item["numerator"] * int(value)
    for i, value in target.items():
        accumulated[int(i)] -= denominator * int(value)
    return all(value == 0 for value in accumulated.values())


def solve(f):
    data = load(Path(f"experiments/ecdlp-hecke-floor-rank-20261012/data/exp11_class_walk_D7_f{f}.json"))
    archived = [{int(i): int(v) for i, v in row.items()}
                for row in data["relation_rows"]]
    n = len(data["column_points"])
    old_keys = Counter(map(row_key, archived))
    target_rows = targets(f)
    assert all(old_keys[row_key(item["row"])] == 0 for item in target_rows)
    mod_matrix = matrix(GF(Q), [[row.get(i, 0) for i in range(n)]
                                for row in archived])
    basis_ids = [int(i) for i in mod_matrix.transpose().pivots()]
    assert len(basis_ids) == int(data["rank"])
    basis = matrix(QQ, [[archived[j].get(i, 0) for i in range(n)]
                        for j in basis_ids])
    operator = basis.transpose()
    certificates = []
    for item in target_rows:
        rhs = vector(QQ, [item["row"].get(i, 0) for i in range(n)])
        solution = operator.solve_right(rhs)
        denominator = math.lcm(*(int(value.denominator()) for value in solution))
        coefficients = [{"row_index": basis_ids[j],
                         "numerator": int(value * denominator)}
                        for j, value in enumerate(solution) if value]
        assert integer_check(archived, item["row"], coefficients, denominator)
        certificates.append({"source": item["source"], "degree": item["degree"],
                             "target_row": {str(i): v for i, v in sorted(item["row"].items())},
                             "denominator": denominator, "coefficients": coefficients,
                             "support_size": len(coefficients),
                             "max_abs_numerator": max(abs(c["numerator"]) for c in coefficients),
                             "integer_identity_verified": True})
    result = {"status": "EXACT_DEPENDENCIES_VERIFIED", "conductor": f,
              "points": n, "archived_rows": len(archived), "archived_rank": int(data["rank"]),
              "modular_basis_rank": len(basis_ids), "targets": certificates}
    path = HERE / f"certificates_f{f}.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"conductor": f, "status": result["status"],
                      "support_sizes": [c["support_size"] for c in certificates],
                      "denominators": [c["denominator"] for c in certificates]}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--conductor", type=int, choices=sorted(EXPECTED_NEW), required=True)
    args = parser.parse_args()
    solve(args.conductor)
