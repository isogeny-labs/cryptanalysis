"""Fresh degree-13 fiber replay with two support-five rank-stop baselines."""
import argparse
import hashlib
import importlib.util
import itertools
import json
import resource
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from sage.all import GF, QQ, classical_modular_polynomial

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE/'inputs.json').read_text())
sys.path.insert(0, str(ROOT/'experiments/hecke-d79-cache-interface-20261027'))
from cache_api import resolve


def pinned(name):
    item = PLAN['frozen'][name]
    raw = (ROOT/item['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != item['sha256']:
        raise ValueError('PIN_MISMATCH:' + name)
    return json.loads(raw)


def module(path, sha, name):
    path = ROOT/path
    if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
        raise ValueError('SOURCE_MISMATCH:' + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def canonical(item):
    return json.dumps(item, sort_keys=True, separators=(',', ':'))


def enumerate_visited(indices, traces, class_parts, points, E, P):
    pairs = defaultdict(list)
    for i, j in itertools.combinations(indices, 2):
        for a, b in itertools.product((-1, 1), repeat=2):
            pairs[a*traces[i] + b*traces[j]].append((i, j, a, b))
    keys = set()
    hits = 0
    for i, j, k in itertools.combinations(indices, 3):
        for b, c in itertools.product((-1, 1), repeat=2):
            total = traces[i] + b*traces[j] + c*traces[k]
            for u, v, a, d in pairs.get(-total, ()):
                if u <= i or len({i, j, k, u, v}) != 5:
                    continue
                hits += 1
                signed = sorted(((i, 1), (j, b), (k, c), (u, a), (v, d)))
                if signed[0][1] != 1:
                    raise ValueError('SIGN_CANONICALIZATION_FAIL')
                keys.add((tuple(x for x, _ in signed), tuple(s for _, s in signed)))
    records = []
    for sources, signs in sorted(keys):
        row = Counter()
        for i, sign in zip(sources, signs):
            for k, coeff in class_parts[i].items():
                row[k] += sign*coeff
        row = {k: coeff for k, coeff in row.items() if coeff}
        if sum((coeff*points[k] for k, coeff in row.items()), E(0)) != E(0):
            raise ValueError('GROUP_ROW_MISMATCH')
        records.append({'sources': list(sources), 'coefficients': list(signs),
                        'row': {str(k): coeff for k, coeff in sorted(row.items())}})
    return records, hits, sum(map(len, pairs.values())), 4*len(list(itertools.combinations(indices, 3)))


def main(order_name):
    cls = next(x for x in pinned('class')['cases'] if x['p'] == PLAN['p'])
    source_cell = next(x for x in pinned('source')['cases'] if x['p'] == PLAN['p'])
    support4 = next(x for x in pinned('support4')['cases'] if x['p'] == PLAN['p'])
    support5 = pinned('support5')
    if pinned('support5_audit')['status'] != 'PASS' or pinned('q_log_audit')['status'] != 'PASS':
        raise ValueError('PARENT_AUDIT_NOT_PASS')
    H = module(PLAN['source_path'], PLAN['source_sha256'], 'hecke_support5_prefix_H')
    P = module(PLAN['prefix_runner_path'], PLAN['prefix_runner_sha256'], 'hecke_support5_prefix_P')
    S = module(PLAN['shared_runner_path'], PLAN['shared_runner_sha256'], 'hecke_support5_prefix_S')
    def forbidden_build(*_args, **_kwargs):
        raise RuntimeError('H_BUILD_FORBIDDEN')
    H.build = forbidden_build
    total_start = time.perf_counter_ns()
    funcs, jfun, cache_receipt = resolve(
        H, ROOT/PLAN['artifact_path'], PLAN['artifact_sha256'],
        PLAN['source_sha256'], PLAN['function_digest'], S.build_digest, 'strict')
    if cache_receipt['status'] != 'CACHE_HIT' or cache_receipt['build_invocations'] != 0:
        raise ValueError('CACHE_MISMATCH')
    R = H.Reduced(PLAN['p'], funcs, jfun, [13])
    E = R.E
    if int(E.cardinality()) != cls['curve_order']:
        raise ValueError('CURVE_ORDER_MISMATCH')
    points = [E(x, y) for x, y in cls['class_points']]
    base = [P.sparse(x['row']) for x in cls['base_rows']]
    base += [P.sparse(x['row']) for x in support4['direct_candidates']]
    base += [P.sparse(x['row']) for x in support4['hecke_candidates']]
    direct5 = [P.sparse(x['row']) for x in support5['arms']['direct']['candidates']]
    if (P.rank(base, 40, QQ), P.rank(base+direct5, 40, QQ)) != (34, 39):
        raise ValueError('BASELINE_RANK_MISMATCH')
    order = cls['ascending_order' if order_name == 'ascending' else 'priority_order']
    modpoly = classical_modular_polynomial(13)
    traces, class_parts, fiber_cache = {}, {}, {}
    steps = []
    expected_all = support5['arms']['hecke']['candidates']
    stop = {'support4': None, 'support4_plus_direct5': None}
    for source in order:
        t0 = time.perf_counter_ns()
        prior = source_cell['degree13_sources'][source]
        entry, total = P.lift_source(source, points[source], R, jfun, points,
                                     {}, fiber_cache, modpoly,
                                     prior['factor_pattern'])
        fiber_ns = time.perf_counter_ns()-t0
        if entry != {k: value for k, value in prior.items() if k != 'lift_wall_ns'}:
            raise ValueError('FIBER_MISMATCH')
        traces[source] = total
        class_parts[source] = P.sparse(entry['class_part'])
        indices = sorted(traces)
        t0 = time.perf_counter_ns()
        candidates, hits, pair_entries, triple_queries = enumerate_visited(
            indices, traces, class_parts, points, E, P)
        index_ns = time.perf_counter_ns()-t0
        seen = set(indices)
        expected = {canonical(x) for x in expected_all if set(x['sources']) <= seen}
        if {canonical(x) for x in candidates} != expected or len(candidates) != len(expected):
            raise ValueError('CANDIDATE_PREFIX_MISMATCH')
        hecke5 = [P.sparse(x['row']) for x in candidates]
        t0 = time.perf_counter_ns()
        ranks = {}
        for label, rows in [('support4', base+hecke5),
                            ('support4_plus_direct5', base+direct5+hecke5)]:
            ranks[label] = {'rank_qq': P.rank(rows, 40, QQ),
                            'rank_mod_q': P.rank(rows, 40, GF(PLAN['q']))}
            if ranks[label]['rank_qq'] == 40 and stop[label] is None:
                stop[label] = len(steps)+1
        rank_ns = time.perf_counter_ns()-t0
        steps.append({'source': source, 'source_count': len(steps)+1,
                      'fiber_wall_ns': fiber_ns, 'index_wall_ns': index_ns,
                      'rank_wall_ns': rank_ns, 'pair_entries': pair_entries,
                      'triple_queries': triple_queries, 'raw_index_hits': hits,
                      'candidate_count': len(candidates), 'ranks': ranks})
        if all(value is not None for value in stop.values()):
            break
    out = {'schema': 'hecke-d79-p68437-support5-prefix-run-v1',
           'status': 'COMPLETE' if all(value is not None for value in stop.values()) else 'CAP40',
           'order': order_name, 'p': PLAN['p'], 'stop_source_counts': stop,
           'visited_sources': len(steps), 'steps': steps, 'cache': cache_receipt,
           'total_measured_wall_ns': time.perf_counter_ns()-total_start,
           'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           'candidate_id': None, 'target_online_ms': None}
    (HERE/f'run-{order_name}.json').write_text(json.dumps(out, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'order': order_name, 'status': out['status'],
                      'stops': stop, 'visited_sources': len(steps)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--order', choices=['ascending', 'priority'], required=True)
    main(parser.parse_args().order)
