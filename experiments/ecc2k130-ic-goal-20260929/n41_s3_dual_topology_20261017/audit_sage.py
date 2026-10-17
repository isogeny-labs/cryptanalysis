"""Independent checked-Sage replay of both six-source point-sum trees."""
import hashlib
import json
from pathlib import Path
from sage.all import GF, PolynomialRing, EllipticCurve

D = Path(__file__).resolve().parent
ROOT = D.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = json.loads((D / "protocol.json").read_text())
    build = json.loads((D / "build_result.json").read_text())
    g = json.loads((ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json").read_text())
    hit = json.loads((ROOT / "n41_sixpair_shared_target_20261017/join_audit_result.json").read_text())
    assert sha(D / "protocol.json") == build["protocol_sha256"]
    for relative, digest in p["sources"].items():
        assert sha(ROOT / relative) == digest, relative
    assert build["status"] == "PASS_DUAL_TREE_PUBLIC_FORMULA_BUILD"
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, "t", modulus=t**41 + t**3 + 1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def dec(word):
        return field(ring([(int(word) >> i) & 1 for i in range(41)]))

    def point(pair):
        return curve(dec(pair[0]), dec(pair[1]))

    source = []
    columns = set()
    for slot, row in enumerate(hit["pair_rows"]):
        state = g["blocks"][slot]["states"][row["state_id"]]
        assert state["raw_sum"] == row["raw_sum"]
        assert columns.isdisjoint(state["columns"])
        columns.update(state["columns"])
        source.append(point(state["raw_sum"]))
    assert len(columns) == 12
    target = point(p["public_raw_point"])
    intermediates = []
    for label in ("first_links", "second_links"):
        nodes = list(source) + [None] * 4 + [target]
        branch_points = []
        for left, right, out in p[label]:
            actual = nodes[left] + nodes[right]
            if out == 10:
                assert actual == target
            else:
                assert actual != curve(0) and actual[0] != 0
                nodes[out] = actual
                branch_points.append([int(out), str(actual[0]), str(actual[1])])
        assert sum(source, curve(0)) == target
        intermediates.append({"tree": label, "intermediate_count": len(branch_points),
                              "target_reached": True, "intermediates": branch_points})
    out = {"status": "PASS_INDEPENDENT_DUAL_TREE_GROUP_REPLAY",
           "protocol_sha256": sha(D / "protocol.json"),
           "build_result_sha256": sha(D / "build_result.json"),
           "audit_source_sha256": sha(D / "audit_sage.py"),
           "curve_order": int(curve.cardinality()),
           "witness_state_ids": [row["state_id"] for row in hit["pair_rows"]],
           "distinct_columns": len(columns),
           "trees": intermediates}
    (D / "audit_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: out[key] for key in (
        "status", "curve_order", "witness_state_ids", "distinct_columns")}, sort_keys=True))


if __name__ == "__main__":
    main()
