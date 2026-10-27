"""Exact Fricke plus/minus decomposition of a saved Hecke relation matrix."""
import hashlib
import json
from pathlib import Path

from sage.all import GF, QQ, matrix


HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "hecke-new-quotient-holdout-20261026"
ATKIN = HERE.parent / "hecke-d2631-atkin-commutation-20261026"
SOURCE = BASE / "data" / "exp11_class_walk_D2631_f6.json"
FLOOR = BASE / "floor_audit.json"
SCAN = ATKIN / "scan.json"
EXPECTED = {
    SOURCE: "3ea1440f009ad62e135f6211d56d366fda476f84e82e8bb714f4a7962629c193",
    FLOOR: "d0e553d08ab1cf2bc76aea5bf3ef7ca097b865e8dd8551259a29250de15ec556",
    SCAN: "ce3dfedc0a5a9bda06520106bd39882f9fa5ce662cbb5db150947595edad8ae8",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project(row, pairs, sign):
    return [row.get(i, 0) + sign * row.get(j, 0) for i, j in pairs]


def ranks(rows, pairs):
    out = {}
    for sign, label in ((1, "plus"), (-1, "minus")):
        projected = [project(row, pairs, sign) for row in rows]
        out[label] = {
            "QQ": int(matrix(QQ, projected).rank()),
            "mod_23": int(matrix(GF(23), projected).rank()),
            "mod_1000000007": int(matrix(GF(1000000007), projected).rank()),
        }
    return out


def main():
    for path, expected in EXPECTED.items():
        assert digest(path) == expected, path
    data = json.loads(SOURCE.read_text())
    floor = json.loads(FLOOR.read_text())
    scan = json.loads(SCAN.read_text())
    assert scan["status"] == "VERIFIED_POINTWISE_COMMUTATION"
    assert scan["source_hashes"][str(SOURCE.relative_to(HERE.parent))] == digest(SOURCE)
    assert scan["source_hashes"][str(FLOOR.relative_to(HERE.parent))] == digest(FLOOR)
    perm = scan["class_permutation"]
    n = len(perm)
    assert n == 768 and all(perm[perm[i]] == i and perm[i] != i for i in range(n))
    pairs = [(i, perm[i]) for i in range(n) if i < perm[i]]
    assert len(pairs) == 384
    rows = [{int(k): int(v) for k, v in row.items() if v} for row in data["relation_rows"]]
    witnesses = [{int(k): int(v) for k, v in x["signed_floor_columns"].items() if v}
                 for x in floor["cycles"] + floor["pairs"]]
    assert len(rows) == 576 and len(witnesses) == 54
    row_map = {int(k): int(v) for k, v in scan["row_map"].items()}
    assert len(row_map) == len(rows)
    assert all(row_map[row_map[i]] == i for i in row_map)
    assert all({perm[k]: v for k, v in row.items()} == rows[row_map[i]]
               for i, row in enumerate(rows))
    row_pair_count = sum(i < row_map[i] for i in row_map)
    row_fixed_count = sum(i == row_map[i] for i in row_map)
    relation_ranks = ranks(rows, pairs)
    floor_ranks = ranks(witnesses, pairs)
    assert sum(relation_ranks[s]["QQ"] for s in ("plus", "minus")) == 480
    assert sum(floor_ranks[s]["QQ"] for s in ("plus", "minus")) == 54
    assert all(relation_ranks[s]["QQ"] == relation_ranks[s]["mod_23"]
               == relation_ranks[s]["mod_1000000007"] for s in ("plus", "minus"))
    assert all(floor_ranks[s]["QQ"] == floor_ranks[s]["mod_23"]
               == floor_ranks[s]["mod_1000000007"] for s in ("plus", "minus"))
    result = {
        "status": "FRICKE_EIGENSPACE_RANKS_VERIFIED",
        "point_pairs": len(pairs),
        "row_pairs": row_pair_count,
        "row_fixed": row_fixed_count,
        "relation_ranks": relation_ranks,
        "floor_witness_ranks": floor_ranks,
        "relation_nullities": {s: len(pairs) - relation_ranks[s]["QQ"] for s in ("plus", "minus")},
        "source_hashes": {str(p.relative_to(HERE.parent)): digest(p) for p in (SOURCE, FLOOR, SCAN)},
    }
    (HERE / "ranks.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
