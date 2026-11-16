"""Independent finite-field replay of every holdout query and saved status."""
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
        slope = ((3*x1*x1 - 1) * pow(2*y1, -1, p)) % p
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

def prime(n):
    return n > 1 and all(n % d for d in range(2, int(n**0.5) + 1))

def order_by_squares(p):
    counts = Counter((y*y) % p for y in range(p))
    return 1 + sum(counts[(x*x*x-x-2) % p] for x in range(p))

def main():
    selection = json.loads((HERE / "selection.json").read_text())
    screen = json.loads((HERE / "result.json").read_text())
    generators = json.loads((HERE / "generators.json").read_text())
    result = json.loads((HERE / "relation-result.json").read_text())
    assert selection["protocol_sha256"] == sha(HERE / "protocol.json")
    assert selection["source_sha256"] == sha(HERE / "select_fields.py")
    assert screen["protocol_sha256"] == sha(HERE / "protocol.json")
    assert screen["source_sha256"] == sha(HERE / "screen.py")
    assert screen["worker_sha256"] == sha(HERE / "worker.py")
    assert screen["input_sha256"] == sha(HERE / "selection.json")
    assert generators["screen_sha256"] == sha(HERE / "result.json")
    assert generators["source_sha256"] == sha(HERE / "generator_screen.py")
    assert generators["worker_sha256"] == sha(HERE / "generator.py")
    assert result["protocol_sha256"] == sha(HERE / "relation-protocol.json")
    assert result["source_sha256"] == sha(HERE / "relation.py")
    assert result["selection_sha256"] == sha(HERE / "selection.json")
    assert result["screen_sha256"] == sha(HERE / "result.json")
    assert result["generators_sha256"] == sha(HERE / "generators.json")
    for row in screen["rows"] + generators["rows"]:
        assert sha(HERE / row["stdout_path"]) == row["stdout_sha256"]
        assert sha(HERE / row["stderr_path"]) == row["stderr_sha256"]
    approved = {(r["field_prime"], r["u"]) for r in generators["rows"] if
                r["status"] == "completed" and
                r["generator"]["generator_status"] == "proved" and
                r["generator"]["point_is_signed_generator"]}
    assert len(screen["rows"]) == 40 and len(generators["rows"]) == 3
    assert len(approved) == 3
    assert screen["status_counts"] == {"completed": 30, "rank_unknown": 3, "timeout": 7}
    screened = {(r["field_prime"], r["u"]): r["candidate"] for r in screen["rows"] if "candidate" in r}
    totals = Counter()
    for (p, q), field in zip(selection["selected"], result["fields"]):
        assert field["field_prime"] == p and field["subgroup_order"] == q
        assert prime(p) and prime(q) and order_by_squares(p) == q
        G = (2 % p, 2 % p)
        multiples = [None]
        for _ in range(1, q): multiples.append(add(multiples[-1], G, p))
        assert add(multiples[-1], G, p) is None
        points = [multiples[(17-t) % q] for t in range(q)]
        doubles_neg = [neg(mul(2, P, p), p) for P in points]
        maps = []
        for model in field["models"]:
            u = model["u"]
            assert u == 1 or (p, u) in approved
            c = screened[p, u]
            x, y = c["centered_point"]
            assert y*y-x*x*x+x == c["curve_B"]
            assert c["curve_B"] % p == (-2) % p
            P = (x % p, y % p)
            assert P == multiples[u]
            mapping = {mul(k, P, p): k for k in range(-4, 5)}
            assert len(mapping) == 9
            maps.append(mapping)
        counts = [Counter() for _ in maps]
        hits = [[] for _ in maps]
        first_direct = first_rational = None
        direct_count = 0
        raw = HERE / field["raw_path"]
        assert sha(raw) == field["raw_sha256"]
        with gzip.open(raw, "rt") as rows:
            for t1, R1 in enumerate(points):
                for t2, R2 in enumerate(points):
                    row = json.loads(next(rows))
                    assert row["t"] == [t1, t2] and len(row["s"]) == len(maps)
                    admissible = R1 is not None and R2 is not None and R1 != R2
                    direct = admissible and R1 == doubles_neg[t2]
                    assert row["d"] == int(direct)
                    if admissible: direct_count += 1
                    if direct and first_direct is None:
                        first_direct = {"t": [t1, t2], "query_index_one_based": t1*q+t2+1,
                                        "direct_tests_to_hit": direct_count,
                                        "recovered_scalar": ((t1+2*t2)*pow(3,-1,q)) % q}
                        assert mul(first_direct["recovered_scalar"], G, p) == multiples[17]
                    for j, mapping in enumerate(maps):
                        if R1 is None or R2 is None: code = "I"
                        elif R1 == R2: code = "D"
                        elif R1 not in mapping or R2 not in mapping: code = "O"
                        else:
                            a, b = mapping[R1], mapping[R2]
                            rational = add(mul(a, multiples[field["models"][j]["u"]], p),
                                           mul(2*b, multiples[field["models"][j]["u"]], p), p) is None
                            assert rational == direct
                            code = "R" if rational else "N"
                            if rational:
                                hit = {"u": field["models"][j]["u"], "t": [t1, t2],
                                       "k": [a, b], "query_index_one_based": t1*q+t2+1,
                                       "recovered_scalar": ((t1+2*t2)*pow(3,-1,q)) % q}
                                assert mul(hit["recovered_scalar"], G, p) == multiples[17]
                                hits[j].append(hit)
                                if first_rational is None: first_rational = hit
                        assert row["s"][j] == code
                        counts[j][code] += 1
            assert next(rows, None) is None
        for j, model in enumerate(field["models"]):
            assert model["counts"] == dict(counts[j]) and model["hits"] == hits[j]
        assert field["first_direct"] == first_direct
        assert field["first_rational"] == first_rational
        assert field["direct_tests_complete"] == direct_count
        image_union = set().union(*(set(mapping) for mapping in maps))
        pair_union = set().union(*(set((a,b) for a in mapping for b in mapping) for mapping in maps))
        unique = set(tuple(hit["t"]) for hs in hits for hit in hs)
        assert field["image_union_size"] == len(image_union)
        assert field["pair_union_size"] == len(pair_union)
        assert field["unique_rational_relation_queries"] == len(unique)
        totals["queries"] += q*q
        totals["membership_tests"] += q*q*len(maps)
        totals["admitted_relation_tests"] += sum(c["N"]+c["R"] for c in counts)
        totals["rational_relations"] += sum(map(len, hits))
        totals["unique_relation_queries"] += len(unique)
        totals["direct_public_tests_complete"] += direct_count
    totals["rank_screen_cells"] = len(screen["rows"])
    totals["generator_check_cells"] = len(generators["rows"])
    assert result["totals"] == dict(totals)
    print(json.dumps({"schema": "xedni-nonisomorphic-holdout-audit-v1", "status": "PASS",
                      "fields": 8, "queries": totals["queries"],
                      "rational_relations": totals["rational_relations"],
                      "unique_relation_queries": totals["unique_relation_queries"]}, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
