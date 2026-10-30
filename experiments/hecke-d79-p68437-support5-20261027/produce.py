"""Indexed signed pair/triple enumeration of p68437 support-five relations."""
import hashlib
import itertools
import json
import math
import resource
import time
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())


def pinned(name):
    item = PLAN['frozen'][name]
    raw = (ROOT / item['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != item['sha256']:
        raise ValueError('PIN_MISMATCH:' + name)
    return json.loads(raw)


def sparse(raw):
    return {int(k): int(v) for k, v in raw.items() if v}


def group_law(p):
    def neg(A):
        return None if A is None else (A[0], (-A[1]-1) % p)
    def add(A, B):
        if A is None:
            return B
        if B is None:
            return A
        x, y = A
        u, v = B
        if x == u and (y+v+1) % p == 0:
            return None
        top, bottom = ((3*x*x-2*x-10, 2*y+1) if A == B else (v-y, u-x))
        slope = top*pow(bottom % p, -1, p) % p
        intercept = (y-slope*x) % p
        X = (slope*slope+1-x-u) % p
        Y = (-slope*X-intercept-1) % p
        return X, Y
    return neg, add


def rank(rows, modulus=None):
    pivots = {}
    for raw in rows:
        v = ({i: Fraction(x) for i, x in raw.items() if x} if modulus is None else
             {i: x % modulus for i, x in raw.items() if x % modulus})
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


def enumerate_indexed(terms, neg, add):
    pairs = defaultdict(list)
    for i, j in itertools.combinations(range(40), 2):
        for a, b in itertools.product((-1, 1), repeat=2):
            total = add(terms[i] if a == 1 else neg(terms[i]),
                        terms[j] if b == 1 else neg(terms[j]))
            pairs[total].append((i, j, a, b))
    results = set()
    raw_hits = 0
    for i, j, k in itertools.combinations(range(40), 3):
        for b, c in itertools.product((-1, 1), repeat=2):
            total = add(add(terms[i], terms[j] if b == 1 else neg(terms[j])),
                        terms[k] if c == 1 else neg(terms[k]))
            for u, v, a, d in pairs.get(neg(total), ()):
                if u <= i or len({i, j, k, u, v}) != 5:
                    continue
                raw_hits += 1
                signed = sorted(((i, 1), (j, b), (k, c), (u, a), (v, d)))
                if signed[0][1] != 1:
                    raise ValueError('CANONICAL_SIGN_FAIL')
                results.add((tuple(x for x, _ in signed), tuple(s for _, s in signed)))
    return sorted(results), raw_hits, sum(map(len, pairs.values()))


def main():
    classes = pinned('class-result.json')
    sources = pinned('source-result.json')
    analysis = pinned('analysis.json')
    audit = pinned('audit.json')
    if audit['status'] != 'PASS':
        raise ValueError('PARENT_AUDIT_NOT_PASS')
    p = PLAN['p']
    cls = next(x for x in classes['cases'] if x['p'] == p)
    src = next(x for x in sources['cases'] if x['p'] == p)
    prior = next(x for x in analysis['cases'] if x['p'] == p)
    if cls['class_size'] != 40 or src['status'] != 'COMPLETE':
        raise ValueError('PARENT_CLASS_OR_SOURCES_INCOMPLETE')
    neg, add = group_law(p)
    points = [tuple(x) for x in cls['class_points']]
    totals = []
    for item in src['degree13_sources']:
        total = None
        for raw in item['outside_traces']:
            total = add(total, tuple(raw))
        totals.append(total)
    baseline = [sparse(x['row']) for x in cls['base_rows']]
    baseline += [sparse(x['row']) for x in prior['direct_candidates']]
    baseline += [sparse(x['row']) for x in prior['hecke_candidates']]
    if rank(baseline) != 34 or rank(baseline, 109) != 34:
        raise ValueError('BASELINE_RANK_MISMATCH')
    out = {'schema': 'hecke-d79-p68437-support5-result-v1',
           'status': 'RUNNING', 'p': p, 'baseline_rows': len(baseline),
           'baseline_rank_qq': 34, 'baseline_rank_mod_q': 34,
           'arms': {}, 'candidate_id': None, 'target_online_ms': None}
    path = HERE / 'result.json'
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    new_rows = {}
    for label, terms in [('direct', points), ('hecke', totals)]:
        t0 = time.perf_counter_ns()
        candidates, raw_hits, pair_entries = enumerate_indexed(terms, neg, add)
        index_ns = time.perf_counter_ns() - t0
        rows = []
        records = []
        t0 = time.perf_counter_ns()
        for indices, signs in candidates:
            if label == 'direct':
                row = dict(zip(indices, signs))
            else:
                row = Counter()
                for i, sign in zip(indices, signs):
                    for k, coeff in sparse(src['degree13_sources'][i]['class_part']).items():
                        row[k] += sign*coeff
                row = {k: v for k, v in row.items() if v}
            group_sum = None
            for k, coeff in row.items():
                for _ in range(abs(coeff)):
                    group_sum = add(group_sum, points[k] if coeff > 0 else neg(points[k]))
            if group_sum is not None:
                raise ValueError('ROW_GROUP_MISMATCH')
            records.append({'indices' if label == 'direct' else 'sources': list(indices),
                            'coefficients': list(signs),
                            'row': {str(k): v for k, v in sorted(row.items())}})
            rows.append(row)
        verify_ns = time.perf_counter_ns() - t0
        new_rows[label] = rows
        out['arms'][label] = {'status': 'COMPLETE', 'signed_patterns': math.comb(40, 5)*16,
                              'pair_entries': pair_entries, 'raw_index_hits': raw_hits,
                              'candidate_count': len(records), 'candidates': records,
                              'index_wall_ns': index_ns, 'verification_wall_ns': verify_ns,
                              'rank_qq': rank(baseline+rows),
                              'rank_mod_q': rank(baseline+rows, 109)}
        path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'arm': label, 'candidates': len(records),
                          'rank_qq': out['arms'][label]['rank_qq'],
                          'rank_mod_q': out['arms'][label]['rank_mod_q']}), flush=True)
    out['combined_rank_qq'] = rank(baseline+new_rows['direct']+new_rows['hecke'])
    out['combined_rank_mod_q'] = rank(baseline+new_rows['direct']+new_rows['hecke'], 109)
    out['status'] = 'COMPLETE'
    out['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': out['status'], 'combined_rank_qq': out['combined_rank_qq'],
                      'combined_rank_mod_q': out['combined_rank_mod_q']}))


if __name__ == '__main__':
    main()
