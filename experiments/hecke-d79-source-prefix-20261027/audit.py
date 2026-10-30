"""Independent pure-Python replay of ascending-source prefix cancellations."""
import argparse
import hashlib
import itertools
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == PLAN['auditor_sha256']


def pinned(path, expected):
    raw = (ROOT / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected
    return json.loads(raw)


def sparse(raw):
    return {int(i): int(v) for i, v in raw.items() if v}


def rank(rows, modulus=None):
    pivots = {}
    for row in rows:
        v = ({i: Fraction(x) for i, x in row.items() if x} if modulus is None else
             {i: x % modulus for i, x in row.items() if x % modulus})
        while v:
            i = min(v)
            if i not in pivots:
                z = v[i]
                pivots[i] = ({j: x/z for j, x in v.items()} if modulus is None else
                             {j: x*pow(z, -1, modulus) % modulus for j, x in v.items()})
                break
            z = v[i]
            for j, x in pivots[i].items():
                y = v.get(j, 0) - z*x
                if modulus is not None:
                    y %= modulus
                if y:
                    v[j] = y
                else:
                    v.pop(j, None)
    return len(pivots)


def main(p):
    case = next(x for x in PLAN['cases'] if x['p'] == p)
    parent = pinned(case['producer_receipt'], case['producer_sha256'])
    prior = pinned(case['analysis_receipt'], case['analysis_sha256'])
    out_path = HERE / f'p{p}-result.json'
    raw = out_path.read_bytes()
    data = json.loads(raw)
    assert data['p'] == p and data['status'] in ('RANK40_STOP', 'SOURCE_CAP')
    assert len(data['sources']) == data['stop_source_count'] <= 40
    assert data['candidate_id'] is None and data['target_online_ms'] is None
    points = [tuple(P) for P in parent['class_points']]
    assert len(points) == 40

    def neg(A):
        return None if A is None else (A[0], (-A[1]-1) % p)

    def add(A, B):
        if A is None:
            return B
        if B is None:
            return A
        x, y = A
        u, v = B
        if x == u and (y + v + 1) % p == 0:
            return None
        if A == B:
            top, bottom = 3*x*x - 2*x - 10, 2*y + 1
        else:
            top, bottom = v - y, u - x
        slope = top * pow(bottom % p, -1, p) % p
        intercept = (y - slope*x) % p
        X = (slope*slope + 1 - x - u) % p
        Y = (-slope*X - intercept - 1) % p
        assert (Y*Y + Y - X*X*X + X*X + 10*X + 20) % p == 0
        return X, Y

    def mul(n, A):
        if n < 0:
            return mul(-n, neg(A))
        total = None
        while n:
            if n & 1:
                total = add(total, A)
            A = add(A, A)
            n >>= 1
        return total

    base = [sparse(x['row']) for x in parent['base_rows']]
    direct = [sparse(x['row']) for x in prior['direct']['candidates']]
    assert rank(base + direct) == 39
    assert rank(base + direct, case['q']) == 39
    sums = []
    rows = []
    candidates = []
    prefix = []
    for i, source in enumerate(data['sources']):
        assert source['source'] == i
        frozen = parent['degree13_sources'][i]
        assert all(source[k] == frozen[k] for k in
                   ('source', 'factor_pattern', 'splitting_degree', 'modpoly_checks',
                    'orbits', 'class_part', 'outside_traces', 'status'))
        total = None
        for x, y in source['outside_traces']:
            total = add(total, (x, y))
        assert total is not None
        sums.append(total)
        trials = 0
        new = []
        for support in range(1, PLAN['policy']['support_max'] + 1):
            for previous in itertools.combinations(range(i), support - 1):
                inds = previous + (i,)
                for rest in itertools.product(PLAN['policy']['coefficient_order'],
                                              repeat=support - 1):
                    signs = (1,) + rest
                    trials += 1
                    aggregate = None
                    for j, s in zip(inds, signs):
                        aggregate = add(aggregate, sums[j] if s == 1 else neg(sums[j]))
                    if aggregate is not None:
                        continue
                    combined = Counter()
                    for j, s in zip(inds, signs):
                        for k, v in sparse(data['sources'][j]['class_part']).items():
                            combined[k] += s*v
                    row = {k: v for k, v in combined.items() if v}
                    check = None
                    for k, v in row.items():
                        check = add(check, mul(v, points[k]))
                    assert check is None
                    new.append({'sources': list(inds), 'coefficients': list(signs),
                                'row': {str(k): v for k, v in sorted(row.items())}})
                    rows.append(row)
        candidates.extend(new)
        qrank = rank(base + direct + rows, case['q'])
        zrank = rank(base + direct + rows)
        assert (trials, len(new), len(candidates), zrank, qrank) == (
            source['search_trials'], source['new_candidate_count'],
            source['cumulative_candidate_count'], source['rank_qq'], source['rank_mod_q'])
        prefix.append({'source_count': i+1, 'trials': trials, 'new_rows': len(new),
                       'rank_qq': zrank, 'rank_mod_q': qrank})
    assert candidates == data['candidates']
    assert data['cumulative_search_trials'] == sum(x['trials'] for x in prefix)
    assert all(x['rank_qq'] < 40 for x in prefix[:-1])
    assert (data['status'] == 'RANK40_STOP') == (prefix[-1]['rank_qq'] == 40)
    parent_subset = [x for x in prior['hecke']['candidates']
                     if max(x['sources']) < data['stop_source_count']]
    assert sorted(map(json.dumps, parent_subset)) == sorted(map(json.dumps, candidates))
    receipt = {'schema': 'hecke-d79-source-prefix-audit-v1', 'status': 'PASS',
               'p': p, 'producer_sha256': hashlib.sha256(raw).hexdigest(),
               'source_count': data['stop_source_count'], 'candidate_count': len(candidates),
               'search_trials': data['cumulative_search_trials'],
               'final_rank_qq': prefix[-1]['rank_qq'],
               'final_rank_mod_q': prefix[-1]['rank_mod_q'], 'prefix': prefix}
    (HERE / f'p{p}-audit.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'p': p, 'status': 'PASS', 'sources': len(prefix),
                      'candidates': len(candidates), 'trials': receipt['search_trials']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--p', type=int, choices=[c['p'] for c in PLAN['cases']], required=True)
    main(parser.parse_args().p)
