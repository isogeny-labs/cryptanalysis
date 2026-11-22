"""Exhaustively compare a branch-free two-pair resultant with EC sums at N41."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

import psutil
from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'protocol.json').read_text())
assert protocol['status'] == 'FROZEN_BEFORE_N41_PAIR_RESULTANT_EXHAUSTIVE_TEST'
assert protocol['script_sha256'] == sha(Path(__file__))
for path, digest in protocol['sources'].items():
    assert sha(path) == digest, path
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('wall cap')))
signal.alarm(protocol['wall_cap_seconds'])
started = time.monotonic()
process = psutil.Process()
peak_rss = process.memory_info().rss


def check_rss():
    global peak_rss
    peak_rss = max(peak_rss, process.memory_info().rss)
    if peak_rss > protocol['rss_cap_bytes']:
        raise MemoryError('RSS cap')

R = PolynomialRing(GF(2), 'u')
u = R.gen()
K = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
Ecurve = EllipticCurve(K, [1, 0, 0, 0, 1])
dec = lambda word: K(R([(int(word) >> i) & 1 for i in range(41)]))
enc = lambda value: sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def halftrace(value):
    return sum((value**(4**j) for j in range(21)), K.zero())


seed = dec(112)
H = halftrace(seed)**2
C = K.one() + H
assert C and halftrace(seed)**2 + halftrace(seed) == seed
beta = H / C


def f3_reciprocal(z, w, t):
    product = z * w * t
    return product**2 + product + (z + w + t)**2


def branch_free_resultant(alpha, gamma, beta, t):
    """Norm of the doubly reduced reciprocal S3; zero is necessary for a witness."""
    t2 = t**2
    k = K.one() + t2 * beta
    A = t2 * alpha * gamma + t
    B = alpha * k
    D = gamma * k
    E = t2 * (beta**2 + K.one())
    U = B**2 + gamma * B * A + beta * A**2
    V = gamma * (B * D + E * A)
    W = E**2 + gamma * E * D + beta * D**2
    L1 = U * alpha + V
    L0 = U * beta + W
    return L0**2 + alpha * L0 * L1 + beta * L1**2


input_rows = Path(protocol['join_input']).read_text().splitlines()
assert input_rows[0] == 'W11FIVE 5 1124 1'
target_row = next(row.split() for row in input_rows if row.startswith('T '))
public = Ecurve(dec(target_row[2]), dec(target_row[3]))
assert [enc(public[0]), enc(public[1])] == protocol['public_raw_point']
by_code = {}
by_sid = {}
for row in input_rows:
    a = row.split()
    if not a or a[0] != 'S' or a[1] != '0':
        continue
    sid, code, branch = map(int, a[2:5])
    mask_a, mask_b = map(int, a[5:7])
    point = Ecurve(dec(a[-2]), dec(a[-1]))
    entry = by_code.setdefault(code, {'masks': [mask_a, mask_b],
                                      'columns': list(map(int, a[7:9])),
                                      'states': [None] * 4})
    assert entry['masks'] == [mask_a, mask_b]
    assert entry['columns'] == list(map(int, a[7:9]))
    entry['states'][branch] = point
    by_sid[sid] = point
assert len(by_code) == 281 and len(by_sid) == 1124
alphas = {}
for code, entry in by_code.items():
    assert all(point is not None and point != Ecurve(0) and point[0]
               for point in entry['states'])
    p = dec(entry['masks'][0]) * dec(entry['masks'][1])
    alpha = p / C
    alphas[code] = alpha
    roots = {1 / point[0] for point in entry['states']}
    assert len(roots) == 2
    assert all(z**2 + alpha * z + beta == 0 for z in roots)

audited = json.loads(Path(protocol['n41_relation']).read_text())
assert audited['status'] == 'PASS_ALL_ALIGNED_N41_PUBLIC_RELATION'
ids = audited['state_ids']
residual = public - sum((by_sid[sid] for sid in ids[:3]), Ecurve(0))
assert residual != Ecurve(0) and residual[0]
t = 1 / residual[0]
positive = tuple(sorted(audited['codes'][3:]))
assert len(positive) == 2 and positive[0] != positive[1]
assert by_sid[ids[3]] + by_sid[ids[4]] == residual
assert f3_reciprocal(1 / by_sid[ids[3]][0], 1 / by_sid[ids[4]][0], t) == 0
assert branch_free_resultant(alphas[positive[0]], alphas[positive[1]], beta, t) == 0
prepared = time.monotonic()

codes = sorted(by_code)
pairs = [(a, b) for i, a in enumerate(codes) for b in codes[i+1:]
         if len(set(by_code[a]['columns'] + by_code[b]['columns'])) == 4]
assert positive in pairs
assert len(pairs) == protocol['expected_code_pairs']
filter_started = time.monotonic()
filter_hits = []
for index, pair in enumerate(pairs):
    if index % 1024 == 0:
        check_rss()
    if branch_free_resultant(alphas[pair[0]], alphas[pair[1]], beta, t) == 0:
        filter_hits.append(pair)
filter_seconds = time.monotonic() - filter_started
partial = {'status': 'FILTER_COMPLETE_BASELINE_PENDING',
           'filter_hits': filter_hits, 'filter_seconds': filter_seconds,
           'pair_count': len(pairs), 'protocol_sha256': sha(HERE / 'protocol.json')}
(HERE / 'partial.json').write_text(json.dumps(partial, sort_keys=True, indent=2) + '\n')

baseline_started = time.monotonic()
baseline_hits = []
exact_group_hits = []
for index, (a, b) in enumerate(pairs):
    if index % 1024 == 0:
        check_rss()
    coordinate_match = False
    group_match = False
    for pa in by_code[a]['states']:
        for pb in by_code[b]['states']:
            summed = pa + pb
            if summed != Ecurve(0) and summed[0] == residual[0]:
                coordinate_match = True
                if summed == residual:
                    group_match = True
    if coordinate_match:
        baseline_hits.append((a, b))
    if group_match:
        exact_group_hits.append((a, b))
baseline_seconds = time.monotonic() - baseline_started
assert set(filter_hits) == set(baseline_hits)
assert positive in exact_group_hits
finished = time.monotonic()
check_rss()
signal.alarm(0)
result = {'status': 'PASS_EXHAUSTIVE_N41_PAIR_RESULTANT_EQUIVALENCE',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'public_raw_point': protocol['public_raw_point'],
          'residual_point': [enc(residual[0]), enc(residual[1])],
          'positive_control_codes': positive,
          'source_codes': len(codes), 'code_pairs': len(pairs),
          'filter_hits': filter_hits, 'baseline_hits': baseline_hits,
          'exact_group_hits': exact_group_hits,
          'filter_seconds': filter_seconds,
          'baseline_seconds': baseline_seconds,
          'setup_and_residual_seconds': prepared - started,
          'total_wall_seconds': finished - started,
          'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'sampled_peak_self_rss_bytes': peak_rss,
          'protocol_sha256': sha(HERE / 'protocol.json')}
(HERE / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
