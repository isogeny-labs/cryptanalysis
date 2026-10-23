"""Signed norm-2 certificates and norm-3 cycle audit for frozen D623."""
from collections import Counter, defaultdict, deque
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def sha(name):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()


def rank_mod(vectors, q):
    pivots = {}
    for vector in vectors:
        current = {int(k): int(v) % q for k, v in vector.items() if int(v) % q}
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


def replay(rows, coeffs):
    total = Counter()
    for i, sign in coeffs.items():
        for col, value in rows[i].items():
            total[col] += sign * value
    return {col: value for col, value in total.items() if value}


def degree2_certificates(rows, meta, floor, lower, expected):
    selected = {i: row for i, row in enumerate(rows)
                if meta[i]["degree"] == 2 and meta[i]["source_conductor"] == 3}
    owners = defaultdict(list)
    for i, row in selected.items():
        for col in row:
            if col in lower:
                owners[col].append(i)
    parent = {i: i for i in selected}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for incident in owners.values():
        for i in incident[1:]:
            parent[find(i)] = find(incident[0])
    grouped = defaultdict(list)
    for i in selected:
        grouped[find(i)].append(i)
    groups = sorted((sorted(g) for g in grouped.values()), key=lambda g: g[0])
    assert len(groups) == expected["norm2_cycles"]
    assert all(len(g) == expected["norm2_cycle_length"] for g in groups)
    certificates = []
    for group in groups:
        touched = {col for i in group for col in selected[i] if col in lower}
        assert len(touched) == len(group)
        assert all(sum(col in floor for col in selected[i]) == 1 for i in group)
        adjacency = defaultdict(list)
        for col in touched:
            incident = [(i, selected[i][col]) for i in owners[col]]
            assert sorted(value for _, value in incident) == [1, 1, 2]
            heavy = next(i for i, value in incident if value == 2)
            for light in (i for i, value in incident if value == 1):
                adjacency[heavy].append(light)
                adjacency[light].append(heavy)
        signs = {group[0]: 1}
        queue = deque([group[0]])
        while queue:
            i = queue.popleft()
            for j in adjacency[i]:
                needed = -signs[i]
                if j in signs:
                    assert signs[j] == needed
                else:
                    signs[j] = needed
                    queue.append(j)
        assert set(signs) == set(group)
        vector = replay(rows, signs)
        assert set(vector) <= floor and len(vector) == len(group)
        assert set(vector.values()) <= {-1, 1}
        certificates.append({"row_coefficients": {str(i): signs[i] for i in sorted(signs)},
                             "floor_vector": {str(col): value for col, value in sorted(vector.items())},
                             "row_support": len(signs), "floor_support": len(vector)})
    covered = Counter(int(col) for c in certificates for col in c["floor_vector"])
    assert set(covered) == floor and set(covered.values()) == {1}
    return certificates


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
            previous, current = current, choices[0]
        assert current == first
        orders.append(order)
    return orders


def degree3_certificates(rows, meta, point_records, floor, expected):
    c2 = {r["column"] for r in point_records if r["endomorphism_conductor"] == 2}
    indexed = {}
    neighbours = {}
    for record in meta:
        if record["degree"] != 3 or record["source_conductor"] != 2:
            continue
        i, src = record["row"], record["source_column"]
        projected = {col: value for col, value in rows[i].items() if col not in floor}
        assert len(projected) == 3 and set(projected) <= c2
        assert set(projected.values()) == {1} and src in projected
        indexed[src] = i
        neighbours[src] = set(projected) - {src}
    assert set(indexed) == c2
    assert all(len(adj) == 2 and all(src in neighbours[j] for j in adj)
               for src, adj in neighbours.items())
    cycles = cycle_orders(neighbours)
    assert len(cycles) == expected["norm3_cycles"]
    assert all(len(c) == expected["norm3_cycle_length"] for c in cycles)
    assert all(len(cycle) % 3 != 0 for cycle in cycles)
    # The three-term recurrence has period three, so these cycles admit no
    # nonzero rational projected dependency. The exact matrix rank is audited
    # independently by audit.py, including the other conductor strata.
    return cycles, []


def main():
    protocol, selection = read("producer_protocol.json"), read("selection.json")
    assert protocol["status"] == "FROZEN_BEFORE_GATE_AND_PRODUCER"
    assert protocol["selection_sha256"] == sha("selection.json")
    data, audit = read("data/exp11_class_walk_D623_f6.json"), read("audit.json")
    assert audit["status"] == "VERIFIED_D623_F6_MATRIX"
    rows = [{int(k): int(v) for k, v in row.items() if v} for row in data["relation_rows"]]
    floor = {r["column"] for r in audit["point_records"] if r["endomorphism_conductor"] == 6}
    lower = set(range(data["class_size"])) - floor
    expected = protocol["predictions"]
    d2 = degree2_certificates(rows, audit["row_records"], floor, lower, expected)
    cycles, d3 = degree3_certificates(rows, audit["row_records"], audit["point_records"], floor, expected)
    assert len(d2) == expected["degree2_floor_directions"] == 4
    assert len(d3) == expected["degree3_floor_directions"] == 0
    vectors = [c["floor_vector"] for c in d2]
    ranks = {str(q): {"degree2": rank_mod(vectors, q),
                      "degree3": 0,
                      "combined": rank_mod(vectors, q)}
             for q in (23, 1000000007, 2147483647)}
    assert all(v == {"degree2": 4, "degree3": 0, "combined": 4} for v in ranks.values())
    assert audit["ranks"]["3"] == {"full_QQ": 88, "nonfloor_QQ": 88}
    assert audit["ranks"]["2+3"] == {"full_QQ": 176, "nonfloor_QQ": 172}
    assert expected["floor_kernel_rank"] == 4
    result = {"status": "PASS_PROSPECTIVE_FOUR_FLOOR_DIRECTIONS",
              "producer_protocol_sha256": sha("producer_protocol.json"),
              "selection_sha256": sha("selection.json"),
              "data_sha256": sha("data/exp11_class_walk_D623_f6.json"),
              "audit_sha256": sha("audit.json"),
              "degree2_certificates": d2, "degree3_certificates": d3,
              "degree3_cycles": cycles,
              "ranks_mod_prime": ranks,
              "frozen_floor_rank": 4, "observed_floor_rank": 4,
              "candidate_id": None, "timing_claim": None}
    (HERE / "certificates.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in
                      ("degree2_certificates", "degree3_certificates", "degree3_cycles")}, sort_keys=True))


if __name__ == "__main__":
    main()
