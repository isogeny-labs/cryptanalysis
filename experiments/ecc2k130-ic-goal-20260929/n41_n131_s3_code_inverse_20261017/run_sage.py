"""Exact target-conditioned second-code inversion by S3 half-trace roots."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_n131_w29_rotation_alignment_20261017'
PRIOR = ROOT / 'n41_n131_aligned_quotient_transfer_20261017'
QUARTIC = ROOT / 'n41_n131_two_code_quartic_inverse_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'protocol.json').read_text())
for name, path in {
    'script': Path(__file__), 'runtime': HERE / 'sage_runtime_info.json',
    'states': SOURCE / 'aligned_states.json',
    'relation_audit': SOURCE / 'n41_audit_result.json',
    'panel': PRIOR / 'n41_panel_result.json',
    'panel_audit': PRIOR / 'n41_panel_audit_result.json',
    'quartic_result': QUARTIC / 'result.json',
}.items():
    assert sha(path) == protocol['source_sha256'][name], name
assert not (HERE / 'result.json').exists()

R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(c) << i for i, c in enumerate(value.polynomial().list()))


def halftrace(value):
    original = value
    result = F.zero()
    for _ in range(21):
        result += value
        value = value**4
    assert result**2 + result == original
    return result


def s3(a, b, t):
    abt = a*b*t
    return abt**2 + abt + a**2 + b**2 + t**2


def backward_roots(a, t):
    """All field b with S3(a,b,t)=0, including degenerate leading term."""
    A = 1 + (a*t)**2
    B = a*t
    D = a**2 + t**2
    assert B
    if not A:
        b = D/B
        assert s3(a, b, t) == 0
        return [b], 'linear'
    rhs = A*D/(B**2)
    if rhs.trace():
        return [], 'trace_miss'
    h = halftrace(rhs)
    scale = B/A
    roots = [scale*h, scale*(h+1)]
    assert roots[0] != roots[1]
    assert all(s3(a, b, t) == 0 for b in roots)
    return roots, 'two_roots'


source = json.loads((SOURCE / 'aligned_states.json').read_text())
relation = json.loads((SOURCE / 'n41_audit_result.json').read_text())
panel = json.loads((PRIOR / 'n41_panel_result.json').read_text())
quartic = json.loads((QUARTIC / 'result.json').read_text())
assert source['rotations'] == [0, 0, 12, 12, 24]
assert relation['orientation'] == 6 and relation['state_ids'] == [105, 244, 66, 47, 111]
assert len(panel['miss_panel']) == 64 and len(quartic['queries']) == 5
states = [[E(dec(row['point'][0]), dec(row['point'][1])) for row in slot]
          for slot in source['states']]
raw = E(dec(source['target_raw_point'][0]), dec(source['target_raw_point'][1]))
public = E(raw[0]**(1 << 6), raw[1]**(1 << 6))
seed = dec(source['seed'] << 1)
h = halftrace(seed)
H, C = h**2, 1+h**2
assert C and H
products = []
root_pairs = []
lookup = {}
for i in range(71):
    rows = source['states'][0][4*i:4*i+4]
    assert len({tuple(row['masks']) for row in rows}) == 1
    a = dec(rows[0]['masks'][0] << 1)
    p = a*(a+seed)
    roots = sorted({enc(1/states[0][sid][0]) for sid in range(4*i, 4*i+4)})
    assert len(roots) == 2
    assert all(C*dec(z)**2 + p*dec(z) + H == 0 for z in roots)
    assert enc(p) not in lookup
    lookup[enc(p)] = i
    products.append(p)
    root_pairs.append([dec(z) for z in roots])

queries = [('ordinary_relation_suffix', [66, 47, 111], [1529])]
queries += [(f'ordinary_miss_{i}', row['suffix_state_ids'], [])
            for i, row in enumerate(panel['miss_panel'])]
rows = []
for kind, suffix_ids, expected in queries:
    tick = time.monotonic()
    suffix = sum((states[slot][sid] for slot, sid in enumerate(suffix_ids, 2)), E(0))
    required = public - suffix
    assert required != E(0) and required[0]
    t = 1/required[0]
    candidate_pairs = set()
    cases = {'linear': 0, 'trace_miss': 0, 'two_roots': 0}
    b_roots = 0
    zero_b = 0
    for i, roots in enumerate(root_pairs):
        for a in roots:
            solutions, case = backward_roots(a, t)
            cases[case] += 1
            b_roots += len(solutions)
            for b in solutions:
                if not b:
                    zero_b += 1
                    continue
                q = (C*b**2+H)/b
                j = lookup.get(enc(q))
                if j is not None and i < j:
                    assert C*b**2 + q*b + H == 0
                    assert b in root_pairs[j]
                    candidate_pairs.add((i, j))
    candidate_indices = sorted(sum(71-k-1 for k in range(i)) + j-i-1
                               for i, j in candidate_pairs)
    exact_indices = []
    for i, j in sorted(candidate_pairs):
        if any(states[0][aa] + states[1][bb] == required
               for aa in range(4*i, 4*i+4) for bb in range(4*j, 4*j+4)):
            exact_indices.append(sum(71-k-1 for k in range(i)) + j-i-1)
    assert exact_indices == expected
    if kind == 'ordinary_relation_suffix':
        assert candidate_indices == [1529]
    if len(rows) < 5:
        old = quartic['queries'][len(rows)]
        assert old['source_code_family_indices'] == candidate_indices
        assert old['exact_group_family_indices'] == exact_indices
        assert old['field_roots_enumerated'] == b_roots
    rows.append({
        'kind': kind, 'suffix_state_ids': suffix_ids,
        'required_partial_point': [enc(required[0]), enc(required[1])],
        'target_reciprocal': enc(t), 'first_code_count': 71,
        'first_pair_root_count': 142,
        's3_case_counts': cases, 's3_field_roots': b_roots,
        'zero_b_roots': zero_b,
        'source_code_family_indices': candidate_indices,
        'exact_group_family_indices': exact_indices,
        'query_seconds': time.monotonic()-tick,
    })
result = {
    'status': 'PASS_N41_DIRECT_S3_SOURCE_CODE_INVERSE_PANEL',
    'curve_id': source['curve_id'], 'candidate_id': None,
    'source_codes': len(products), 'queries': rows,
    'total_s3_quadratics': sum(row['first_pair_root_count'] for row in rows),
    'total_s3_field_roots': sum(row['s3_field_roots'] for row in rows),
    'total_source_code_family_hits': sum(len(row['source_code_family_indices']) for row in rows),
    'resource_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'resource_maxrss_unit': 'macOS bytes; process self only',
    'protocol_sha256': sha(HERE / 'protocol.json'),
    'source_sha256': {'script': sha(Path(__file__)),
                      'states': sha(SOURCE / 'aligned_states.json'),
                      'runtime': sha(HERE / 'sage_runtime_info.json')},
}
(HERE / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ('status', 'source_codes',
                                        'total_s3_quadratics',
                                        'total_s3_field_roots',
                                        'total_source_code_family_hits')}))
print(json.dumps({'positive_seconds': rows[0]['query_seconds'],
                  'miss_seconds_min': min(row['query_seconds'] for row in rows[1:]),
                  'miss_seconds_max': max(row['query_seconds'] for row in rows[1:])}))
