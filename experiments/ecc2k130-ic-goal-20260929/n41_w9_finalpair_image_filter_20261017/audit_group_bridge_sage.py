"""Check that target residual points supply unrestricted final-pair products."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
p = json.loads((HERE / "group_bridge_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in p["sources"].items():
    assert sha(path) == expected, path
assert not (HERE / "group_bridge_result.json").exists()
started = time.monotonic()
protocol = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())
source = json.loads(Path(protocol["states"]).read_text())
fixture = json.loads(Path(protocol["fixture"]).read_text())

K = PolynomialRing(GF(2), "u")
u = K.gen()
F = GF(2**41, name="u", modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(number):
    return F(K([(int(number) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(coef) << i for i, coef in enumerate(value.polynomial().list()))


seed = dec(source["seed"] << 1)
half = F(0)
term = seed
for _ in range(21):
    half += term
    term = term**4
assert half**2 + half == seed
H = (half**2)**(2**24)
C = 1 + H
t = dec(fixture["public_reciprocal"])
Q = E(dec(fixture["public_point"][0]), dec(fixture["public_point"][1]))


def state_point(slot, state_id):
    x, y = source["states"][slot][state_id]["point"]
    return E(dec(x), dec(y))


def check(row, ids):
    P = sum((state_point(slot, state_id) for slot, state_id in
             enumerate(ids)), E(0))
    assert P != E(0) and P[0]
    w = 1/P[0]
    assert enc(w) == row["w"]
    B = t*w
    A = 1+B**2
    D = t**2+w**2
    M = A*H+C*D
    L_a = A*D
    L_b = B*M
    right = M**2+C*H*B**2
    products = []
    exceptions = []
    for tag, residual in (("minus", Q-P), ("plus", Q+P)):
        if residual == E(0) or not residual[0]:
            exceptions.append(tag)
            continue
        e = 1/residual[0]
        assert A*e**2+B*e+D == 0
        product = (C*e**2+H)/e
        assert C*e**2+product*e+H == 0
        assert L_a*product**2+L_b*product+right == 0
        products.append(enc(product))
    return products, exceptions


positive, positive_exceptions = check(
    result["positive"], fixture["state_ids"][:4])
products = []
exception_counts = {"minus": 0, "plus": 0}
for row in result["reachable"]:
    current, exceptions = check(row, row["first_four_state_ids"])
    products.append(current)
    for tag in exceptions:
        exception_counts[tag] += 1
    assert not row["linear_image_codes"]
    assert len(current) == row["field_root_count"]
    assert len(set(current)) == len(current)
assert not positive_exceptions
assert len(positive) == result["positive"]["field_root_count"]

audit = {"status": "PASS_GROUP_TO_UNRESTRICTED_PRODUCT_BRIDGE",
         "curve_id": result["curve_id"], "candidate_id": None,
         "reachable_sums_checked": len(products),
         "reachable_with_two_residual_products": sum(len(p) == 2 for p in products),
         "exception_counts": exception_counts,
         "positive_products": positive,
         "elapsed_seconds": time.monotonic()-started,
         "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         "protocol_sha256": sha(HERE / "group_bridge_protocol.json")}
(HERE / "group_bridge_result.json").write_text(json.dumps(audit,sort_keys=True,indent=2)+"\n")
print(json.dumps(audit,sort_keys=True))
