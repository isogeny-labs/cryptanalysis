"""Independent checked-Sage group join for the frozen three-free-slot panel."""
import hashlib
import json
from pathlib import Path
from sage.all import GF, PolynomialRing, EllipticCurve

D = Path(__file__).resolve().parent
ROOT = D.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    protocol = read(D / "protocol.json")
    result = read(D / "result.json")
    assert sha(D / "run.py") == protocol["runner_sha256"]
    assert result["protocol_sha256"] == sha(D / "protocol.json")
    for relative, digest in protocol["sources"].items():
        assert sha(ROOT / relative) == digest, relative
    g = read(ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json")
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, "t", modulus=t**41 + t**3 + 1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def dec(word):
        return field(ring([(int(word) >> i) & 1 for i in range(41)]))

    def point(pair):
        return curve(dec(pair[0]), dec(pair[1]))

    fixed = [g["blocks"][slot]["states"][sid]
             for slot, sid in zip((3, 4, 5), protocol["fixed_state_ids"])]
    fixed_point = sum((point(s["raw_sum"]) for s in fixed), curve(0))
    target = point(protocol["raw_target"])
    residual = target - fixed_point
    used = {column for s in fixed for column in s["columns"]}
    states = []
    for slot in range(3):
        states.append([(sid, state, point(state["raw_sum"]))
                       for sid, state in enumerate(g["blocks"][slot]["states"])
                       if used.isdisjoint(state["columns"])])
    pair_table = {}
    pair_additions = 0
    for i, a, pa in states[0]:
        ca = set(a["columns"])
        for j, b, pb in states[1]:
            if not ca.isdisjoint(b["columns"]):
                continue
            pair_table.setdefault(pa + pb, []).append((i, j, ca | set(b["columns"])))
            pair_additions += 1
    group_hits = []
    for k, c, pc in states[2]:
        for i, j, columns in pair_table.get(residual - pc, []):
            if columns.isdisjoint(c["columns"]):
                group_hits.append([i, j, k])
    group_hits.sort()
    determinant_hits = sorted(result["valid_determinant_zero_states"])
    assert group_hits == determinant_hits
    assert result["expected_state_triple"] in group_hits
    assert result["family_triples"] == result["determinant_evaluations"] // 64
    receipt = {
        "status": "PASS_INDEPENDENT_THREE_FAMILY_GROUP_JOIN",
        "curve_order": int(curve.cardinality()),
        "protocol_sha256": sha(D / "protocol.json"),
        "result_sha256": sha(D / "result.json"),
        "audit_source_sha256": sha(D / "audit_sage.py"),
        "eligible_states": [len(x) for x in states],
        "valid_pair_additions": pair_additions,
        "group_hits": group_hits,
        "determinant_hits": determinant_hits,
    }
    (D / "audit_result.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
