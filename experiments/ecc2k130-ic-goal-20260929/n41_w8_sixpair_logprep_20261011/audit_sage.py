#!/usr/bin/env sage -python
"""Replay all collected relations, measure rank, and solve folded-column logs."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, Zmod

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_w8_sixpair_mitm_20261011"
BASE = HERE.parent / "n41_w7_entropy_cubic_20261011/w8"
R = 549756390943
ROTATIONS = (0, 7, 14, 21, 28, 35)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    query = json.loads((HERE / "query_result.json").read_text())
    panel_result = json.loads((HERE / "panel_result.json").read_text())
    geometry = json.loads((BASE / "geometry.json").read_text())
    prior_relation = json.loads((PRIOR / "audit_result.json").read_text())
    assert query["status"] == "PANEL_COMPLETE_PENDING_SAGE_RANK_AUDIT"
    assert query["protocol_sha256"] == sha(HERE / "protocol.json")
    assert query["stdout_sha256"] == sha(HERE / "batch.stdout.txt")
    assert query["stderr_sha256"] == sha(HERE / "batch.stderr.txt")
    assert protocol["source_sha256"]["panel"] == sha(HERE / "panel.tsv")
    assert protocol["source_sha256"]["prior_states"] == sha(PRIOR / "join_input.tsv")
    assert json.loads((HERE / "sage_runtime_info.json").read_text())["status"] == "verified"
    rows = {int(row["mask"]): row for row in geometry["rows"]}
    edges = [(a, a ^ 184) for a in sorted(rows)
             if a < (a ^ 184) and a ^ 184 in rows
             and rows[a]["column"] != rows[a ^ 184]["column"]]
    assert len(edges) == 35
    chosen_masks = {mask for edge in edges for mask in edge}
    columns = sorted({int(rows[mask]["column"]) for mask in chosen_masks})
    assert len(chosen_masks) == len(columns) == 70
    col_position = {column: index for index, column in enumerate(columns)}
    representative = {}
    for mask, item in sorted(rows.items()):
        representative.setdefault(int(item["column"]), mask)
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
    sample = projected[representative[columns[0]]]
    ring_r = PolynomialRing(Zmod(R), "L")
    L = ring_r.gen()
    roots = [int(root) for root, _ in (L**2 + L + 2).roots()]
    eigenvalues = [value for value in roots if value * sample == frobenius(sample, 1)]
    assert len(eigenvalues) == 1
    eigenvalue = eigenvalues[0]
    for column in columns:
        rep = projected[representative[column]]
        assert eigenvalue * rep == frobenius(rep, 1)
    quotient = {}
    for mask in chosen_masks:
        col = int(rows[mask]["column"])
        rep = projected[representative[col]]
        orbit = [(frobenius(rep, exponent), exponent, 1) for exponent in range(41)]
        orbit += [(-point, exponent, -1) for point, exponent, _ in orbit]
        matches = [(exponent, sign) for point, exponent, sign in orbit
                   if point == projected[mask]]
        assert len(matches) == 1
        quotient[mask] = matches[0]

    panel = {}
    for line in (HERE / "panel.tsv").read_text().splitlines()[1:]:
        tag, index, raw_index, scalar, x, y = line.split()
        assert tag == "T"
        i, j, k = int(index), int(raw_index), int(scalar)
        panel.setdefault(i, {"scalar": k, "raw": {}})
        assert panel[i]["scalar"] == k and j not in panel[i]["raw"]
        panel[i]["raw"][j] = curve(dec(x), dec(y))
    assert len(panel) == 128 and all(len(item["raw"]) == 4 for item in panel.values())
    generator = projected[panel_result["generator_mask"]]
    assert xy(generator) == panel_result["generator_projected"]
    for item in panel.values():
        assert all(4 * point == item["scalar"] * generator
                   for point in item["raw"].values())

    pivot_rows = {}
    rank_history = []

    def insert(row, rhs):
        vector = list(row)
        value = rhs % R
        for pivot in sorted(pivot_rows):
            basis, target = pivot_rows[pivot]
            factor = vector[pivot]
            if factor:
                vector = [(a - factor * b) % R for a, b in zip(vector, basis)]
                value = (value - factor * target) % R
        nonzero = [index for index, coefficient in enumerate(vector) if coefficient]
        if not nonzero:
            assert value == 0
            return False
        pivot = nonzero[0]
        inverse = pow(vector[pivot], -1, R)
        normalized = [coefficient * inverse % R for coefficient in vector]
        normalized_rhs = value * inverse % R
        # Keep all earlier basis rows reduced at this newly discovered pivot.
        # Without this step, a later smaller pivot can reintroduce a column
        # cleared earlier during insertion of subsequent rows.
        for old_pivot, (basis, target) in list(pivot_rows.items()):
            factor = basis[pivot]
            if factor:
                pivot_rows[old_pivot] = (
                    [(a - factor * b) % R for a, b in zip(basis, normalized)],
                    (target - factor * normalized_rhs) % R)
        pivot_rows[pivot] = (normalized, normalized_rhs)
        return True

    anchor = [0] * len(columns)
    generator_mask = panel_result["generator_mask"]
    generator_col = int(rows[generator_mask]["column"])
    exponent, sign = quotient[generator_mask]
    anchor[col_position[generator_col]] = sign * pow(eigenvalue, exponent, R) % R
    assert insert(anchor, 1)
    row_records = []
    seen_targets = set()
    misses = []
    for line in (HERE / "batch.stdout.txt").read_text().splitlines():
        items = line.split()
        if not items or items[0] not in ("ROW", "MISS"):
            continue
        index = int(items[1])
        assert index not in seen_targets and 0 <= index < 128
        seen_targets.add(index)
        if items[0] == "MISS":
            assert int(items[2]) == panel[index]["scalar"]
            misses.append(index)
            continue
        assert len(items) == 13
        raw_index, scalar = int(items[2]), int(items[3])
        state_ids = list(map(int, items[4:10]))
        assert scalar == panel[index]["scalar"]
        assert raw_index in panel[index]["raw"]
        running = curve(0)
        occupied_edges, occupied_columns = set(), set()
        vector = [0] * len(columns)
        for slot, sid in enumerate(state_ids):
            edge, choice = divmod(sid, 4)
            a, b = edges[edge]
            assert edge not in occupied_edges
            occupied_edges.add(edge)
            sign_a, sign_b = divmod(choice, 2)
            first = -raw[a] if sign_a else raw[a]
            second = -raw[b] if sign_b else raw[b]
            running += frobenius(first + second, ROTATIONS[slot])
            for mask, sign_bit in ((a, sign_a), (b, sign_b)):
                column = int(rows[mask]["column"])
                assert column not in occupied_columns
                occupied_columns.add(column)
                exponent, orbit_sign = quotient[mask]
                coefficient = ((-1 if sign_bit else 1) * orbit_sign *
                               pow(eigenvalue, ROTATIONS[slot] + exponent, R)) % R
                vector[col_position[column]] = coefficient
        assert len(occupied_columns) == 12
        assert running == panel[index]["raw"][raw_index]
        assert 4 * running == scalar * generator
        novel = insert(vector, scalar)
        rank_history.append({"target_index": index, "rank_after": len(pivot_rows),
                             "novel": novel, "raw_preimage_index": raw_index,
                             "probe_count": int(items[10]),
                             "query_seconds_exploratory": float(items[11])})
        row_records.append({"target_index": index, "scalar": scalar,
                            "raw_preimage_index": raw_index,
                            "state_ids": state_ids,
                            "nonzero_columns": [columns[i] for i, value in enumerate(vector) if value],
                            "coefficients_mod_r": [str(value) for value in vector if value],
                            "novel": novel})
    assert len(seen_targets) == 128
    assert len(row_records) == query["relation_rows_native"]
    assert len(misses) == query["restricted_source_misses"]
    logs = None
    recovered = None
    if len(pivot_rows) == len(columns):
        solved = [0] * len(columns)
        for pivot in sorted(pivot_rows, reverse=True):
            basis, rhs = pivot_rows[pivot]
            solved[pivot] = (rhs - sum(basis[j] * solved[j]
                                       for j in range(pivot + 1, len(columns)))) % R
        assert all(solved[col_position[column]] * generator ==
                   projected[representative[column]] for column in columns)
        logs = {str(column): str(solved[i]) for i, column in enumerate(columns)}
        terms = prior_relation["relation_row"]
        assert all(str(term["column"]) in logs for term in terms)
        discrete_log = sum(int(term["coefficient_mod_r"]) *
                           int(logs[str(term["column"])]) for term in terms) % R
        public = curve(*map(dec, prior_relation["public_target_transported"]))
        assert discrete_log * generator == public
        recovered = {"public_target_transported": xy(public),
                     "target_log_mod_r": str(discrete_log),
                     "generator_projected": xy(generator),
                     "independent_scalar_replay": True}
    result = {"status": "PASS_N41_FULL_FACTOR_LOG_AND_TARGET_RECOVERY" if logs
              else "PASS_N41_RELATION_RANK_PARTIAL",
              "candidate_id": None, "panel_target_count": 128,
              "verified_relations": len(row_records), "restricted_source_misses": len(misses),
              "factor_base_folded_columns": len(columns), "final_rank_including_generator_anchor":
                  len(pivot_rows), "generator_anchor_rank": 1,
              "frobenius_eigenvalue_mod_r": str(eigenvalue),
              "generator_projected": xy(generator),
              "rank_history": rank_history, "relations": row_records,
              "factor_logs": logs, "recovered_public_target": recovered,
              "source_sha256": {"script": sha(Path(__file__)),
                                "protocol": sha(HERE / "protocol.json"),
                                "query": sha(HERE / "query_result.json"),
                                "panel": sha(HERE / "panel.tsv"),
                                "batch_stdout": sha(HERE / "batch.stdout.txt"),
                                "prior_relation": sha(PRIOR / "audit_result.json"),
                                "runtime": sha(HERE / "sage_runtime_info.json")}}
    save(HERE / "audit_result.json", result)
    print(result["status"], len(row_records), len(pivot_rows))


if __name__ == "__main__":
    main()
