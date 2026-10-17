"""Independent checked-Sage replay of the final-pair image panel."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
audit_protocol = json.loads((HERE / "audit_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in audit_protocol["sources"].items():
    assert sha(path) == expected, path
assert not (HERE / "audit_sage_result.json").exists()
start = time.monotonic()
protocol = json.loads((HERE / "protocol.json").read_text())
run = json.loads((HERE / "result.json").read_text())
source = json.loads(Path(protocol["states"]).read_text())
fixture = json.loads(Path(protocol["fixture"]).read_text())
witness = json.loads(Path(protocol["witness"]).read_text())
wires = json.loads(Path(protocol["wires"]).read_text())
assert run["status"] == "PASS_EXACT_FINALPAIR_CODE_RECOVERY_PANEL"
assert run["protocol_sha256"] == sha(HERE / "protocol.json")

K = PolynomialRing(GF(2), "u")
u = K.gen()
F = GF(2**41, name="u", modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(number):
    return F(K([(int(number) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(coef) << i for i, coef in enumerate(value.polynomial().list()))


def trace(value):
    acc = F(0)
    for _ in range(41):
        acc += value
        value = value**2
    assert acc in (0, 1)
    return int(acc)


seed = dec(source["seed"] << 1)
half = F(0)
term = seed
for _ in range(21):
    half += term
    term = term**4
assert half**2 + half == seed
H = (half**2) ** (2**24)
C = 1 + H
t = dec(fixture["public_reciprocal"])
bits = [i for i in range(9) if i != 5]
basis = [(dec((1 << bit) << 1) * dec(((1 << bit) << 1) ^
          (source["seed"] << 1))) ** (2**24) for bit in bits]
pvals = [sum((basis[j] for j in range(8) if code >> j & 1), F(0))
         for code in range(256)]
assert len({enc(p) for p in pvals}) == 256
allowed = set(wires["allowed_code_words"])


def coefficients(w):
    B = t*w
    A = 1 + B**2
    D = t**2 + w**2
    M = A*H + C*D
    return A*D, B*M, M**2 + C*H*B**2


def rank(values):
    pivots = {}
    for value in values:
        v = enc(value)
        while v:
            bit = v.bit_length() - 1
            if bit in pivots:
                v ^= pivots[bit]
            else:
                pivots[bit] = v
                break
    return len(pivots)


def audit_row(row):
    w = dec(row["w"])
    a, b, q = coefficients(w)
    direct = [code for code, p in enumerate(pvals)
              if a*p**2 + b*p + q == 0]
    assert direct == row["linear_image_codes"]
    assert [code for code in direct if code in allowed] == row["allowed_codes"]
    assert rank([a*p**2 + b*p for p in basis]) == row["map_rank"]
    if a and b:
        chart = "ARTIN_SCHREIER"
        rhs = q*a/b**2
        assert row["field_root_count"] == (0 if trace(rhs) else 2)
    elif a:
        chart = "SQUARE"
        assert row["field_root_count"] == 1
    elif b:
        chart = "LINEAR"
        assert row["field_root_count"] == 1
    else:
        chart = "ZERO_MAP"
        assert row["field_root_count"] == (2**41 if q == 0 else 0)
    assert row["chart"] == chart


for row in [run["positive"], *run["special"], *run["uniform"], *run["reachable"]]:
    audit_row(row)


def state_point(slot, state_id):
    x, y = source["states"][slot][state_id]["point"]
    return E(dec(x), dec(y))


public = E(dec(fixture["public_point"][0]),
           dec(fixture["public_point"][1]))
positive_ids = fixture["state_ids"]
first = sum((state_point(slot, state_id) for slot, state_id in
             enumerate(positive_ids[:4])), E(0))
assert enc(1/first[0]) == witness["intermediate_reciprocal"]
assert first + state_point(4, positive_ids[4]) == public
assert run["positive"]["allowed_codes"] == [fixture["code_bit_words"][4]]

for row in run["reachable"]:
    ids = row["first_four_state_ids"]
    points = [state_point(slot, state_id) for slot, state_id in enumerate(ids)]
    assert len({column for slot, state_id in enumerate(ids)
                for column in source["states"][slot][state_id]["columns"]}) == 8
    point = sum(points, E(0))
    assert point != E(0) and point[0]
    assert enc(1/point[0]) == row["w"]
    assert not row["allowed_codes"] and "exact_group_hits" not in row

elapsed = time.monotonic() - start
audit = {"status": "PASS_INDEPENDENT_SAGE_FINALPAIR_IMAGE_REPLAY",
         "curve_id": run["curve_id"], "candidate_id": None,
         "rows_checked": 1 + len(run["special"]) + len(run["uniform"]) +
                         len(run["reachable"]),
         "reachable_group_sums_checked": len(run["reachable"]),
         "positive_group_relation_checked": True,
         "elapsed_seconds": elapsed,
         "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         "audit_protocol_sha256": sha(HERE / "audit_protocol.json")}
(HERE / "audit_sage_result.json").write_text(json.dumps(audit, sort_keys=True, indent=2)+"\n")
print(json.dumps(audit, sort_keys=True))
