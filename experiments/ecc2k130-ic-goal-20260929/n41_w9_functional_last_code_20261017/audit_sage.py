"""Independent Sage replay of the guarded decoder's regular root formula."""
import hashlib
import json
import resource
import time
from collections import Counter
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ap = json.loads((HERE / "audit_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in ap["sources"].items():
    assert sha(path) == expected, path
assert not (HERE / "audit_result.json").exists()
started = time.monotonic()
p = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())
source = json.loads(Path(p["states"]).read_text())
fixture = json.loads(Path(p["fixture"]).read_text())
table = json.loads(Path(p["table"]).read_text())
panel = json.loads(Path(ap["control_panel"]).read_text())
assert result["status"] == "PASS_N41_GUARDED_FUNCTIONAL_LAST_CODE_BUILD"

K = PolynomialRing(GF(2), "u")
u = K.gen()
F = GF(2**41, name="u", modulus=u**41+u**3+1)


def dec(number):
    return F(K([(int(number) >> i) & 1 for i in range(41)]))


seed = dec(source["seed"] << 1)


def halftrace(value):
    out = F(0)
    for _ in range(21):
        out += value
        value = value**4
    return out


def trace(value):
    out = F(0)
    for _ in range(41):
        out += value
        value = value**2
    return out


half = halftrace(seed)
assert half**2+half == seed
H = (half**2)**(2**24)
C = F(1)+H
t = dec(fixture["public_reciprocal"])
basis = [(dec((1 << bit) << 1)*dec(((1 << bit) << 1) ^
          (source["seed"] << 1)))**(2**24)
         for bit in range(9) if bit != 5]
image_to_code = {}
for code in range(256):
    product = sum((basis[i] for i in range(8) if code >> i & 1), F(0))
    assert product not in image_to_code
    image_to_code[product] = code


def roots_and_codes(w_int):
    w = dec(w_int)
    B = t*w
    A = 1+B**2
    D = t**2+w**2
    M = A*H+C*D
    a = A*D
    b = B*M
    q = M**2+C*H*B**2
    assert a and b
    step = b/a
    z = q*a/(b**2)
    half_z = halftrace(z)
    trace_z = trace(z)
    assert half_z**2+half_z == z+trace_z
    p0 = step*half_z
    p1 = p0+step
    roots = [candidate for candidate in (p0, p1)
             if a*candidate**2+b*candidate == q]
    codes = sorted(image_to_code[value] for value in roots if value in image_to_code)
    return roots, codes, image_to_code, (p0, p1)


branch_counts = Counter()
for entry in table:
    roots, codes, _, choices = roots_and_codes(entry["w"])
    assert len(roots) == 2 and codes == [entry["code"]]
    product = sum((basis[i] for i in range(8) if entry["code"] >> i & 1), F(0))
    branch_counts[str(choices.index(product))] += 1
assert dict(branch_counts) == result["root_choice_counts"]

for label in ("uniform", "reachable"):
    for entry in panel[label]:
        _, codes, _, _ = roots_and_codes(entry["w"])
        assert codes == entry["linear_image_codes"]

audit = {"status": "PASS_SAGE_GUARDED_ROOT_REPLAY",
         "candidate_id": None, "curve_id": result["curve_id"],
         "positive_rows_checked": len(table),
         "uniform_rows_checked": len(panel["uniform"]),
         "reachable_rows_checked": len(panel["reachable"]),
         "root_choice_counts": dict(branch_counts),
         "elapsed_seconds": time.monotonic()-started,
         "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         "audit_protocol_sha256": sha(HERE / "audit_protocol.json")}
(HERE / "audit_result.json").write_text(json.dumps(audit,sort_keys=True,indent=2)+"\n")
print(json.dumps(audit,sort_keys=True))
