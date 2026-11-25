"""Replay the sibling contingency tables from the archived root bytes."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from subprocess import check_output

here = Path(__file__).resolve().parent
meta = json.loads((here.parents[1] / "m31-batch-smooth/basis-identity.json").read_bytes())
roots_bytes = check_output(["git", "show", meta["roots_commit"] + ":" + meta["roots_path"]], cwd=here)
assert sha256(roots_bytes).hexdigest() == meta["roots_file_sha256"]
roots = json.loads(roots_bytes)
p = meta["field_prime"]
assert len(set(roots)) == len(roots) == meta["root_count"]
smooth, accepted = set(), []
for x in roots:
    v = min(x, p - x)
    assert v > 0
    for divisor in range(2, meta["signed_smooth_bound"] + 1):
        while v % divisor == 0:
            v //= divisor
    if v == 1:
        smooth.add(x)
        rhs = (x**3 + meta["curve_a"]*x + meta["curve_b"]) % p
        y = pow(rhs, (p+1)//4, p)
        if y*y % p == rhs:
            accepted.append(x)
assert accepted == list(map(int, (here.parent / "coordinates.txt").read_text().splitlines()))
half = len(roots) // 2
pairs = list(zip(roots[:half], roots[half:], strict=True))
assert all(a*b % p == 1 for a,b in pairs)
for label, members in [("smooth", smooth), ("accepted", set(accepted))]:
    counts = Counter((a in members, b in members) for a,b in pairs)
    print(label, [counts[key] for key in [(False,False),(True,False),(False,True),(True,True)]])
