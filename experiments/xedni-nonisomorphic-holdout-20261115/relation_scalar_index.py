"""Complete holdout relation census and matched direct public control."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

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
        models = []
        for u in [1] + [u for u in range(2, 6) if (p, u) in approved]:
            c = screened[p, u]
            mapping = {(k * u) % q: k for k in range(-4, 5)}
            assert len(mapping) == 9
            models.append({"u": u, "curve_B": c["curve_B"], "map": mapping,
                           "counts": Counter(), "hits": []})
        direct_count = 0
        first_direct = None
        first_rational = None
        row_path = HERE / "rows" / f"p{p}.jsonl.gz"
        with row_path.open("wb") as f:
            with gzip.GzipFile(fileobj=f, mode="wb", filename="", mtime=0) as gz:
                for t1 in range(q):
                    s1 = (17 - t1) % q
                    for t2 in range(q):
                        s2 = (17 - t2) % q
                        admissible = s1 != 0 and s2 != 0 and s1 != s2
                        direct = admissible and (s1 + 2 * s2) % q == 0
                        if admissible:
                            direct_count += 1
                        if direct and first_direct is None:
                            first_direct = {"t": [t1, t2], "query_index_one_based": t1*q+t2+1,
                                            "direct_tests_to_hit": direct_count,
                                            "recovered_scalar": ((t1+2*t2)*pow(3,-1,q)) % q}
                            assert first_direct["recovered_scalar"] == 17
                        codes = []
                        for model in models:
                            mapping = model["map"]
                            if s1 == 0 or s2 == 0: code = "I"
                            elif s1 == s2: code = "D"
                            elif s1 not in mapping or s2 not in mapping: code = "O"
                            else:
                                a, b = mapping[s1], mapping[s2]
                                relation = a + 2*b == 0
                                assert relation == direct
                                code = "R" if relation else "N"
                                if relation:
                                    hit = {"u": model["u"], "t": [t1, t2], "k": [a, b],
                                           "query_index_one_based": t1*q+t2+1,
                                           "recovered_scalar": ((t1+2*t2)*pow(3,-1,q)) % q}
                                    assert hit["recovered_scalar"] == 17
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
