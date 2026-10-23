"""Independent class-number and dense-rank replay of the prospective holdout."""
from collections import Counter
import hashlib
import json
from math import gcd, isqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def sha(name):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()


def class_number(disc):
    total = 0
    for a in range(1, isqrt((-disc)//3)+2):
        for b in range(-a, a+1):
            n = b*b-disc
            if n % (4*a):
                continue
            c = n//(4*a)
            if a > c or (b < 0 and (abs(b) == a or a == c)):
                continue
            if gcd(gcd(a, abs(b)), c) == 1:
                total += 1
    return total


def dense_rank(rows, columns, prime):
    a = [[int(row.get(str(j), 0)) % prime for j in columns] for row in rows]
    pivot = 0
    for col in range(len(columns)):
        chosen = next((r for r in range(pivot, len(a)) if a[r][col]), None)
        if chosen is None:
            continue
        a[pivot], a[chosen] = a[chosen], a[pivot]
        inverse = pow(a[pivot][col], -1, prime)
        a[pivot] = [value*inverse % prime for value in a[pivot]]
        for row in range(pivot+1, len(a)):
            factor = a[row][col]
            if factor:
                a[row] = [(x-factor*y) % prime for x, y in zip(a[row], a[pivot])]
        pivot += 1
        if pivot == len(a):
            break
    return pivot


def replay_row_sum(data, encoded):
    result = Counter()
    for row_index, coefficient in encoded.items():
        for col, value in data["relation_rows"][int(row_index)].items():
            result[col] += int(coefficient)*int(value)
    return {col: value for col, value in result.items() if value}


def main():
    selection, protocol = read("selection.json"), read("producer_protocol.json")
    gate, data, audit, certs = (read(name) for name in
                                 ("fiber_gate_result.json", "data/exp11_class_walk_D623_f6.json",
                                  "audit.json", "certificates.json"))
    assert selection["status"] == "FROZEN_QUALIFIED_HOLDOUT_SELECTED"
    assert selection["protocol_sha256"] == sha("selection_protocol.json")
    assert selection["chosen"] == {"d":623,"h1":22,"h2":22,"h3":44,
                                   "norm2_order_f3":22,"norm3_order_f2":22,
                                   "frobenius_discriminant_mod_11":1,
                                   "degree2_directions_predicted":4,
                                   "degree3_directions_predicted":0,
                                   "floor_rank_predicted":4,"v":74,"p":11083,"u_abs":148}
    assert protocol["selection_sha256"] == sha("selection.json")
    for name, digest in protocol["source_sha256"].items():
        assert sha(name) == digest, name
    assert all(11083 % q for q in range(2, isqrt(11083)+1))
    assert 148*148-4*11083 == -623*6*6
    assert (148*148-4*11083)%11 == 1
    classes = {str(f):class_number(-623*f*f) for f in (1,2,3,6)}
    assert classes == {"1":22,"2":22,"3":44,"6":44}
    assert gate["status"] == "PASS_UNIFORM_TWO_SHEET_GATE"
    assert {f: row["class_number"] for f, row in gate["strata"].items()} == classes
    assert audit["status"] == "VERIFIED_D623_F6_MATRIX"
    assert (data["class_size"],data["relations"],data["rank"]) == (264,220,176)
    assert audit["ranks"]["3"] == {"full_QQ":88,"nonfloor_QQ":88}
    assert audit["ranks"]["2+3"] == {"full_QQ":176,"nonfloor_QQ":172}
    assert certs["status"] == "PASS_PROSPECTIVE_FOUR_FLOOR_DIRECTIONS"
    floor = {str(row["column"]) for row in audit["point_records"]
             if row["endomorphism_conductor"] == 6}
    vectors = []
    for cert in certs["degree2_certificates"]+certs["degree3_certificates"]:
        replay = replay_row_sum(data, cert["row_coefficients"])
        assert replay == cert["floor_vector"] and set(replay) <= floor
        vectors.append(replay)
    assert len(vectors) == 4
    columns = sorted(map(int, floor))
    dense = {str(q):dense_rank(vectors, columns, q) for q in (23,1000000007,2147483647)}
    assert all(rank == 4 for rank in dense.values())
    result = {"status":"PASS_PROSPECTIVE_NONPERIODIC_FLOOR_RULE",
              "selection_protocol_sha256":sha("selection_protocol.json"),
              "producer_protocol_sha256":sha("producer_protocol.json"),
              "data_sha256":sha("data/exp11_class_walk_D623_f6.json"),
              "audit_sha256":sha("audit.json"),
              "certificates_sha256":sha("certificates.json"),
              "class_numbers":classes,"dense_certificate_ranks":dense,
              "frozen_floor_rank":4,"observed_floor_rank":4,
              "candidate_id":None,"timing_claim":None}
    (HERE/'validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
