"""Exact overlap histogram over nonzero common field rescalings."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from census import EXPECTED_PAIRS, P, PERIOD, representatives

revision = "efb9330c1ee7e30743b7674f686cccb49f1cb25e"
path = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0/public.json"
digest = "a5fd508b6deacd2e2036a790946d7700929a822caf92e1fed699e6a7657fb9ca"
data = subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=root)
if hashlib.sha256(data).hexdigest() != digest:
    raise ValueError("archive identity mismatch")
fixture = json.loads(data)
groups = representatives()
keys = {k for k in groups if k != (inverse := pow(k, -1, P)) and inverse in groups}
assert len(keys) == 2 * EXPECTED_PAIRS
assert pow(2, PERIOD, P) == 1 and all(pow(2, i, P) != 1 for i in range(1, PERIOD))
# Independent membership lookup using the actual 31 cyclic rotations.
support = {groups[k] * (1 << i) % P for k in keys for i in range(PERIOD)}
assert len(support) == len(keys) * PERIOD


def summarize(xs):
    assert len(xs) == len(set(xs)) and all(0 < x < P for x in xs)
    counts = Counter()
    witnesses = {}
    for x in xs:
        inv = pow(x, -1, P)
        inv_key = pow(inv, PERIOD, P)
        for key in keys:
            scale_key = key * inv_key % P
            counts[scale_key] += 1
            if scale_key not in witnesses:
                witnesses[scale_key] = groups[key] * inv % P
    max_count = max(counts.values())
    winner = min(k for k, v in counts.items() if v == max_count)
    scale = witnesses[winner]
    hits = [x for x in xs if x * scale % P in support]
    identity = [x for x in xs if x in support]
    assert len(hits) == max_count and len(identity) == counts[1]
    hist = Counter(counts.values())
    hist[0] = (P-1)//PERIOD - len(counts)
    assert sum(n*h for h,n in hist.items()) == len(xs)*len(keys)
    return dict(coordinates=len(xs), unchanged_hits=identity, maximum=max_count,
                maximizing_scale=scale, scaled_hits=hits,
                field_scales_by_hits={h: PERIOD*n for h,n in sorted(hist.items())})


summary = dict(archive=revision, fixture_sha256=digest, orbit_keys=len(keys),
               coordinate_support=len(support), roots=summarize(fixture['structured_roots']),
               columns=summarize([x for x,y in fixture['factor_base']]),
               random_columns=summarize([x for x,y in fixture['random_factor_base']]))
print(json.dumps(summary, indent=2))
