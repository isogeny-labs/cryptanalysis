#!/usr/bin/env python3
"""Find signed floor certificates from degree-2 incidence components."""
import hashlib
import json
from collections import Counter, defaultdict, deque
from pathlib import Path

from degree_subset_audit import row_degree

HERE = Path(__file__).resolve().parent
CASES = [(42, "conductor_validation42.json"),
         (60, "conductor_validation.json"),
         (70, "conductor_validation70.json"),
         (90, "conductor_validation90.json"),
         (150, "conductor_validation150.json"),
         (210, "conductor_validation210.json")]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(rows, nonfloor):
    owners = defaultdict(list)
    for row_index, row in rows.items():
        for column in row:
            if column in nonfloor:
                owners[column].append(row_index)
    parent = {index: index for index in rows}

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for incident in owners.values():
        for index in incident[1:]:
            parent[find(index)] = find(incident[0])
    grouped = defaultdict(list)
    for index in rows:
        grouped[find(index)].append(index)
    return list(grouped.values()), owners


def signed_component(row_indices, rows, owners, floor):
    touched = {column for index in row_indices for column in rows[index] if column not in floor}
    if len(touched) != len(row_indices):
        return None, "unequal row and lower-column counts"
    if not all(sum(column in floor for column in rows[index]) == 1 for index in row_indices):
        return None, "a row does not touch exactly one floor column"
    adjacency = defaultdict(list)
    for column in touched:
        incident = [(index, rows[index][column]) for index in owners[column]]
        if sorted(value for _, value in incident) != [1, 1, 2]:
            return None, "a lower-column incidence is not [1,1,2]"
        heavy = next(index for index, value in incident if value == 2)
        light = [index for index, value in incident if value == 1]
        for index in light:
            adjacency[heavy].append((index, -1))
            adjacency[index].append((heavy, -1))
    signs = {row_indices[0]: 1}
    queue = deque([row_indices[0]])
    while queue:
        index = queue.popleft()
        for neighbour, multiplier in adjacency[index]:
            required = signs[index] * multiplier
            if neighbour in signs:
                if signs[neighbour] != required:
                    return None, "inconsistent signed incidence cycle"
            else:
                signs[neighbour] = required
                queue.append(neighbour)
    if len(signs) != len(row_indices):
        return None, "signed incidence disconnected"
    result = Counter()
    for index, sign in signs.items():
        for column, value in rows[index].items():
            result[column] += sign * value
    result = {column: value for column, value in result.items() if value}
    if not set(result) <= floor or set(result.values()) - {-1, 1}:
        return None, "integer replay failed"
    if len(result) != len(row_indices):
        return None, "floor support does not match row count"
    return {"signed_rows": {str(index): value for index, value in sorted(signs.items())},
            "signed_floor_columns": {str(column): value for column, value in sorted(result.items())}}, None


def main():
    cases = []
    for f, receipt_name in CASES:
        source = HERE / f"data/exp11_class_walk_D7_f{f}.json"
        receipt_path = HERE / receipt_name
        data = json.loads(source.read_text())
        receipt = json.loads(receipt_path.read_text())
        assert receipt["status"] == "verified" and receipt["source_sha256"] == digest(source)
        floor = {i for i, d in enumerate(receipt["column_conductors"]) if d == f}
        nonfloor = set(range(data["class_size"])) - floor
        degree2_rows = {index: {int(k): int(v) for k, v in encoded.items()}
                        for index, encoded in enumerate(data["relation_rows"]) if row_degree(encoded) == 2}
        groups, owners = components(degree2_rows, nonfloor)
        accepted = []
        rejected = []
        for group in groups:
            certificate, reason = signed_component(group, degree2_rows, owners, floor)
            if certificate:
                accepted.append(certificate)
            else:
                rejected.append({"rows": len(group), "reason": reason})
        used_rows = Counter(int(index) for certificate in accepted for index in certificate["signed_rows"])
        used_floor = Counter(int(index) for certificate in accepted for index in certificate["signed_floor_columns"])
        assert all(count == 1 for count in used_rows.values())
        assert all(count == 1 for count in used_floor.values())
        if f in (42, 70, 90, 150, 210):
            assert set(used_floor) == floor
        j_pairs = defaultdict(list)
        for column in floor:
            j_pairs[receipt["column_j"][column]].append(column)
        assert all(len(columns) == 2 for columns in j_pairs.values())
        partner = {a: b for a, b in j_pairs.values()} | {b: a for a, b in j_pairs.values()}
        vectors = [{int(k): value for k, value in certificate["signed_floor_columns"].items()}
                   for certificate in accepted]
        owner = {column: block for block, vector in enumerate(vectors) for column in vector}
        pair_swap = []
        for block, vector in enumerate(vectors):
            targets = {owner[partner[column]] for column in vector}
            assert len(targets) == 1
            target = next(iter(targets))
            signs = {value * vectors[target][partner[column]] for column, value in vector.items()}
            assert len(signs) == 1 and signs <= {-1, 1}
            pair_swap.append({"from_block": block, "to_block": target, "sign": next(iter(signs))})
        cases.append({"f": f, "source_sha256": digest(source),
                      "conductor_receipt_sha256": digest(receipt_path),
                      "degree2_rows": len(degree2_rows), "components": len(groups),
                      "signed_floor_components": len(accepted),
                      "component_sizes": [len(certificate["signed_rows"]) for certificate in accepted],
                      "covered_floor_columns": len(used_floor),
                      "rejected_components": rejected, "pair_swap": pair_swap,
                      "certificates": accepted})
    output = {"status": "verified", "integer_replay": True, "cases": cases}
    (HERE / "degree2_graph_audit.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "verified", "components": {str(c["f"]): c["signed_floor_components"] for c in cases}}))


if __name__ == "__main__":
    main()
