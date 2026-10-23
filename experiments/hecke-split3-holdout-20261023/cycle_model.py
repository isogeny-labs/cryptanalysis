"""Replay the norm-3 cycle projection and its period-three kernel."""
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CASES = {
    "D215": ROOT / "experiments/hecke-regular-branch-second-class-20261023",
    "D431": HERE,
}
DATA = {"D215": "data/exp11_class_walk_D215_f6.json",
        "D431": "data/exp11_class_walk_D431_f6.json"}


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rank_mod(rows, q):
    pivots = {}
    for row in rows:
        current = {int(k): int(v) % q for k, v in row.items() if int(v) % q}
        while current:
            col = min(current)
            if col not in pivots:
                inv = pow(current[col], -1, q)
                pivots[col] = {k: v * inv % q for k, v in current.items()}
                break
            a = current[col]
            for k, v in pivots[col].items():
                updated = (current.get(k, 0) - a * v) % q
                if updated:
                    current[k] = updated
                else:
                    current.pop(k, None)
    return len(pivots)


def cycle_orders(neighbours):
    unseen = set(neighbours)
    orders = []
    while unseen:
        first = min(unseen)
        order, previous, current = [], None, first
        while current not in order:
            order.append(current)
            unseen.remove(current)
            choices = sorted(neighbours[current] - ({previous} if previous is not None else set()))
            assert choices
            next_vertex = choices[0]
            previous, current = current, next_vertex
        assert current == first and len(order) >= 3
        assert set(order) == set(order) & set(neighbours)
        orders.append(order)
    return orders


def analyze(label, protocol):
    path = CASES[label]
    data, audit = read(path / DATA[label]), read(path / "audit.json")
    points = audit["point_records"]
    floor = {r["column"] for r in points if r["endomorphism_conductor"] == 6}
    c2 = {r["column"] for r in points if r["endomorphism_conductor"] == 2}
    indexed_rows = {}
    neighbours = {}
    for record in audit["row_records"]:
        if record["degree"] != 3 or record["source_conductor"] != 2:
            continue
        row_index, src = record["row"], record["source_column"]
        row = {int(k): int(v) for k, v in data["relation_rows"][row_index].items() if v}
        lower = {k: v for k, v in row.items() if k not in floor}
        assert len(lower) == 3 and set(lower.values()) == {1}
        assert set(lower) <= c2 and src in lower
        indexed_rows[src] = (row_index, row)
        neighbours[src] = set(lower) - {src}
    assert set(indexed_rows) == c2
    assert all(len(adj) == 2 and all(src in neighbours[j] for j in adj)
               for src, adj in neighbours.items())
    cycles = cycle_orders(neighbours)
    predicted = protocol["predicted"][label]
    lengths = sorted(map(len, cycles))
    assert lengths == [predicted["norm3_order"]] * predicted["cycle_count"]
    projected = [{str(k): v for k, v in row.items() if k in c2}
                 for _, row in indexed_rows.values()]
    predicted_nullity = sum(2 if len(cycle) % 3 == 0 else 0 for cycle in cycles)
    assert predicted_nullity == predicted["degree3_c2_floor_kernel_rank"]
    modular_ranks = {str(q): rank_mod(projected, q) for q in (23, 1000000007, 2147483647)}
    assert all(len(indexed_rows) - rank == predicted_nullity for rank in modular_ranks.values())
    certificates = []
    for cycle in cycles:
        if len(cycle) % 3:
            continue
        for pattern in ((1, -1, 0), (0, 1, -1)):
            coeffs = {indexed_rows[src][0]: pattern[k % 3]
                      for k, src in enumerate(cycle) if pattern[k % 3]}
            combined = Counter()
            for row_index, coefficient in coeffs.items():
                row = data["relation_rows"][row_index]
                for col, value in row.items():
                    combined[int(col)] += coefficient * int(value)
            combined = {k: v for k, v in combined.items() if v}
            assert set(combined) <= floor and combined
            certificates.append({"row_coefficients": {str(k): v for k, v in sorted(coeffs.items())},
                                 "floor_vector": {str(k): v for k, v in sorted(combined.items())},
                                 "row_support": len(coeffs), "floor_support": len(combined)})
    assert len(certificates) == predicted_nullity
    floor_vector_ranks = {str(q): rank_mod([c["floor_vector"] for c in certificates], q)
                          for q in (23, 1000000007, 2147483647)}
    assert all(rank == predicted_nullity for rank in floor_vector_ranks.values())
    return {"status": "PASS_NORM3_CYCLE_MODEL", "label": label,
            "row_count": len(indexed_rows), "cycle_count": len(cycles),
            "cycle_lengths": lengths, "cycles": cycles,
            "predicted_nullity": predicted_nullity,
            "projected_modular_ranks": modular_ranks,
            "floor_vector_modular_ranks": floor_vector_ranks,
            "certificates": certificates,
            "source_data_sha256": sha(path / DATA[label]),
            "source_audit_sha256": sha(path / "audit.json")}


def main():
    protocol = read(HERE / "cycle_protocol.json")
    sources = {"D431_data": CASES["D431"] / DATA["D431"],
               "D431_audit": CASES["D431"] / "audit.json",
               "D215_data": CASES["D215"] / DATA["D215"],
               "D215_audit": CASES["D215"] / "audit.json",
               "D215_class_action": ROOT / "experiments/hecke-d215-floor-model-20261023/class_action.json",
               "D431_degree3_diagnostic": HERE / "degree3_diagnostic.json"}
    for name, digest in protocol["source_sha256"].items():
        assert sha(sources[name]) == digest, name
    cases = {label: analyze(label, protocol) for label in ("D215", "D431")}
    result = {"status": "VERIFIED_TWO_CLASS_NORM3_CYCLE_RULE",
              "protocol_sha256": sha(HERE / "cycle_protocol.json"),
              "cases": cases, "candidate_id": None, "timing_claim": None}
    (HERE / "cycle_model.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({label: {k: v for k, v in case.items() if k in
                              ("cycle_count", "cycle_lengths", "predicted_nullity", "projected_modular_ranks")}
                      for label, case in cases.items()}, sort_keys=True))


if __name__ == "__main__":
    main()
