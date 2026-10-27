"""Prospective Fricke rank-balance panel on four frozen Hecke matrices."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, matrix


HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "ecdlp-hecke-floor-rank-20261012" / "data"
EXPECTED = {
    42: "f4a8b964dad70fc8d697d1163f2fa8a963a44882731ae18518e1ace2951c311d",
    70: "efe387fe31c22001b9eeaabe72d920835f80a2300b1aaa4d151015b05d2357ef",
    150: "49e33851a0ed64e470f1693001664c6f76f58aea9e2e65b6974d1618dfa15e06",
    210: "616c4583ac761e9eb965c9ce36b366e3a67b104b881d9eb8a8cee47f2799844e",
}
PREDICTED = {42: 52, 70: 70, 150: 250, 210: 392}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_key(row):
    return tuple(sorted((int(k), int(v)) for k, v in row.items() if v))


def ranks(rows, pairs, sign):
    projected = [[row.get(i, 0) + sign * row.get(j, 0) for i, j in pairs]
                 for row in rows]
    return {
        "QQ": int(matrix(QQ, projected).rank()),
        "mod_23": int(matrix(GF(23), projected).rank()),
        "mod_1000000007": int(matrix(GF(1000000007), projected).rank()),
    }


def one_case(f):
    path = BASE / f"exp11_class_walk_D7_f{f}.json"
    assert digest(path) == EXPECTED[f], path
    data = json.loads(path.read_text())
    assert (data["DK"], data["f"]) == (-7, f)
    E = EllipticCurve(GF(int(data["p"])), [0, -1, 1, -10, -20])
    T = E([16, -61, 1])
    assert 5 * T == E(0)
    pts = []
    for encoded in data["column_points"]:
        match = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded)
        assert match, encoded
        pts.append(E([int(match.group(1)), int(match.group(2)), 1]))
    index = {P: i for i, P in enumerate(pts)}
    missing = [i for i, P in enumerate(pts) if T - P not in index]
    result = {
        "conductor": f, "p": int(data["p"]), "degrees": data["hecke_primes"],
        "point_count": len(pts), "row_count": len(data["relation_rows"]),
        "archived_rank": int(data["rank"]), "predicted_rank_each": PREDICTED[f],
        "input_sha256": EXPECTED[f], "missing_W_points": missing,
    }
    if missing:
        result.update(status="CLASS_NOT_W_CLOSED", plus_rank=None, minus_rank=None)
        return result
    perm = [index[T - P] for P in pts]
    assert all(perm[perm[i]] == i for i in range(len(perm)))
    pairs = [(i, perm[i]) for i in range(len(perm)) if i < perm[i]]
    fixed = [i for i in range(len(perm)) if i == perm[i]]
    rows = [{int(k): int(v) for k, v in row.items() if v}
            for row in data["relation_rows"]]
    row_counts = Counter(row_key(row) for row in rows)
    mapped_counts = Counter(row_key({perm[k]: v for k, v in row.items()}) for row in rows)
    row_closed = row_counts == mapped_counts
    row_fixed_count = sum(row_key(row) == row_key({perm[k]: v for k, v in row.items()})
                          for row in rows)
    result.update(point_pairs=len(pairs), fixed_points=fixed, row_closed=row_closed,
                  row_fixed_count=row_fixed_count,
                  row_pair_count=(len(rows) - row_fixed_count) // 2 if row_closed else None,
                  missing_transformed_rows=sum((mapped_counts - row_counts).values()),
                  unmatched_saved_rows=sum((row_counts - mapped_counts).values()))
    if fixed or not row_closed:
        result.update(status="INCOMPLETE_W_ACTION", plus_rank=None, minus_rank=None)
        return result
    plus, minus = ranks(rows, pairs, 1), ranks(rows, pairs, -1)
    result.update(plus_rank=plus, minus_rank=minus,
                  plus_nullity=len(pairs)-plus["QQ"],
                  minus_nullity=len(pairs)-minus["QQ"],
                  rank_sum=plus["QQ"]+minus["QQ"],
                  prediction_match=plus["QQ"] == minus["QQ"] == PREDICTED[f],
                  status="RANK_BALANCE_VERIFIED" if plus["QQ"] == minus["QQ"] == PREDICTED[f]
                         else "RANK_BALANCE_MISMATCH")
    assert result["rank_sum"] == int(data["rank"])
    return result


def main():
    cases = []
    for f in (42, 70, 150, 210):
        case = one_case(f)
        cases.append(case)
        print(json.dumps(case, sort_keys=True), flush=True)
        (HERE / "result.json").write_text(json.dumps({"cases": cases}, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
