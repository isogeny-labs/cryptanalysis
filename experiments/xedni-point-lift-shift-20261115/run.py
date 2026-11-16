"""Deterministic minimal y-coordinate p-shift on the frozen CRT subgroup panel."""
import gzip
import hashlib
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, crt

HERE = Path(__file__).resolve().parent
PARENT_PANEL = HERE.parent / "xedni-crt-band-panel-20261115"
PARENT_RUN = HERE.parent / "xedni-crt-prime-panel-20261115" / "run.py"
spec = importlib.util.spec_from_file_location("xedni_shift_parent", PARENT_RUN)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shift(points, p):
    (x1, y1), (x2, y2) = points
    dx = x1 - x2
    if dx == 0:
        return None, points
    d = abs(dx)
    k0 = (- (y1 - y2) * pow(p, -1, d)) % d if d > 1 else 0
    k = min((k0, k0 - d), key=lambda n: (abs(n), n)) if d > 1 else 0
    shifted = [(x1, y1 + k * p), (x2, y2)]
    assert (shifted[0][1] - y2) % dx == 0
    assert shifted[0][1] % p == y1 % p
    assert 2 * abs(k) <= d
    return k, shifted


def run_field(reference, protocol, orders, characters, total_probes):
    p = reference["field_prime"]
    curve = EllipticCurve(GF(p), [0, 0, 0, -1, -2])
    group_order, r, generator = parent.base_subgroup(curve, 43)
    assert group_order == reference["curve_order"]
    assert r == reference["subgroup_order"]
    assert parent.point_coords(generator) == reference["generator"]
    scalar = reference["fixture_scalar"]
    public = scalar * generator
    assert parent.point_coords(public) == reference["public_target"]
    sampled = [public - t * generator for t in range(r)]
    counts = Counter()
    first_hit = None
    row_hash = hashlib.sha256()
    shards = []
    output = None
    field_status = "PASS"
    for t1, t2 in itertools.product(range(r), repeat=2):
        if t1 % 8 == 0 and t2 == 0:
            if output is not None:
                output.close()
            shard = HERE / "rows" / f"p{p}-t{t1:03d}.jsonl.gz"
            shards.append(shard.name)
            output = gzip.GzipFile(filename=str(shard), mode="wb", mtime=0)
        P1, P2 = sampled[t1], sampled[t2]
        row = {"t": [t1, t2], "status": None, "accepted": False,
               "reduced_relation": False, "rational_relation": False,
               "attempts_7": 0, "attempts_11": 0, "k": None}
        counts["target_queries"] += 1
        if P1.is_zero() or P2.is_zero():
            row["status"] = "identity"
        elif P1 == P2:
            row["status"] = "duplicate"
        else:
            counts["admissible_pairs"] += 1
            reduced = bool((P1 + 2 * P2).is_zero())
            row["reduced_relation"] = reduced
            centered = [(parent.parent.centered(P1[0], p), parent.parent.centered(P1[1], p)),
                        (parent.parent.centered(P2[0], p), parent.parent.centered(P2[1], p))]
            k, points = shift(centered, p)
            row["k"] = k
            if k is None:
                row["status"] = "same_x_base"
            else:
                counts["distinct_x"] += 1
                counts["nonzero_shifts"] += (k != 0)
                counts["sum_abs_k"] += abs(k)
                counts["max_abs_k"] = max(counts["max_abs_k"], abs(k))
                counts["max_abs_y_lift"] = max(counts["max_abs_y_lift"],
                                               abs(points[0][1]), abs(points[1][1]))
                if reduced:
                    counts["reduced_distinct_x"] += 1
                dx = points[0][0] - points[1][0]
                if dx % 7 == 0:
                    row["status"] = "same_x_7"
                elif dx % 11 == 0:
                    row["status"] = "same_x_11"
                else:
                    c7, row["attempts_7"] = parent.parent.first_candidate(
                        points, 7, 4, orders[7], characters[7])
                    counts["attempts_7"] += row["attempts_7"]
                    if c7 is None:
                        row["status"] = "no_order_4_at_7"
                    else:
                        c11, row["attempts_11"] = parent.parent.first_candidate(
                            points, 11, 6, orders[11], characters[11])
                        counts["attempts_11"] += row["attempts_11"]
                        if c11 is None:
                            row["status"] = "no_order_6_at_11"
                        else:
                            modulus = 77 * p
                            free = [int(crt([0, c7[i], c11[i]], [p, 7, 11]))
                                    for i in range(3)]
                            free = [n if n <= modulus // 2 else n - modulus for n in free]
                            a1, a2, a3 = free
                            a4, a6 = parent.parent.solved(points, a1, a2, a3)
                            coeffs = [a1, a2, a3, a4, a6]
                            if parent.parent.delta(*coeffs) == 0:
                                row["status"] = "singular_rational_curve"
                            else:
                                assert all(int(QQ(c).denominator()) % l
                                           for c in coeffs for l in (p, 7, 11))
                                assert [int(GF(p)(c)) for c in coeffs] == [0, 0, 0, p-1, p-2]
                                assert [int(GF(7)(c)) for c in coeffs] == list(c7)
                                assert [int(GF(11)(c)) for c in coeffs] == list(c11)
                                row["status"] = "accepted"
                                row["accepted"] = True
                                counts["accepted_pairs"] += 1
                                if reduced:
                                    counts["accepted_reduced_relations"] += 1
                                    slope = (points[0][1] - points[1][1]) // dx
                                    equality = slope*slope + a1*slope == a2 + points[0][0] + 2*points[1][0]
                                    row["monic_equality"] = bool(equality)
                                    counts["monic_equalities"] += equality
                                    E = EllipticCurve(QQ, coeffs)
                                    U, V = [E([x, y]) for x, y in points]
                                    rational = bool((U + 2 * V).is_zero())
                                    row["rational_relation"] = rational
                                    assert rational == equality
                                    if rational:
                                        counts["rational_relations"] += 1
                                        recovered = ((t1 + 2*t2) * pow(3, -1, r)) % r
                                        assert recovered == scalar and recovered * generator == public
                                        row["recovered_scalar"] = recovered
                                        if first_hit is None:
                                            first_hit = {"t": [t1, t2],
                                                         "query_index_one_based": counts["target_queries"]}
        counts[f"status_{row['status']}"] += 1
        encoded = (json.dumps(row, sort_keys=True) + "\n").encode()
        output.write(encoded)
        row_hash.update(encoded)
        if total_probes + counts["attempts_7"] + counts["attempts_11"] > \
                protocol["max_total_auxiliary_probes"]:
            field_status = "probe_cap"
            break
    if output is not None:
        output.close()
    return {"field_prime": p, "status": field_status,
            "curve_order": group_order, "subgroup_order": r,
            "generator": parent.point_coords(generator),
            "public_target": parent.point_coords(public),
            "fixture_scalar": scalar, "row_shards": shards,
            "rows_sha256": row_hash.hexdigest(),
            "counts": dict(counts), "first_rational_relation": first_hit}


def main():
    protocol_path = HERE / "protocol.json"
    protocol = json.loads(protocol_path.read_text())
    assert protocol["schema"] == "xedni-point-lift-shift-protocol-v1"
    reference_path = PARENT_PANEL / "result.json"
    for key, path in (("parent_panel_protocol_sha256", PARENT_PANEL / "protocol.json"),
                      ("parent_panel_result_sha256", reference_path),
                      ("parent_prime_run_source_sha256", PARENT_RUN),
                      ("parent_curve_search_source_sha256", parent.PARENT)):
        assert sha(path) == protocol[key]
    reference = json.loads(reference_path.read_text())
    assert [f["field_prime"] for f in reference["fields"]] == protocol["fields"]
    assert reference["projected_queries"] == protocol["max_total_queries"]
    orders = {l: parent.parent.coefficient_order(l) for l in (7, 11)}
    chars = {l: parent.character_table(l) for l in (7, 11)}
    fields = []
    probes = 0
    for record in reference["fields"]:
        field = run_field(record, protocol, orders, chars, probes)
        fields.append(field)
        probes += field["counts"].get("attempts_7", 0) + field["counts"].get("attempts_11", 0)
        if field["status"] != "PASS":
            break
    result = {"schema": "xedni-point-lift-shift-result-v1",
              "status": "PASS" if len(fields) == len(protocol["fields"]) and
              all(field["status"] == "PASS" for field in fields) else "probe_cap",
              "protocol_sha256": sha(protocol_path),
              "source_sha256": sha(Path(__file__)),
              "sage_runtime_sha256": sha(HERE / "sage-runtime-info.json"),
              "parent_panel_result_sha256": sha(reference_path),
              "target_queries_completed": sum(f["counts"].get("target_queries", 0) for f in fields),
              "auxiliary_probes": probes, "fields": fields}
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
