"""Replay D=-7 conductor-60/90 classes with multiplicity-aware recovery."""
import hashlib
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

from sage.all import GF, QQ, classical_modular_polynomial, matrix

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "ecdlp-hecke-floor-rank-20261012" / "data"
COLLECTOR = HERE.parent / "hecke-multiplicity-collector-20261026" / "multiplicity.py"
KERNEL = HERE.parent / "ecdlp-hecke-floor-rank-20261012" / "tools" / "hecke11.py"
assert hashlib.sha256(COLLECTOR.read_bytes()).hexdigest() == "89a6cfd5951666587589834d8b8e288aaf0dfc48d9e310df62ef44c48f5bca1e"
assert hashlib.sha256(KERNEL.read_bytes()).hexdigest() == "7e66144e76bf62f7e645d87cc58be2bb0f7cc5e52601665650ef0706a6f715fb"
spec = importlib.util.spec_from_file_location("_d7_multiplicity_collector", COLLECTOR)
assert spec is not None and spec.loader is not None
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)
H = C.H
MultiplicityReduced = C.MultiplicityReduced
EXPECTED = {
    60: "39faa7734979733b3035fb6c25c39b1c0a5e389bd4c54a6c65965da1d8cce434",
    90: "4cb80fb8f8a10a138455dbf6be0c3fb229af6d6367f255000bf06ab9010f38b8",
}


def rank(rows, columns, domain):
    return int(matrix(domain, [[r.get(i, 0) for i in range(columns)] for r in rows]).rank())


def one_case(conductor):
    path = BASE / f"exp11_class_walk_D7_f{conductor}.json"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == EXPECTED[conductor]
    data = json.loads(path.read_text())
    p = int(data["p"])
    degrees = data["hecke_primes"]
    funcs, jfun = H.build(degrees)
    old = H.Reduced(p, funcs, jfun, degrees)
    corrected = MultiplicityReduced(p, funcs, jfun, degrees)
    points = []
    for encoded in data["column_points"]:
        match = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded)
        assert match, encoded
        points.append(old.E([int(match.group(1)), int(match.group(2)), 1]))
    index = {P: i for i, P in enumerate(points)}
    assert len(index) == data["class_size"]
    original = [{int(k): int(v) for k, v in r.items()}
                for r in data["relation_rows"]]
    status = {str(ell): Counter() for ell in degrees}
    patterns = {str(ell): Counter() for ell in degrees}
    reconstructed = []
    ledger = []
    old_mismatch = []
    repeated = []
    bad_complete = []
    modular = {}
    for source_index, P in enumerate(points):
        for ell in degrees:
            roots = old.neighbour_x(ell, P).roots()
            pattern = tuple(sorted(int(m) for _, m in roots))
            patterns[str(ell)][str(pattern)] += 1
            previous = old.neighbours_all(ell, P)
            outcome, neighbors = corrected.recover(ell, P)
            status[str(ell)][outcome] += 1
            if previous is not None and (neighbors is None or Counter(previous) != Counter(neighbors)):
                old_mismatch.append({"source": source_index, "degree": ell, "status": outcome})
            entry = None
            if any(m > 1 for m in pattern):
                entry = {"source": source_index, "degree": ell,
                         "root_multiplicities": list(pattern), "status": outcome,
                         "old_complete": previous is not None,
                         "new_complete": neighbors is not None}
                repeated.append(entry)
            if neighbors is None or not all(Q in index for Q in neighbors):
                continue
            if ell not in modular:
                modular[ell] = classical_modular_polynomial(ell)
            j_source = old.j(P)
            modular_ok = (j_source is not None and all(
                old.j(Q) is not None and modular[ell](j_source, old.j(Q)) == 0
                for Q in neighbors))
            sum_ok = sum(neighbors, old.E(0)) == old.a_l[ell] * P
            if entry is not None:
                entry["modular_verified"] = modular_ok
                entry["group_sum_verified"] = sum_ok
            if not modular_ok or not sum_ok:
                bad_complete.append({"source": source_index, "degree": ell,
                                     "modular_verified": modular_ok,
                                     "group_sum_verified": sum_ok})
                continue
            row = Counter(index[Q] for Q in neighbors)
            row[source_index] -= old.a_l[ell]
            concrete = {int(i): int(v) for i, v in row.items() if v}
            reconstructed.append(concrete)
            item = {"source": source_index, "degree": ell,
                    "row": {str(i): v for i, v in sorted(concrete.items())}}
            ledger.append(item)
            if entry is not None:
                entry["row"] = item["row"]
    key = lambda row: tuple(sorted(row.items()))
    old_count = Counter(map(key, original))
    new_count = Counter(map(key, reconstructed))
    additions = [{int(i): int(v) for i, v in row}
                 for row in (new_count - old_count).elements()]
    removals = [{int(i): int(v) for i, v in row}
                for row in (old_count - new_count).elements()]
    n = len(points)
    rank_result = {}
    for label, domain in (("QQ", QQ), ("mod_23", GF(23)),
                          ("mod_1000000007", GF(1000000007))):
        before = rank(original, n, domain)
        after = rank(reconstructed, n, domain)
        rank_result[label] = {"before": before, "after": after, "increment": after-before}
    torsion = old.E([16, -61, 1])
    permutation = [index[torsion - P] for P in points]
    row_counts = Counter(map(key, reconstructed))
    transformed_counts = Counter(key({permutation[i]: v for i, v in row.items()})
                                 for row in reconstructed)
    fricke_row_closed = row_counts == transformed_counts
    unrecovered_full_repeats = [entry for entry in repeated
                                if sum(entry["root_multiplicities"]) == entry["degree"] + 1
                                and entry["status"] != "RECOVERED_REPEATED"]
    result = {
        "status": "REPLAY_PASS" if not old_mismatch and not removals and not bad_complete and
                  not unrecovered_full_repeats and
                  fricke_row_closed else "REPLAY_MISMATCH",
        "conductor": conductor, "p": p, "degrees": degrees,
        "points": n, "old_rows": len(original), "new_rows": len(additions),
        "reconstructed_rows": len(reconstructed), "removed_rows": len(removals),
        "source_sha256": EXPECTED[conductor],
        "status_counts": {ell: dict(counts) for ell, counts in status.items()},
        "root_patterns": {ell: dict(counts) for ell, counts in patterns.items()},
        "old_neighbor_mismatches": old_mismatch,
        "unrecovered_full_repeats": unrecovered_full_repeats,
        "bad_complete_rows": bad_complete,
        "additions": [{str(i): v for i, v in sorted(row.items())} for row in additions],
        "removals": [{str(i): v for i, v in sorted(row.items())} for row in removals],
        "fricke_row_closed_after_recovery": fricke_row_closed,
        "fricke_row_pairs_after_recovery": len(reconstructed) // 2 if fricke_row_closed else None,
        "repeated_fibers": repeated,
        "ranks": rank_result,
    }
    (HERE / f"ledger_f{conductor}.json").write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n")
    return result


def main():
    cases = []
    for conductor in (60, 90):
        result = one_case(conductor)
        cases.append(result)
        print(json.dumps({k: v for k, v in result.items() if k != "repeated_fibers"},
                         sort_keys=True), flush=True)
        (HERE / "replay.json").write_text(json.dumps({"cases": cases}, indent=2, sort_keys=True) + "\n")
    if any(case["status"] != "REPLAY_PASS" for case in cases):
        raise SystemExit("D=-7 multiplicity replay mismatch; inspect replay.json")


if __name__ == "__main__":
    main()
