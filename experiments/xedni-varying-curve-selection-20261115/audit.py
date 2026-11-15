"""Independent arithmetic and gate audit of both varying-curve censuses."""

import hashlib
import gzip
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent


def data_bytes(name):
    path = HERE / name
    if path.exists():
        return path.read_bytes()
    assert name.endswith(".jsonl")
    return gzip.decompress((HERE / (name + ".gz")).read_bytes())


def sha(name):
    return hashlib.sha256(data_bytes(name)).hexdigest()


def centered(n, p):
    return n if n <= p // 2 else n - p


def add(P, Q, A, modulus=None):
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and (y1 + y2 == 0 if modulus is None else (y1 + y2) % modulus == 0):
        return None
    numerator = 3 * x1 * x1 + A if P == Q else y2 - y1
    denominator = 2 * y1 if P == Q else x2 - x1
    slope = numerator / denominator if modulus is None else numerator * pow(int(denominator) % modulus, -1, modulus) % modulus
    x3 = slope * slope - x1 - x2
    y3 = slope * (x1 - x3) - y1
    return (x3, y3) if modulus is None else (x3 % modulus, y3 % modulus)


def relation(P, Q, A, modulus=None):
    return add(P, add(Q, Q, A, modulus), A, modulus) is None


def auxiliary_order(a, b, l):
    return 1 + sum((y * y - x * x * x - a * x - b) % l == 0
                   for x in range(l) for y in range(l))


def incidence_row(x, y, l):
    return tuple(v % l for v in (y * y, x * y, y, x ** 3, x ** 2, x, 1))


def check(version):
    suffix = "" if version == 1 else "-v2"
    source = "run.py" if version == 1 else "run_v2.py"
    protocol_name = f"protocol{suffix}.json"
    result = json.loads((HERE / f"result{suffix}.json").read_text())
    protocol = json.loads((HERE / protocol_name).read_text())
    rows_name = f"rows{suffix}.jsonl"
    assert result["status"] == "PASS"
    assert result["protocol_sha256"] == sha(protocol_name)
    assert result["source_sha256"] == sha(source)
    assert result["sage_runtime_sha256"] == sha(f"sage-runtime-info{suffix}.json")
    assert result["rows_sha256"] == sha(rows_name)
    assert (HERE / f"run{suffix}.stderr").stat().st_size == 0
    rows = [json.loads(line) for line in data_bytes(rows_name).decode().splitlines()]
    p = protocol["finite_field_curve"]["prime"]
    l = protocol["auxiliary_condition"]["prime"]
    gate_count = protocol["auxiliary_condition"]["reverse_mestre_count"]
    counts = Counter()
    aux_counts = Counter()
    reduced = rational = accepted = accepted_reduced = accepted_rational = 0
    for rec in rows:
        x1p, y1p = rec["reduced_points"][0]
        x2p, y2p = rec["reduced_points"][1]
        x1, y1 = rec["lifted_points"][0]
        x2, y2 = rec["lifted_points"][1]
        assert (x1, y1, x2, y2) == tuple(centered(n, p) for n in (x1p, y1p, x2p, y2p))
        assert (y1p * y1p - x1p ** 3 + x1p + 2) % p == 0
        assert (y2p * y2p - x2p ** 3 + x2p + 2) % p == 0
        reduced_event = relation((x1p, y1p), (x2p, y2p), -1, p)
        assert reduced_event == rec["reduced_relation"]
        reduced += int(reduced_event)
        rational_event = False
        if x1 == x2:
            status = "same_x"
        else:
            v1 = Fraction(y1 * y1 - x1 ** 3)
            v2 = Fraction(y2 * y2 - x2 ** 3)
            A = (v1 - v2) / (x1 - x2)
            B = v1 - A * x1
            assert (str(A), str(B)) == (rec["A"], rec["B"])
            assert A.denominator % p and B.denominator % p
            assert (A.numerator * pow(A.denominator, -1, p) + 1) % p == 0
            assert (B.numerator * pow(B.denominator, -1, p) + 2) % p == 0
            if 4 * A ** 3 + 27 * B ** 2 == 0:
                status = "singular_curve"
            else:
                assert y1 * y1 == x1 ** 3 + A * x1 + B
                assert y2 * y2 == x2 ** 3 + A * x2 + B
                rational_event = relation((Fraction(x1), Fraction(y1)),
                                          (Fraction(x2), Fraction(y2)), A)
                assert not rational_event or reduced_event
                if A.denominator % l == 0 or B.denominator % l == 0:
                    status = "aux_nonintegral"
                else:
                    a = A.numerator * pow(A.denominator, -1, l) % l
                    b = B.numerator * pow(B.denominator, -1, l) % l
                    if (4 * a ** 3 + 27 * b ** 2) % l == 0:
                        status = "aux_bad_reduction"
                    else:
                        order = auxiliary_order(a, b, l)
                        aux_counts[order] += 1
                        assert order == rec["aux_order"]
                        rank = 1 if incidence_row(x1, y1, l) == incidence_row(x2, y2, l) else 2
                        assert rank == rec["aux_incidence_rank"]
                        if rank < 2:
                            status = "aux_rank_lt_2"
                        elif order != gate_count:
                            status = "aux_order_other"
                        else:
                            status = "accepted"
        assert status == rec["status"]
        assert rational_event == rec["rational_relation"]
        assert (status == "accepted") == rec["accepted"]
        counts[status] += 1
        rational += int(rational_event)
        if status == "accepted":
            accepted += 1
            accepted_reduced += int(reduced_event)
            accepted_rational += int(rational_event)
    assert len(rows) == result["total_pairs"]
    assert counts == result["status_counts"]
    assert aux_counts == {int(k): v for k, v in result["auxiliary_curve_order_counts"].items()}
    assert (reduced, rational, accepted, accepted_reduced, accepted_rational) == (
        result["reduced_relation_pairs"], result["rational_relation_pairs"],
        result["accepted_pairs"], result["accepted_reduced_relation_pairs"],
        result["accepted_rational_relation_pairs"])
    return rows


