"""Independent Sage replay of two-code box determinants and decisive ranks."""
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
hit = json.loads((ROOT / "n41_sixpair_shared_target_20261017/join_audit_result.json").read_text())
geometry = json.loads((ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json").read_text())
R = PolynomialRing(GF(2), "t")
t = R.gen()
F = GF(2**41, name="t", modulus=t**41+t**3+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


fixed = []
for slot in range(2, 6):
    witness = hit["pair_rows"][slot]["raw_sum"]
    state_points = [s["raw_sum"] for s in geometry["blocks"][slot]["states"]
                    if s["raw_sum"][0] == witness[0]]
    assert len(state_points) == 2
    fixed.append(min(state_points, key=lambda p: p[1]))


def direct_values(chart):
    points = [chart["point_a"], chart["point_b"]] + fixed
    target = hit["raw_target"]
    coords = points + [[target[0], target[1] ^ target[0]]]
    assert all(E.is_on_curve(dec(x), dec(y)) for x, y in coords)
    xs = [dec(x) for x, _ in coords]
    ys = [dec(y) for _, y in coords]
    assert len(set(xs)) == 7
    values = []
    for signs in range(64):
        mat = Matrix(F, 7, 7)
        for i, (x, y) in enumerate(zip(xs, ys)):
            if i < 6 and signs >> i & 1:
                y += x
            mat[i] = [F.one(), x, y, x**2, x*y, x**3, x**2*y]
        values.append(mat.det())
    return values


def anf(values):
    out = [enc(value) for value in values]
    for bit in range(6):
        for mask in range(64):
            if mask >> bit & 1:
                out[mask] ^= out[mask ^ (1 << bit)]
    return out


def rank(words, width):
    return Matrix(GF(2), [[word >> i & 1 for i in range(width)] for word in words]).rank()


audited = []
for box in result["boxes"]:
    rows = []
    zeros = 0
    for chart in box["charts"]:
        assert chart["status"] == "VALID_CHART"
        values = direct_values(chart)
        zeros += sum(value == 0 for value in values)
        assert [i for i, value in enumerate(values) if value == 0] == chart["zero_sign_masks"]
        assert hashlib.sha256(json.dumps(anf(values)).encode()).hexdigest() == chart["coefficient_sha256"]
        if box["name"] == "lexical_2x2":
            powers = [anf([value**exponent for value in values])
                      for exponent in range(1, 50, 2)]
            rows.extend((tuple(power[mask] for power in powers), int(mask == 0))
                        for mask in range(64))
    assert zeros == box["zero_count"]
    rank_checks = []
    if rows:
        for count in (1, 2, 24, 25):
            feature_words = [sum(value << (i*41) for i, value in enumerate(features[:count]))
                             for features, _ in rows]
            feature_rank = rank(feature_words, count*41)
            augmented_rank = rank([word | (label << (count*41))
                                   for word, (_, label) in zip(feature_words, rows)], count*41+1)
            saved = box["trace"]["ranks"][count-1]
            assert (feature_rank, augmented_rank) == (saved["feature_rank"], saved["augmented_rank"])
            rank_checks.append({"power_count": count, "feature_rank": feature_rank,
                                "augmented_rank": augmented_rank})
    audited.append({"name": box["name"], "charts": len(box["charts"]),
                    "zeros": zeros, "rank_checks": rank_checks})
assert audited[0]["zeros"] == 0 and audited[1]["zeros"] == 1
out = {"status": "PASS_INDEPENDENT_SAGE_TWO_CODE_BOX_REPLAY",
       "protocol_sha256": sha(D / "audit_protocol.json"),
       "producer_sha256": sha(D / "result.json"), "boxes": audited}
(D / "audit_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(out["status"], flush=True)
