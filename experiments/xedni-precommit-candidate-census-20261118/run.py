"""Exact rational group-law census over the frozen precommit candidate ledger."""
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
import gzip
import hashlib
import json
import time

HERE = Path(__file__).resolve().parent
PROTOCOL = json.loads((HERE / 'protocol.json').read_text())
SOURCE = (HERE / PROTOCOL['source_dir']).resolve()
manifest_bytes = (SOURCE / 'run-result.json').read_bytes()
assert hashlib.sha256(manifest_bytes).hexdigest() == PROTOCOL['source_result_sha256']
MANIFEST = json.loads(manifest_bytes)


def read_ledger(info):
    blob = (SOURCE / info['path']).read_bytes()
    assert len(blob) == info['gzip_bytes']
    assert hashlib.sha256(blob).hexdigest() == info['gzip_sha256']
    raw = gzip.decompress(blob)
    assert hashlib.sha256(raw).hexdigest() == info['raw_sha256']
    rows = [json.loads(line) for line in raw.splitlines()]
    assert len(rows) == info['rows']
    return rows


def add(p, q, a):
    if p is None:
        return q
    if q is None:
        return p
    x, y = p
    u, v = q
    if x == u and y + v == 0:
        return None
    slope = (3 * x * x + a) / (2 * y) if p == q else (v - y) / (u - x)
    X = slope * slope - x - u
    return (X, slope * (x - X) - y)


def mul(n, p, a):
    if n < 0:
        p = (p[0], -p[1])
        n = -n
    acc = None
    while n:
        if n & 1:
            acc = add(acc, p, a)
        p = add(p, p, a)
        n >>= 1
    return acc


def lift(query, row):
    prime = query['p']
    def center(x):
        return x - prime if x > prime // 2 else x
    x1, y1 = map(center, query['U'])
    x2, y2 = map(center, query['V'])
    shift = row['shift']
    if shift is None:
        assert query['branch'] == 'equal_x_opposite'
        assert query['U'][0] == query['V'][0]
        assert (query['U'][1] + query['V'][1]) % prime == 0
        x2, y2 = x1, -y1
        a = Fraction(-1)
        b = Fraction(y1 * y1 - x1 * x1 * x1 + x1)
    else:
        assert query['branch'] == 'distinct_x' and len(shift) == 4
        x1 += prime * shift[0]
        y1 += prime * shift[1]
        x2 += prime * shift[2]
        y2 += prime * shift[3]
        f1, f2 = y1*y1 - x1*x1*x1, y2*y2 - x2*x2*x2
        a = Fraction(f1 - f2, x1 - x2)
        b = Fraction(f1) - a*x1
    assert (str(a), str(b)) == (row['A'], row['B'])
    assert 4*a**3 + 27*b**2 != 0
    p1, p2 = (Fraction(x1), Fraction(y1)), (Fraction(x2), Fraction(y2))
    assert p1[1]**2 == p1[0]**3 + a*p1[0] + b
    assert p2[1]**2 == p2[0]**3 + a*p2[0] + b
    assert (x1 % prime, y1 % prime) == tuple(query['U'])
    assert (x2 % prime, y2 % prime) == tuple(query['V'])
    return a, p1, p2


def main():
    started = time.monotonic()
    queries = read_ledger(MANIFEST['queries'])
    vectors = read_ledger(MANIFEST['vectors'])
    candidates = defaultdict(list)
    for info in MANIFEST['candidate_parts']:
        for row in read_ledger(info):
            candidates[row['event_index']].append(row)
    assert len(queries) == 512 and len(vectors) == 6656
    hits = [v for v in vectors if v['public_relation']]
    assert len(hits) == 22
    outcomes = []
    for hit in hits:
        event = hit['event_index']
        query = queries[event]
        rows = candidates[event]
        assert query['event_index'] == event
        assert len(rows) == query['candidate_count']
        assert len({str(r['shift']) for r in rows}) == len(rows)
        # Public relation is independently checked from the frozen scalar fixtures.
        assert (hit['a']*(query['w']-query['t1']) + hit['b']*(query['w']-query['t2'])) % query['q'] == 0
        for row in rows:
            outcome = {'event_index': event, 'p': query['p'], 'vector_index': hit['vector_index'],
                       'a': hit['a'], 'b': hit['b'], 'shift': row['shift'],
                       'score_bits': row['score_bits']}
            try:
                a, p1, p2 = lift(query, row)
                residual = add(mul(hit['a'], p1, a), mul(hit['b'], p2, a), a)
                outcome['status'] = 'relation' if residual is None else 'nonidentity'
            except (AssertionError, ArithmeticError, ValueError, TypeError, ZeroDivisionError) as exc:
                outcome['status'] = 'failure'
                outcome['error'] = type(exc).__name__ + ': ' + str(exc)
            outcomes.append(outcome)
    counts = {s: sum(x['status'] == s for x in outcomes) for s in ('relation','nonidentity','failure')}
    events_with_relation = sorted({x['event_index'] for x in outcomes if x['status'] == 'relation'})
    result = {'schema': 'xedni-precommit-candidate-census-result-v1',
              'protocol_sha256': hashlib.sha256((HERE/'protocol.json').read_bytes()).hexdigest(),
              'source_result_sha256': PROTOCOL['source_result_sha256'],
              'public_hit_rows': len(hits), 'candidate_vector_tests': len(outcomes),
              'status_counts': counts, 'hit_events_with_relation': events_with_relation,
              'public_hit_rows_with_any_rational_relation': sum(any(x['status']=='relation' for x in outcomes if x['event_index']==h['event_index'] and x['vector_index']==h['vector_index']) for h in hits),
              'elapsed_wall_seconds': round(time.monotonic() - started, 3),
              'outcomes_sha256': hashlib.sha256((''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in outcomes)).encode()).hexdigest()}
    (HERE/'outcomes.jsonl').write_text(''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in outcomes))
    (HERE/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__ == '__main__':
    main()
