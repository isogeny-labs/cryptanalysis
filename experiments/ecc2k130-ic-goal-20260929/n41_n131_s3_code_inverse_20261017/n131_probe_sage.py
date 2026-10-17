"""Direct S3 inverse on frozen W29 source-code controls at N131."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ALIGN = ROOT / 'n41_n131_w29_rotation_alignment_20261017'
LABEL = ROOT / 'n41_n131_aligned_quotient_transfer_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'n131_protocol.json').read_text())
for name, path in {
    'script': Path(__file__), 'runtime': HERE / 'sage_runtime_info.json',
    'sample': LABEL / 'n131_result.json',
    'sample_audit': LABEL / 'n131_audit_result.json',
    'group_audit': LABEL / 'n131_group_audit_result.json',
    'control': ALIGN / 'n131_aligned_control.json',
    'public': ALIGN / 'build_n131_result.json',
}.items():
    assert sha(path) == protocol['source_sha256'][name], name
assert not (HERE / 'n131_result.json').exists()

R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**131, name='u', modulus=u**131 + u**13 + u**2 + u + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(131)]))


def enc(value):
    return sum(int(c) << i for i, c in enumerate(value.polynomial().list()))


def halftrace(value):
    initial = value
    result = F.zero()
    for _ in range(66):
        result += value
        value = value**4
    assert result**2 + result == initial
    return result


def s3(a, b, t):
    abt = a*b*t
    return abt**2 + abt + a**2 + b**2 + t**2


def backward_roots(a, t):
    A = 1 + (a*t)**2
    B = a*t
    D = a**2 + t**2
    assert B
    if not A:
        root = D/B
        assert s3(a, root, t) == 0
        return [root], 'linear'
    rhs = A*D/(B**2)
    if rhs.trace():
        return [], 'trace_miss'
    v = halftrace(rhs)
    scale = B/A
    roots = [scale*v, scale*(v+1)]
    assert all(s3(a, root, t) == 0 for root in roots)
    return roots, 'two_roots'


sample = json.loads((LABEL / 'n131_result.json').read_text())
sample_audit = json.loads((LABEL / 'n131_audit_result.json').read_text())
group_audit = json.loads((LABEL / 'n131_group_audit_result.json').read_text())
control = json.loads((ALIGN / 'n131_aligned_control.json').read_text())
public_record = json.loads((ALIGN / 'build_n131_result.json').read_text())
assert sample['status'] == 'PASS_SAMPLED_N131_DEGREE_TWO_EXCLUSION'
assert sample_audit['root_checks'] == 1024 and group_audit['sampled_source_codes'] == 512
assert control['status'] == 'PASS_N131_ALIGNED_CONSTRUCTED_GROUP_CONTROL'
assert public_record['curve_id'] == control['curve_id']
seed = dec(898618 << 1)
h = halftrace(seed)
H, C = h**2, 1+h**2
assert H and C
bits = [i for i in range(29) if i != (898618).bit_length()-1]
products = []
roots = []
lookup = {}


def add_source(p, root):
    key = enc(p)
    if key in lookup:
        return lookup[key]
    z1 = root + p/C
    assert root and z1 and root != z1
    assert C*root**2+p*root+H == 0
    assert C*z1**2+p*z1+H == 0
    index = len(products)
    lookup[key] = index
    products.append(p)
    roots.append((root, z1))
    return index


for code, root_word in zip(sample['codes'], sample['roots']):
    mask = sum(1 << bit for index, bit in enumerate(bits) if code >> index & 1)
    a = dec(mask << 1)
    add_source(a*(a+seed), dec(root_word))
sample_count = len(products)
assert sample_count == 512
pair_points = [E(dec(x), dec(y)) for x, y in control['rotated_pair_points']]
known_indices = []
for j in (0, 1):
    p = dec(control['pairs'][j]['source_product'])
    z = 1/pair_points[j][0]
    known_indices.append(add_source(p, z))
assert known_indices[0] != known_indices[1]
assert len(products) in (512, 513, 514)
constructed = pair_points[0] + pair_points[1]
assert constructed != E(0) and constructed[0]
assert sum(pair_points, E(0)) == E(dec(control['raw_target'][0]),
                                   dec(control['raw_target'][1]))
public = E(dec(public_record['public_raw_point'][0]),
           dec(public_record['public_raw_point'][1]))
suffix = sum(pair_points[2:], E(0))
ordinary_residual = public - suffix
assert ordinary_residual != E(0) and ordinary_residual[0]
queries = [('constructed_positive', constructed),
           ('frozen_public_fixed_suffix', ordinary_residual)]
rows = []
for kind, required in queries:
    tick = time.monotonic()
    t = 1/required[0]
    cases = {'linear': 0, 'trace_miss': 0, 'two_roots': 0}
    field_roots = 0
    candidate_pairs = set()
    for i, pair_roots in enumerate(roots):
        for a in pair_roots:
            solutions, case = backward_roots(a, t)
            cases[case] += 1
            field_roots += len(solutions)
            for b in solutions:
                if not b:
                    continue
                q = (C*b**2+H)/b
                j = lookup.get(enc(q))
                if j is not None and i < j:
                    assert b in roots[j]
                    candidate_pairs.add((i, j))
    if kind == 'constructed_positive':
        assert tuple(sorted(known_indices)) in candidate_pairs
        assert pair_points[0]+pair_points[1] == required
    rows.append({
        'kind': kind, 'required_partial_point': [enc(required[0]), enc(required[1])],
        'target_reciprocal': enc(t), 'source_code_count': len(products),
        's3_quadratics': 2*len(products), 's3_case_counts': cases,
        'field_roots': field_roots,
        'sample_source_pair_hits': [list(pair) for pair in sorted(candidate_pairs)],
        'known_positive_pair_indices': known_indices if kind == 'constructed_positive' else None,
        'query_seconds': time.monotonic()-tick,
    })
result = {
    'status': 'PASS_N131_DIRECT_S3_INVERSE_SOURCE_SAMPLE',
    'curve_id': control['curve_id'], 'candidate_id': None,
    'sampled_valid_codes': sample_count, 'source_codes_with_controls': len(products),
    'queries': rows, 'resource_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'resource_maxrss_unit': 'macOS bytes; process self only',
    'protocol_sha256': sha(HERE / 'n131_protocol.json'),
    'source_sha256': {'script': sha(Path(__file__)),
                      'runtime': sha(HERE / 'sage_runtime_info.json'),
                      'sample': sha(LABEL / 'n131_result.json')},
}
(HERE / 'n131_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: result[key] for key in
                  ('status', 'sampled_valid_codes', 'source_codes_with_controls')}))
for row in rows:
    print(json.dumps({key: row[key] for key in
                      ('kind', 's3_quadratics', 'field_roots',
                       'sample_source_pair_hits', 'query_seconds')}))
