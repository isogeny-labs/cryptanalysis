"""Replay the exact chord-slope filter on the frozen matched-band target rows."""
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "xedni-crt-band-panel-20261115"
ARITH = HERE.parent / "xedni-crt-prime-panel-20261115" / "audit.py"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["schema"] == "xedni-integral-chord-filter-protocol-v1"
    for key, path in (("parent_protocol_sha256", PARENT / "protocol.json"),
                      ("parent_result_sha256", PARENT / "result.json"),
                      ("parent_audit_source_sha256", PARENT / "audit.py"),
                      ("parent_arithmetic_source_sha256", ARITH)):
        assert digest(path) == protocol[key], key
    spec = importlib.util.spec_from_file_location("xedni_chord_parent_arithmetic", ARITH)
    arith = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arith)
    parent = json.loads((PARENT / "result.json").read_text())
    base = [0, 0, 0, -1, -2]
    orders = {prime: arith.prior.candidates(prime) for prime in (7, 11)}
    characters = {}
    for prime in orders:
        squares = {x * x % prime for x in range(1, prime)}
        characters[prime] = [0 if x == 0 else 1 if x in squares else -1
                             for x in range(prime)]
    fields = []
    total = Counter()
    for record in parent["fields"]:
        p, r = record["field_prime"], record["subgroup_order"]
        generator = tuple(record["generator"])
        public = tuple(record["public_target"])
        sampled = [arith.add(public,
                             arith.neg(arith.mul(t, generator, base, p), base, p),
                             base, p) for t in range(r)]
        counts = Counter()
        raw_hash = hashlib.sha256()
        index = 0
        examples = []
        for shard in record["row_shards"]:
            raw = gzip.open(PARENT / "rows" / shard, "rb").read()
            raw_hash.update(raw)
            for line in raw.splitlines():
                row = json.loads(line)
                t1, t2 = divmod(index, r)
                index += 1
                assert row["t"] == [t1, t2]
                counts["target_queries"] += 1
                U, V = sampled[t1], sampled[t2]
                reduced = U is not None and V is not None and U != V and \
                    arith.add(U, arith.mul(2, V, base, p), base, p) is None
                assert row["reduced_relation"] == reduced
                if not reduced:
                    assert not row["rational_relation"]
                    continue
                counts["reduced_relations"] += 1
                (x1, y1), (x2, y2) = [(arith.centered(x, p), arith.centered(y, p))
                                      for x, y in (U, V)]
                if x1 == x2:
                    counts["same_x"] += 1
                    assert not row["rational_relation"]
                    continue
                counts["distinct_x"] += 1
                integral = (y1 - y2) % (x1 - x2) == 0
                counts["integral_slope"] += integral
                counts["accepted_reduced"] += row["accepted"]
                counts["accepted_integral_slope"] += row["accepted"] and integral
                counts["rational_relation"] += row["rational_relation"]
                assert not row["rational_relation"] or (row["accepted"] and integral)
                equality = False
                if row["accepted"] and integral:
                    points = [(x1, y1), (x2, y2)]
                    c7, n7 = arith.prior.find_candidate(points, 7, 4,
                                                        orders[7], characters[7])
                    c11, n11 = arith.prior.find_candidate(points, 11, 6,
                                                          orders[11], characters[11])
                    assert c7 is not None and c11 is not None
                    assert n7 == row["attempts_7"] and n11 == row["attempts_11"]
                    a1 = arith.crt_free(p, c7[0], c11[0])
                    a2 = arith.crt_free(p, c7[1], c11[1])
                    slope = (y1 - y2) // (x1 - x2)
                    equality = slope*slope + a1*slope == a2 + x1 + 2*x2
                    counts["monic_equality"] += equality
                    assert equality == row["rational_relation"]
                if integral:
                    examples.append({"t": [t1, t2], "slope": (y1-y2)//(x1-x2),
                                     "accepted": row["accepted"],
                                     "monic_equality": equality,
                                     "rational_relation": row["rational_relation"]})
        assert index == r*r and raw_hash.hexdigest() == record["rows_sha256"]
        assert counts["accepted_reduced"] == record["counts"].get("accepted_reduced_relations", 0)
        assert counts["rational_relation"] == record["counts"].get("accepted_rational_relations", 0)
        total.update(counts)
        fields.append({"field_prime": p, "subgroup_order": r,
                       "counts": dict(counts), "integral_slope_rows": examples})
    result = {"schema": "xedni-integral-chord-filter-result-v1", "status": "PASS",
              "protocol_sha256": digest(HERE / "protocol.json"),
              "source_sha256": digest(HERE / "audit.py"),
              "fields": fields, "total": dict(total)}
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