def main():
    old = check(1)
    new = check(2)
    assert len(old) == len(new) == 1722
    assert all(a["reduced_points"] == b["reduced_points"] and
               a["A"] == b["A"] and a["B"] == b["B"]
               for a, b in zip(old, new) if "A" in a and "A" in b)
    accepted = [rec for rec in new if rec["accepted"]]
    accepted_reduced = [rec for rec in accepted if rec["reduced_relation"]]
    local_witnesses = []
    for rec in accepted_reduced:
        A = Fraction(rec["A"])
        a = A.numerator * pow(A.denominator, -1, 7) % 7
        P1 = tuple(x % 7 for x in rec["lifted_points"][0])
        P2 = tuple(x % 7 for x in rec["lifted_points"][1])
        two_P2 = add(P2, P2, a, 7)
        relation_sum = add(P1, two_P2, a, 7)
        assert relation_sum is not None
        local_witnesses.append({"P1_mod7": P1, "P2_mod7": P2,
                                "twice_P2_mod7": two_P2,
                                "relation_sum_mod7": relation_sum})
    assert len(local_witnesses) == 2
    third_protocol = json.loads((HERE / "protocol-v3.json").read_text())
    third = json.loads((HERE / "result-v3.json").read_text())
    sage_third = json.loads((HERE / "sage-audit-v3.json").read_text())
    assert third["status"] == sage_third["status"] == "PASS"
    assert third["protocol_sha256"] == sha("protocol-v3.json")
    assert third["source_sha256"] == sha("run_v3.py")
    assert third["input_rows_sha256"] == third_protocol["input"]["rows_sha256"] == sha("rows-v2.jsonl")
    assert third["rows_sha256"] == sage_third["rows_sha256"] == sha("rows-v3.jsonl")
    assert sage_third["source_sha256"] == sha("sage_audit_v3.py")
    assert sage_third["runtime_sha256"] == sha("sage-runtime-info-v3.json")
    assert (HERE / "run-v3.stderr").stat().st_size == 0
    assert (HERE / "sage-audit-v3.stderr").stat().st_size == 0
    third_rows = [json.loads(line) for line in (HERE / "rows-v3.jsonl").read_text().splitlines()]
    assert len(third_rows) == third["input_pairs"] == sage_third["checked_rows"] == len(accepted)
    assert Counter(row["status"] for row in third_rows) == third["status_counts"]
    assert Counter(row["aux_order"] for row in third_rows) == {int(k): v for k, v in third["auxiliary_curve_order_counts"].items()}
    assert sum(row["strict_accepted"] for row in third_rows) == third["strict_accepted_pairs"]
    assert sum(row["weak_accepted"] for row in third_rows) == third["weak_accepted_pairs"]
    assert sum(row["local_relation"] for row in third_rows) == third["good_reduction_local_relation_count"]
    print(json.dumps({
        "status": "PASS",
        "v1_rows": len(old),
        "v2_rows": len(new),
        "v2_accepted_ordered_pairs": len(accepted),
        "v2_accepted_curves": len({(rec["A"], rec["B"]) for rec in accepted}),
        "v2_accepted_unordered_pairs": len({tuple(sorted(map(tuple, rec["reduced_points"]))) for rec in accepted}),
        "v2_accepted_reduced_event_local_witnesses": local_witnesses,
        "v3_second_prime_checked_rows": len(third_rows),
        "v3_strict_accepted_pairs": third["strict_accepted_pairs"],
        "v3_weak_accepted_pairs": third["weak_accepted_pairs"],
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
