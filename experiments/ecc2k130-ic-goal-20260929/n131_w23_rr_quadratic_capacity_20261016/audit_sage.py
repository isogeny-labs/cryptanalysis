"""Independently evaluate every saved N131 seven-point RR determinant."""
import hashlib
import json
import time
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing, matrix

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
freeze = json.loads((HERE / "audit_protocol.json").read_text())
for path, digest in freeze["sources"].items():
    assert sha(path) == digest, path
assert sha(HERE / "audit_sage.py") == freeze["auditor_sha256"]
panel = json.loads((HERE / "panel.json").read_text())
coefficients = json.loads((HERE / "coefficients.json").read_text())
assert len(coefficients) == 68

R = PolynomialRing(GF(2), "t")
t = R.gen()
F = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])

def dec(value):
    return F(R([(int(value) >> i) & 1 for i in range(131)]))

def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

def anf_truth(coeffs, sign):
    answer = 0
    for support, value in enumerate(coeffs):
        if support & sign == support:
            answer ^= value
    return answer

target = [dec(x) for x in panel["target"]]
assert E(target) != E(0)
target_row = [target[0], target[1] + target[0]]
fixed = [[dec(x), dec(y)] for x, y in panel["fixed_points"]]
for point in fixed:
    assert E(point) != E(0)

def rr_row(point):
    x, y = point
    return [F.one(), x, y, x*x, x*y, x*x*x, x*x*y]

start = time.monotonic()
chart_digests = []
zero_states = []
for ordinal, record in enumerate(coefficients):
    variant = panel["variants"][ordinal]
    assert record["mask"] == variant["mask"]
    for root in range(2):
        first = [dec(value) for value in variant["roots"][root][0]]
        second = [dec(value) for value in variant["roots"][root][1]]
        assert first[0] == second[0] and first[1] + first[0] == second[1]
        assert E(first) != E(0) and E(second) != E(0)
        base = [first] + fixed
        assert len({enc(point[0]) for point in base + [target_row]}) == 7
        observed = []
        for sign in range(64):
            selected = [[point[0], point[1] + (point[0] if sign >> i & 1 else F.zero())]
                        for i, point in enumerate(base)]
            direct = enc(matrix(F, [rr_row(point) for point in selected] +
                                [rr_row(target_row)]).det())
            expected = anf_truth(record["coefficients"][root], sign)
            assert direct == expected, (ordinal, root, sign, direct, expected)
            observed.append(direct)
            if direct == 0:
                zero_states.append([ordinal, variant["mask"], root, sign])
        chart_digests.append({"ordinal": ordinal, "mask": variant["mask"],
                              "root": root,
                              "truth_sha256": hashlib.sha256(json.dumps(observed).encode()).hexdigest()})
    if (ordinal + 1) % 10 == 0 or ordinal + 1 == len(coefficients):
        print(json.dumps({"audited_codes": ordinal + 1,
                          "audited_determinants": (ordinal + 1) * 128,
                          "elapsed_seconds": time.monotonic() - start}, sort_keys=True), flush=True)

out = {"status": "PASS_FULL_N131_W23_RR_DETERMINANT_REPLAY",
       "candidate_id": None, "audited_codes": len(coefficients),
       "audited_charts": len(chart_digests),
       "audited_determinants": len(chart_digests) * 64,
       "zero_states": zero_states,
       "chart_digests": chart_digests,
       "elapsed_seconds_exploratory": time.monotonic() - start,
       "audit_protocol_sha256": sha(HERE / "audit_protocol.json")}
(HERE / "audit_result.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print(out["status"])
