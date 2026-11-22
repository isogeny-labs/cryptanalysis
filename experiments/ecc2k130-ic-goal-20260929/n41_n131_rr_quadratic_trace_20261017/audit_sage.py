"""Independent Sage determinant, feature-rank, and trace replay."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, Matrix, PolynomialRing

D = Path(__file__).resolve().parent
ROOT = D.parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
protocol = json.loads((D / "audit_protocol.json").read_text())
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
result = json.loads((D / "result.json").read_text())


def audit_field(n, modulus):
    R = PolynomialRing(GF(2), "t")
    t = R.gen()
    F = GF(2**n, name="t", modulus=sum(((modulus >> i) & 1) * t**i
                                        for i in range(n + 1)))
    E = EllipticCurve(F, [1, 0, 0, 0, 1])
    def dec(word):
        return F(R([(int(word) >> i) & 1 for i in range(n)]))
    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
    return F, E, dec, enc


def chart(points, target, field):
    F, E, dec, enc = field
    assert all(E.is_on_curve(dec(x), dec(y)) for x, y in points + [target])
    coords = points + [[target[0], target[1] ^ target[0]]]
    xs = [dec(point[0]) for point in coords]
    ys = [dec(point[1]) for point in coords]
    assert len(set(xs)) == 7
    values = []
    for signs in range(64):
        mat = Matrix(F, 7, 7)
        for i, (x, y) in enumerate(zip(xs, ys)):
            if i < 6 and signs >> i & 1:
                y += x
            mat[i] = [F.one(), x, y, x**2, x*y, x**3, x**2*y]
        values.append(enc(mat.det()))
    coefficients = values[:]
    cubes = [enc(dec(v)**3) for v in values]
    for bit in range(6):
        for mask in range(64):
            if mask >> bit & 1:
                coefficients[mask] ^= coefficients[mask ^ (1 << bit)]
                cubes[mask] ^= cubes[mask ^ (1 << bit)]
    return values, coefficients, cubes


def rank(words, width):
    return Matrix(GF(2), [[(word >> j) & 1 for j in range(width)]
                          for word in words]).rank()


def audit_panel(name, n, modulus, target, fixed, families, selected_codes=None):
    field = audit_field(n, modulus)
    records = result[name]["records"]
    assert len(families) == len(records)
    all_features = []
    all_values = []
    checked = []
    for family, saved in zip(families, records):
        assert family["code"] == saved["code"]
        if selected_codes is not None and family["code"] not in selected_codes:
            continue
        root_rows = []
        for root_index, first in enumerate(family["roots"]):
            values, c, d = chart([first] + fixed, target, field)
            expected = saved["roots"][root_index]
            assert expected["status"] == "VALID_CHART"
            assert hashlib.sha256(json.dumps(c).encode()).hexdigest() == expected["coefficient_sha256"]
            assert hashlib.sha256(json.dumps(d).encode()).hexdigest() == expected["cube_coefficient_sha256"]
            assert [i for i, value in enumerate(values) if value == 0] == expected["zero_sign_masks"]
            all_values.extend(values)
            root_rows.extend((c[mask] | (d[mask] << n), int(mask == 0))
                             for mask in range(64))
        if selected_codes is None or name == "n131" or family["code"] == 2:
            all_features.extend(root_rows)
            feature_rank = rank([w for w, _ in all_features], 2*n)
            augmented_rank = rank([w | (label << (2*n))
                                   for w, label in all_features], 2*n + 1)
            assert (feature_rank, augmented_rank) == (saved["feature_rank"], saved["augmented_rank"])
            if saved["certificate"] is not None:
                a = field[2](saved["certificate"]["trace_a"])
                b = field[2](saved["certificate"]["trace_b"])
                assert all(int((a*field[2](v)+b*field[2](v)**3).trace()) == 1
                           for v in all_values)
        checked.append({"code": family["code"], "charts": len(family["roots"]),
                        "zeros": sum(len(root["zero_sign_masks"]) for root in saved["roots"])})
    failure = result[name]["first_failure"]
    if name in ("n131", "n41"):
        witnesses = failure["xor_row_indices"]
        assert max(witnesses) < len(all_features)
        assert 0 == __import__("functools").reduce(
            lambda x, i: x ^ all_features[i][0], witnesses, 0)
        assert 1 == (__import__("functools").reduce(
            lambda x, i: x ^ all_features[i][1], witnesses, 0))
    if name == "n41":
        assert checked[0]["code"] == 2 and checked[1]["code"] == 6
        assert checked[1]["zeros"] == 1
    return checked


span = ROOT / "n41_n131_rr_code_family_span_20261017"
panel = json.loads((span / "panel_n131_v2.json").read_text())
families131 = [{"code": variant["masks"][0],
                "roots": [root[0] for root in variant["roots"]]}
               for variant in panel["variants"]]
checked131 = audit_panel("n131", 131, panel["field_modulus"], panel["target"],
                         panel["fixed_points"], families131)
geometry = json.loads((ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json").read_text())
hit = json.loads((ROOT / "n41_sixpair_shared_target_20261017/join_audit_result.json").read_text())
fixed41 = [min((state["raw_sum"] for state in geometry["blocks"][slot]["states"]
                if state["raw_sum"][0] == hit["pair_rows"][slot]["raw_sum"][0]),
               key=lambda p: p[1]) for slot in range(1, 6)]
families41 = []
used = {column for row in hit["pair_rows"][1:] for column in row["columns"]}
for mask in geometry["permitted_canonical_a"]:
    states = [s for s in geometry["blocks"][0]["states"] if s["a"] == mask]
    if not used.isdisjoint(states[0]["columns"]):
        continue
    roots = [min((s["raw_sum"] for s in states if s["raw_sum"][0] == x),
                 key=lambda p: p[1]) for x in sorted({s["raw_sum"][0] for s in states})]
    families41.append({"code": mask, "roots": roots})
checked41 = audit_panel("n41", 41, (1 << 41) | (1 << 3) | 1,
                        hit["raw_target"], fixed41, families41, {2, 6})
out = {"status": "PASS_INDEPENDENT_SAGE_QUADRATIC_TRACE_REPLAY",
       "protocol_sha256": sha(D / "audit_protocol.json"),
       "producer_sha256": sha(D / "result.json"),
       "checked_n41": checked41, "checked_n131": checked131}
(D / "audit_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(out["status"], flush=True)
