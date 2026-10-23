"""Independently replay the D=-431/f6 regularized Hecke matrix."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

from sage.all import EllipticCurve_from_j, PolynomialRing, QQ, classical_modular_polynomial, matrix

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tools"))
import hecke11 as H


def sha(name):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()


def decode(E, text):
    match = re.fullmatch(r"\((\d+) : (\d+) : 1\)", text)
    assert match, text
    return E([int(match.group(1)), int(match.group(2)), 1])


def rank(rows, columns, keep=None):
    if not rows:
        return 0
    return int(matrix(QQ, [[int(row.get(str(j), 0)) if keep is None or j in keep else 0
                            for j in range(columns)] for row in rows]).rank())


def main():
    protocol = json.loads((HERE / "producer_protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_GATE_AND_PRODUCER"
    for name, digest in protocol["source_sha256"].items():
        assert sha(name) == digest, name
    data = json.loads((HERE / "data/exp11_class_walk_D431_f6.json").read_text())
    assert (data["DK"], data["f"], data["p"], data["u"], data["hecke_primes"]) == (-431, 6, 12343, 184, [2, 3])
    funcs, jfun = H.build([2, 3])
    rd = H.Reduced(12343, funcs, jfun, [2, 3])
    points = [decode(rd.E, text) for text in data["column_points"]]
    index = {q: i for i, q in enumerate(points)}
    assert len(points) == len(index) == 252
    phi = {l: classical_modular_polynomial(l) for l in (2, 3)}
    ring = PolynomialRing(rd.Fp, "J")
    J = ring.gen()
    by_j = {}
    strata, root_counts = Counter(), {2: Counter(), 3: Counter()}
    point_records, row_records = [], []
    row_index = 0
    for i, q in enumerate(points):
        j = rd.j(q)
        assert j is not None
        key = int(j)
        if key not in by_j:
            model = EllipticCurve_from_j(j)
            assert abs(int(model.trace_of_frobenius())) == 184
            by_j[key] = int(model.endomorphism_order().conductor())
        c = by_j[key]
        assert 6 % c == 0
        strata[c] += 1
        record = {"column": i, "point": str(q), "j": key, "endomorphism_conductor": c}
        for l in (2, 3):
            expected = l + 1 if (6 // c) % l == 0 else 1
            roots_x = rd.neighbour_x(l, q).roots()
            roots_j = ring(phi[l](j, J)).roots()
            got_x, got_j = sum(int(m) for _, m in roots_x), sum(int(m) for _, m in roots_j)
            assert got_x == got_j == expected, (i, l, c, got_x, got_j, expected)
            root_counts[l][expected] += 1
            if expected != l + 1:
                continue
            neighbours = rd.neighbours_all(l, q)
            assert neighbours is not None and len(neighbours) == l + 1
            assert sum(neighbours, rd.E(0)) == rd.a_l[l] * q
            assert all(neighbour in index for neighbour in neighbours)
            row = Counter(index[neighbour] for neighbour in neighbours)
            row[i] -= rd.a_l[l]
            decoded = {str(k): int(v) for k, v in row.items() if v}
            saved = {k: int(v) for k, v in data["relation_rows"][row_index].items() if v}
            assert decoded == saved, (i, l, row_index)
            row_records.append({"row": row_index, "source_column": i,
                                "source_conductor": c, "degree": l})
            row_index += 1
        point_records.append(record)
    assert row_index == data["relations"] == 210
    assert dict(strata) == {1: 42, 2: 42, 3: 84, 6: 84}
    assert [r["degree"] for r in row_records].count(2) == 126
    assert [r["degree"] for r in row_records].count(3) == 84
    nonfloor = {r["column"] for r in point_records if r["endomorphism_conductor"] != 6}
    ranks = {}
    for subset in ((2,), (3,), (2, 3)):
        selected = [row for row, rec in zip(data["relation_rows"], row_records)
                    if rec["degree"] in subset]
        ranks["+".join(map(str, subset))] = {"full_QQ": rank(selected, len(points)),
                                             "nonfloor_QQ": rank(selected, len(points), nonfloor)}
    assert ranks["2+3"]["full_QQ"] == data["rank"] == 168
    result = {"status": "VERIFIED_D431_F6_MATRIX",
              "producer_sha256": sha("data/exp11_class_walk_D431_f6.json"),
              "protocol_sha256": sha("producer_protocol.json"),
              "script_sha256": sha("audit.py"),
              "point_count": len(points), "row_count": row_index,
              "conductor_counts": dict(sorted(strata.items())),
              "root_counts": {str(l): dict(sorted(root_counts[l].items())) for l in (2, 3)},
              "ranks": ranks,
              "point_records": point_records, "row_records": row_records,
              "candidate_id": None, "timing_claim": None}
    (HERE / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("point_records", "row_records")}, sort_keys=True))


if __name__ == "__main__":
    main()
