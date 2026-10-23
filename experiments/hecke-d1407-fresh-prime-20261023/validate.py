"""Pure-Python replay of the frozen fresh-prime producer receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def digest(name):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()


def rank_mod(rows, modulus):
    pivots = {}
    for row in rows:
        current = {int(k): int(v) % modulus for k, v in row.items() if int(v) % modulus}
        while current:
            col = min(current)
            if col not in pivots:
                inverse = pow(current[col], -1, modulus)
                pivots[col] = {k: v * inverse % modulus for k, v in current.items()}
                break
            multiplier = current[col]
            for k, v in pivots[col].items():
                updated = (current.get(k, 0) - multiplier * v) % modulus
                if updated:
                    current[k] = updated
                else:
                    current.pop(k, None)
    return len(pivots)


def main():
    protocol, gate = read("protocol.json"), read("fiber_gate_result.json")
    data = read("data/exp11_class_walk_D1407_f6.json")
    audit, floor, branch = read("audit.json"), read("floor.json"), read("branch_probe.json")
    for name, expected in protocol["source_sha256"].items():
        assert digest(name) == expected, name
    assert (protocol["p"], protocol["u"]) == (data["p"], data["u"]) == (20407, 176)
    assert 176**2 - 4 * 20407 == -1407 * 6**2
    assert gate["status"] == "PASS_UNIFORM_TWO_SHEET_GATE" and not gate["exceptions"]
    assert {c: v["rational_point_count"] for c, v in gate["strata"].items()} == protocol["expected"]["conductor_counts"]
    assert data["class_size"] == len(data["column_points"]) == protocol["expected"]["class_columns"]
    assert len(set(data["column_points"])) == data["class_size"]
    assert data["relations"] == len(data["relation_rows"]) == protocol["expected"]["relations"]
    assert data["relations_per_l"] == {"2": 192, "3": 96}
    assert audit["status"] == "VERIFIED_D1407_F6_MATRIX"
    assert audit["source_sha256"] == digest("data/exp11_class_walk_D1407_f6.json")
    assert floor["status"] == "VERIFIED_D1407_F6_FLOOR_PREDICTION"
    assert floor["source_sha256"] == digest("data/exp11_class_walk_D1407_f6.json")
    assert all((floor[f] for f in ("graph_match", "pair_match", "span_match", "rank_match")))
    assert branch["status"] == "PASS_FRESH_PRIME_REGULAR_BRANCH"
    assert branch["regular_j"] == 20407 - 121
    assert branch["regular_point"] in branch["regular_fiber"]
    assert branch["cusp_point"] not in branch["regular_fiber"]
    assert branch["branch_in_selected_class"] is False
    assert branch["regular_j_trace"] == 230
    rows = data["relation_rows"]
    nonfloor = {v["column"] for v in audit["points"] if v["endomorphism_conductor"] != 6}
    projected = [{k: v for k, v in row.items() if int(k) in nonfloor} for row in rows]
    ranks = {str(q): {"full": rank_mod(rows, q), "nonfloor": rank_mod(projected, q)}
             for q in (23, 1000000007, 2147483647)}
    assert all(v == {"full": 240, "nonfloor": 206} for v in ranks.values())
    result = {"status": "PASS_FRESH_PRIME_REPLAY", "protocol_sha256": digest("protocol.json"),
              "producer_sha256": digest("data/exp11_class_walk_D1407_f6.json"),
              "ranks": ranks, "branch_in_selected_class": False,
              "candidate_id": None, "timing_claim": None}
    (HERE / "validation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
