"""Cross-replay D=-2631 repeated roots with an independent collector branch."""
import hashlib
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

from sage.all import GF, QQ, classical_modular_polynomial, matrix


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "hecke-new-quotient-holdout-20261026" / "data" / "exp11_class_walk_D2631_f6.json"
KERNEL = ROOT / "hecke-new-quotient-holdout-20261026" / "tools" / "hecke11.py"
COLLECTOR = ROOT / "hecke-multiplicity-collector-20261026" / "multiplicity.py"
EXPECTED = {
    SOURCE: "3ea1440f009ad62e135f6211d56d366fda476f84e82e8bb714f4a7962629c193",
    KERNEL: "d13a8663c1beb145c0b66147305831bb15678208d126df5b69ddf5e17962b32b",
    COLLECTOR: "89a6cfd5951666587589834d8b8e288aaf0dfc48d9e310df62ef44c48f5bca1e",
}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row_key(row):
    return tuple(sorted((int(i), int(v)) for i, v in row.items() if v))


def rank(rows, domain):
    return int(matrix(domain, [[row.get(i, 0) for i in range(768)] for row in rows]).rank())


def main():
    for path, expected in EXPECTED.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, path
    H = load(KERNEL, "_d2631_regularized_hecke11")
    C = load(COLLECTOR, "_d2631_generic_multiplicity")
    data = json.loads(SOURCE.read_text())
    funcs, jfun = H.build([2, 3])

    class CrossReduced(H.Reduced):
        MAX_ASSIGNMENTS = 65536
        recover = C.MultiplicityReduced.recover

    reduced = CrossReduced(23743, funcs, jfun, [2, 3])
    points = []
    for encoded in data["column_points"]:
        a, b = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded).groups()
        points.append(reduced.E([int(a), int(b), 1]))
    index = {P: i for i, P in enumerate(points)}
    assert len(index) == 768
    archived = [{int(i): int(v) for i, v in row.items()} for row in data["relation_rows"]]
    reconstructed = []
    patterns = {"2": Counter(), "3": Counter()}
    statuses = {"2": Counter(), "3": Counter()}
    mismatches = []
    repeated_records = []
    modular = {}
    for source_index, P in enumerate(points):
        for ell in (2, 3):
            roots = reduced.neighbour_x(ell, P).roots()
            pattern = tuple(sorted(int(m) for _, m in roots))
            patterns[str(ell)][str(pattern)] += 1
            old = H.Reduced.neighbours_all(reduced, ell, P)
            if any(m > 1 for _, m in roots):
                status, neighbors = reduced.recover(ell, P)
                statuses[str(ell)][status] += 1
                if ((old is None and neighbors is not None) or
                    (old is not None and
                     (neighbors is None or Counter(old) != Counter(neighbors)))):
                    mismatches.append({"source": source_index, "degree": ell, "status": status})
                if neighbors is not None:
                    if ell not in modular:
                        modular[ell] = classical_modular_polynomial(ell)
                    jP = reduced.j(P)
                    modular_ok = jP is not None and all(
                        reduced.j(Q) is not None and modular[ell](jP, reduced.j(Q)) == 0
                        for Q in neighbors)
                    repeated_records.append({"source": source_index, "degree": ell,
                        "root_multiplicities": [int(m) for _, m in roots],
                        "status": status, "old_match": old is not None and Counter(old) == Counter(neighbors),
                        "modular_verified": modular_ok,
                        "group_sum_verified": sum(neighbors, reduced.E(0)) == reduced.a_l[ell] * P})
            else:
                neighbors = old
            if neighbors is None or not all(Q in index for Q in neighbors):
                continue
            if sum(neighbors, reduced.E(0)) != reduced.a_l[ell] * P:
                mismatches.append({"source": source_index, "degree": ell, "status": "GROUP_SUM_FAIL"})
                continue
            row = Counter(index[Q] for Q in neighbors)
            row[source_index] -= reduced.a_l[ell]
            concrete_row = {int(i): int(v) for i, v in row.items() if v}
            reconstructed.append(concrete_row)
            if (repeated_records and repeated_records[-1]["source"] == source_index and
                    repeated_records[-1]["degree"] == ell):
                repeated_records[-1]["row"] = {str(i): v for i, v in sorted(concrete_row.items())}
    rows_equal = Counter(map(row_key, archived)) == Counter(map(row_key, reconstructed))
    ranks = {}
    for label, domain in (("QQ", QQ), ("mod_23", GF(23)),
                          ("mod_1000000007", GF(1000000007))):
        ranks[label] = {"archived": rank(archived, domain),
                        "reconstructed": rank(reconstructed, domain)}
    good = (not mismatches and rows_equal and len(reconstructed) == 576 and
            all(r["old_match"] and r["modular_verified"] and r["group_sum_verified"]
                for r in repeated_records) and
            all(v == {"archived": 480, "reconstructed": 480} for v in ranks.values()))
    result = {"status": "D2631_MULTIPLICITY_CROSS_REPLAY_PASS" if good else "CROSS_REPLAY_MISMATCH",
              "point_count": len(points), "archived_rows": len(archived),
              "reconstructed_rows": len(reconstructed), "row_multisets_equal": rows_equal,
              "root_patterns": {ell: dict(counts) for ell, counts in patterns.items()},
              "repeated_status_counts": {ell: dict(counts) for ell, counts in statuses.items()},
              "repeated_records": repeated_records, "mismatches": mismatches,
              "ranks": ranks,
              "source_hashes": {str(path.relative_to(ROOT)): expected for path, expected in EXPECTED.items()}}
    (HERE / "reconstructed_rows.json").write_text(json.dumps(
        [{str(i): v for i, v in sorted(row.items())} for row in reconstructed],
        indent=2, sort_keys=True) + "\n")
    (HERE / "replay.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if not good:
        raise SystemExit("D2631 multiplicity cross-replay failed; inspect replay.json")


if __name__ == "__main__":
    main()
