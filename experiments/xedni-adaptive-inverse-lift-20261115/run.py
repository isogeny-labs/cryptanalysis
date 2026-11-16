"""Complete public-pair census for the adaptive inverse-lift construction."""

import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "xedni-large-order-admission-20261115" / "result.json"
PARENT_SOURCE = HERE.parent / "xedni-public-coordinate-lift-20261115" / "run.py"
spec = importlib.util.spec_from_file_location("xedni_public_group", PARENT_SOURCE)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def centered(value, p):
    return value if value <= p // 2 else value - p


def run_field(item):
    p, q = item["field_prime"], item["subgroup_order"]
    P = (2 % p, 2 % p)
    order = parent.point_order(P, p, item["curve_order"])
    assert order % q == 0
    m = order // q
    G = parent.mul(m, P, p)
    assert parent.mul(q, G, p) is None and G is not None
    Q = parent.mul(17, G, p)
    points = [parent.add(Q, parent.mul(-t, G, p), p) for t in range(q)]
    counters = Counter()
    shards = []
    first = None
    raw_dir = HERE / "rows"
    raw_dir.mkdir(parents=True, exist_ok=True)
    out = raw = None
    for t1 in range(q):
        if t1 % 32 == 0:
            if out is not None:
                out.close()
                raw.close()
            path = raw_dir / f"p{p}-t{t1:03d}.jsonl.gz"
            shards.append(path)
            raw = path.open("wb")
            out = gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0)
        R1 = points[t1]
        for t2 in range(q):
            R2 = points[t2]
            counters["queries"] += 1
            row = {"t": [t1, t2], "status": None,
                   "public_group_tests": 0, "curve_constructions": 0}
            if R1 is None or R2 is None:
                row["status"] = "identity"
            elif R1 == R2:
                row["status"] = "duplicate"
            else:
                row["public_group_tests"] = 1
                counters["public_group_tests"] += 1
                if parent.add(R1, R2, p) is not None:
                    row["status"] = "public_nonrelation"
                else:
                    counters["public_inverse_pairs"] += 1
                    assert R1[0] == R2[0] and (R1[1] + R2[1]) % p == 0
                    x, y = centered(R1[0], p), centered(R1[1], p)
                    B = y * y - x * x * x + x
                    discriminant = -16 * (-4 + 27 * B * B)
                    row["curve_constructions"] = 1
                    counters["curve_constructions"] += 1
                    if discriminant == 0 or discriminant % p == 0:
                        row["status"] = "invalid_curve"
                    else:
                        assert B % p == (-2) % p
                        assert y * y == x * x * x - x + B
                        assert parent.rational_add((x, y), (x, -y)) is None
                        assert (x % p, (-y) % p) == R2
                        recovered = ((t1 + t2) * pow(2, -1, q)) % q
                        assert recovered == 17 and parent.mul(recovered, G, p) == Q
                        row.update({"status": "rational_relation",
                                    "curve_B": B,
                                    "lifted_points": [[x, y], [x, -y]],
                                    "recovered_scalar": recovered})
                        counters["rational_relations"] += 1
                        if first is None:
                            first = {"t": [t1, t2],
                                     "query_index_one_based": counters["queries"]}
            counters[f"status_{row['status']}"] += 1
            out.write((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode())
    if out is not None:
        out.close()
        raw.close()
    assert counters["queries"] == q * q
    assert sum(value for key, value in counters.items()
               if key.startswith("status_")) == q * q
    return {"field_prime": p, "subgroup_order": q,
            "generator_reduction_order": order, "subgroup_multiplier_m": m,
            "generator": list(G), "public_target": list(Q),
            "counts": dict(counters), "first_rational_relation": first,
            "row_shards": [{"path": str(path.relative_to(HERE)), "sha256": sha(path)}
                           for path in shards]}


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["schema"] == "xedni-adaptive-inverse-lift-protocol-v1"
    assert sha(INPUT) == protocol["input_selection_result_sha256"]
    assert sha(PARENT_SOURCE) == protocol["parent_finite_group_source_sha256"]
    selected = [r for r in json.loads(INPUT.read_text())["rows"] if r["selected"]]
    fields = [run_field(item) for item in selected]
    keys = ("queries", "public_group_tests", "public_inverse_pairs",
            "curve_constructions", "rational_relations", "status_identity",
            "status_duplicate", "status_public_nonrelation", "status_rational_relation",
            "status_invalid_curve")
    result = {"schema": "xedni-adaptive-inverse-lift-result-v1",
              "status": "PASS", "protocol_sha256": sha(HERE / "protocol.json"),
              "source_sha256": sha(Path(__file__)),
              "input_sha256": sha(INPUT), "parent_source_sha256": sha(PARENT_SOURCE),
              "fields": fields,
              "totals": {key: sum(f["counts"].get(key, 0) for f in fields) for key in keys}}
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
