"""Reconstruct the archived public Torus7 columns and print x, one per line."""
import json
import struct
from pathlib import Path

from blake3 import blake3

p = 2**31 - 1

def iterate(x, count):
    for _ in range(count):
        x = (x*x - 2) % p
    return x

trace = next(x for x in range(4096) if iterate(x, 30) == p - 2)
roots = {iterate(trace, 7)}
for _ in range(7):
    children = set()
    for v in roots:
        x = pow((v + 2) % p, (p+1)//4, p)
        assert iterate(x, 1) == v
        children.update([x, -x % p])
    roots = children
assert len(roots) == 128
points = []
for x in sorted(roots):
    rhs = (x**3 + 2*x + 14) % p
    y = pow(rhs, (p+1)//4, p)
    if y*y % p == rhs:
        points.append((x, min(y, -y % p)))
assert len(points) == 71
digest = blake3(b"auxiliary-ic-signed-columns/v1\0")
digest.update(struct.pack("<5Q", p, 2, 14, 2147505293, len(points)))
for point in points:
    digest.update(struct.pack("<2Q", *point))
archive = Path(__file__).resolve().parent.parent / "m34-and-3arm-20261119/end_to_end_solves_summary.json"
rows = json.loads(archive.read_text())["e1_m2_5target_solves"]
assert len(rows) == 5
for row in rows:
    for arm in ("arm_E_torus7_direct", "arm_E_torus7_circuit"):
        assert digest.hexdigest() == row["arms"][arm]["columns_blake3"]
print(*(x for x, _ in points), sep="\n")
