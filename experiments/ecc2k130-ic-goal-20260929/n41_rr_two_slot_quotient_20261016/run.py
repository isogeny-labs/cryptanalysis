"""Exact two-free-slot Riemann--Roch quotient join on a frozen public point."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009/geometry.json'
HIT = ROOT / 'n41_sixpair_shared_target_20261017/join_audit_result.json'
FIELD_SOURCE = ROOT / 'n41_n131_sixpair_rr_root_span_20261016/run.py'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

spec = importlib.util.spec_from_file_location('rr_field', FIELD_SOURCE)
rr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rr)
F = rr.Field(41, (1 << 41) | (1 << 3) | 1)

def power(a, e):
    z = 1
    while e:
        if e & 1:
            z = F.mul(z, a)
        a = F.mul(a, a)
        e >>= 1
    return z

def inv(a):
    assert a
    return power(a, (1 << 41) - 2)

def row(point):
    x, y = point
    x2 = F.mul(x, x)
    return [1, x, y, x2, F.mul(x, y), F.mul(x2, x), F.mul(x2, y)]

def kernel(rows):
    a = [r[:] for r in rows]
    pivots = []
    for col in range(7):
        first = next((k for k in range(len(pivots), len(a)) if a[k][col]), None)
        if first is None:
            continue
        k = len(pivots)
        a[k], a[first] = a[first], a[k]
        scale = inv(a[k][col])
        a[k] = [F.mul(v, scale) for v in a[k]]
        for i in range(len(a)):
            if i != k and a[i][col]:
                factor = a[i][col]
                a[i] = [u ^ F.mul(factor, v) for u, v in zip(a[i], a[k])]
        pivots.append(col)
    free = [j for j in range(7) if j not in pivots]
    assert len(pivots) == 5 and len(free) == 2
    out = []
    for j in free:
        v = [0] * 7
        v[j] = 1
        for k, p in enumerate(pivots):
            v[p] = a[k][j]
        assert all(dot(r, v) == 0 for r in rows)
        out.append(v)
    return out, pivots, free

def dot(a, b):
    z = 0
    for x, y in zip(a, b):
        z ^= F.mul(x, y)
    return z

def signature(point, basis):
    r = row(point)
    return [dot(r, v) for v in basis]

def key(pair):
    a, b = pair
    if not a and not b:
        return None
    if not b:
        return 'inf'
    return power(b, (1 << 41) - 2) if a == 1 else F.mul(a, inv(b))

def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert sha(HERE / 'run.py') == protocol['runner_sha256']
    for path, digest in protocol['sources'].items():
        assert sha(ROOT / path) == digest, path
    g = json.loads(GEOMETRY.read_text())
    hit = json.loads(HIT.read_text())
    assert hit['raw_target'] == protocol['raw_target']
    fixed = [g['blocks'][i]['states'][hit['pair_rows'][i]['state_id']] for i in range(2, 6)]
    for i, state in enumerate(fixed, 2):
        assert state['raw_sum'] == hit['pair_rows'][i]['raw_sum']
    # The seventh divisor point is -Q.
    qx, qy = hit['raw_target']
    rows = [row(state['raw_sum']) for state in fixed] + [row([qx, qy ^ qx])]
    start = time.monotonic_ns()
    basis, pivots, free = kernel(rows)
    used = {c for state in fixed for c in state['columns']}
    eligible = []
    for slot in (0, 1):
        eligible.append([(i, s) for i, s in enumerate(g['blocks'][slot]['states'])
                         if not used.intersection(s['columns'])])
    table = {}
    zero = [0, 0]
    for i, state in eligible[0]:
        sig = signature(state['raw_sum'], basis)
        k = key(sig)
        if k is None:
            zero[0] += 1
        else:
            table.setdefault(k, []).append((i, state))
    matches = []
    raw_matches = 0
    for j, state in eligible[1]:
        sig = signature(state['raw_sum'], basis)
        k = key(sig)
        if k is None:
            zero[1] += 1
            continue
        for i, other in table.get(k, []):
            raw_matches += 1
            if set(other['columns']).isdisjoint(state['columns']):
                matches.append([i, j])
    assert zero == [0, 0], 'zero quotient signature requires an explicit exceptional branch'
    elapsed = time.monotonic_ns() - start
    expected = [hit['pair_rows'][0]['state_id'], hit['pair_rows'][1]['state_id']]
    assert expected in matches
    result = {'status': 'COMPLETE_N41_RR_TWO_SLOT_JOIN', 'candidate_id': None,
              'source_sha256': {path: sha(ROOT / path) for path in protocol['sources']},
              'protocol_sha256': sha(HERE / 'protocol.json'), 'fixed_state_ids':
              [hit['pair_rows'][i]['state_id'] for i in range(2, 6)],
              'pivots': pivots, 'free': free, 'basis': basis,
              'eligible_states': [len(x) for x in eligible], 'zero_signature': zero,
              'signature_buckets': len(table), 'raw_key_matches': raw_matches,
              'distinct_column_matches': len(matches), 'matches': matches,
              'expected_pair': expected, 'join_wall_ns': elapsed}
    (HERE / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'eligible_states',
          'zero_signature', 'raw_key_matches', 'distinct_column_matches', 'expected_pair', 'join_wall_ns')}))

if __name__ == '__main__':
    main()
