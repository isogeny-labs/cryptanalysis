"""Replay frozen Hecke classes with multiplicity-aware neighbor recovery."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from sage.all import GF, QQ, classical_modular_polynomial, matrix

from multiplicity import H, MultiplicityReduced


HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "ecdlp-hecke-floor-rank-20261012" / "data"
EXPECTED = {
    42: "f4a8b964dad70fc8d697d1163f2fa8a963a44882731ae18518e1ace2951c311d",
    70: "efe387fe31c22001b9eeaabe72d920835f80a2300b1aaa4d151015b05d2357ef",
    150: "49e33851a0ed64e470f1693001664c6f76f58aea9e2e65b6974d1618dfa15e06",
    210: "616c4583ac761e9eb965c9ce36b366e3a67b104b881d9eb8a8cee47f2799844e",
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
    additions = []
    old_mismatch = []
    repeated = []
    modular = {}
    for source_index, P in enumerate(points):
        for ell in degrees:
            previous = old.neighbours_all(ell, P)
            outcome, neighbors = corrected.recover(ell, P)
            status[str(ell)][outcome] += 1
            if previous is not None and (neighbors is None or Counter(previous) != Counter(neighbors)):
                old_mismatch.append({"source": source_index, "degree": ell, "status": outcome})
            if outcome != "RECOVERED_REPEATED":
                continue
            entry = {"source": source_index, "degree": ell,
                     "root_multiplicities": [int(m) for _, m in old.neighbour_x(ell, P).roots()],
                     "all_in_class": all(Q in index for Q in neighbors)}
            if entry["all_in_class"]:
                if ell not in modular:
                    modular[ell] = classical_modular_polynomial(ell)
                j_source = old.j(P)
                entry["modular_verified"] = (j_source is not None and
                    all(old.j(Q) is not None and modular[ell](j_source, old.j(Q)) == 0
                        for Q in neighbors))
                row = Counter(index[Q] for Q in neighbors)
                row[source_index] -= old.a_l[ell]
                entry["row"] = {str(i): int(v) for i, v in sorted(row.items()) if v}
                if entry["modular_verified"]:
                    additions.append({int(i): int(v) for i, v in entry["row"].items()})
            repeated.append(entry)
    n = len(points)
    rank_result = {}
    for label, domain in (("QQ", QQ), ("mod_23", GF(23)),
                          ("mod_1000000007", GF(1000000007))):
        before = rank(original, n, domain)
        after = rank(original + additions, n, domain)
        rank_result[label] = {"before": before, "after": after, "increment": after-before}
    torsion = old.E([16, -61, 1])
    permutation = [index[torsion - P] for P in points]
    all_rows = original + additions
    key = lambda row: tuple(sorted(row.items()))
    row_counts = Counter(map(key, all_rows))
    transformed_counts = Counter(key({permutation[i]: v for i, v in row.items()})
                                 for row in all_rows)
    fricke_row_closed = row_counts == transformed_counts
    return {
        "status": "REPLAY_PASS" if not old_mismatch and
                  all(e.get("modular_verified", True) for e in repeated) and
                  fricke_row_closed else "REPLAY_MISMATCH",
        "conductor": conductor, "p": p, "degrees": degrees,
        "points": n, "old_rows": len(original), "new_rows": len(additions),
        "source_sha256": EXPECTED[conductor],
        "status_counts": {ell: dict(counts) for ell, counts in status.items()},
        "old_neighbor_mismatches": old_mismatch,
        "fricke_row_closed_after_recovery": fricke_row_closed,
        "fricke_row_pairs_after_recovery": len(all_rows) // 2 if fricke_row_closed else None,
        "repeated_fibers": repeated,
        "ranks": rank_result,
    }


def main():
    cases = []
    for conductor in (42, 70, 150, 210):
        result = one_case(conductor)
        cases.append(result)
        print(json.dumps({k: v for k, v in result.items() if k != "repeated_fibers"},
                         sort_keys=True), flush=True)
        (HERE / "replay.json").write_text(json.dumps({"cases": cases}, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
