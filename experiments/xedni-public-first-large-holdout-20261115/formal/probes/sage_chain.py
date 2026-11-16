"""Emit the binary doubling chain for the first frozen curve row."""
import json
from sage.all import EllipticCurve, GF

p, q = 313, 331
curve = EllipticCurve(GF(p), [-1, -2])
generator = curve(2, 2)
rows = []
for i in range(9):
    point = (2**i) * generator
    rows.append({
        "multiple": 2**i,
        "point": None if point.is_zero() else [int(point[0]), int(point[1])],
    })
assert q * generator == curve(0)
print(json.dumps({
    "field_prime": p,
    "subgroup_order": q,
    "doubling_chain": rows,
    "q_multiple_is_identity": True,
}, sort_keys=True))
