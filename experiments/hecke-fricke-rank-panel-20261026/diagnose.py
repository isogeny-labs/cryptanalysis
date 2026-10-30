"""Reconstruct the degree-7 Fricke partner with repeated x-roots."""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

from sage.all import GF, QQ, classical_modular_polynomial, matrix


HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "ecdlp-hecke-floor-rank-20261012"
DATA = BASE / "data" / "exp11_class_walk_D7_f42.json"
KERNEL = BASE / "tools" / "hecke11.py"
assert hashlib.sha256(DATA.read_bytes()).hexdigest() == "f4a8b964dad70fc8d697d1163f2fa8a963a44882731ae18518e1ace2951c311d"
assert hashlib.sha256(KERNEL.read_bytes()).hexdigest() == "7e66144e76bf62f7e645d87cc58be2bb0f7cc5e52601665650ef0706a6f715fb"
sys.path.insert(0, str(BASE / "tools"))
import hecke11 as H  # noqa: E402


def rank(rows, domain):
    return int(matrix(domain, [[row.get(i, 0) for i in range(160)] for row in rows]).rank())


def main():
    data = json.loads(DATA.read_text())
    funcs, jfun = H.build([7])
    reduced = H.Reduced(3187, funcs, jfun, [7])
    E = reduced.E
    T = E([16, -61, 1])
    pts = []
    for encoded in data["column_points"]:
        a, b = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded).groups()
        pts.append(E([int(a), int(b), 1]))
    index = {P: i for i, P in enumerate(pts)}
    source, target = pts[88], pts[67]
    assert T - source == target
    source_nb = reduced.neighbours_all(7, source)
    assert source_nb is not None and len(source_nb) == 8
    target_nb = [T - P for P in source_nb]
    assert all(P in index for P in target_nb)
    poly_source = reduced.neighbour_x(7, source)
    poly_target = reduced.neighbour_x(7, target)
    roots_source = [(int(x), int(m)) for x, m in poly_source.roots()]
    roots_target = [(int(x), int(m)) for x, m in poly_target.roots()]
    x_multiset_match = Counter(P[0] for P in target_nb) == Counter({x: m for x, m in poly_target.roots()})
    phi = classical_modular_polynomial(7)
    j_source, j_target = reduced.j(source), reduced.j(target)
    source_modular = [bool(phi(j_source, reduced.j(P)) == 0) for P in source_nb]
    target_modular = [bool(phi(j_target, reduced.j(P)) == 0) for P in target_nb]
    group_sum = sum(target_nb, E(0)) == reduced.a_l[7] * target
    old_target = reduced.neighbours_all(7, target)
    row = Counter(index[P] for P in target_nb)
    row[index[target]] -= int(reduced.a_l[7])
    row = {i: int(v) for i, v in row.items() if v}
    archived = [{int(k): int(v) for k, v in r.items()} for r in data["relation_rows"]]
    archived_source = archived[74]
    mapped = Counter(index[T - pts[i]] for i, v in archived_source.items() for _ in range(v))
    mapped = {i: int(v) for i, v in mapped.items() if v}
    row_matches = row == mapped
    rank_results = {}
    for label, domain in (("QQ", QQ), ("mod_23", GF(23)), ("mod_1000000007", GF(1000000007))):
        before, after = rank(archived, domain), rank(archived + [row], domain)
        rank_results[label] = {"before": before, "after": after, "increment": after-before}
    good = x_multiset_match and all(source_modular) and all(target_modular) and group_sum and row_matches
    result = {
        "status": "REPEATED_X_PARTNER_VERIFIED" if good else "RECONSTRUCTION_MISMATCH",
        "source_column": 88, "target_column": 67, "source_row": 74,
        "roots_source": roots_source, "roots_target": roots_target,
        "target_old_neighbours_all": old_target is not None,
        "x_multiset_match": x_multiset_match,
        "source_modular_all": all(source_modular), "target_modular_all": all(target_modular),
        "group_sum_verified": group_sum, "row_matches_transported": row_matches,
        "recovered_row": {str(k): v for k, v in sorted(row.items())},
        "ranks": rank_results,
        "source_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(),
        "kernel_sha256": hashlib.sha256(KERNEL.read_bytes()).hexdigest(),
    }
    (HERE / "diagnostic.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
