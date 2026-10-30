"""Fresh ascending degree-13 source lifts with incremental support-four rank stop."""
import argparse
import hashlib
import importlib.util
import itertools
import json
import math
import resource
import time
from collections import Counter
from pathlib import Path

from sage.all import GF, QQ, classical_modular_polynomial, matrix, vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == PLAN['runner_sha256']


def read_pinned(path, expected):
    raw = (ROOT / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected
    return json.loads(raw)


def rank(rows, width, field):
    if not rows:
        return 0
    return int(matrix(field, len(rows), width, lambda i, j: rows[i].get(j, 0)).rank())


def sparse(raw):
    return {int(i): int(v) for i, v in raw.items() if v}


def save(path, output):
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')


def lift_source(i, P, R, jfun, points, index, cache, modpoly, pattern_expected):
    E, p = R.E, int(R.Fp.cardinality())
    poly = R.neighbour_x(13, P)
    pattern = [[int(f.degree()), int(mult)] for f, mult in poly.factor()]
    assert pattern == pattern_expected
    d = math.lcm(*(degree for degree, _ in pattern))
    assert d <= 12 and all(mult == 1 for _, mult in pattern)
    if d not in cache:
        F = GF(p ** d, name=f'z{d}')
        EE = E.change_ring(F)
        lifted = [EE(F(Q[0]), F(Q[1])) for Q in points]
        cache[d] = F, EE, lifted, {Q: k for k, Q in enumerate(lifted)}
    F, EE, lifted, lifted_index = cache[d]
    roots = sorted(poly.change_ring(F).roots(multiplicities=False), key=str)
    assert len(roots) == 14
    moments = [F(R.funcs[13, 'xy', k](P[0], P[1])) for k in range(14)]
    V = matrix(F, [[x ** k for x in roots] for k in range(14)])
    ys = V.solve_right(vector(F, moments))
    nb = [EE(x, y) for x, y in zip(roots, ys)]
    assert sum(nb, EE(0)) == R.a_l[13] * lifted[i]
    assert all(sum(ys[j] * roots[j] ** k for j in range(14)) == moments[k]
               for k in range(14))
    jP = R.j(P)
    A, x0, _ = jfun
    cusp_count = 0
    modpoly_checked = 0
    for Q in nb:
        if Q[0] == F(x0):
            cusp_count += 1
            continue
        numer = sum(F(c) * Q[0] ** int(a) * Q[1] ** int(b)
                    for (a, b), c in A.items())
        jQ = numer / (Q[0] - F(x0)) ** 11
        assert modpoly(F(jP), jQ) == 0
        modpoly_checked += 1
    assert cusp_count + modpoly_checked == 14
    unseen = set(nb)
    orbits = []
    class_row = Counter({i: -int(R.a_l[13])})
    outside = []
    while unseen:
        seed = min(unseen, key=lambda Q: (str(Q[0]), str(Q[1])))
        orbit, Q = [], seed
        while Q not in orbit:
            orbit.append(Q)
            Q = EE(Q[0] ** p, Q[1] ** p)
        assert Q == seed and all(Q in unseen for Q in orbit)
        unseen.difference_update(orbit)
        T = sum(orbit, EE(0))
        if T.is_zero():
            status, coord = 'IDENTITY', None
        elif T in lifted_index:
            status, coord = 'IN_CLASS', [int(T[0]), int(T[1])]
            class_row[lifted_index[T]] += 1
        else:
            status, coord = 'OUTSIDE_CLASS', [int(T[0]), int(T[1])]
            outside.append(tuple(coord))
        orbits.append({'size': len(orbit), 'status': status, 'trace': coord})
    assert outside
    entry = {'source': i, 'factor_pattern': pattern, 'splitting_degree': d,
             'modpoly_checks': {'finite_j': modpoly_checked, 'cusp_j_pole': cusp_count},
             'orbits': orbits, 'class_part': {str(k): x for k, x in sorted(class_row.items()) if x},
             'outside_traces': [list(x) for x in sorted(outside)],
             'status': 'OUTSIDE_CLASS_TRACE'}
    total = sum((E(x, y) for x, y in entry['outside_traces']), E(0))
    assert sum((v * points[k] for k, v in sparse(entry['class_part']).items()), E(0)) + total == E(0)
    return entry, total


def main(p):
    case = next(x for x in PLAN['cases'] if x['p'] == p)
    parent = read_pinned(case['producer_receipt'], case['producer_sha256'])
    analysis = read_pinned(case['analysis_receipt'], case['analysis_sha256'])
    assert parent['status'] == 'COMPLETE' and parent['p'] == analysis['p'] == p
    assert parent['degree13_statuses'] == {'OUTSIDE_CLASS_TRACE': 40}
    assert hashlib.sha256((ROOT / PLAN['source_path']).read_bytes()).hexdigest() == PLAN['source_sha256']
    source = ROOT / PLAN['source_path']
    spec = importlib.util.spec_from_file_location(f'hecke13_prefix_{p}', source)
    H = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(H)
    start = time.perf_counter_ns()
    funcs, jfun = H.build([13])
    R = H.Reduced(p, funcs, jfun, [13])
    source_build_ns = time.perf_counter_ns() - start
    E = R.E
    assert int(E.cardinality()) == case['curve_order']
    points = [E(x, y) for x, y in parent['class_points']]
    assert len(points) == 40
    index = {P: i for i, P in enumerate(points)}
    direct = [sparse(x['row']) for x in analysis['direct']['candidates']]
    base = [sparse(x['row']) for x in parent['base_rows']]
    start = time.perf_counter_ns()
    for row in base + direct:
        assert sum((v * points[k] for k, v in row.items()), E(0)) == E(0)
    assert rank(base + direct, 40, QQ) == analysis['ranks']['base_direct_qq'] == 39
    assert rank(base + direct, 40, GF(case['q'])) == analysis['ranks']['base_direct_mod_q'] == 39
    baseline_check_ns = time.perf_counter_ns() - start
    out = {'schema': 'hecke-d79-source-prefix-producer-v1', 'status': 'RUNNING',
           'p': p, 'curve_order': case['curve_order'], 'q': case['q'],
           'parent_producer_sha256': case['producer_sha256'],
           'parent_analysis_sha256': case['analysis_sha256'],
           'source_sha256': PLAN['source_sha256'], 'source_build_wall_ns': source_build_ns,
           'baseline_check_wall_ns': baseline_check_ns, 'baseline_rows': len(base) + len(direct),
           'baseline_rank_qq': 39, 'baseline_rank_mod_q': 39,
           'sources': [], 'candidates': [], 'candidate_id': None, 'target_online_ms': None}
    output_path = HERE / f'p{p}-result.json'
    save(output_path, out)
    modpoly = classical_modular_polynomial(13)
    cache = {}
    sums = []
    all_rows = []
    for i in range(PLAN['policy']['max_sources']):
        start = time.perf_counter_ns()
        entry, total = lift_source(i, points[i], R, jfun, points, index, cache, modpoly,
                                   case['expected_factor_pattern'])
        fiber_ns = time.perf_counter_ns() - start
        frozen = parent['degree13_sources'][i]
        assert all(entry[k] == frozen[k] for k in
                   ('source', 'factor_pattern', 'splitting_degree', 'modpoly_checks',
                    'orbits', 'class_part', 'outside_traces', 'status'))
        sums.append(total)
        start = time.perf_counter_ns()
        trials = 0
        new_candidates = []
        for support in range(1, PLAN['policy']['support_max'] + 1):
            for previous in itertools.combinations(range(i), support - 1):
                inds = previous + (i,)
                for rest in itertools.product(PLAN['policy']['coefficient_order'],
                                              repeat=support - 1):
                    signs = (1,) + rest
                    trials += 1
                    if sum((s * sums[j] for j, s in zip(inds, signs)), E(0)) != E(0):
                        continue
                    combined = Counter()
                    for j, s in zip(inds, signs):
                        for k, v in sparse(out['sources'][j]['class_part'] if j < i else entry['class_part']).items():
                            combined[k] += s * v
                    row = {k: v for k, v in combined.items() if v}
                    assert sum((v * points[k] for k, v in row.items()), E(0)) == E(0)
                    candidate = {'sources': list(inds), 'coefficients': list(signs),
                                 'row': {str(k): v for k, v in sorted(row.items())}}
                    new_candidates.append(candidate)
                    all_rows.append(row)
        search_ns = time.perf_counter_ns() - start
        start = time.perf_counter_ns()
        qq_rank = rank(base + direct + all_rows, 40, QQ)
        q_rank = rank(base + direct + all_rows, 40, GF(case['q']))
        rank_ns = time.perf_counter_ns() - start
        entry.update(fiber_wall_ns=fiber_ns, search_wall_ns=search_ns,
                     rank_wall_ns=rank_ns, search_trials=trials,
                     new_candidate_count=len(new_candidates),
                     cumulative_candidate_count=len(all_rows),
                     rank_qq=qq_rank, rank_mod_q=q_rank)
        out['sources'].append(entry)
        out['candidates'].extend(new_candidates)
        out['cumulative_search_trials'] = sum(x['search_trials'] for x in out['sources'])
        out['measured_wall_ns'] = source_build_ns + baseline_check_ns + sum(
            x['fiber_wall_ns'] + x['search_wall_ns'] + x['rank_wall_ns'] for x in out['sources'])
        out['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save(output_path, out)
        print(json.dumps({'p': p, 'source': i, 'new_rows': len(new_candidates),
                          'rank_qq': qq_rank, 'rank_mod_q': q_rank,
                          'cumulative_trials': out['cumulative_search_trials']}), flush=True)
        if qq_rank == 40:
            out['status'] = 'RANK40_STOP'
            out['stop_source_count'] = i + 1
            save(output_path, out)
            break
    else:
        out['status'] = 'SOURCE_CAP'
        out['stop_source_count'] = PLAN['policy']['max_sources']
        save(output_path, out)
    print(json.dumps({'p': p, 'status': out['status'],
                      'stop_source_count': out['stop_source_count'],
                      'candidates': len(out['candidates'])}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--p', type=int, choices=[c['p'] for c in PLAN['cases']], required=True)
    main(parser.parse_args().p)
