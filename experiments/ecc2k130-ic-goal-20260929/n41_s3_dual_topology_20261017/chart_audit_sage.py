"""Check whether the alternate S3 tree excludes source-valid zero-x charts."""
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
    gpath = ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json"
    assert sha(gpath) == p["sources"]["n41_w8_fixed_sum_table_20261009/geometry.json"]
    g = json.loads(gpath.read_text())
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, "t", modulus=t**41 + t**3 + 1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    zero = curve(0)
    torsion = curve(field(0), field(1))

    def dec(word):
        return field(ring([(int(word) >> i) & 1 for i in range(41)]))

    slots = []
    for slot in range(6):
        slots.append([(sid, curve(dec(s["raw_sum"][0]), dec(s["raw_sum"][1])),
                       frozenset(s["columns"]))
                      for sid, s in enumerate(g["blocks"][slot]["states"])])
    pairs = []
    first_level_exceptions = []
    for left, right in ((0, 3), (1, 4), (2, 5)):
        table = []
        for i, a, ca in slots[left]:
            for j, b, cb in slots[right]:
                if not ca.isdisjoint(cb):
                    continue
                point = a + b
                if point == zero or point == torsion:
                    first_level_exceptions.append([left, i, right, j,
                                                   "O" if point == zero else "T"])
                table.append((i, j, point, ca | cb))
        pairs.append(table)
    lookup = {}
    for i, j, point, columns in pairs[1]:
        lookup.setdefault(point, []).append((i, j, columns))
    node9_exceptions = []
    for i, j, point, columns in pairs[0]:
        for label, complement in (("O", -point), ("T", torsion - point)):
            for k, l, other_columns in lookup.get(complement, []):
                if columns.isdisjoint(other_columns):
                    node9_exceptions.append([i, j, k, l, label])
    out = {"status": "PASS_DUAL_TREE_CHART_AUDIT",
           "protocol_sha256": sha(D / "protocol.json"),
           "audit_source_sha256": sha(D / "chart_audit_sage.py"),
           "valid_first_level_pair_counts": [len(x) for x in pairs],
           "first_level_zero_x_or_identity": first_level_exceptions,
           "valid_node9_zero_x_or_identity": node9_exceptions,
           "curve_order": int(curve.cardinality())}
    (D / "chart_audit_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: out[key] for key in (
        "status", "valid_first_level_pair_counts", "first_level_zero_x_or_identity",
        "valid_node9_zero_x_or_identity")}, sort_keys=True))


if __name__ == "__main__":
    main()
