"""Target-conditioned quartic block polynomials and subspace-root GCDs."""
import hashlib
import json
import resource
import signal
import sys
import time
from collections import defaultdict
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol_name = sys.argv[1]
cfg = json.loads((HERE / protocol_name).read_text())
for name, digest in cfg['sources'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
out = HERE / cfg['result_file']
assert not out.exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('quartic block cap')))
signal.alarm(cfg['wall_cap_seconds'])
started = time.monotonic()
P = PolynomialRing(GF(2), 'u')
u = P.gen()
K = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(K, [1, 0, 0, 0, 1])
F = PolynomialRing(K, 'z')
z = F.gen()


def dec(n):
    return K(P([(n >> i) & 1 for i in range(41)]))


def enc(x):
    return sum(int(v) << i for i, v in enumerate(x.polynomial().list()))


seed = dec(112)
H0 = K.zero()
power = seed
for _ in range(21):
    H0 += power
    power = power**4
assert H0**2 + H0 == seed
H = H0**2
C = K.one() + H
Hr = H ** (1 << 24)
Cr = C ** (1 << 24)
bits = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]


def product(code):
    a = sum((dec(1 << (bit + 1)) for j, bit in enumerate(bits)
             if code >> j & 1), K.zero())
    return (a * (a + seed)) ** (1 << 24)


source_products = [product(code) for code in range(1024)]
basis = [source_products[1 << j] for j in range(10)]
assert len({enc(p) for p in source_products}) == 1024
assert all(source_products[code] == sum((basis[j] for j in range(10)
                                         if code >> j & 1), K.zero())
           for code in range(1024))

# The monic vanishing polynomial of the ten-dimensional product space.
# Its Frobenius-linear form makes degree 1024 inexpensive to construct.
L = z
for b in basis:
    L = L**2 + L(b) * L
assert L.degree() == 1024 and all(L(p) == 0 for p in source_products)
assert len(L.dict()) <= 11

source = json.loads((ROOT / cfg['source_count']).read_text())
valid = sorted(source['valid_codes'])
assert len(valid) == 281
by_code = defaultdict(list)
with (ROOT / cfg['state_table']).open() as table:
    assert table.readline().split() == ['W11FIVE', '5', '1124', '1']
    for line in table:
        row = line.split()
        if row[0] == 'S' and row[1] == '3':
            by_code[int(row[3])].append((dec(int(row[9])), dec(int(row[10]))))
assert sorted(by_code) == valid and all(len(by_code[code]) == 4 for code in valid)
pair_reciprocals = {}
for code in valid:
    roots = {~x for x, _ in by_code[code]}
    assert len(roots) == 2
    pair_reciprocals[code] = tuple(sorted(roots, key=enc))
blocks = defaultdict(list)
for code in valid:
    blocks[code >> cfg['free_code_bits']].append(code)
assert len(blocks) == 109


def quartic(w0, w1, t):
    def branch(w):
        B = t*w
        A = 1 + B*B
        D = t*t + w*w
        M = A*Hr + Cr*D
        return F([M*M + Cr*Hr*B*B, B*M, A*D])
    return branch(w0) * branch(w1)


input_rows = json.loads((ROOT / cfg['target_rows']).read_text())['rows']
assert input_rows[0]['name'] == 'positive_residual'
selected = input_rows[:cfg['target_count']]
setup_seconds = time.monotonic() - started
rows = []
for target_row in selected:
    target = E(*(dec(v) for v in target_row['target_point']))
    assert target != E(0) and target[0]
    t = ~target[0]
    qstart = time.monotonic()
    quartics = {code: quartic(*pair_reciprocals[code], t) for code in valid}
    quartic_seconds = time.monotonic()-qstart
    assert all(q.degree() == 4 for q in quartics.values())
    # Direct group subtraction tests the four source-product roots of one
    # frozen code. This check uses the y-coordinate omitted by the gate.
    audit_code = 253 if target_row['name'] == 'positive_residual' else valid[0]
    direct_products = []
    for x, y in by_code[audit_code]:
        other = target - E(x, y)
        assert other != E(0) and other[0]
        direct_products.append(Cr*~other[0] + Hr*other[0])
    assert len(set(direct_products)) == 4
    assert all(quartics[audit_code](p) == 0 for p in direct_products)
    roots = [p for p, multiplicity in quartics[audit_code].roots()
             for _ in range(int(multiplicity))]
    assert sorted(map(enc, roots)) == sorted(map(enc, direct_products))
    block_start = time.monotonic()
    degrees = {}
    for prefix, codes in sorted(blocks.items()):
        f = F.one()
        for code in codes:
            f *= quartics[code]
        degrees[prefix] = int(f.gcd(L).degree())
    block_seconds = time.monotonic()-block_start
    retained = [prefix for prefix, degree in degrees.items() if degree > 0]
    if target_row['name'] == 'positive_residual':
        assert 253 >> cfg['free_code_bits'] in retained
    rows.append({'name': target_row['name'],
                 'target_point': target_row['target_point'],
                 'quartic_count': len(quartics), 'block_count': len(blocks),
                 'rejected_blocks': len(blocks)-len(retained),
                 'retained_prefixes': retained,
                 'gcd_degree_histogram': {str(i): list(degrees.values()).count(i)
                                          for i in sorted(set(degrees.values()))},
                 'direct_root_audit_code': audit_code,
                 'direct_root_audit_products': list(map(enc, direct_products)),
                 'quartic_seconds': quartic_seconds,
                 'block_product_and_gcd_seconds': block_seconds,
                 'query_seconds_including_audit': time.monotonic()-qstart,
                 'prior_exact_product_hits': target_row['exact_product_subspace_hits']})

signal.alarm(0)
result = {'status': 'COMPLETE_N41_W11_QUARTIC_BLOCK_GCD',
          'candidate_id': None, 'curve_id': cfg['curve_id'],
          'source_codes': len(valid), 'source_product_space_dimension': 10,
          'source_product_vanishing_degree': L.degree(),
          'source_product_vanishing_terms': len(L.dict()),
          'block_free_code_bits': cfg['free_code_bits'],
          'setup_seconds': setup_seconds, 'rows': rows,
          'total_wall_seconds': time.monotonic()-started,
          'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'protocol_sha256': hashlib.sha256((HERE / protocol_name).read_bytes()).hexdigest()}
out.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps({'status': result['status'], 'queries': len(rows),
                  'setup_seconds': setup_seconds,
                  'total_seconds': result['total_wall_seconds']}, sort_keys=True))
