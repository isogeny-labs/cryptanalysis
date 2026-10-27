"""Cross-replay frozen conductor-6 Hecke matrices with repeated-root recovery."""
import hashlib
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

from sage.all import GF, QQ, classical_modular_polynomial, matrix


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())


def verified_path(entry):
    path = ROOT / entry["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"], path
    return path


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row_key(row):
    return tuple(sorted((int(i), int(v)) for i, v in row.items() if v))


def rank(rows, columns, domain):
    return int(matrix(domain, [[row.get(i, 0) for i in range(columns)]
                               for row in rows]).rank())


def inspect(entry, H, C, funcs, jfun, modular):
    data = json.loads(verified_path(entry).read_text())
    assert data["p"] == entry["p"] and data["hecke_primes"] == [2, 3]
    assert len(data["column_points"]) == entry["points"]
    assert len(data["relation_rows"]) == entry["rows"]

    class CrossReduced(H.Reduced):
        MAX_ASSIGNMENTS = INPUTS["policy"]["repeated_fiber_assignment_cap"]
        recover = C.MultiplicityReduced.recover

    reduced = CrossReduced(int(data["p"]), funcs, jfun, [2, 3])
    points = []
    for encoded in data["column_points"]:
        a, b = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded).groups()
        points.append(reduced.E([int(a), int(b), 1]))
    index = {P: i for i, P in enumerate(points)}
    assert len(index) == len(points)

    archived = [{int(i): int(v) for i, v in row.items()}
                for row in data["relation_rows"]]
    reconstructed = []
    new_ledger = []
    patterns = {"2": Counter(), "3": Counter()}
    statuses = {"2": Counter(), "3": Counter()}
    repeated = []
    mismatches = []
    bad_complete = []
    for source, P in enumerate(points):
        for ell in (2, 3):
            roots = reduced.neighbour_x(ell, P).roots()
            multiplicities = sorted(int(m) for _, m in roots)
            patterns[str(ell)][str(tuple(multiplicities))] += 1
            old = H.Reduced.neighbours_all(reduced, ell, P)
            if max(multiplicities, default=0) > 1:
                status, neighbors = reduced.recover(ell, P)
                statuses[str(ell)][status] += 1
                repeated.append({"source": source, "degree": ell,
                                 "root_multiplicities": multiplicities,
                                 "status": status, "old_complete": old is not None,
                                 "new_complete": neighbors is not None})
                if old is not None and (neighbors is None or
                                        Counter(old) != Counter(neighbors)):
                    mismatches.append({"source": source, "degree": ell,
                                       "status": status})
            else:
                neighbors = old
            if neighbors is None or not all(Q in index for Q in neighbors):
                continue
            jP = reduced.j(P)
            modular_ok = jP is not None and all(
                reduced.j(Q) is not None and modular[ell](jP, reduced.j(Q)) == 0
                for Q in neighbors)
            sum_ok = sum(neighbors, reduced.E(0)) == reduced.a_l[ell] * P
            if not modular_ok or not sum_ok:
                bad_complete.append({"source": source, "degree": ell,
                                     "modular_ok": modular_ok, "group_sum_ok": sum_ok})
                continue
            row = Counter(index[Q] for Q in neighbors)
            row[source] -= reduced.a_l[ell]
            concrete = {int(i): int(v) for i, v in row.items() if v}
            reconstructed.append(concrete)
            new_ledger.append({"source": source, "degree": ell,
                               "row": {str(i): v for i, v in sorted(concrete.items())}})

    old_count = Counter(map(row_key, archived))
    new_count = Counter(map(row_key, reconstructed))
    added = list((new_count - old_count).elements())
    removed = list((old_count - new_count).elements())
    ranks = None
    if added or removed:
        ranks = {}
        for label, domain in (("QQ", QQ), ("mod_23", GF(23)),
                              ("mod_1000000007", GF(1000000007))):
            ranks[label] = {"archived": rank(archived, len(points), domain),
                            "reconstructed": rank(reconstructed, len(points), domain)}
    result = {"input": entry, "status": "PASS" if not (removed or mismatches or bad_complete)
              else "MISMATCH", "root_patterns": {ell: dict(counts)
              for ell, counts in patterns.items()}, "repeated_statuses": {ell: dict(counts)
              for ell, counts in statuses.items()}, "repeated_records": repeated,
              "archived_rows": len(archived), "reconstructed_rows": len(reconstructed),
              "added_rows": [{str(i): v for i, v in key} for key in added],
              "removed_rows": [{str(i): v for i, v in key} for key in removed],
              "old_neighbor_mismatches": mismatches, "bad_complete_rows": bad_complete,
              "ranks_if_changed": ranks}
    slug = Path(entry["path"]).stem + "_p" + str(entry["p"])
    (HERE / "cases").mkdir(exist_ok=True)
    (HERE / "cases" / (slug + ".json")).write_text(json.dumps(
        result, indent=2, sort_keys=True) + "\n")
    (HERE / "cases" / (slug + "_ledger.json")).write_text(json.dumps(
        new_ledger, indent=2, sort_keys=True) + "\n")
    if added:
        (HERE / "cases" / (slug + "_added_ledger.json")).write_text(json.dumps(
            [item for item in new_ledger if row_key(item["row"]) in set(added)],
            indent=2, sort_keys=True) + "\n")
    print(json.dumps({"case": slug, "status": result["status"],
                      "repeated": len(repeated), "added": len(added),
                      "removed": len(removed), "ranks": ranks}, sort_keys=True), flush=True)
    return result


def main():
    assert INPUTS["schema"] == "hecke-f6-multiplicity-census-v1"
    source = {Path(entry["path"]).name: verified_path(entry)
              for entry in INPUTS["sources"]}
    H = load(source["hecke11.py"], "_f6_regularized_hecke11")
    C = load(source["multiplicity.py"], "_f6_generic_multiplicity")
    funcs, jfun = H.build([2, 3])
    modular = {ell: classical_modular_polynomial(ell) for ell in (2, 3)}
    results = [inspect(entry, H, C, funcs, jfun, modular)
               for entry in INPUTS["matrices"]]
    summary = {"status": "PASS" if all(r["status"] == "PASS" for r in results)
               else "MISMATCH", "case_count": len(results),
               "added_rows": sum(len(r["added_rows"]) for r in results),
               "repeated_fibers": sum(len(r["repeated_records"]) for r in results),
               "cases": [{"input": r["input"]["path"], "p": r["input"]["p"],
                          "status": r["status"], "repeated": len(r["repeated_records"]),
                          "added": len(r["added_rows"]), "removed": len(r["removed_rows"]),
                          "ranks_if_changed": r["ranks_if_changed"]} for r in results],
               "inputs_sha256": hashlib.sha256((HERE / "inputs.json").read_bytes()).hexdigest()}
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)
    if summary["status"] != "PASS":
        raise SystemExit("census mismatch; inspect case receipts")


if __name__ == "__main__":
    main()
