"""Compare branch-free norm with four reciprocal S3 root checks per code pair."""
import gc
import hashlib
import json
import statistics
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'field_compare_protocol.json').read_text())
assert protocol['status'] == 'FROZEN_BEFORE_N41_FIELD_BASELINE_COMPARISON'
assert protocol['script_sha256'] == sha(Path(__file__))
for path, digest in protocol['sources'].items():
    assert sha(path) == digest, path
previous = json.loads((HERE / 'result.json').read_text())
assert previous['status'] == 'PASS_EXHAUSTIVE_N41_PAIR_RESULTANT_EQUIVALENCE'

P = PolynomialRing(GF(2), 'u')
u = P.gen()
K = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
Ecurve = EllipticCurve(K, [1, 0, 0, 0, 1])
dec = lambda word: K(P([(int(word) >> i) & 1 for i in range(41)]))
halftrace = lambda value: sum((value**(4**j) for j in range(21)), K.zero())
H = halftrace(dec(112))**2
C = K.one() + H
beta = H / C
residual = Ecurve(dec(previous['residual_point'][0]),
                  dec(previous['residual_point'][1]))
t = 1 / residual[0]
t2 = t**2
k = K.one() + t2 * beta
constant = t2 * (beta**2 + K.one())


def norm_filter(alpha, gamma):
    A = t2 * alpha * gamma + t
    B = alpha * k
    D = gamma * k
    E = constant
    U = B**2 + gamma * B * A + beta * A**2
    V = gamma * (B * D + E * A)
    W = E**2 + gamma * E * D + beta * D**2
    L1 = U * alpha + V
    L0 = U * beta + W
    return L0**2 + alpha * L0 * L1 + beta * L1**2 == 0


def four_roots(left, right):
    for z in left:
        for w in right:
            product = z * w * t
            if product**2 + product + (z + w + t)**2 == 0:
                return True
    return False


by_code = {}
for line in Path(protocol['join_input']).read_text().splitlines():
    row = line.split()
    if not row or row[0] != 'S' or row[1] != '0':
        continue
    code = int(row[3])
    entry = by_code.setdefault(code, {'masks': list(map(int, row[5:7])),
                                      'columns': list(map(int, row[7:9])),
                                      'roots': set()})
    assert entry['masks'] == list(map(int, row[5:7]))
    point = Ecurve(dec(row[-2]), dec(row[-1]))
    entry['roots'].add(1 / point[0])
assert len(by_code) == 281 and all(len(row['roots']) == 2 for row in by_code.values())
codes = sorted(by_code)
pairs = [(a, b) for i, a in enumerate(codes) for b in codes[i+1:]
         if len(set(by_code[a]['columns'] + by_code[b]['columns'])) == 4]
assert len(pairs) == previous['code_pairs'] == 39335
alpha = {code: dec(row['masks'][0]) * dec(row['masks'][1]) / C
         for code, row in by_code.items()}
roots = {code: tuple(row['roots']) for code, row in by_code.items()}
for code in codes:
    assert all(z**2 + alpha[code] * z + beta == 0 for z in roots[code])

rows = []
gc.collect()
gc.disable()
try:
    for method in protocol['order']:
        start = time.perf_counter()
        if method == 'resultant':
            hits = [(a, b) for a, b in pairs if norm_filter(alpha[a], alpha[b])]
        elif method == 'four_roots':
            hits = [(a, b) for a, b in pairs if four_roots(roots[a], roots[b])]
        else:
            raise ValueError(method)
        elapsed = time.perf_counter() - start
        assert hits == [tuple(pair) for pair in previous['filter_hits']]
        rows.append({'method': method, 'wall_seconds': elapsed,
                     'accepted_code_pairs': len(hits)})
finally:
    gc.enable()

times = {method: [row['wall_seconds'] for row in rows if row['method'] == method]
         for method in ('resultant', 'four_roots')}
result = {'status': 'PASS_EXHAUSTIVE_N41_FIELD_BASELINE_COMPARISON',
          'candidate_id': None, 'code_pairs': len(pairs),
          'accepted_pairs': previous['filter_hits'],
          'order': protocol['order'], 'runs': rows,
          'median_seconds': {method: statistics.median(values)
                             for method, values in times.items()},
          'protocol_sha256': sha(HERE / 'field_compare_protocol.json')}
(HERE / 'field_compare_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
