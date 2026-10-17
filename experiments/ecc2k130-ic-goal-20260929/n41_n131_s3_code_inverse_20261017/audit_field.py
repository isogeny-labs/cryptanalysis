"""Independent bit-field replay of every direct S3 inverse panel query."""
import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_n131_w29_rotation_alignment_20261017'
PRIOR = ROOT / 'n41_n131_aligned_quotient_transfer_20261017'
MOD = (1 << 41) | (1 << 3) | 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mul(a, b):
    out = 0
    while b:
        if b & 1:
            out ^= a
        b >>= 1
        a <<= 1
        if a & (1 << 41):
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
    while u.bit_length() > 41:
        u ^= MOD << (u.bit_length()-42)
    assert mul(a, u) == 1
    return u


def trace(a):
    acc = 0
    for _ in range(41):
        acc ^= a
        a = sq(a)
    assert acc in (0, 1)
    return acc


def halftrace(a):
    initial = a
    acc = 0
    for _ in range(21):
        acc ^= a
        a = sq(sq(a))
    assert sq(acc) ^ acc == initial
    return acc


def s3(a, b, t):
    abt = mul(mul(a, b), t)
    return sq(abt) ^ abt ^ sq(a) ^ sq(b) ^ sq(t)


start = time.monotonic()
protocol = json.loads((HERE / 'audit_protocol.json').read_text())
producer = json.loads((HERE / 'result.json').read_text())
source = json.loads((SOURCE / 'aligned_states.json').read_text())
panel = json.loads((PRIOR / 'n41_panel_result.json').read_text())
for key, path in {'script': Path(__file__), 'producer': HERE / 'result.json',
                  'states': SOURCE / 'aligned_states.json',
                  'panel': PRIOR / 'n41_panel_result.json'}.items():
    assert sha(path) == protocol['source_sha256'][key]
assert producer['status'] == 'PASS_N41_DIRECT_S3_SOURCE_CODE_INVERSE_PANEL'
assert len(producer['queries']) == 65
seed = source['seed'] << 1
h = halftrace(seed)
H, C = sq(h), 1 ^ sq(h)
assert C and H
products = []
roots = []
lookup = {}
for i in range(71):
    states = source['states'][0][4*i:4*i+4]
    mask = states[0]['masks'][0] << 1
    p = mul(mask, mask ^ seed)
    pair_roots = sorted({inv(row['point'][0]) for row in states})
    assert len(pair_roots) == 2
    assert all(mul(C, sq(z)) ^ mul(p, z) ^ H == 0 for z in pair_roots)
    assert p not in lookup
    lookup[p] = i
    products.append(p)
    roots.append(pair_roots)
rows = []
for index, row in enumerate(producer['queries']):
    point = tuple(row['required_partial_point'])
    if index == 0:
        assert point == tuple(panel['required_partial_point'])
    else:
        assert point == tuple(panel['miss_panel'][index-1]['required_partial_point'])
    t = inv(point[0])
    assert t == row['target_reciprocal']
    candidate_pairs = set()
    cases = {'linear': 0, 'trace_miss': 0, 'two_roots': 0}
    output_roots = 0
    zero_b = 0
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
                    x = halftrace(rhs)
                    factor = mul(B, inv(A))
                    solutions = [mul(factor, x), mul(factor, x ^ 1)]
                    case = 'two_roots'
            cases[case] += 1
            output_roots += len(solutions)
            for b in solutions:
                assert s3(a, b, t) == 0
                if b == 0:
                    zero_b += 1
                    continue
                q = mul(mul(C, sq(b)) ^ H, inv(b))
                j = lookup.get(q)
                if j is not None and i < j:
                    assert b in roots[j]
                    candidate_pairs.add((i, j))
    family_indices = sorted(sum(71-k-1 for k in range(i)) + j-i-1
                            for i, j in candidate_pairs)
    assert family_indices == row['source_code_family_indices']
    assert cases == row['s3_case_counts']
    assert output_roots == row['s3_field_roots']
    assert zero_b == row['zero_b_roots']
    rows.append({'kind': row['kind'], 'family_indices': family_indices,
                 'cases': cases, 'field_roots': output_roots})
result = {
    'status': 'PASS_INDEPENDENT_FULL_N41_DIRECT_S3_INVERSE_PANEL',
    'source_codes': len(products), 'queries': len(rows),
    'total_s3_quadratics': sum(sum(row['cases'].values()) for row in rows),
    'total_s3_field_roots': sum(row['field_roots'] for row in rows),
    'total_source_code_family_hits': sum(len(row['family_indices']) for row in rows),
    'elapsed_seconds': time.monotonic()-start,
    'source_sha256': {'script': sha(Path(__file__)),
                      'producer': sha(HERE / 'result.json'),
                      'protocol': sha(HERE / 'audit_protocol.json')},
}
(HERE / 'audit_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
