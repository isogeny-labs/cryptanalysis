"""Frozen multi-prime CRT xedni correctness and probe-count panel."""

import gzip
import hashlib
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, ZZ, crt

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "xedni-crt-curve-choice-20261115" / "run_v2.py"
spec = importlib.util.spec_from_file_location("xedni_crt_parent", PARENT)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def character_table(prime):
    squares = {x * x % prime for x in range(1, prime)}
    return [0 if x == 0 else 1 if x in squares else -1 for x in range(prime)]


def point_coords(point):
    return [int(point[0]), int(point[1])]


def base_subgroup(curve, minimum):
    order = int(curve.cardinality())
    r = max(int(factor) for factor, _ in ZZ(order).factor())
    if r < minimum:
        return order, r, None
    cofactor = order // r
    points = sorted((point for point in curve.points() if not point.is_zero()),
                    key=lambda point: (int(point[0]), int(point[1])))
    generator = next((cofactor * point for point in points
                      if not (cofactor * point).is_zero()), None)
    assert generator is not None and (r * generator).is_zero()
    return order, r, generator


def run_prime(p, protocol, orders, characters):
    curve = EllipticCurve(GF(p), protocol["base_curve_coefficients"])
    group_order, r, generator = base_subgroup(
        curve, protocol["subgroup_policy"]["required_minimum_order"])
    if generator is None:
        return {"field_prime": p, "status": "subgroup_too_small",
                "curve_order": group_order, "subgroup_order": r}
    w = 17 if r > 17 else 1
    public = w * generator
    points_by_t = [public - t * generator for t in range(r)]
    counts = Counter()
    first_hit = None
    raw_dir = HERE / "rows"
    raw_dir.mkdir(exist_ok=True)
    shards = []
    output = None
    row_hash = hashlib.sha256()
    for t1, t2 in itertools.product(range(r), repeat=2):
        if t1 % 8 == 0 and t2 == 0:
            if output is not None:
                output.close()
            shard = raw_dir / f"p{p}-t{t1:03d}.jsonl.gz"
            shards.append(shard.name)
            output = gzip.GzipFile(filename=str(shard), mode="wb", mtime=0)
        P1, P2 = points_by_t[t1], points_by_t[t2]
        counts["target_queries"] += 1
        row = {"t": [t1, t2], "status": None, "accepted": False,
               "reduced_relation": False, "rational_relation": False,
               "attempts_7": 0, "attempts_11": 0}
        if P1.is_zero() or P2.is_zero():
            row["status"] = "identity"
        elif P1 == P2:
            row["status"] = "duplicate"
        else:
            counts["admissible_pairs"] += 1
            reduced = (P1 + 2 * P2).is_zero()
            row["reduced_relation"] = bool(reduced)
            points = [(parent.centered(P1[0], p), parent.centered(P1[1], p)),
                      (parent.centered(P2[0], p), parent.centered(P2[1], p))]
            dx = points[0][0] - points[1][0]
            if dx == 0:
                row["status"] = "same_x_base"
            elif dx % 7 == 0:
                row["status"] = "same_x_7"
            elif dx % 11 == 0:
                row["status"] = "same_x_11"
            else:
                candidate7, row["attempts_7"] = parent.first_candidate(
                    points, 7, 4, orders[7], characters[7])
                counts["attempts_7"] += row["attempts_7"]
                if candidate7 is None:
                    row["status"] = "no_order_4_at_7"
                else:
                    candidate11, row["attempts_11"] = parent.first_candidate(
                        points, 11, 6, orders[11], characters[11])
                    counts["attempts_11"] += row["attempts_11"]
                    if candidate11 is None:
                        row["status"] = "no_order_6_at_11"
                    else:
                        modulus = p * 7 * 11
                        free = [int(crt([0, candidate7[i], candidate11[i]],
                                        [p, 7, 11])) for i in range(3)]
                        free = [x if x <= modulus // 2 else x - modulus for x in free]
                        a1, a2, a3 = free
                        a4, a6 = parent.solved(points, a1, a2, a3)
                        coeffs = [a1, a2, a3, a4, a6]
                        if parent.delta(*coeffs) == 0:
                            row["status"] = "singular_rational_curve"
                        else:
                            assert all(int(QQ(c).denominator()) % l for c in coeffs
                                       for l in (p, 7, 11))
                            assert [int(GF(p)(c)) for c in coeffs] == \
                                protocol["base_curve_coefficients"][:3] + [p - 1, p - 2]
                            assert [int(GF(7)(c)) for c in coeffs] == list(candidate7)
                            assert [int(GF(11)(c)) for c in coeffs] == list(candidate11)
                            row["status"] = "accepted"
                            row["accepted"] = True
                            counts["accepted_pairs"] += 1
                            if reduced:
                                counts["accepted_reduced_relations"] += 1
                                rational = EllipticCurve(QQ, coeffs)
                                lift1, lift2 = [rational([x, y]) for x, y in points]
                                row["rational_relation"] = bool((lift1 + 2 * lift2).is_zero())
                                if row["rational_relation"]:
                                    counts["accepted_rational_relations"] += 1
                                    recovered = ((t1 + 2 * t2) * pow(3, -1, r)) % r
                                    assert recovered == w and recovered * generator == public
                                    row["recovered_scalar"] = recovered
                                    if first_hit is None:
                                        first_hit = {"t": [t1, t2],
                                                     "query_index_one_based": counts["target_queries"]}
        counts[f"status_{row['status']}"] += 1
        if first_hit is not None and "counters" not in first_hit:
            first_hit["counters"] = dict(counts)
        encoded = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
        output.write(encoded)
        row_hash.update(encoded)
    if output is not None:
        output.close()
    assert sum(value for name, value in counts.items() if name.startswith("status_")) == r * r
    return {"field_prime": p, "status": "PASS", "curve_order": group_order,
            "subgroup_order": r, "cofactor": group_order // r,
            "generator": point_coords(generator), "public_target": point_coords(public),
            "fixture_scalar": w, "first_rational_relation": first_hit,
            "counts": dict(counts), "rows_sha256": row_hash.hexdigest(),
            "row_shards": shards}


def main():
    protocol_path = HERE / "protocol.json"
    protocol = json.loads(protocol_path.read_text())
    assert protocol["schema"] == "xedni-crt-prime-panel-protocol-v1"
    assert sha(PARENT.read_bytes()) == protocol["parent_search_source_sha256"]
    orders = {l: parent.coefficient_order(l) for l in (7, 11)}
    characters = {l: character_table(l) for l in (7, 11)}
    results = [run_prime(p, protocol, orders, characters)
               for p in protocol["base_field_primes"]]
    result = {"schema": "xedni-crt-prime-panel-result-v1", "status": "PASS",
              "protocol_sha256": sha(protocol_path.read_bytes()),
              "source_sha256": sha(Path(__file__).read_bytes()),
              "parent_source_sha256": sha(PARENT.read_bytes()),
              "sage_runtime_sha256": sha((HERE / "sage-runtime-info.json").read_bytes()),
              "fields": results}
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
