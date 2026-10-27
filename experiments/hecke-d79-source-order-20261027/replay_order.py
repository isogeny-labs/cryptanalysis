"""Freshly lift repetition-zero sources, enumerate cancellations, and stop at rank 40."""
import argparse
import hashlib
import importlib.util
import itertools
import json
import resource
import sys
import time
from collections import Counter
from pathlib import Path

from sage.all import GF, QQ, classical_modular_polynomial

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
ANALYSIS = json.loads((HERE / 'analysis.json').read_text())
sys.path.insert(0, str(ROOT / 'experiments/hecke-d79-cache-interface-20261027'))
from cache_api import resolve


def pinned(path, sha):
    raw = (ROOT / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != sha:
        raise ValueError('PIN_MISMATCH:' + path)
    return ROOT / path


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def canonical(item):
    return json.dumps(item, sort_keys=True, separators=(',', ':'))


def main(p):
    case = next(x for x in PLAN['cases'] if x['p'] == p)
    schedule = next(x for x in ANALYSIS['cases'] if x['p'] == p)
    parent = json.loads(pinned(case['result_path'], case['result_sha256']).read_text())
    prior = json.loads(pinned(case['analysis_path'], case['analysis_sha256']).read_text())
    H = module(pinned(PLAN['source_path'], PLAN['source_sha256']), 'hecke_order_H')
    P = module(pinned(PLAN['prefix_runner_path'], PLAN['prefix_runner_sha256']), 'hecke_order_P')
    S = module(pinned(PLAN['shared_runner_path'], PLAN['shared_runner_sha256']), 'hecke_order_S')
    def forbidden_build(*_args, **_kwargs):
        raise RuntimeError('H_BUILD_FORBIDDEN')
    H.build = forbidden_build
    t0 = time.perf_counter_ns()
    funcs, jfun, cache_receipt = resolve(
        H, ROOT / PLAN['artifact_path'], PLAN['artifact_sha256'],
        PLAN['source_sha256'], PLAN['function_digest'], S.build_digest, 'strict')
    if cache_receipt['status'] != 'CACHE_HIT' or cache_receipt['build_invocations'] != 0:
        raise ValueError('CACHE_RESULT_MISMATCH')
    R = H.Reduced(p, funcs, jfun, [13])
    E = R.E
    if int(E.cardinality()) != parent['curve_order']:
        raise ValueError('CURVE_ORDER_MISMATCH')
    points = [E(x, y) for x, y in parent['class_points']]
    baseline = [P.sparse(x['row']) for x in parent['base_rows']]
    direct = prior['direct']['candidates']
    baseline += [P.sparse(direct[i]['row']) for i in prior['direct']['selected_candidate_indices']]
    if P.rank(baseline, 40, QQ) != 39:
        raise ValueError('BASELINE_RANK_MISMATCH')
    base_setup_ns = time.perf_counter_ns() - t0
    modpoly = classical_modular_polynomial(13)
    cache = {}
    traces = {}
    entries = {}
    candidates = []
    steps = []
    expected = prior['hecke']['candidates']
    for source in schedule['replay_order']:
        t0 = time.perf_counter_ns()
        entry, total = P.lift_source(source, points[source], R, jfun, points,
                                     {}, cache, modpoly,
                                     parent['degree13_sources'][source]['factor_pattern'])
        lift_ns = time.perf_counter_ns() - t0
        if entry != parent['degree13_sources'][source]:
            raise ValueError('FIBER_MISMATCH:' + str(source))
        traces[source], entries[source] = total, entry
        visited = sorted(traces)
        t0 = time.perf_counter_ns()
        trials = 0
        for support in range(1, min(4, len(visited)) + 1):
            for subset in itertools.combinations(visited, support):
                if source not in subset:
                    continue
                for rest in itertools.product((-1, 1), repeat=support - 1):
                    signs = (1,) + rest
                    trials += 1
                    if sum((s * traces[i] for i, s in zip(subset, signs)), E(0)) != E(0):
                        continue
                    combined = Counter()
                    for i, sign in zip(subset, signs):
                        for k, value in P.sparse(entries[i]['class_part']).items():
                            combined[k] += sign * value
                    row = {k: v for k, v in combined.items() if v}
                    if sum((v * points[k] for k, v in row.items()), E(0)) != E(0):
                        raise ValueError('ROW_GROUP_MISMATCH')
                    candidates.append({'sources': list(subset),
                                       'coefficients': list(signs),
                                       'row': {str(k): v for k, v in sorted(row.items())}})
        search_ns = time.perf_counter_ns() - t0
        visited_set = set(visited)
        expected_now = {canonical(x) for x in expected if set(x['sources']) <= visited_set}
        if {canonical(x) for x in candidates} != expected_now or len(candidates) != len(expected_now):
            raise ValueError('CANDIDATE_SET_MISMATCH')
        t0 = time.perf_counter_ns()
        rows = baseline + [P.sparse(x['row']) for x in candidates]
        rank_qq = P.rank(rows, 40, QQ)
        rank_q = P.rank(rows, 40, GF(parent['largest_prime_factor']))
        rank_ns = time.perf_counter_ns() - t0
        steps.append({'source': source, 'visited_count': len(visited),
                      'lift_wall_ns': lift_ns, 'search_wall_ns': search_ns,
                      'rank_wall_ns': rank_ns, 'trials': trials,
                      'candidates': len(candidates), 'rank_qq': rank_qq,
                      'rank_mod_q': rank_q})
        if rank_qq == 40:
            break
    if (len(steps) != schedule['replay_predicted_source_count'] or
        steps[-1]['rank_qq'] != 40 or any(x['rank_qq'] >= 40 for x in steps[:-1])):
        raise ValueError('STOP_MISMATCH')
    out = {'schema': 'hecke-d79-source-order-replay-v1', 'status': 'PASS',
           'p': p, 'source_count': len(steps), 'total_trials': sum(x['trials'] for x in steps),
           'candidate_count': len(candidates), 'final_rank_qq': steps[-1]['rank_qq'],
           'final_rank_mod_q': steps[-1]['rank_mod_q'], 'cache': cache_receipt,
           'setup_wall_ns': base_setup_ns, 'steps': steps,
           'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           'candidate_id': None, 'target_online_ms': None}
    (HERE / f'replay-p{p}.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'p': p, 'status': out['status'],
                      'source_count': out['source_count'], 'trials': out['total_trials']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--p', type=int, choices=[8597, 12197], required=True)
    main(parser.parse_args().p)
