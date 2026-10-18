"""Measure exact target-conditioned affine-span rejection by code prefix."""
import hashlib
import json
import random
import resource
import signal
import time
from collections import defaultdict
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
cfg = json.loads((HERE / 'protocol.json').read_text())
for name, digest in cfg['sources'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
assert not (HERE / 'result.json').exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('block gate cap')))
signal.alarm(cfg['wall_cap_seconds'])
started = time.monotonic()
R = PolynomialRing(GF(2), 'u')
u = R.gen()
K = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(K, [1, 0, 0, 0, 1])


def dec(n):
    return K(R([(n >> i) & 1 for i in range(41)]))


def enc(x):
    return sum(int(b) << i for i, b in enumerate(x.polynomial().list()))


def insert(v, pivots):
    for bit in range(40, -1, -1):
        if v & (1 << bit):
            if bit in pivots:
                v ^= pivots[bit]
            else:
                pivots[bit] = v
                return True
    return False


def basis(items):
    pivots = {}
    for v in items:
        insert(v, pivots)
    return pivots


def in_span(v, pivots):
    for bit in range(40, -1, -1):
        if v & (1 << bit):
            if bit not in pivots:
                return False
            v ^= pivots[bit]
    return True


states = [[] for _ in range(5)]
raw_point = None
with (ROOT / cfg['state_table']).open() as source:
    header = source.readline().split()
    assert header == ['W11FIVE', '5', '1124', '1']
    for line in source:
        row = line.split()
        if row[0] == 'T':
            assert raw_point is None and row[1] == '0'
            raw_point = E(dec(int(row[2])), dec(int(row[3])))
        elif row[0] == 'S':
            slot, sid, code = map(int, row[1:4])
            assert sid == len(states[slot]) and int(row[4]) == sid % 4
            states[slot].append((code, E(dec(int(row[9])), dec(int(row[10])))))
        elif row[0] == 'C':
            continue
        else:
            raise AssertionError(row[0])
assert raw_point is not None and all(len(s) == 1124 for s in states)
fixture = json.loads((ROOT / cfg['positive_fixture']).read_text())
positive = E(*(dec(n) for n in fixture['target_residual_point']))
assert states[3][278][1] + states[4][74][1] == positive

# Rotated product subspace for the second pair. The source code map is
# linear in its ten free bits only after taking the pair product.
seed = dec(112)
bits = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]
products = []
for code in range(1024):
    a = sum((dec(1 << (bit + 1)) for j, bit in enumerate(bits)
             if code >> j & 1), K.zero())
    products.append(enc((a * (a + seed)) ** (1 << 24)))
product_basis = basis(products)
assert len(product_basis) == 10
valid = set(json.loads((ROOT / cfg['source_count']).read_text())['valid_codes'])
assert len(valid) == 281
H0 = K.zero()
power = seed
for _ in range(21):
    H0 += power
    power = power**4
assert H0**2 + H0 == seed
H = H0**2
C = K.one() + H
Crot, Hrot = C ** (1 << 24), H ** (1 << 24)

rng = random.Random(cfg['sample_seed'])
queries = [('positive_residual', positive)]
for i in range(cfg['ordinary_residual_count']):
    while True:
        ids = [rng.randrange(1124) for _ in range(3)]
        codes = [states[j][sid][0] for j, sid in enumerate(ids)]
        if len(set(codes)) == 3:
            break
    T = raw_point - sum((states[j][sid][1] for j, sid in enumerate(ids)), E(0))
    queries.append((f'public_minus_three_{i}', T))

rows = []
for name, target in queries:
    qstart = time.monotonic()
    by_code = defaultdict(list)
    exact_product_hits = 0
    for sid, (code, point) in enumerate(states[3]):
        second = target - point
        if second == E(0) or not second[0]:
            continue
        x = second[0]
        p = enc(Crot * ~x + Hrot * x)
        by_code[code].append(p)
        exact_product_hits += in_span(p, product_basis)
    levels = []
    for free_bits in cfg['free_code_bits']:
        blocks = defaultdict(list)
        for code, ps in by_code.items():
            blocks[code >> free_bits].extend(ps)
        block_ids = {code >> free_bits for code in valid}
        rejected = 0
        full_rank = 0
        rank_hist = defaultdict(int)
        positive_retained = None
        for block_id in sorted(block_ids):
            ps = blocks[block_id]
            if not ps:
                rejected += 1
                continue
            # The affine hull is p0 + span(p_i + p0). Its intersection
            # with the 10-dimensional allowed product space is nonempty
            # exactly when p0 lies in span(U, p_i + p0).
            pivots = basis(products + [p ^ ps[0] for p in ps[1:]])
            rank_hist[len(pivots)] += 1
            full_rank += len(pivots) == 41
            reject = not in_span(ps[0], pivots)
            rejected += reject
            if name == 'positive_residual' and 253 >> free_bits == block_id:
                positive_retained = not reject
        assert positive_retained is None or positive_retained
        levels.append({'free_code_bits': free_bits, 'blocks': len(block_ids),
                       'rejected_blocks': rejected, 'full_rank_blocks': full_rank,
                       'rank_histogram': dict(sorted(rank_hist.items())),
                       'positive_block_retained': positive_retained})
    rows.append({'name': name, 'target_point': [enc(target[0]), enc(target[1])],
                 'exact_product_subspace_hits': exact_product_hits,
                 'levels': levels, 'query_seconds_including_all_levels': time.monotonic()-qstart})

signal.alarm(0)
result = {'status': 'COMPLETE_N41_W11_TARGET_BLOCK_SPAN_DIAGNOSTIC',
          'candidate_id': None, 'curve_id': cfg['curve_id'],
          'source_codes': len(valid), 'states_per_slot': len(states[3]),
          'product_subspace_rank': len(product_basis), 'rows': rows,
          'setup_and_query_seconds': time.monotonic()-started,
          'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'protocol_sha256': hashlib.sha256((HERE / 'protocol.json').read_bytes()).hexdigest()}
(HERE / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps({'status': result['status'], 'queries': len(rows),
                  'seconds': result['setup_and_query_seconds']}, sort_keys=True))
