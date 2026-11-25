"""Audit reciprocal-key compatibility in each two-isogeny fiber."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

here = Path(__file__).resolve().parent
receipt = json.loads((here.parent / "result.json").read_text())
path = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0/public.json"
raw = subprocess.check_output(["git", "show", f"{receipt['archive']}:{path}"], cwd=here)
assert hashlib.sha256(raw).hexdigest() == receipt["fixture_sha256"]
fixture = json.loads(raw)
p = fixture["auxiliary"]["p"]
seeds = list(map(int, subprocess.check_output([str(Path(sys.argv[1]).resolve())]).splitlines()))
coordinates = {seed * (1 << i) % p for x in seeds for seed in (x, pow(x, -1, p)) for i in range(31)}
keys = {pow(x, 31, p) for x in coordinates}
assert len(coordinates) == 204724 and len(keys) == 6604
rotations = [pow(2, i, p) for i in range(31)]
xs = set(fixture["structured_roots"])
levels = []
for m in fixture["auxiliary"]["maps"]:
    r, a, b = [m[k] for k in ("r", "A", "B")]
    us = {(x-r) % p for x in xs}
    assert 0 not in us
    siblings = []
    parents = set()
    for u in sorted(us):
        v = b * pow(u, -1, p) % p
        assert v in us and u != v
        if u < v:
            siblings.append((u, v))
            parents.add((u+a+v) % p)
    assert len(us) == 2*len(siblings) == 2*len(parents)
    # Count common scale keys capturing one or more complete sibling pairs.
    counts = Counter()
    for u,v in siblings:
        ku, kv = pow(u, 31, p), pow(v, 31, p)
        inv = pow(ku, -1, p)
        for target in keys:
            scale_key = target*inv % p
            if scale_key*kv % p in keys:
                counts[scale_key] += 1
    histogram = Counter(counts.values())
    histogram[0] = (p-1)//31 - len(counts)
    # A compatible scale sends the two keys to mutual inverses. Enumerate
    # every solution of s^2 = 2^i/B and check the actual field coordinates.
    compatible = set()
    for rot in rotations:
        square = rot * pow(b, -1, p) % p
        s = pow(square, (p+1)//4, p)
        if s*s % p == square:
            compatible.update({s, p-s})
    hit_counts = Counter()
    for s in compatible:
        hits = sum(s*u % p in coordinates and s*v % p in coordinates for u,v in siblings)
        assert hits == counts[pow(s,31,p)]
        hit_counts[hits] += 1
    levels.append(dict(r=r,A=a,B=b,sibling_pairs=len(siblings),
        scales_by_complete_pairs={n:31*k for n,k in sorted(histogram.items())},
        compatible_scales=len(compatible),compatible_by_complete_pairs=dict(sorted(hit_counts.items()))))
    xs = parents
assert xs == {fixture["auxiliary"]["terminal_c"]}
print(json.dumps(dict(archive=receipt["archive"],levels=levels),indent=2))
