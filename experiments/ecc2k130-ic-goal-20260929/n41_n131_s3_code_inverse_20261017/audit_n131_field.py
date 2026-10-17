"""Independent GF(2^131) bit-field replay of direct S3 inverse controls."""
import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LABEL = ROOT / 'n41_n131_aligned_quotient_transfer_20261017'
ALIGN = ROOT / 'n41_n131_w29_rotation_alignment_20261017'
N = 131
MOD = (1 << N) | (1 << 13) | (1 << 2) | (1 << 1) | 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mul(a, b):
    out = 0
    while b:
        if b & 1:
            out ^= a
        b >>= 1
        a <<= 1
        if a & (1 << N):
            a ^= MOD
    return out


def sq(a):
    return mul(a, a)


def inv(a):
    assert a
    x, y = a, MOD
    u, v = 1, 0
    while x != 1:
        k = x.bit_length()-y.bit_length()
        if k < 0:
            x, y = y, x
            u, v = v, u
            k = -k
        x ^= y << k
        u ^= v << k
    while u.bit_length() > N:
        u ^= MOD << (u.bit_length()-N-1)
    assert mul(a, u) == 1
    return u


def trace(a):
    acc = 0
    for _ in range(N):
        acc ^= a
        a = sq(a)
    assert acc in (0, 1)
    return acc


def halftrace(a):
    initial = a
    acc = 0
    for _ in range((N+1)//2):
        acc ^= a
        a = sq(sq(a))
    assert sq(acc) ^ acc == initial
    return acc


def s3(a, b, t):
    abt = mul(mul(a, b), t)
    return sq(abt) ^ abt ^ sq(a) ^ sq(b) ^ sq(t)


start = time.monotonic()
protocol = json.loads((HERE / 'n131_audit_protocol.json').read_text())
producer = json.loads((HERE / 'n131_result.json').read_text())
sample = json.loads((LABEL / 'n131_result.json').read_text())
control = json.loads((ALIGN / 'n131_aligned_control.json').read_text())
for key, path in {
    'script': Path(__file__), 'producer': HERE / 'n131_result.json',
    'sample': LABEL / 'n131_result.json',
    'control': ALIGN / 'n131_aligned_control.json',
}.items():
    assert sha(path) == protocol['source_sha256'][key]
assert producer['status'] == 'PASS_N131_DIRECT_S3_INVERSE_SOURCE_SAMPLE'
seed = 898618 << 1
h = halftrace(seed)
H, C = sq(h), 1 ^ sq(h)
assert H and C
invC = inv(C)
bits = [i for i in range(29) if i != (898618).bit_length()-1]
products = []
roots = []
lookup = {}


def add_source(p, z):
    if p in lookup:
        assert z in roots[lookup[p]]
        return lookup[p]
    z1 = z ^ mul(p, invC)
    assert z and z1 and z != z1
    assert mul(C, sq(z)) ^ mul(p, z) ^ H == 0
    assert mul(C, sq(z1)) ^ mul(p, z1) ^ H == 0
    index = len(products)
    lookup[p] = index
    products.append(p)
    roots.append((z, z1))
    return index


for code, root in zip(sample['codes'], sample['roots']):
    mask = sum(1 << bit for index, bit in enumerate(bits) if code >> index & 1)
    a = mask << 1
    add_source(mul(a, a ^ seed), root)
assert len(products) == 512
known = []
for j in (0, 1):
    p = int(control['pairs'][j]['source_product'])
    x = int(control['rotated_pair_points'][j][0])
    known.append(add_source(p, inv(x)))
assert len(products) == producer['source_codes_with_controls'] == 514
assert known == producer['queries'][0]['known_positive_pair_indices']
rows = []
for row in producer['queries']:
    required = row['required_partial_point']
    t = inv(int(required[0]))
    assert t == row['target_reciprocal']
    cases = {'linear': 0, 'trace_miss': 0, 'two_roots': 0}
    output_roots = 0
    candidate_pairs = set()
    for i, pair_roots in enumerate(roots):
        for a in pair_roots:
            B = mul(a, t)
            A = 1 ^ sq(B)
            D = sq(a) ^ sq(t)
            assert B
            if A == 0:
                solutions = [mul(D, inv(B))]
                case = 'linear'
            else:
                rhs = mul(mul(A, D), inv(sq(B)))
                if trace(rhs):
                    solutions = []
                    case = 'trace_miss'
                else:
                    v = halftrace(rhs)
                    factor = mul(B, inv(A))
                    solutions = [mul(factor, v), mul(factor, v ^ 1)]
                    case = 'two_roots'
            cases[case] += 1
            output_roots += len(solutions)
            for b in solutions:
                assert s3(a, b, t) == 0
                if b == 0:
                    continue
                q = mul(mul(C, sq(b)) ^ H, inv(b))
                j = lookup.get(q)
                if j is not None and i < j:
                    assert b in roots[j]
                    candidate_pairs.add((i, j))
    assert cases == row['s3_case_counts']
    assert output_roots == row['field_roots']
    assert [list(pair) for pair in sorted(candidate_pairs)] == row['sample_source_pair_hits']
    rows.append({'kind': row['kind'], 'cases': cases, 'field_roots': output_roots,
                 'source_pair_hits': [list(pair) for pair in sorted(candidate_pairs)]})
result = {
    'status': 'PASS_INDEPENDENT_N131_DIRECT_S3_SOURCE_SAMPLE',
    'source_codes': len(products), 'queries': len(rows),
    'total_s3_quadratics': sum(sum(row['cases'].values()) for row in rows),
    'total_field_roots': sum(row['field_roots'] for row in rows),
    'source_pair_hits': [row['source_pair_hits'] for row in rows],
    'elapsed_seconds': time.monotonic()-start,
    'source_sha256': {'script': sha(Path(__file__)),
                      'producer': sha(HERE / 'n131_result.json'),
                      'protocol': sha(HERE / 'n131_audit_protocol.json')},
}
(HERE / 'n131_audit_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
