"""Independent Sage determinant replay of all odd-power feature ranks."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, Matrix, PolynomialRing

D = Path(__file__).resolve().parent
ROOT = D.parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
protocol = json.loads((D / "odd_audit_protocol.json").read_text())
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
panel = json.loads((ROOT / "n41_n131_rr_code_family_span_20261017/panel_n131_v2.json").read_text())
producer = json.loads((D / "odd_result.json").read_text())
n = 131
R = PolynomialRing(GF(2), "t")
t = R.gen()
F = GF(2**n, name="t", modulus=t**n+t**13+t**2+t+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(n)]))


def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def determinant_values(points):
    coords = points + [[panel["target"][0], panel["target"][1] ^ panel["target"][0]]]
    assert all(E.is_on_curve(dec(x), dec(y)) for x, y in coords)
    xs = [dec(x) for x, _ in coords]
    ys = [dec(y) for _, y in coords]
    assert len(set(xs)) == 7
    out = []
    for signs in range(64):
        mat = Matrix(F, 7, 7)
        for i, (x, y) in enumerate(zip(xs, ys)):
            if i < 6 and signs >> i & 1:
                y += x
            mat[i] = [F.one(), x, y, x**2, x*y, x**3, x**2*y]
        out.append(mat.det())
    return out


def anf(values):
    out = [enc(value) for value in values]
    for bit in range(6):
        for mask in range(64):
            if mask >> bit & 1:
                out[mask] ^= out[mask ^ (1 << bit)]
    return out


def matrix_rank(words, width):
    return Matrix(GF(2), [[word >> bit & 1 for bit in range(width)]
                          for word in words]).rank()


family_features = []
for variant in panel["variants"]:
    family = []
    for root in variant["roots"]:
        values = determinant_values([root[0]] + panel["fixed_points"])
        powers = [anf([value**exponent for value in values]) for exponent in (1, 3, 5, 7)]
        family.extend((tuple(power[mask] for power in powers), int(mask == 0))
                      for mask in range(64))
    family_features.append(family)
audited = []
for count, saved in enumerate(producer["screens"], 1):
    assert saved["odd_powers"] == [1, 3, 5, 7][:count]
    rows = []
    failed = None
    ranks = []
    for family, record in zip(family_features, saved["records"]):
        rows.extend((sum(value << (i*n) for i, value in enumerate(coeff[:count])), label)
                    for coeff, label in family)
        rank = matrix_rank([word for word, _ in rows], n*count)
        augmented = matrix_rank([word | (label << (n*count)) for word, label in rows], n*count+1)
        assert (rank, augmented) == (record["feature_rank"], record["augmented_rank"])
        assert (rank == augmented) == record["shared_certificate_exists"]
        ranks.append(rank)
        if rank != augmented and failed is None:
            failed = record["code"]
    assert failed == saved["first_failed_code"]
    audited.append({"odd_powers": saved["odd_powers"], "ranks": ranks,
                    "first_failed_code": failed})
out = {"status": "PASS_INDEPENDENT_SAGE_ODD_POWER_RANK_REPLAY",
       "protocol_sha256": sha(D / "odd_audit_protocol.json"),
       "producer_sha256": sha(D / "odd_result.json"), "screens": audited}
(D / "odd_audit_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(out["status"], flush=True)
