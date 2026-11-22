"""Target-conditioned S3 root intersection for three free code families."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'
RELATION = ROOT / 'n41_n131_w29_rotation_alignment_20261017/n41_audit_result.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_words(values):
    return hashlib.sha256(json.dumps(sorted(values), separators=(',', ':')).encode()).hexdigest()


protocol = json.loads((HERE / 'protocol.json').read_text())
for name, path in {'script': Path(__file__), 'runtime': HERE/'sage_runtime_info.json',
                   'states': SOURCE, 'relation': RELATION,
                   'panel': HERE/'panel.json'}.items():
    assert sha(path) == protocol['source_sha256'][name], name
assert not (HERE/'result.json').exists()
panel = json.loads((HERE/'panel.json').read_text())
source = json.loads(SOURCE.read_text())
relation = json.loads(RELATION.read_text())
assert panel['orientation'] == relation['orientation'] == 6
assert len(panel['boxes']) == 1025

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


def backward_roots(a, b):
    """Finite roots t of S3(a,b,t); flag a possible missing infinity chart."""
    if not a or not b:
        return [], 'exception'
    A = 1 + (a*b)**2
    B = a*b
    D = a**2 + b**2
    if not A:
        return [D/B], 'exception'
    rhs = A*D/(B**2)
    if rhs.trace():
        return [], 'trace_miss'
    h = halftrace(rhs)
    scale = B/A
    roots = [scale*h, scale*(h+1)]
    assert roots[0] != roots[1]
    assert all(s3(a, b, t) == 0 for t in roots)
    return roots, 'two_roots'


states = [[E(dec(row['point'][0]), dec(row['point'][1])) for row in slot]
          for slot in source['states']]
raw = E(dec(source['target_raw_point'][0]), dec(source['target_raw_point'][1]))
public = E(raw[0]**(1 << 6), raw[1]**(1 << 6))
fixed0 = states[0][panel['fixed_slot_state_ids']['0']]
fixed4 = states[4][panel['fixed_slot_state_ids']['4']]

setup_start = time.monotonic()
root_pairs = {}
for slot in (1, 2, 3):
    root_pairs[slot] = []
    for code in range(71):
        roots = sorted({enc(1/states[slot][sid][0])
                        for sid in range(4*code, 4*code+4)})
        assert len(roots) == 2
        root_pairs[slot].append([dec(v) for v in roots])
setup_seconds = time.monotonic()-setup_start

target_start = time.monotonic()
target = public-fixed0-fixed4
assert target != E(0) and target[0]
t = 1/target[0]
target_setup_seconds = time.monotonic()-target_start

rows = []
for box in panel['boxes']:
    started = time.monotonic()
    c1, c2, c3 = box['codes']
    left = set()
    right = set()
    cases = {'two_roots': 0, 'trace_miss': 0, 'exception': 0}
    for a in root_pairs[1][c1]:
        for b in root_pairs[2][c2]:
            roots, case = backward_roots(a, b)
            cases[case] += 1
            left.update(enc(v) for v in roots if v)
            if any(not v for v in roots):
                cases['exception'] += 1
    for c in root_pairs[3][c3]:
        roots, case = backward_roots(c, t)
        cases[case] += 1
        right.update(enc(v) for v in roots if v)
        if any(not v for v in roots):
            cases['exception'] += 1
    intersection = sorted(left & right)
    algebraic_hit = bool(intersection)
    unknown_exception = bool(cases['exception'])
    exact_states = []
    if algebraic_hit or unknown_exception:
        for i in range(4*c1, 4*c1+4):
            for j in range(4*c2, 4*c2+4):
                ij = states[1][i]+states[2][j]
                for k in range(4*c3, 4*c3+4):
                    if ij+states[3][k] == target:
                        exact_states.append([i, j, k])
    if box['kind'] == 'archived_positive':
        assert [244, 66, 47] in exact_states
        assert algebraic_hit
    row = {
        'kind': box['kind'], 'codes': box['codes'],
        'left_root_count': len(left), 'right_root_count': len(right),
        'left_digest': digest_words(left), 'right_digest': digest_words(right),
        'intersection': intersection, 'algebraic_hit': algebraic_hit,
        'unknown_exception': unknown_exception, 's3_cases': cases,
        'exact_state_triples': sorted(exact_states),
        'query_seconds': time.monotonic()-started,
    }
    rows.append(row)

result = {
    'status': 'PASS_N41_THREE_FREE_CODE_FAMILY_S3_PANEL',
    'candidate_id': None, 'curve_id': source['curve_id'],
    'orientation': 6, 'fixed_slot_state_ids': panel['fixed_slot_state_ids'],
    'target_partial_point': [enc(target[0]), enc(target[1])],
    'target_reciprocal': enc(t),
    'box_count': len(rows), 'algebraic_hits': sum(r['algebraic_hit'] for r in rows),
    'exact_hit_boxes': sum(bool(r['exact_state_triples']) for r in rows),
    'unknown_exception_boxes': sum(r['unknown_exception'] for r in rows),
    's3_quadratics': sum(sum(r['s3_cases'].values())-r['s3_cases']['exception']
                         for r in rows),
    'setup_seconds': setup_seconds, 'target_setup_seconds': target_setup_seconds,
    'box_query_seconds': sum(r['query_seconds'] for r in rows),
    'self_maxrss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'rows': rows, 'protocol_sha256': sha(HERE/'protocol.json'),
    'source_sha256': {'script': sha(Path(__file__)),
                      'runtime': sha(HERE/'sage_runtime_info.json'),
                      'panel': sha(HERE/'panel.json'), 'states': sha(SOURCE)},
}
(HERE/'result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps({key: result[key] for key in
                  ('status','box_count','algebraic_hits','exact_hit_boxes',
                   'unknown_exception_boxes','s3_quadratics','box_query_seconds')}))
