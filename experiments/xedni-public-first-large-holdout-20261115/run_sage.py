"""Frozen public-first xedni rank-one construction on the larger-order panel."""
import hashlib
import json
from collections import Counter
from pathlib import Path
from sage.all import EllipticCurve, GF, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ADMISSION = ROOT / 'xedni-large-order-admission-20261115/result.json'
COORD = ROOT / 'xedni-rank-one-coordinate-control-20261115/result.json'
FAMILY = ROOT / 'xedni-coefficient-optimization-20261115/family-selection.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def center(z, p):
    z = int(z) % p
    return z if z <= p // 2 else z - p

def reduced(z, p):
    n, d = int(z.numerator()), int(z.denominator())
    assert d % p != 0
    return n * pow(d, -1, p) % p

def offsets(seed, p, q, i):
    return tuple(int.from_bytes(hashlib.sha256(
        f'{seed}:{p}:{i}:{axis}'.encode()).digest(), 'big') % q
        for axis in (0, 1))

def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert protocol['admission_sha256'] == sha(ADMISSION)
    assert protocol['coordinate_control_sha256'] == sha(COORD)
    assert protocol['family_sha256'] == sha(FAMILY)
    assert protocol['producer_sha256'] == sha(Path(__file__))
    vectors = [tuple(x) for x in json.loads(FAMILY.read_text())['selected']]
    assert len(vectors) == 13
    selected = {r['field_prime']: r for r in json.loads(ADMISSION.read_text())['rows']
                if r['selected']}
    coord = {r['field_prime']: r for r in json.loads(COORD.read_text())['rows']}
    assert list(protocol['field_panel']) == sorted(selected) == sorted(coord)
    results = []
    totals = Counter()
    for p in protocol['field_panel']:
        q = selected[p]['subgroup_order']
        m = coord[p]['subgroup_multiplier_m']
        assert q == coord[p]['subgroup_order']
        E = EllipticCurve(GF(p), [0, 0, 0, -1, -2])
        G = m * E([2, 2])
        Q = protocol['target_scalar'] * G
        assert int(G.order()) == q and not Q.is_zero()
        counts = Counter()
        events = []
        first_hit = None
        for i in range(protocol['queries_per_field']):
            t1, t2 = offsets(protocol['schedule_seed'], p, q, i)
            U, V = Q - t1 * G, Q - t2 * G
            counts['queries'] += 1
            if U.is_zero() or V.is_zero() or U == V:
                counts['filtered_queries'] += 1
                continue
            counts['admitted_queries'] += 1
            for a, b in vectors:
                counts['public_vector_tests'] += 1
                if not (a * U + b * V).is_zero():
                    continue
                counts['public_hits'] += 1
                first_hit = first_hit or i + 1
                event = {'query_index_one_based': i + 1, 't': [t1, t2],
                         'vector': [a, b], 'status': 'started'}
                try:
                    inv_b = pow(b % q, -1, q)
                    T = inv_b * U
                    assert b * T == U and (-a) * T == V
                    x, y = center(T[0], p), center(T[1], p)
                    B = y*y - x*x*x + x
                    C = EllipticCurve(QQ, [0, 0, 0, -1, B])
                    P = C([x, y])
                    A, D = b * P, (-a) * P
                    assert C.discriminant() != 0 and (B + 2) % p == 0
                    assert (a * A + b * D).is_zero()
                    assert not A.is_zero() and not D.is_zero()
                    assert E([reduced(A[0], p), reduced(A[1], p)]) == U
                    assert E([reduced(D[0], p), reduced(D[1], p)]) == V
                    w = ((a*t1 + b*t2) * pow((a+b) % q, -1, q)) % q
                    assert w * G == Q
                    point_text = [str(A[0]), str(A[1]), str(D[0]), str(D[1])]
                    event.update(status='verified', inverse_b=inv_b, lift_T=[x, y],
                                 curve_B=B, recovered_scalar=w,
                                 rational_points_sha256=hashlib.sha256(json.dumps(
                                     point_text, separators=(',', ':')).encode()).hexdigest())
                    counts['verified'] += 1
                    counts['modular_inverses'] += 1
                    counts['public_scalar_multiplications'] += 1
                    counts['curve_constructions'] += 1
                    counts['rational_scalar_multiplications'] += 2
                    counts['rational_relation_tests'] += 1
                    counts['reduction_checks'] += 2
                    counts['scalar_replays'] += 1
                except Exception as exc:
                    event.update(status='failed', error_type=type(exc).__name__, error=str(exc))
                    counts['failed'] += 1
                events.append(event)
        path = HERE / f'p{p}-events.jsonl'
        path.write_text(''.join(json.dumps(e, sort_keys=True, separators=(',', ':')) + '\n'
                                for e in events))
        results.append({'field_prime': p, 'subgroup_order': q, 'subgroup_multiplier': m,
                        'counts': dict(counts), 'first_hit_query': first_hit,
                        'events_path': path.name, 'events_sha256': sha(path)})
        totals.update(counts)
    status = 'PASS' if totals['public_hits'] == totals['verified'] and not totals['failed'] else 'INCOMPLETE'
    print(json.dumps({'schema': 'xedni-public-first-large-holdout-result-v1',
                      'status': status, 'protocol_sha256': sha(HERE / 'protocol.json'),
                      'source_sha256': sha(Path(__file__)),
                      'sage_runtime_sha256': sha(HERE / 'sage-runtime-info.json'),
                      'fields': results, 'totals': dict(totals)}, sort_keys=True, indent=2))

if __name__ == '__main__':
    main()
