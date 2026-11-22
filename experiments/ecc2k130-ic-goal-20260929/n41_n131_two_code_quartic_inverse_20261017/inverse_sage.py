"""Target-conditioned inverse search: one source code, then quartic roots."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_n131_aligned_quotient_transfer_20261017'
SOURCE = ROOT / 'n41_n131_w29_rotation_alignment_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'protocol.json').read_text())
for name, path in {'script': Path(__file__),
                   'runtime': HERE / 'sage_runtime_info.json',
                   'states': SOURCE / 'aligned_states.json',
                   'public_audit': SOURCE / 'n41_audit_result.json',
                   'panel': PRIOR / 'n41_panel_result.json',
                   'panel_audit': PRIOR / 'n41_panel_audit_result.json'}.items():
    assert sha(path) == protocol['source_sha256'][name], name
assert not (HERE / 'result.json').exists()

R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])
Q = PolynomialRing(F, 'q')
q = Q.gen()


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(c) << i for i, c in enumerate(value.polynomial().list()))


def add2(a, b):
    return (a[0] + b[0], a[1] + b[1])


def scale2(a, c):
    return (a[0] * c, a[1] * c)


def mul2(a, b, alpha, beta):
    return (a[0]*b[0] + beta*a[1]*b[1],
            a[0]*b[1] + a[1]*b[0] + alpha*a[1]*b[1])


def eliminant(p, t, C, H):
    """Norm_a Res_b(S3(a,b,t), C*b^2+q*b+H), degree <= 4 in q."""
    alpha, beta = p/C, H/C
    t2 = t**2
    # In F[q,a]/(a^2 + alpha*a + beta), use the basis (1,a).
    A = (Q(1 + beta*t2), Q(alpha*t2))
    B = (Q(0), Q(t))
    D = (Q(beta+t2), Q(alpha))
    N = add2(scale2(A, H), scale2(D, C))
    M = add2(scale2(A, q), scale2(B, C))
    K = add2(scale2(B, H), scale2(D, q))
    Ry = add2(mul2(N, N, alpha, beta), mul2(M, K, alpha, beta))
    r0, r1 = Ry
    return r0**2 + alpha*r0*r1 + beta*r1**2


source = json.loads((SOURCE / 'aligned_states.json').read_text())
audit = json.loads((SOURCE / 'n41_audit_result.json').read_text())
panel = json.loads((PRIOR / 'n41_panel_result.json').read_text())
assert source['rotations'] == [0, 0, 12, 12, 24]
assert audit['orientation'] == 6 and audit['state_ids'] == [105, 244, 66, 47, 111]
assert panel['status'] == 'PASS_EXACT_N41_TWO_CODE_QUOTIENT_PANEL'
states = [[E(dec(row['point'][0]), dec(row['point'][1])) for row in slot]
          for slot in source['states']]
public_raw = E(dec(source['target_raw_point'][0]), dec(source['target_raw_point'][1]))
public = E(public_raw[0]**(1 << 6), public_raw[1]**(1 << 6))
seed = dec(source['seed'] << 1)
h = F.zero()
v = seed
for _ in range(21):
    h += v
    v = v**4
assert h**2 + h == seed
H, C = h**2, 1+h**2
assert C and H
products = []
root_pairs = []
product_to_index = {}
for i in range(71):
    rows = source['states'][0][4*i:4*i+4]
    assert len({tuple(row['masks']) for row in rows}) == 1
    a = dec(rows[0]['masks'][0] << 1)
    p = a*(a+seed)
    roots = sorted({enc(1/states[0][sid][0]) for sid in range(4*i, 4*i+4)})
    assert len(roots) == 2
    assert all(C*dec(root)**2 + p*dec(root) + H == 0 for root in roots)
    assert enc(p) not in product_to_index
    product_to_index[enc(p)] = i
    products.append(p)
    root_pairs.append([dec(root) for root in roots])


def s3(a, b, t):
    abt = a*b*t
    return abt**2 + abt + a**2 + b**2 + t**2


positive = {'kind': 'ordinary_relation_suffix', 'suffix_state_ids': [66, 47, 111],
            'expected_exact_family_indices': panel['exact_surviving_indices']}
queries = [positive] + [
    {'kind': f'ordinary_miss_{i}', 'suffix_state_ids': row['suffix_state_ids'],
     'expected_exact_family_indices': []}
    for i, row in enumerate(panel['miss_panel'][:4])]
query_rows = []
for query in queries:
    tick = time.monotonic()
    suffix = sum((states[slot][sid]
                  for slot, sid in enumerate(query['suffix_state_ids'], 2)), E(0))
    required = public - suffix
    assert required != E(0) and required[0]
    t = 1/required[0]
    candidates = []
    quartic_degrees = {}
    total_field_roots = 0
    for i, p in enumerate(products):
        poly = eliminant(p, t, C, H)
        degree = int(poly.degree())
        quartic_degrees[degree] = quartic_degrees.get(degree, 0) + 1
        assert 0 <= degree <= 4, (i, degree)
        for candidate_q, multiplicity in poly.roots():
            total_field_roots += 1
            j = product_to_index.get(enc(candidate_q))
            if j is not None and i < j:
                assert poly(products[j]) == 0
                candidates.append((i, j, multiplicity))
    family_indices = []
    exact_indices = []
    for i, j, multiplicity in candidates:
        index = sum(71-k-1 for k in range(i)) + j-i-1
        family_indices.append(index)
        if any(states[0][a] + states[1][b] == required
               for a in range(4*i, 4*i+4) for b in range(4*j, 4*j+4)):
            exact_indices.append(index)
    assert sorted(set(exact_indices)) == query['expected_exact_family_indices']
    assert len(family_indices) == len(set(family_indices))
    if query['kind'] == 'ordinary_relation_suffix':
        assert family_indices == [1529] and exact_indices == [1529]
        assert any(s3(a, b, t) == 0
                   for a in root_pairs[105//4] for b in root_pairs[244//4])
    query_rows.append({
        'kind': query['kind'], 'suffix_state_ids': query['suffix_state_ids'],
        'required_partial_point': [enc(required[0]), enc(required[1])],
        'target_reciprocal': enc(t), 'first_code_count': len(products),
        'quartic_degrees': quartic_degrees,
        'field_roots_enumerated': total_field_roots,
        'source_code_family_indices': sorted(family_indices),
        'exact_group_family_indices': sorted(exact_indices),
        'query_seconds': time.monotonic() - tick,
    })
result = {
    'status': 'PASS_N41_TARGET_CONDITIONED_QUARTIC_INVERSE_PILOT',
    'curve_id': source['curve_id'], 'candidate_id': None,
    'source_codes': len(products), 'queries': query_rows,
    'total_quartics': sum(row['first_code_count'] for row in query_rows),
    'total_field_roots': sum(row['field_roots_enumerated'] for row in query_rows),
    'resource_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'resource_maxrss_unit': 'macOS bytes; process self only',
    'protocol_sha256': sha(HERE / 'protocol.json'),
    'source_sha256': {'script': sha(Path(__file__)),
                      'states': sha(SOURCE / 'aligned_states.json'),
                      'runtime': sha(HERE / 'sage_runtime_info.json')},
}
(HERE / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ('status', 'source_codes',
                                        'total_quartics', 'total_field_roots')}))
for row in query_rows:
    print(json.dumps({k: row[k] for k in ('kind', 'field_roots_enumerated',
                                         'source_code_family_indices',
                                         'exact_group_family_indices',
                                         'query_seconds')}))
