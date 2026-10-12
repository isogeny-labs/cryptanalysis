#!/usr/bin/env sage -python
"""Replay the nine-pair hit from source masks in independently checked Sage."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, Zmod


HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "n41_w7_entropy_cubic_20261011/w8"
INPUT = HERE.parent / "n41_w8_sixpair_mitm_20261011/join_input.tsv"
R = 549756390943
ROTATIONS = (0, 7, 14, 21, 28, 35)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipt = json.loads((HERE / "receipt.json").read_text())
    assert receipt["status"] == "HIT" and receipt["sha256"]["input"] == sha(INPUT)
    assert receipt["sha256"]["join9.cpp"] == sha(HERE / "join9.cpp")
    assert receipt["sha256"]["join9"] == sha(HERE / "join9")
    assert json.loads((HERE / "sage_runtime_info.json").read_text())["status"] == "verified"
    geometry = json.loads((BASE / "geometry.json").read_text())
    fixture = json.loads((BASE / "fixture.json").read_text())
    stdout = (HERE / "stdout.log").read_text().splitlines()
    hits = [line.split() for line in stdout if line.startswith("HIT ")]
    assert len(hits) == 1 and stdout[-1].startswith("COMPLETE_HITS 1 ")
    hit = hits[0]
    assert [int(x) for x in hit[1:5]] == [0, 0, 132, 136]
    free = [int(x) for x in hit[5:12]]
    assert len(free) == 7
    sources = [("prefix0", 0, 132), ("prefix1", 1, 136)]
    sources += [(f"free{i}", i, sid) for i, sid in enumerate(free[:6])]
    sources += [("terminal", 0, free[6])]
    assert len(sources) == 9
    rows = {int(row["mask"]): row for row in geometry["rows"]}
    edges = [(a, a ^ 184) for a in sorted(rows)
             if a < (a ^ 184) and a ^ 184 in rows
             and rows[a]["column"] != rows[a ^ 184]["column"]]
    assert len(edges) == 35
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, name="t", modulus=t**41 + t**3 + 1)
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
    input_states = {}
    input_targets = {}
    for line in INPUT.read_text().splitlines()[1:]:
        parts = line.split()
        if parts[0] == "T":
            input_targets[int(parts[1])] = [int(parts[2]), int(parts[3])]
        if parts[0] == "S":
            input_states[(int(parts[1]), int(parts[2]))] = [int(parts[-2]), int(parts[-1])]
    assert input_targets[0] == fixture["raw_target_preimages"][0]
    representatives = {}
    for mask, row in sorted(rows.items()):
        representatives.setdefault(int(row["column"]), mask)

    ring_r = PolynomialRing(Zmod(R), "L")
    L = ring_r.gen()
    roots = [int(root) for root, _ in (L**2 + L + 2).roots()]
    sample = projected[representatives[min(representatives)]]
    eigenvalues = [value for value in roots if value * sample == frobenius(sample, 1)]
    assert len(eigenvalues) == 1
    eigenvalue = eigenvalues[0]
    quotient = {}
    selected_masks = {m for _, _, sid in sources for m in edges[sid // 4]}
    for mask in selected_masks:
        column = int(rows[mask]["column"])
        rep = projected[representatives[column]]
        matches = []
        for exponent in range(41):
            image = frobenius(rep, exponent)
            if image == projected[mask]:
                matches.append((exponent, 1))
            if -image == projected[mask]:
                matches.append((exponent, -1))
        assert len(matches) == 1
        quotient[mask] = matches[0]

    running = curve(0)
    occupied_edges = set()
    terms = []
    source_points = []
    coefficients = defaultdict(int)
    for label, slot, sid in sources:
        assert 0 <= sid < 140
        edge_id, choice = divmod(sid, 4)
        assert edge_id not in occupied_edges
        occupied_edges.add(edge_id)
        a, b = edges[edge_id]
        sign_a, sign_b = divmod(choice, 2)
        first = -raw[a] if sign_a else raw[a]
        second = -raw[b] if sign_b else raw[b]
        rotation = ROTATIONS[slot]
        pair = frobenius(first + second, rotation)
        assert xy(pair) == input_states[(slot, sid)]
        running += pair
        source_points.append({"label": label, "slot": slot, "state_id": sid,
                              "edge_id": edge_id, "masks": [a, b],
                              "source_sign_bits": [sign_a, sign_b],
                              "rotation": rotation, "pair_rotated": xy(pair)})
        for mask, sign_bit in ((a, sign_a), (b, sign_b)):
            column = int(rows[mask]["column"])
            exponent, orbit_sign = quotient[mask]
            coefficient = ((-1 if sign_bit else 1) * orbit_sign *
                           pow(eigenvalue, rotation + exponent, R)) % R
            coefficients[column] = (coefficients[column] + coefficient) % R
            terms.append({"label": label, "mask": mask, "column": column,
                          "coefficient_mod_r": str(coefficient)})
    assert len(occupied_edges) == 9 and len(terms) == 18
    assert xy(running) == input_targets[0]
    assert xy(4 * running) == fixture["public_target_transported"]
    row_sum = curve(0)
    for column, coefficient in coefficients.items():
        row_sum += coefficient * projected[representatives[column]]
    assert row_sum == 4 * running
    nonzero = {column: str(value) for column, value in coefficients.items() if value}
    prior_path = HERE.parent / "n41_w8_sixpair_mitm_20261011" / "audit_result.json"
    prior = json.loads(prior_path.read_text())
    assert prior["status"] == "PASS_INDEPENDENT_N41_PUBLIC_SIX_PAIR_RELATION"
    assert prior["public_target_transported"] == xy(4 * running)
    prior_columns = {int(term["column"]) for term in prior["relation_row"]}
    current_columns = set(nonzero)
    assert prior_columns.isdisjoint(current_columns)
    result = {
        "status": "PASS_INDEPENDENT_N41_PUBLIC_NINE_PAIR_RELATION",
        "curve_id": "EC1N41Ckb1h7d5e80d3c4d0", "candidate_id": None,
        "target_count": 1, "raw_target_preimage_index": 0,
        "raw_target_replayed": xy(running),
        "public_target_transported": xy(4 * running),
        "frobenius_eigenvalue_mod_r": str(eigenvalue),
        "source_edges_distinct": len(occupied_edges),
        "term_count": len(terms), "folded_columns_nonzero": len(nonzero),
        "relation_row": nonzero, "row_rank_from_empty_matrix": int(bool(nonzero)),
        "rank_with_prior_six_pair_row": 2,
        "new_columns_vs_prior_six_pair_row": len(current_columns - prior_columns),
        "source_pairs": source_points, "source_terms": terms,
        "sha256": {"script": sha(Path(__file__)), "input": sha(INPUT),
                   "geometry": sha(BASE / "geometry.json"),
                   "fixture": sha(BASE / "fixture.json"),
                   "prior_six_pair_audit": sha(prior_path),
                   "stdout": sha(HERE / "stdout.log"),
                   "sage_runtime": sha(HERE / "sage_runtime_info.json")},
    }
    (HERE / "audit_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["status"], len(nonzero), result["row_rank_from_empty_matrix"])


if __name__ == "__main__":
    main()
