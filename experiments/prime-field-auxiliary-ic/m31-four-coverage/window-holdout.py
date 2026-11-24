"""Run on two sample.gp JSONL outputs, training then holdout.
For the holdout replace setrand(291160) by setrand(291161) and count<256
by count<4096 in the frozen m31-projection-controls/sample.gp generator.
"""
import collections
import hashlib
import json
from pathlib import Path
import sys

prime = 2**31-1
family = (0, 1, 3, 4, 9, 12, 15, 17, 19, 21)
def load(path):
    for line in Path(path).read_text().splitlines():
        rows = json.loads(line)
        assert len(rows) == len(dict(rows)) == 32
        assert all(0 <= x < prime and bit == (pow((x**3+2*x+14) % prime, (prime-1)//2, prime) != prime-1) for x, bit in rows)
        keys = tuple(sorted(x for x, bit in rows if bit))
        assert len(keys) == 17
        yield keys

def fits(keys, width, shift):
    return len({(x >> shift) % (1 << width) for x in keys}) == 17

train = set(load(sys.argv[1]))
assert len(train) == 256
seen = set()
counts = collections.Counter()
widths = collections.Counter()
first = None
for row, keys in enumerate(load(sys.argv[2]), 1):
    if keys in train or keys in seen:
        counts['excluded'] += 1
        continue
    seen.add(keys)
    seven = [s for s in range(25) if fits(keys,7,s)]
    counts['frozen six'] += fits(keys,6,10)
    counts['frozen family'] += any(s in family for s in seven)
    counts['any seven'] += bool(seven)
    w = next(w for w in range(5,32) if any(fits(keys,w,s) for s in range(32-w)))
    widths[w] += 1
    if not seven and first is None:
        first = {'row':row, 'keys':keys, 'seven_bit_occupied_slots':[len({(x>>s)%128 for x in keys}) for s in range(25)]}
print(json.dumps({'seed':291161,'raw_rows':row,'distinct_holdout':len(seen),'counts':dict(counts),'minimum_width':dict(widths),'first_failure':first,'input_sha256':hashlib.sha256(Path(sys.argv[2]).read_bytes()).hexdigest()},indent=2))
