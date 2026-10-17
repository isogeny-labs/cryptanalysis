"""Exact determinant-value affine-rank screen on frozen six-slot boxes."""
import hashlib
import itertools
import json
import resource
import time
from pathlib import Path

D = Path(__file__).resolve().parent
S = D.parent / 'n41_sixpair_shared_target_20261017' / 'join_input.tsv'
MOD = (1 << 41) | (1 << 3) | 1

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def mul(a, b):
    z = 0
    while b:
        if b & 1:
            z ^= a
        b >>= 1
        a <<= 1
        if a & (1 << 41):
            a ^= MOD
    return z

SUBSETS = list(itertools.combinations(range(7), 3))
ALL = set(range(7))
COMPLEMENTS = [tuple(sorted(ALL-set(s))) for s in SUBSETS]

def determinant(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    if len(set(xs)) != 7:
        return None
    differences = {(i, j): xs[i] ^ xs[j] for i in range(7) for j in range(i+1, 7)}
    def vandermonde(indices):
        v = 1
        for i, j in itertools.combinations(indices, 2):
            v = mul(v, differences[i, j])
        return v
    result = 0
    for sel, rest in zip(SUBSETS, COMPLEMENTS):
        y = mul(mul(ys[sel[0]], ys[sel[1]]), ys[sel[2]])
        result ^= mul(mul(y, vandermonde(sel)), vandermonde(rest))
    return result

def rank_insert(basis, value):
    while value:
        k = value.bit_length()-1
        if k in basis:
            value ^= basis[k]
        else:
            basis[k] = value
            return True
    return False

panel = json.loads((D/'panel.json').read_text())
assert panel['source_sha256'] == sha(S)
h = S.read_text().splitlines()
rows = {}
for line in h[1:]:
    v = line.split()
    j, i = map(int, v[1:3])
    rows[j, i] = (int(v[9]), int(v[10]))
assert len(rows) == 960
target = tuple(panel['target'])
assert tuple(map(int, h[0].split()[3:])) == target
negative_target = (target[0], target[1] ^ target[0])
protocol = {'schema': 1, 'panel_sha256': sha(D/'panel.json'),
            'source_sha256': sha(S), 'worker_sha256': sha(Path(__file__)),
            'one_worker': True, 'wall_cap_s': 180, 'rss_boundary_bytes': 4294967296,
            'determinant': 'Laplace 3-y-row expansion of L(7O) evaluation matrix',
            'enumeration': 'lexicographic state-index product; stop a box only at affine rank 41'}
(D/'protocol.json').write_text(json.dumps(protocol, indent=2, sort_keys=True)+'\n')
started = time.monotonic()
results = []
for idx, box in enumerate(panel['panels']):
    basis = {}
    first = None
    evaluated = 0
    zeros = 0
    exceptional = 0
    complete = True
    reason = None
    total = 1
    for slot in box['slots']:
        total *= len(slot)
    for ids in itertools.product(*box['slots']):
        if time.monotonic()-started > protocol['wall_cap_s']:
            complete = False
            reason = 'WALL_CAP'
            break
        points = [rows[j, ids[j]] for j in range(6)] + [negative_target]
        d = determinant(points)
        evaluated += 1
        if d is None:
            exceptional += 1
            complete = False
            reason = 'DISTINCT_X_CHART_EXCEPTION'
            break
        zeros += d == 0
        if first is None:
            first = d
        else:
            rank_insert(basis, d ^ first)
        if len(basis) == 41:
            complete = False
            reason = 'AFFINE_RANK_FULL'
            break
    if reason == 'AFFINE_RANK_FULL':
        classification = 'NO_LINEAR_SEPARATOR'
    elif reason is not None:
        classification = 'UNRESOLVED'
    else:
        assert evaluated == total
        residual = first
        for k in sorted(basis, reverse=True):
            if residual >> k & 1:
                residual ^= basis[k]
        classification = 'CERTIFIED_NO_ZERO' if residual else 'AFFINE_HULL_CONTAINS_ZERO'
        if classification == 'CERTIFIED_NO_ZERO':
            assert zeros == 0
    rec = {'box': idx, 'kind': box['kind'], 'trial': box['trial'],
           'possible_assignments': total, 'evaluated': evaluated,
           'difference_rank': len(basis), 'zero_determinants_seen': zeros,
           'exceptional_charts': exceptional, 'stop_reason': reason,
           'classification': classification, 'first_determinant': first}
    results.append(rec)
    if (idx+1) % 16 == 0 or idx == len(panel['panels'])-1:
        print(json.dumps({'completed_boxes': idx+1, 'elapsed_s': time.monotonic()-started,
                          'last': rec}), flush=True)
    if reason == 'WALL_CAP':
        break
summary = {}
for kind in ('sign', 'root_sign', 'two_code', 'witness_two_code'):
    group = [r for r in results if r['kind'] == kind]
    summary[kind] = {'count': len(group), 'classifications': {
        c: sum(r['classification'] == c for r in group)
        for c in ('CERTIFIED_NO_ZERO', 'AFFINE_HULL_CONTAINS_ZERO',
                  'NO_LINEAR_SEPARATOR', 'UNRESOLVED')},
        'evaluated': sum(r['evaluated'] for r in group)}
out = {'protocol_sha256': sha(D/'protocol.json'), 'status': 'COMPLETE' if len(results)==97 else 'BOUNDED_UNKNOWN',
       'elapsed_s': time.monotonic()-started,
       'peak_self_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       'summary': summary, 'rows': results}
(D/'result.json').write_text(json.dumps(out, indent=2, sort_keys=True)+'\n')
print(json.dumps({'status': out['status'], 'elapsed_s': out['elapsed_s'],
                  'summary': summary}), flush=True)
