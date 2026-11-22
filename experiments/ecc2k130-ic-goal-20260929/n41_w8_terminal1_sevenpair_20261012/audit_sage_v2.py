#!/usr/bin/env sage -python
"""Replay the first-edge four-sign N41 relation and measure row rank."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "n41_w8_sixpair_mitm_20261011"
GEOMETRY = ROOT / "n41_w7_entropy_cubic_20261011/w8/geometry.json"
FIXTURE = ROOT / "n41_w7_entropy_cubic_20261011/w8/fixture.json"
R = 549756390943
ROTATIONS = (0, 7, 14, 21, 28, 35, 0)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    audit_protocol = json.loads((HERE / "audit_protocol_v2.json").read_text())
    assert audit_protocol["status"] == "FROZEN_N41_TERMINAL4_SAGE_AUDIT"
    inputs = {"source": Path(__file__), "protocol": HERE / "protocol_v2.json",
              "query": HERE / "query_result_v2.json",
              "geometry": GEOMETRY, "fixture": FIXTURE,
              "input": BASE / "join_input.tsv",
              "runtime": HERE / "sage_runtime_info.json"}
    assert audit_protocol["sha256"] == {name: sha(path) for name, path in inputs.items()}
    protocol = json.loads((HERE / "protocol_v2.json").read_text())
    query = json.loads((HERE / "query_result_v2.json").read_text())
    geometry = json.loads(GEOMETRY.read_text())
    fixture = json.loads(FIXTURE.read_text())
    runtime = json.loads((HERE / "sage_runtime_info.json").read_text())
    assert runtime["status"] == "verified"
    assert protocol["source_sha256"]["geometry"] == sha(GEOMETRY)
    assert protocol["source_sha256"]["fixture"] == sha(FIXTURE)
    assert query["protocol_sha256"] == sha(HERE / "protocol_v2.json")
    assert query["stdout_sha256"] == sha(HERE / "join_v2.stdout.txt")
    assert query["stderr_sha256"] == sha(HERE / "join_v2.stderr.txt")
    assert query["status"] == "HITS_PENDING_SAGE_REPLAY" and len(query["hit_lines"]) == 1
    assert query["preflight_group_checks_passed"]
    rows = {int(row["mask"]): row for row in geometry["rows"]}
    edges = [(a, a ^ 184) for a in sorted(rows)
             if a < (a ^ 184) and a ^ 184 in rows
             and rows[a]["column"] != rows[a ^ 184]["column"]]
    assert len(edges) == 35
    selected_columns = sorted({int(rows[mask]["column"])
                               for edge in edges for mask in edge})
    assert len(selected_columns) == 70
    column_position = {column: index for index, column in enumerate(selected_columns)}
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, name="t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def dec(value):
        return field(ring([(int(value) >> i) & 1 for i in range(41)]))

    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

    def xy(point):
        return [enc(point[0]), enc(point[1])]

    def frobenius(point, exponent):
        return curve(point[0]**(1 << exponent), point[1]**(1 << exponent))

    raw = {mask: curve(*map(dec, row["raw_point"])) for mask, row in rows.items()}
    projected = {mask: 4 * point for mask, point in raw.items()}
    assert all(point != curve(0) and R * point == curve(0)
               for point in projected.values())
    representatives = {}
    for mask, row in sorted(rows.items()):
        representatives.setdefault(int(row["column"]), mask)
    quotient = {}
    used_masks = {mask for line in query["hit_lines"]
                  for sid in map(int, line.split()[2:9])
                  for mask in edges[sid // 4]}
    for mask in used_masks:
        column = int(rows[mask]["column"])
        rep = projected[representatives[column]]
        images = [(frobenius(rep, exponent), exponent, 1) for exponent in range(41)]
        images += [(-point, exponent, -1) for point, exponent, _ in images]
        matches = [(exponent, sign) for point, exponent, sign in images
                   if point == projected[mask]]
        assert len(matches) == 1
        quotient[mask] = matches[0]

    ring_r = PolynomialRing(GF(R), "L")
    L = ring_r.gen()
    roots = [int(root) for root, _ in (L**2 + L + 2).roots()]
    assert len(roots) == 2
    sample = projected[representatives[min(representatives)]]
    eigenvalues = [value for value in roots if value * sample == frobenius(sample, 1)]
    assert len(eigenvalues) == 1
    eigenvalue = eigenvalues[0]
    replayed = []
    rank_rows = []
    for line in query["hit_lines"]:
        tokens = line.split()
        assert len(tokens) == 12 and tokens[0] == "HIT"
        target_index = int(tokens[1])
        ids = list(map(int, tokens[2:9]))
        assert target_index == 0 and len(ids) == 7 and ids[-1] < 4
        occupied_edges, occupied_columns = set(), set()
        running = curve(0)
        terms = []
        source_pairs = []
        vector = [0] * 70
        for slot, sid in enumerate(ids):
            edge_id, choice = divmod(sid, 4)
            a, b = edges[edge_id]
            assert edge_id not in occupied_edges
            occupied_edges.add(edge_id)
            sign_a, sign_b = divmod(choice, 2)
            pair = (-raw[a] if sign_a else raw[a]) + (-raw[b] if sign_b else raw[b])
            rotated = frobenius(pair, ROTATIONS[slot])
            running += rotated
            source_pairs.append({"slot": slot, "state_id": sid,
                                 "edge_id": edge_id, "masks": [a, b],
                                 "signs": [sign_a, sign_b],
                                 "rotation": ROTATIONS[slot],
                                 "pair_rotated": xy(rotated)})
            for mask, sign_bit in ((a, sign_a), (b, sign_b)):
                column = int(rows[mask]["column"])
                assert column not in occupied_columns
                occupied_columns.add(column)
                exponent, orbit_sign = quotient[mask]
                coefficient = ((-1 if sign_bit else 1) * orbit_sign *
                               pow(eigenvalue, ROTATIONS[slot] + exponent, R)) % R
                assert coefficient != 0
                vector[column_position[column]] = coefficient
                terms.append({"slot": slot, "mask": mask,
                              "column": column,
                              "representative_mask": representatives[column],
                              "orbit_exponent": exponent,
                              "orbit_sign": orbit_sign,
                              "source_sign_bit": sign_bit,
                              "coefficient_mod_r": str(coefficient)})
        assert len(occupied_edges) == 7 and len(occupied_columns) == 14
        expected_raw = fixture["raw_target_preimages"][0]
        assert xy(running) == expected_raw
        assert xy(4 * running) == fixture["public_target_transported"]
        row_sum = curve(0)
        for term in terms:
            row_sum += int(term["coefficient_mod_r"]) * projected[term["representative_mask"]]
        assert row_sum == 4 * running
        rank_rows.append(vector)
        current_rank = int(matrix(GF(R), rank_rows).rank())
        replayed.append({"status": "PASS_INDEPENDENT_RELATION",
                         "raw_target_preimage_index": 0,
                         "state_ids": ids, "right_probes_before_hit": int(tokens[9]),
                         "folded_columns_distinct": len(occupied_columns),
                         "relation_row": terms, "source_pairs": source_pairs,
                         "rank_after_insert": current_rank,
                         "novel_rank": current_rank - (replayed[-1]["rank_after_insert"] if replayed else 0)})
    result = {"status": "PASS_INDEPENDENT_N41_TERMINAL4_RELATION",
              "candidate_id": None, "curve_id": protocol["curve_id"],
              "public_target_transported": fixture["public_target_transported"],
              "raw_preimage_index": 0,
              "verified_hits": len(replayed),
              "rank_from_empty_matrix": replayed[-1]["rank_after_insert"],
              "replayed": replayed,
              "frobenius_eigenvalue_mod_r": str(eigenvalue),
              "audit_protocol_sha256": sha(HERE / "audit_protocol_v2.json"),
              "source_sha256": {"script": sha(Path(__file__)),
                                "protocol": sha(HERE / "protocol_v2.json"),
                                "query": sha(HERE / "query_result_v2.json"),
                                "input": sha(BASE / "join_input.tsv"),
                                "geometry": sha(GEOMETRY),
                                "fixture": sha(FIXTURE),
                                "sage_runtime": sha(HERE / "sage_runtime_info.json")}}
    with (HERE / "sage_audit_result_v2.json").open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(result["status"], result["verified_hits"], result["rank_from_empty_matrix"])


if __name__ == "__main__":
    main()
