"""Fricke eigenspaces after one verified repeated-x row insertion."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, matrix


HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "ecdlp-hecke-floor-rank-20261012" / "data" / "exp11_class_walk_D7_f42.json"
EXPECTED = "f4a8b964dad70fc8d697d1163f2fa8a963a44882731ae18518e1ace2951c311d"


def rank(rows, domain):
    return int(matrix(domain, rows).rank())


def main():
    assert hashlib.sha256(DATA.read_bytes()).hexdigest() == EXPECTED
    data = json.loads(DATA.read_text())
    diagnostic = json.loads((HERE / "diagnostic.json").read_text())
    assert diagnostic["status"] == "REPEATED_X_PARTNER_VERIFIED"
    assert all(diagnostic[k] for k in ("x_multiset_match", "source_modular_all",
                                       "target_modular_all", "group_sum_verified",
                                       "row_matches_transported"))
    E = EllipticCurve(GF(3187), [0, -1, 1, -10, -20])
    T = E([16, -61, 1])
    points = []
    for encoded in data["column_points"]:
        a, b = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded).groups()
        points.append(E([int(a), int(b), 1]))
    index = {P: i for i, P in enumerate(points)}
    perm = [index[T - P] for P in points]
    pairs = [(i, perm[i]) for i in range(160) if i < perm[i]]
    assert len(pairs) == 80 and all(perm[perm[i]] == i for i in range(160))
    rows = [{int(k): int(v) for k, v in row.items()} for row in data["relation_rows"]]
    recovered = {int(k): int(v) for k, v in diagnostic["recovered_row"].items()}
    rows.append(recovered)
    key = lambda row: tuple(sorted(row.items()))
    source_multiset = Counter(map(key, rows))
    transformed_multiset = Counter(key({perm[i]: v for i, v in row.items()}) for row in rows)
    assert source_multiset == transformed_multiset
    out = {}
    for label, domain in (("QQ", QQ), ("mod_23", GF(23)), ("mod_1000000007", GF(1000000007))):
        full = [[row.get(i, 0) for i in range(160)] for row in rows]
        plus = [[row.get(i, 0) + row.get(j, 0) for i, j in pairs] for row in rows]
        minus = [[row.get(i, 0) - row.get(j, 0) for i, j in pairs] for row in rows]
        out[label] = {"full": rank(full, domain), "plus": rank(plus, domain),
                      "minus": rank(minus, domain)}
        assert out[label] == {"full": 104, "plus": 52, "minus": 52}
    result = {"status": "AUGMENTED_FRICKE_BALANCE_VERIFIED",
              "archived_rows": 129, "augmented_rows": 130,
              "point_pairs": 80, "row_pairs": 65,
              "ranks": out, "input_sha256": EXPECTED,
              "diagnostic_sha256": hashlib.sha256((HERE / "diagnostic.json").read_bytes()).hexdigest()}
    (HERE / "augmented.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
