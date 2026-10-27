"""Independent finite-field group enumeration and source-order rank paths."""
import hashlib
import itertools
import json
import math
import resource
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
POST_CLASS = json.loads((HERE / 'post_class.json').read_text())
POST_SOURCE = json.loads((HERE / 'post_source.json').read_text())


def pinned(name, sha):
    raw = (HERE / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != sha:
        raise ValueError('PIN_MISMATCH:' + name)
    return json.loads(raw)


def sparse(raw):
    return {int(k): int(v) for k, v in raw.items() if v}


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


def main():
    classes = pinned('class-result.json', POST_CLASS['sha256']['class_result'])
    sources = pinned('source-result.json', POST_SOURCE['sha256']['source_result'])
    out = {'schema': 'hecke-d79-priority-analysis-v1', 'status': 'RUNNING',
           'cases': [], 'candidate_id': None, 'target_online_ms': None}
    path = HERE / 'analysis.json'
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    for frozen in classes['cases']:
        p = frozen['p']
        source_cell = next(x for x in sources['cases'] if x['p'] == p)
        if frozen['status'] != 'CLASS_READY' or source_cell['status'] != 'COMPLETE':
            out['cases'].append({'p': p, 'status': 'CENSORED_INPUT'})
            path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
            continue
        neg, add = group_law(p)
        points = [tuple(x) for x in frozen['class_points']]
        base = [sparse(x['row']) for x in frozen['base_rows']]
        source_entries = source_cell['degree13_sources']
        totals = []
        for entry in source_entries:
            total = None
            for raw in entry['outside_traces']:
                total = add(total, tuple(raw))
            class_total = None
            for i, coeff in sparse(entry['class_part']).items():
                for _ in range(abs(coeff)):
                    class_total = add(class_total, points[i] if coeff > 0 else neg(points[i]))
            if add(class_total, total) is not None:
                raise ValueError('SOURCE_GROUP_MISMATCH')
            totals.append(total)
        t0 = time.perf_counter_ns()
        direct = []
        trials = 0
        for support in range(1, 5):
            for inds in itertools.combinations(range(40), support):
                for rest in itertools.product((-1, 1), repeat=support-1):
                    signs = (1,) + rest
                    trials += 1
                    point = None
                    for i, sign in zip(inds, signs):
                        point = add(point, points[i] if sign == 1 else neg(points[i]))
                    if point is None:
                        direct.append({'indices': list(inds), 'coefficients': list(signs),
                                       'row': {str(i): sign for i, sign in zip(inds, signs)}})
        direct_ns = time.perf_counter_ns() - t0
        if trials != 772240:
            raise ValueError('TRIAL_COUNT_MISMATCH')
        baseline = base + [sparse(x['row']) for x in direct]
        baseline_rank = rank(baseline)
        baseline_qrank = rank(baseline, frozen['largest_prime_factor'])
        t0 = time.perf_counter_ns()
        hecke = []
        for support in range(1, 5):
            for inds in itertools.combinations(range(40), support):
                for rest in itertools.product((-1, 1), repeat=support-1):
                    signs = (1,) + rest
                    point = None
                    for i, sign in zip(inds, signs):
                        point = add(point, totals[i] if sign == 1 else neg(totals[i]))
                    if point is not None:
                        continue
                    row = Counter()
                    for i, sign in zip(inds, signs):
                        for k, coeff in sparse(source_entries[i]['class_part']).items():
                            row[k] += sign*coeff
                    row = {k: x for k, x in row.items() if x}
                    check = None
                    for k, coeff in row.items():
                        for _ in range(abs(coeff)):
                            check = add(check, points[k] if coeff > 0 else neg(points[k]))
                    if check is not None:
                        raise ValueError('HECKE_ROW_GROUP_MISMATCH')
                    hecke.append({'sources': list(inds), 'coefficients': list(signs),
                                  'row': {str(k): x for k, x in sorted(row.items())}})
        hecke_ns = time.perf_counter_ns() - t0
        paths = {}
        for label, order in [('ascending', frozen['ascending_order']),
                             ('priority', frozen['priority_order'])]:
            steps = []
            seen = set()
            for source in order:
                seen.add(source)
                rows = baseline + [sparse(x['row']) for x in hecke if set(x['sources']) <= seen]
                qq_rank = rank(rows)
                q_rank = rank(rows, frozen['largest_prime_factor'])
                steps.append({'source': source, 'source_count': len(seen),
                              'candidate_count': len(rows)-len(baseline),
                              'rank_qq': qq_rank, 'rank_mod_q': q_rank})
                if qq_rank == 40:
                    break
            paths[label] = {'status': 'RANK40_STOP' if steps[-1]['rank_qq'] == 40 else 'CAP40',
                            'source_count': len(steps), 'steps': steps}
        cell = {'p': p, 'status': 'COMPLETE', 'base_rank_qq': rank(base),
                'direct_baseline_rank_qq': baseline_rank,
                'direct_baseline_rank_mod_q': baseline_qrank,
                'direct_candidate_count': len(direct),
                'hecke_candidate_count': len(hecke),
                'signed_trials_per_arm': trials,
                'direct_candidates': direct, 'hecke_candidates': hecke,
                'paths': paths,
                'direct_enumeration_wall_ns': direct_ns,
                'hecke_enumeration_wall_ns': hecke_ns}
        out['cases'].append(cell)
        path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'p': p, 'status': cell['status'],
                          'base_direct_rank': baseline_rank,
                          'direct': len(direct), 'hecke': len(hecke),
                          'ascending': paths['ascending']['source_count'],
                          'priority': paths['priority']['source_count']}), flush=True)
    out['status'] = 'COMPLETE'
    out['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
