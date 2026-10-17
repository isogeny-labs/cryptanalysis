"""Independent Sage replay of the saved four-power trace certificate."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, Matrix, PolynomialRing

D = Path(__file__).resolve().parent
ROOT = D.parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
protocol = json.loads((D / "certificate_audit_protocol.json").read_text())
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
panel = json.loads((ROOT / "n41_n131_rr_code_family_span_20261017/panel_n131_v2.json").read_text())
certificate = json.loads((D / "odd_certificate.json").read_text())
R = PolynomialRing(GF(2), "t")
t = R.gen()
F = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])
def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(131)]))
assert certificate["odd_powers"] == [1, 3, 5, 7]
coefficients = [dec(word) for word in certificate["trace_coefficients"]]
checked = 0
for variant in panel["variants"]:
    for root in variant["roots"]:
        points = [root[0]] + panel["fixed_points"]
        coords = points + [[panel["target"][0], panel["target"][1] ^ panel["target"][0]]]
        assert all(E.is_on_curve(dec(x), dec(y)) for x, y in coords)
        xs = [dec(point[0]) for point in coords]
        ys = [dec(point[1]) for point in coords]
        assert len(set(xs)) == 7
        for signs in range(64):
            mat = Matrix(F, 7, 7)
            for i, (x, y) in enumerate(zip(xs, ys)):
                if i < 6 and signs >> i & 1:
                    y += x
                mat[i] = [F.one(), x, y, x**2, x*y, x**3, x**2*y]
            determinant = mat.det()
            trace_value = sum((a * determinant**power for a, power in
                               zip(coefficients, certificate["odd_powers"])), F.zero()).trace()
            assert int(trace_value) == 1
            checked += 1
assert checked == certificate["signed_determinants_checked"] == 512
out = {"status": "PASS_INDEPENDENT_SAGE_FOUR_POWER_CERTIFICATE",
       "protocol_sha256": sha(D / "certificate_audit_protocol.json"),
       "certificate_sha256": sha(D / "odd_certificate.json"),
       "signed_determinants_checked": checked}
(D / "certificate_audit_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(out["status"])
