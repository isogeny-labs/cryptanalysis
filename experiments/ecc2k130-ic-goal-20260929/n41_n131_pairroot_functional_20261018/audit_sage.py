"""Check two-bit functional roots against frozen N41 and N131 source records."""
import hashlib
import json
import resource
import signal
import sys
import time
from collections import defaultdict
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
MODE = sys.argv[1]
assert MODE in ('n41', 'n131')
protocol_path = HERE / f'{MODE}_protocol.json'
protocol = json.loads(protocol_path.read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, digest in protocol['sources'].items():
    assert sha(path) == digest, path
assert not (HERE / f'{MODE}_result.json').exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('audit wall cap')))
signal.alarm(protocol['wall_cap_seconds'])
started = time.monotonic()
n = 41 if MODE == 'n41' else 131
K = PolynomialRing(GF(2), 'x')
x = K.gen()
modulus = x**41+x**3+1 if n == 41 else x**131+x**13+x**2+x+1
F = GF(2**n, name='x', modulus=modulus)


def dec(word):
    return F(K([(int(word) >> i) & 1 for i in range(n)]))


def enc(value):
    return sum(int(c) << i for i, c in enumerate(value.polynomial().list()))


def halftrace(value):
    initial = value
    out = F.zero()
    for _ in range((n+1)//2):
        out += value
        value = value**4
    assert out**2+out == initial+initial.trace()
    return out


def two_roots(A, B, D):
    assert A and B
    rhs = A*D/B**2
    if rhs.trace():
        return [], 'trace_miss'
    h = halftrace(rhs)
    roots = [(B/A)*h, (B/A)*(h+1)]
    assert roots[0] != roots[1]
    assert all(A*z*z+B*z+D == 0 for z in roots)
    return roots, 'two_roots'


def functional_roots(p, C, H, t):
    if not p:
        return None, 'zero_source_product'
    pair, case = two_roots(C, p, H)
    if case != 'two_roots':
        return None, 'source_'+case
    rows = []
    for u in pair:
        A, B, D = 1+(t*u)**2, t*u, t**2+u**2
        if not A or not B:
            return None, 'degenerate_target_quadratic'
        roots, case = two_roots(A, B, D)
        if case != 'two_roots':
            return None, 'target_'+case
        rows.append((u, roots))
    return rows, 'four_roots'


if MODE == 'n41':
    source = json.loads(Path(protocol['states']).read_text())
    fixture = json.loads(Path(protocol['fixture']).read_text())
    table = json.loads(Path(protocol['w_table']).read_text())
    assert source['curve_id'] == protocol['curve_id']
    bits = [i for i in range(9) if i != 5]
    seed = dec(source['seed'] << 1)
    h = halftrace(seed)
    H = (h**2)**(1 << 24)
    C = 1+H
    basis = [(dec((1 << bit) << 1)*dec((((1 << bit) ^ source['seed']) << 1)))**(1 << 24)
             for bit in bits]
    t = dec(fixture['public_reciprocal'])
    expected = defaultdict(set)
    for row in table:
        expected[row['code']].add(row['w'])
    assert len(expected) == 71
    records = [(code, sum((basis[j] for j in range(8) if code >> j & 1), F.zero()))
               for code in sorted(expected)]
    queries = [('frozen_public', t)]
else:
    sample = json.loads(Path(protocol['sample']).read_text())
    previous = json.loads(Path(protocol['previous']).read_text())
    assert len(sample['codes']) == len(sample['roots']) == 512
    seed_word = 898618
    seed = dec(seed_word << 1)
    h = halftrace(seed)
    H, C = h**2, 1+h**2
    bits = [i for i in range(29) if i != seed_word.bit_length()-1]
    records = []
    for code, root_word in zip(sample['codes'], sample['roots']):
        mask = sum(1 << bit for j, bit in enumerate(bits) if code >> j & 1)
        a = dec(mask << 1)
        p = a*(a+seed)
        assert C*dec(root_word)**2+p*dec(root_word)+H == 0
        records.append((int(code), p))
    control = json.loads(Path(protocol['control']).read_text())
    for j in (0, 1):
        p = dec(control['pairs'][j]['source_product'])
        records.append((f'control_{j}', p))
    queries = [(row['kind'], dec(row['target_reciprocal'])) for row in previous['queries']]

assert C and H
results = []
for query_index, (kind, t) in enumerate(queries):
    digest = hashlib.sha256()
    cases = defaultdict(int)
    sources = []
    for code, p in records:
        rows, case = functional_roots(p, C, H, t)
        cases[case] += 1
        assert case == 'four_roots', (kind, code, case)
        roots = sorted(enc(w) for _u, pair in rows for w in pair)
        assert len(set(roots)) == 4
        if MODE == 'n41':
            assert set(roots) == expected[code], code
        elif isinstance(code, int):
            assert dec(sample['roots'][len(sources)]) in [u for u, _ in rows]
        digest.update(json.dumps([code, [(enc(u), sorted(enc(w) for w in pair))
                                        for u, pair in rows]], sort_keys=True, separators=(',', ':')).encode()+b'\n')
        sources.append({'code': code, 'p': enc(p), 'pair_roots': [enc(u) for u, _ in rows],
                        'target_roots': roots})
    results.append({'kind': kind, 'source_count': len(sources), 'case_counts': dict(cases),
                    'branch_records_sha256': digest.hexdigest(), 'sources': sources})

if MODE == 'n131':
    # Independently recover the sampled-pair lookup and replay the prior
    # constructed hit and frozen public fixed-suffix miss from functional roots.
    for result, reference in zip(results, previous['queries']):
        lookup = {row['p']: i for i, row in enumerate(result['sources'])}
        hits = set()
        for i, row in enumerate(result['sources']):
            for w in row['target_roots']:
                z = dec(w)
                if not z:
                    continue
                q = enc((C*z*z+H)/z)
                j = lookup.get(q)
                if j is not None and i < j:
                    assert w in result['sources'][j]['pair_roots']
                    hits.add((i, j))
        assert sorted(map(list, hits)) == reference['sample_source_pair_hits']
        result['sample_source_pair_hits'] = sorted(map(list, hits))

signal.alarm(0)
out = {'status': 'PASS_FUNCTIONAL_ROOT_AUDIT', 'candidate_id': None,
       'curve_id': protocol['curve_id'], 'mode': MODE, 'field_degree': n,
       'source_count': len(records), 'queries': results,
       'wall_seconds': time.monotonic()-started,
       'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       'protocol_sha256': sha(protocol_path)}
(HERE / f'{MODE}_result.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')
print(json.dumps({'status': out['status'], 'mode': MODE,
                  'source_count': len(records), 'case_counts': [r['case_counts'] for r in results],
                  'sample_source_pair_hits': [r.get('sample_source_pair_hits') for r in results],
                  'wall_seconds': out['wall_seconds']}))
