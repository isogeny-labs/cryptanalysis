"""Check fixed, incomplete capped lists against the full bound-83 catalog."""
import json
import runpy
from collections import defaultdict
from pathlib import Path

from bound import P, PRIMES

catalog_dir = Path(__file__).resolve().parents[1] / 'product-support'
replay = runpy.run_path(str(catalog_dir / 'census.py'))['divisor_pairs']
catalog = {int(n) for n in json.loads((catalog_dir / 'report.json').read_text())['83']['products']}


def smooth(primes):
    values = [1]
    for q in primes:
        extra = []
        for x in values:
            x *= q
            while x < P:
                extra.append(x)
                x *= q
        values.extend(extra)
    return values


found = set()
pairs = set()
entries = 0
print('bit,left,right,raw_products_this_split,valid_products_union,orbit_pairs_union,entries_cumulative')
for bit in range(5):
    left = smooth(q for i,q in enumerate(PRIMES) if i & (1 << bit))
    right = smooth(q for i,q in enumerate(PRIMES) if not i & (1 << bit))
    buckets = defaultdict(list)
    for x in left:
        buckets[pow(x,31,P)].append(x)
    candidates = {x*y for y in right for x in buckets.get(pow(y,-31,P), ())}
    for n in candidates - found:
        supported = replay(n,83)
        if supported:
            assert n in catalog
            found.add(n)
            pairs.update(supported)
    entries += len(left) + len(right)
    print(bit,len(left),len(right),len(candidates),len(found),len(pairs),entries,sep=',')
