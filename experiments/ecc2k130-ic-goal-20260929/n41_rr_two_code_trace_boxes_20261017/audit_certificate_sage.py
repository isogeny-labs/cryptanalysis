"""Independent Sage replay of all 1024 signed 25-power trace values."""
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
result = json.loads((D / "result.json").read_text())
certificate = json.loads((D / "certificate.json").read_text())
hit = json.loads((ROOT / "n41_sixpair_shared_target_20261017/join_audit_result.json").read_text())
geometry = json.loads((ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json").read_text())
R = PolynomialRing(GF(2), "t")
t = R.gen()
F = GF(2**41, name="t", modulus=t**41+t**3+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(41)]))


fixed = []
for slot in range(2, 6):
    witness = hit["pair_rows"][slot]["raw_sum"]
    points = [s["raw_sum"] for s in geometry["blocks"][slot]["states"]
              if s["raw_sum"][0] == witness[0]]
    fixed.append(min(points, key=lambda p: p[1]))
assert certificate["odd_powers"] == list(range(1, 50, 2))
coefficients = [dec(word) for word in certificate["trace_coefficients"]]
checked = 0
for chart in result["boxes"][0]["charts"]:
    points = [chart["point_a"], chart["point_b"]] + fixed
    target = hit["raw_target"]
    coords = points + [[target[0], target[1] ^ target[0]]]
    assert all(E.is_on_curve(dec(x), dec(y)) for x, y in coords)
    xs = [dec(x) for x, _ in coords]
    ys = [dec(y) for _, y in coords]
    assert len(set(xs)) == 7
    for signs in range(64):
        mat = Matrix(F, 7, 7)
        for i, (x, y) in enumerate(zip(xs, ys)):
            if i < 6 and signs >> i & 1:
                y += x
            mat[i] = [F.one(), x, y, x**2, x*y, x**3, x**2*y]
        value = mat.det()
        trace_value = sum((a*value**power for a, power in
                           zip(coefficients, certificate["odd_powers"])), F.zero()).trace()
        assert int(trace_value) == 1
        checked += 1
assert checked == certificate["signed_determinants_checked"] == 1024
out = {"status": "PASS_INDEPENDENT_SAGE_N41_25_POWER_CERTIFICATE",
       "protocol_sha256": sha(D / "certificate_audit_protocol.json"),
       "certificate_sha256": sha(D / "certificate.json"),
       "signed_determinants_checked": checked}
(D / "certificate_audit_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(out["status"])
