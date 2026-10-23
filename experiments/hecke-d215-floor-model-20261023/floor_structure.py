"""Integer certificates for the four D215/f6 floor directions."""
from collections import Counter, defaultdict, deque
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "hecke-regular-branch-second-class-20261023"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(rows, lower):
    owners = defaultdict(list)
    for i, row in rows.items():
        for col in row:
            if col in lower:
                owners[col].append(i)
    parent = {i: i for i in rows}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for incident in owners.values():
        for i in incident[1:]:
            parent[find(i)] = find(incident[0])
    groups = defaultdict(list)
    for i in rows:
        groups[find(i)].append(i)
    return sorted((sorted(g) for g in groups.values()), key=lambda g: g[0]), owners


def signed_certificate(indices, rows, owners, floor):
    touched = {col for i in indices for col in rows[i] if col not in floor}
    assert len(touched) == len(indices) == 14
    assert all(sum(col in floor for col in rows[i]) == 1 for i in indices)
    adjacency = defaultdict(list)
    for col in touched:
        incident = [(i, rows[i][col]) for i in owners[col]]
        assert sorted(value for _, value in incident) == [1, 1, 2]
        heavy = next(i for i, value in incident if value == 2)
        for light in (i for i, value in incident if value == 1):
            adjacency[heavy].append(light)
            adjacency[light].append(heavy)
    signs = {indices[0]: 1}
    queue = deque([indices[0]])
    while queue:
        i = queue.popleft()
        for j in adjacency[i]:
            expected = -signs[i]
            if j in signs:
                assert signs[j] == expected
            else:
                signs[j] = expected
                queue.append(j)
    assert set(signs) == set(indices)
    combined = Counter()
    for i, sign in signs.items():
        for col, value in rows[i].items():
            combined[col] += sign * value
    combined = {col: value for col, value in combined.items() if value}
    assert set(combined) <= floor
    assert len(combined) == 14 and set(combined.values()) <= {-1, 1}
    return {"rows": {str(i): signs[i] for i in sorted(signs)},
            "floor_vector": {str(col): combined[col] for col in sorted(combined)},
            "lower_columns_cancelled": len(touched)}


def main():
    protocol = read(HERE / "protocol.json")
    for name, digest in protocol["source_sha256"].items():
        assert sha(SOURCE / name) == digest, name
    data = read(SOURCE / "data/exp11_class_walk_D215_f6.json")
    audit = read(SOURCE / "audit.json")
    exact = read(SOURCE / "exact_rank.json")
    action = read(HERE / "class_action.json")
    assert audit["status"] == "VERIFIED_D215_F6_BRANCH_MATRIX"
    assert exact["ranks"]["regularized"] == {"full_QQ": 112, "nonfloor_QQ": 108}
    floor = {r["column"] for r in audit["point_records"] if r["endomorphism_conductor"] == 6}
    lower = set(range(len(audit["point_records"]))) - floor
    rows = [{int(k): int(v) for k, v in row.items() if v} for row in data["relation_rows"]]
    degree2_c3 = {i: row for i, row in enumerate(rows)
                  if audit["row_records"][i]["degree"] == 2
                  and audit["row_records"][i]["source_conductor"] == 3}
    groups, owners = components(degree2_c3, lower)
    assert len(degree2_c3) == 56 and len(groups) == 4
    assert [len(g) for g in groups] == [14] * 4
    certificates = [signed_certificate(g, degree2_c3, owners, floor) for g in groups]
    covered = Counter(int(col) for cert in certificates for col in cert["floor_vector"])
    assert set(covered) == floor and set(covered.values()) == {1}
    # Disjoint nonempty supports prove these four vectors are independent.
    degree3_c2 = {i: row for i, row in enumerate(rows)
                  if audit["row_records"][i]["degree"] == 3
                  and audit["row_records"][i]["source_conductor"] == 2}
    lower_signatures = [tuple(sorted((col, value) for col, value in row.items() if col in lower))
                        for row in degree3_c2.values()]
    assert len(degree3_c2) == len(set(lower_signatures)) == 28
    assert action["degree2_c3_sheet_orbits_predicted"] == len(groups)
    assert action["degree2_c3_orbit_length_predicted"] == 14
    assert exact["ranks"]["regularized"]["full_QQ"] - exact["ranks"]["regularized"]["nonfloor_QQ"] == len(certificates)
    result = {"status": "VERIFIED_FOUR_SIGNED_FLOOR_DIRECTIONS",
              "protocol_sha256": sha(HERE / "protocol.json"),
              "class_action_sha256": sha(HERE / "class_action.json"),
              "source_sha256": protocol["source_sha256"],
              "c3_degree2_rows": len(degree2_c3),
              "signed_components": len(groups), "component_sizes": [len(g) for g in groups],
              "covered_floor_columns": len(covered),
              "c2_degree3_rows": len(degree3_c2),
              "distinct_degree3_lower_signatures": len(set(lower_signatures)),
              "full_QQ_rank": 112, "nonfloor_QQ_rank": 108,
              "floor_kernel_dimension": 4, "certificates": certificates,
              "candidate_id": None, "timing_claim": None}
    (HERE / "floor_structure.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("certificates", "source_sha256")}, sort_keys=True))


if __name__ == "__main__":
    main()
