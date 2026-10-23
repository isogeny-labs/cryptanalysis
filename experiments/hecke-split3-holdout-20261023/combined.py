"""Replay and prove the ten explicit floor directions span the saved kernel."""
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def sha(name):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()


def rank_mod(rows, q):
    pivots = {}
    for row in rows:
        current = {int(k): int(v) % q for k, v in row.items() if int(v) % q}
        while current:
            col = min(current)
            if col not in pivots:
                inverse = pow(current[col], -1, q)
                pivots[col] = {k: v * inverse % q for k, v in current.items()}
                break
            a = current[col]
            for k, v in pivots[col].items():
                updated = (current.get(k, 0) - a * v) % q
                if updated:
                    current[k] = updated
                else:
                    current.pop(k, None)
    return len(pivots)


def replay(data, coefficients):
    combined = Counter()
    for encoded, sign in coefficients.items():
        for col, value in data["relation_rows"][int(encoded)].items():
            combined[int(col)] += int(sign) * int(value)
    return {str(col): value for col, value in combined.items() if value}


def main():
    protocol = read("producer_protocol.json")
    assert protocol["predictions"]["floor_kernel_rank"] == 6
    data, audit = read("data/exp11_class_walk_D431_f6.json"), read("audit.json")
    d2, d3 = read("floor_structure.json"), read("cycle_model.json")["cases"]["D431"]
    assert d2["status"] == "VERIFIED_SIX_SIGNED_DEGREE2_FLOOR_DIRECTIONS"
    assert d3["status"] == "PASS_NORM3_CYCLE_MODEL"
    floor = {str(r["column"]) for r in audit["point_records"] if r["endomorphism_conductor"] == 6}
    vectors = []
    for cert in d2["certificates"]:
        got = replay(data, cert["rows"])
        assert got == cert["floor_vector"] and set(got) <= floor
        vectors.append(got)
    for cert in d3["certificates"]:
        got = replay(data, cert["row_coefficients"])
        assert got == cert["floor_vector"] and set(got) <= floor
        vectors.append(got)
    assert len(vectors) == 10
    ranks = {str(q): {"degree2": rank_mod(vectors[:6], q),
                      "degree3": rank_mod(vectors[6:], q),
                      "combined": rank_mod(vectors, q)}
             for q in (23, 1000000007, 2147483647)}
    assert all(v == {"degree2": 6, "degree3": 4, "combined": 10} for v in ranks.values())
    exact = audit["ranks"]["2+3"]
    assert exact == {"full_QQ": 168, "nonfloor_QQ": 158}
    result = {"status": "PASS_TEN_FLOOR_DIRECTIONS_SPAN_KERNEL",
              "producer_protocol_sha256": sha("producer_protocol.json"),
              "data_sha256": sha("data/exp11_class_walk_D431_f6.json"),
              "audit_sha256": sha("audit.json"),
              "degree2_certificate_sha256": sha("floor_structure.json"),
              "degree3_certificate_sha256": sha("cycle_model.json"),
              "ranks_mod_prime": ranks,
              "full_QQ_rank": 168, "nonfloor_QQ_rank": 158,
              "floor_kernel_dimension": 10,
              "frozen_rank_prediction": 6,
              "candidate_id": None, "timing_claim": None}
    (HERE / "combined.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
