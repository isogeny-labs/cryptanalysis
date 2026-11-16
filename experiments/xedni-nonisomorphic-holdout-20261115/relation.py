"""Complete holdout relation census and matched direct public control."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def add(P, Q, p):
    if P is None: return Q
    if Q is None: return P
    x1, y1 = P; x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0: return None
    if x1 == x2:
        slope = ((3*x1*x1-1) * pow(2*y1, -1, p)) % p
    else:
        slope = ((y2-y1) * pow((x2-x1) % p, -1, p)) % p
    x3 = (slope*slope-x1-x2) % p
    return (x3, (slope*(x1-x3)-y1) % p)

def neg(P, p):
    return None if P is None else (P[0], -P[1] % p)

def mul(k, P, p):
    if k < 0: return mul(-k, neg(P, p), p)
    R = None
    while k:
        if k & 1: R = add(R, P, p)
        P = add(P, P, p); k >>= 1
    return R

def main():
    protocol = json.loads((HERE / "relation-protocol.json").read_text())
    screen = json.loads((HERE / "result.json").read_text())
    generators = json.loads((HERE / "generators.json").read_text())
    selected = json.loads((HERE / "selection.json").read_text())["selected"]
    assert protocol["coordinate_cap"] == 4 and protocol["relation_vector"] == [1, 2]
    assert generators["screen_sha256"] == sha(HERE / "result.json")
    screened = {(r["field_prime"], r["u"]): r["candidate"] for r in screen["rows"]
                if r.get("candidate", {}).get("rank_status") == "proved" and
                r["candidate"]["rank"] == 1 and r["candidate"]["torsion_order"] == 1}
    approved = {(r["field_prime"], r["u"]) for r in generators["rows"]
                if r["status"] == "completed" and
                r["generator"]["generator_status"] == "proved" and
                r["generator"]["point_is_signed_generator"]}
    assert approved <= set(screened) and all(u > 1 for _, u in approved)
    (HERE / "rows").mkdir(exist_ok=True)
    fields = []
    totals = Counter()
    for p, q in selected:
        G = (2 % p, 2 % p)
        Q = mul(17, G, p)  # fixture construction, outside the query loop
        minus_G = neg(G, p)
        points = [Q]
        for _ in range(1, q): points.append(add(points[-1], minus_G, p))
        assert add(points[-1], minus_G, p) == Q
        neg_doubles = [neg(add(P, P, p), p) for P in points]
        models = []
        for u in [1] + [u for u in range(2, 6) if (p, u) in approved]:
            c = screened[p, u]
            x, y = c["centered_point"]
            P = (x % p, y % p)
            assert P == mul(u, G, p)
            mapping = {mul(k, P, p): k for k in range(-4, 5)}
            assert len(mapping) == 9
            models.append({"u": u, "curve_B": c["curve_B"], "map": mapping,
                           "counts": Counter(), "hits": []})
        direct_count = 0
        first_direct = None
        first_rational = None
        row_path = HERE / "rows" / f"p{p}.jsonl.gz"
        with row_path.open("wb") as f:
            with gzip.GzipFile(fileobj=f, mode="wb", filename="", mtime=0) as gz:
                for t1, R1 in enumerate(points):
                    for t2, R2 in enumerate(points):
                        admissible = R1 is not None and R2 is not None and R1 != R2
                        direct = admissible and R1 == neg_doubles[t2]
                        if admissible:
                            direct_count += 1
                        if direct and first_direct is None:
                            first_direct = {"t": [t1, t2], "query_index_one_based": t1*q+t2+1,
                                            "direct_tests_to_hit": direct_count,
                                            "recovered_scalar": ((t1+2*t2)*pow(3,-1,q)) % q}
                            assert mul(first_direct["recovered_scalar"], G, p) == Q
                        codes = []
                        for model in models:
                            mapping = model["map"]
                            if R1 is None or R2 is None: code = "I"
                            elif R1 == R2: code = "D"
                            elif R1 not in mapping or R2 not in mapping: code = "O"
                            else:
                                a, b = mapping[R1], mapping[R2]
                                relation = a + 2*b == 0
                                assert relation == direct
                                code = "R" if relation else "N"
                                if relation:
                                    hit = {"u": model["u"], "t": [t1, t2], "k": [a, b],
                                           "query_index_one_based": t1*q+t2+1,
                                           "recovered_scalar": ((t1+2*t2)*pow(3,-1,q)) % q}
                                    assert mul(hit["recovered_scalar"], G, p) == Q
                                    model["hits"].append(hit)
                                    if first_rational is None: first_rational = hit
                            model["counts"][code] += 1
                            codes.append(code)
                        gz.write((json.dumps({"t": [t1, t2], "s": codes, "d": int(direct)},
                                             separators=(",", ":")) + "\n").encode())
        image_union = set().union(*(set(model["map"]) for model in models))
        pair_union = set().union(*(set((a, b) for a in model["map"] for b in model["map"])
                                   for model in models))
        unique_hit_queries = set(tuple(hit["t"]) for model in models for hit in model["hits"])
        field = {"field_prime": p, "subgroup_order": q,
                 "models": [{"u": m["u"], "curve_B": m["curve_B"],
                             "counts": dict(m["counts"]), "hits": m["hits"]} for m in models],
                 "image_union_size": len(image_union), "pair_union_size": len(pair_union),
                 "unique_rational_relation_queries": len(unique_hit_queries),
                 "first_direct": first_direct, "first_rational": first_rational,
                 "direct_tests_complete": direct_count,
                 "raw_path": str(row_path.relative_to(HERE)), "raw_sha256": sha(row_path)}
        fields.append(field)
        totals["queries"] += q*q
        totals["membership_tests"] += q*q*len(models)
        totals["admitted_relation_tests"] += sum(m["counts"]["N"]+m["counts"]["R"] for m in models)
        totals["rational_relations"] += sum(len(m["hits"]) for m in models)
        totals["unique_relation_queries"] += len(unique_hit_queries)
        totals["direct_public_tests_complete"] += direct_count
    totals["rank_screen_cells"] = len(screen["rows"])
    totals["generator_check_cells"] = len(generators["rows"])
    print(json.dumps({"schema": "xedni-nonisomorphic-holdout-relation-v1", "status": "PASS",
                      "protocol_sha256": sha(HERE / "relation-protocol.json"),
                      "source_sha256": sha(Path(__file__)),
                      "selection_sha256": sha(HERE / "selection.json"),
                      "screen_sha256": sha(HERE / "result.json"),
                      "generators_sha256": sha(HERE / "generators.json"),
                      "fields": fields, "totals": dict(totals)}, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
