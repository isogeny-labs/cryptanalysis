"""Independent exact-arithmetic replay of every shifted-lift CRT query."""
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT_PANEL = HERE.parent / "xedni-crt-band-panel-20261115"
ARITH = HERE.parent / "xedni-crt-prime-panel-20261115" / "audit.py"
COST = HERE.parent / "xedni-crt-curve-choice-20261115" / "cost_audit.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shifted(points, p):
    (x1, y1), (x2, y2) = points
    d = abs(x1 - x2)
    if not d:
        return None, points
    choices = [k for k in range(-d//2, d//2 + 1) if (y1-y2+k*p) % d == 0]
    assert choices
    k = min(choices, key=lambda n: (abs(n), n))
    return k, [(x1, y1+k*p), (x2, y2)]


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    reference = json.loads((PARENT_PANEL / "result.json").read_text())
    assert protocol["schema"] == "xedni-point-lift-shift-protocol-v1"
    assert result["schema"] == "xedni-point-lift-shift-result-v1"
    assert result["status"] == "PASS"
    for key, path in (("parent_panel_protocol_sha256", PARENT_PANEL / "protocol.json"),
                      ("parent_panel_result_sha256", PARENT_PANEL / "result.json"),
                      ("parent_prime_run_source_sha256", HERE.parent / "xedni-crt-prime-panel-20261115" / "run.py"),
                      ("parent_curve_search_source_sha256", HERE.parent / "xedni-crt-curve-choice-20261115" / "run_v2.py")):
        assert sha(path) == protocol[key], key
    assert sha(ARITH) == "28dd3e4553bfcedc3c646d5d8d284b137e5494ed3ebec5533d0961f1ea5337a8"
    assert sha(COST) == "565365e0e9093dcc512cc551bb19760b4f6aa54538093c557dc1acd1cdf645f7"
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["source_sha256"] == sha(HERE / "run.py")
    assert result["sage_runtime_sha256"] == sha(HERE / "sage-runtime-info.json")
    assert result["parent_panel_result_sha256"] == sha(PARENT_PANEL / "result.json")
    assert [f["field_prime"] for f in result["fields"]] == protocol["fields"]
    spec = importlib.util.spec_from_file_location("xedni_shift_arith", ARITH)
    arith = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arith)
    base = [0, 0, 0, -1, -2]
    orders = {l: arith.prior.candidates(l) for l in (7, 11)}
    chars = {}
    for l in orders:
        squares = {x*x % l for x in range(1, l)}
        chars[l] = [0 if x == 0 else 1 if x in squares else -1 for x in range(l)]
    total = Counter()
    for record, ref in zip(result["fields"], reference["fields"], strict=True):
        p, r = record["field_prime"], record["subgroup_order"]
        assert (p, r) == (ref["field_prime"], ref["subgroup_order"])
        points = arith.field_points(p, base)
        n = len(points) + 1
        assert n == record["curve_order"] == ref["curve_order"]
        assert arith.largest_prime_factor(n) == r
        cofactor = n // r
        generator = next(arith.mul(cofactor, P, base, p) for P in points
                         if arith.mul(cofactor, P, base, p) is not None)
        assert list(generator) == record["generator"] == ref["generator"]
        scalar = record["fixture_scalar"]
        public = arith.mul(scalar, generator, base, p)
        assert list(public) == record["public_target"] == ref["public_target"]
        assert arith.mul(r, generator, base, p) is None
        sampled = [arith.add(public, arith.neg(arith.mul(t, generator, base, p), base, p), base, p)
                   for t in range(r)]
        raw_hash = hashlib.sha256()
        counts = Counter()
        first = None
        index = 0
        for shard in record["row_shards"]:
            raw = gzip.open(HERE / "rows" / shard, "rb").read()
            raw_hash.update(raw)
            for line in raw.splitlines():
                saved = json.loads(line)
                t1, t2 = divmod(index, r)
                index += 1
                U, V = sampled[t1], sampled[t2]
                row = {"t": [t1,t2], "status": None, "accepted": False,
                       "reduced_relation": False, "rational_relation": False,
                       "attempts_7": 0, "attempts_11": 0, "k": None}
                counts["target_queries"] += 1
                if U is None or V is None:
                    row["status"] = "identity"
                elif U == V:
                    row["status"] = "duplicate"
                else:
                    counts["admissible_pairs"] += 1
                    reduced = arith.add(U, arith.mul(2, V, base, p), base, p) is None
                    row["reduced_relation"] = reduced
                    centered = [(arith.centered(x,p), arith.centered(y,p)) for x,y in (U,V)]
                    k, lifts = shifted(centered, p)
                    row["k"] = k
                    if k is None:
                        row["status"] = "same_x_base"
                    else:
                        counts["distinct_x"] += 1
                        counts["nonzero_shifts"] += (k != 0)
                        counts["sum_abs_k"] += abs(k)
                        counts["max_abs_k"] = max(counts["max_abs_k"], abs(k))
                        counts["max_abs_y_lift"] = max(counts["max_abs_y_lift"],
                                                       abs(lifts[0][1]), abs(lifts[1][1]))
                        dx = lifts[0][0] - lifts[1][0]
                        assert dx and (lifts[0][1]-lifts[1][1]) % dx == 0
                        assert lifts[0][1] % p == U[1]
                        if reduced:
                            counts["reduced_distinct_x"] += 1
                        if dx % 7 == 0:
                            row["status"] = "same_x_7"
                        elif dx % 11 == 0:
                            row["status"] = "same_x_11"
                        else:
                            c7, row["attempts_7"] = arith.prior.find_candidate(
                                lifts, 7, 4, orders[7], chars[7])
                            counts["attempts_7"] += row["attempts_7"]
                            if c7 is None:
                                row["status"] = "no_order_4_at_7"
                            else:
                                c11, row["attempts_11"] = arith.prior.find_candidate(
                                    lifts, 11, 6, orders[11], chars[11])
                                counts["attempts_11"] += row["attempts_11"]
                                if c11 is None:
                                    row["status"] = "no_order_6_at_11"
                                else:
                                    free = tuple(arith.crt_free(p,c7[i],c11[i]) for i in range(3))
                                    coeffs = arith.solve_rational(lifts,free)
                                    if arith.delta(coeffs) == 0:
                                        row["status"] = "singular_rational_curve"
                                    else:
                                        for l, expected in ((p,[0,0,0,p-1,p-2]),
                                                            (7,c7),(11,c11)):
                                            assert [arith.mod_rational(v,l) for v in coeffs] == list(expected)
                                            assert arith.mod_rational(arith.delta(coeffs),l) != 0
                                        row["status"] = "accepted"
                                        row["accepted"] = True
                                        counts["accepted_pairs"] += 1
                                        if reduced:
                                            counts["accepted_reduced_relations"] += 1
                                            slope = (lifts[0][1]-lifts[1][1]) // dx
                                            equality = slope*slope + free[0]*slope == free[1]+lifts[0][0]+2*lifts[1][0]
                                            row["monic_equality"] = equality
                                            counts["monic_equalities"] += equality
                                            rational = arith.add(lifts[0],
                                                arith.mul(2,lifts[1],coeffs,None),coeffs,None) is None
                                            row["rational_relation"] = rational
                                            assert rational == equality
                                            if rational:
                                                counts["rational_relations"] += 1
                                                recovered = ((t1+2*t2)*pow(3,-1,r))%r
                                                assert recovered == scalar
                                                assert arith.mul(recovered,generator,base,p) == public
                                                row["recovered_scalar"] = recovered
                                                if first is None:
                                                    first = {"t":[t1,t2],"query_index_one_based":index}
                counts[f"status_{row['status']}"] += 1
                assert row == saved, (p,t1,t2,row,saved)
        assert index == r*r and raw_hash.hexdigest() == record["rows_sha256"]
        assert dict(counts) == record["counts"], (p,dict(counts),record["counts"])
        assert first == record["first_rational_relation"]
        total.update(counts)
    assert total["target_queries"] == result["target_queries_completed"] == protocol["max_total_queries"]
    assert total["attempts_7"]+total["attempts_11"] == result["auxiliary_probes"]
    assert result["auxiliary_probes"] <= protocol["max_total_auxiliary_probes"]
    print(json.dumps({"schema":"xedni-point-lift-shift-audit-v1", "status":"PASS",
                      "source_sha256":sha(Path(__file__)),
                      "fields":protocol["fields"], "rows_audited":total["target_queries"],
                      "auxiliary_probes_replayed":result["auxiliary_probes"],
                      "rational_relations":total["rational_relations"]},sort_keys=True,indent=2))


if __name__ == "__main__":
    main()
