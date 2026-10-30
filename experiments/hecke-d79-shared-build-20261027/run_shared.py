"""Replay two D79 prefix workloads with one or two degree-13 Hecke builds."""
import argparse
import hashlib
import importlib.util
import itertools
import json
import resource
import time
from collections import Counter
from pathlib import Path

from sage.all import GF, QQ, classical_modular_polynomial

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == PLAN['runner_sha256']


def pinned(path, digest):
    raw = (ROOT / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest
    return json.loads(raw)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def build_digest(funcs, jfun):
    def encoded(d):
        return [[str(k), str(v)] for k, v in sorted(d.items(), key=lambda x: str(x[0]))]
    payload = {'funcs': [[str(k), encoded(v)] for k, v in
                         sorted(funcs.items(), key=lambda x: str(x[0]))],
               'jfun_A': encoded(jfun[0]), 'jfun_x0': str(jfun[1]),
               'jfun_cusp': str(jfun[2])}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def run_prime(case, H, prefix_runner, funcs, jfun):
    p = case['p']
    parent = pinned(case['parent_producer_path'], case['parent_producer_sha256'])
    analysis = pinned(case['parent_analysis_path'], case['parent_analysis_sha256'])
    frozen = pinned(case['prefix_result_path'], case['prefix_result_sha256'])
    audit = pinned(case['prefix_audit_path'], case['prefix_audit_sha256'])
    assert audit['status'] == 'PASS' and frozen['status'] == 'RANK40_STOP'
    t0 = time.perf_counter_ns()
    R = H.Reduced(p, funcs, jfun, [13])
    E = R.E
    assert int(E.cardinality()) == parent['curve_order']
    points = [E(x, y) for x, y in parent['class_points']]
    assert len(points) == 40
    base = [prefix_runner.sparse(x['row']) for x in parent['base_rows']]
    direct = [prefix_runner.sparse(x['row']) for x in analysis['direct']['candidates']]
    assert prefix_runner.rank(base + direct, 40, QQ) == 39
    assert prefix_runner.rank(base + direct, 40, GF(parent['largest_prime_factor'])) == 39
    setup_ns = time.perf_counter_ns() - t0
    cache = {}
    sums = []
    all_rows = []
    candidates = []
    paths = []
    for i in range(frozen['stop_source_count']):
        t0 = time.perf_counter_ns()
        entry, total = prefix_runner.lift_source(
            i, points[i], R, jfun, points, {}, cache,
            MODPOLY,
            frozen['sources'][i]['factor_pattern'])
        saved = frozen['sources'][i]
        assert all(entry[k] == saved[k] for k in
                   ('source', 'factor_pattern', 'splitting_degree', 'modpoly_checks',
                    'orbits', 'class_part', 'outside_traces', 'status'))
        fiber_ns = time.perf_counter_ns() - t0
        sums.append(total)
        t0 = time.perf_counter_ns()
        trials = 0
        new_candidates = []
        for support in range(1, 5):
            for previous in itertools.combinations(range(i), support - 1):
                inds = previous + (i,)
                for rest in itertools.product((-1, 1), repeat=support - 1):
                    signs = (1,) + rest
                    trials += 1
                    if sum((s*sums[j] for j, s in zip(inds, signs)), E(0)) != E(0):
                        continue
                    combined = Counter()
                    for j, s in zip(inds, signs):
                        for k, v in prefix_runner.sparse(frozen['sources'][j]['class_part']).items():
                            combined[k] += s*v
                    row = {k: v for k, v in combined.items() if v}
                    assert sum((v*points[k] for k, v in row.items()), E(0)) == E(0)
                    new_candidates.append({'sources': list(inds), 'coefficients': list(signs),
                                           'row': {str(k): v for k, v in sorted(row.items())}})
                    all_rows.append(row)
        search_ns = time.perf_counter_ns() - t0
        t0 = time.perf_counter_ns()
        qq_rank = prefix_runner.rank(base + direct + all_rows, 40, QQ)
        q_rank = prefix_runner.rank(base + direct + all_rows, 40, GF(parent['largest_prime_factor']))
        rank_ns = time.perf_counter_ns() - t0
        candidates.extend(new_candidates)
        assert (trials, len(new_candidates), len(candidates), qq_rank, q_rank) == (
            saved['search_trials'], saved['new_candidate_count'],
            saved['cumulative_candidate_count'], saved['rank_qq'], saved['rank_mod_q'])
        paths.append({'source': i, 'fiber_wall_ns': fiber_ns, 'search_wall_ns': search_ns,
                      'rank_wall_ns': rank_ns, 'search_trials': trials,
                      'new_candidate_count': len(new_candidates),
                      'rank_qq': qq_rank, 'rank_mod_q': q_rank})
    assert candidates == frozen['candidates']
    assert paths[-1]['rank_qq'] == 40 and all(x['rank_qq'] < 40 for x in paths[:-1])
    return {'p': p, 'source_count': len(paths), 'candidate_count': len(candidates),
            'search_trials': sum(x['search_trials'] for x in paths),
            'candidate_sha256': hashlib.sha256(json.dumps(candidates, sort_keys=True,
                                                          separators=(',', ':')).encode()).hexdigest(),
            'setup_wall_ns': setup_ns, 'sources': paths,
            'final_rank_qq': paths[-1]['rank_qq'],
            'final_rank_mod_q': paths[-1]['rank_mod_q'],
            'prefix_result_sha256': case['prefix_result_sha256']}


def main(run_id):
    global MODPOLY
    run = next(x for x in PLAN['runs'] if x['run_id'] == run_id)
    assert hashlib.sha256((ROOT / PLAN['source_path']).read_bytes()).hexdigest() == PLAN['source_sha256']
    assert hashlib.sha256((ROOT / PLAN['prefix_runner_path']).read_bytes()).hexdigest() == PLAN['prefix_runner_sha256']
    H = module(ROOT / PLAN['source_path'], f'hecke_shared_{run_id}')
    prefix_runner = module(ROOT / PLAN['prefix_runner_path'], f'prefix_shared_{run_id}')
    total_start = time.perf_counter_ns()
    modpoly_start = time.perf_counter_ns()
    MODPOLY = classical_modular_polynomial(13)
    modpoly_wall_ns = time.perf_counter_ns() - modpoly_start
    out = {'schema': 'hecke-d79-shared-build-run-v1', 'status': 'RUNNING',
           'run_id': run_id, 'mode': run['mode'], 'order': run['order'],
           'source_sha256': PLAN['source_sha256'],
           'prefix_runner_sha256': PLAN['prefix_runner_sha256'],
           'modpoly_wall_ns': modpoly_wall_ns, 'builds': [], 'cases': [], 'candidate_id': None, 'target_online_ms': None}
    path = HERE / f'{run_id}.json'
    funcs = jfun = None
    for p in run['order']:
        if run['mode'] == 'separate' or funcs is None:
            t0 = time.perf_counter_ns()
            funcs, jfun = H.build([13])
            build_ns = time.perf_counter_ns() - t0
            out['builds'].append({'before_p': p, 'wall_ns': build_ns,
                                  'content_sha256': build_digest(funcs, jfun)})
            path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
        case = next(x for x in PLAN['cases'] if x['p'] == p)
        out['cases'].append(run_prime(case, H, prefix_runner, funcs, jfun))
        path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'run_id': run_id, 'p': p,
                          'build_count': len(out['builds']),
                          'source_count': out['cases'][-1]['source_count']}), flush=True)
    assert len(out['builds']) == (1 if run['mode'] == 'shared' else 2)
    assert len(set(x['content_sha256'] for x in out['builds'])) == 1
    out['total_wall_ns'] = time.perf_counter_ns() - total_start
    out['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    out['status'] = 'COMPLETE'
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'run_id': run_id, 'status': out['status'],
                      'build_count': len(out['builds']),
                      'total_wall_ns': out['total_wall_ns']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', choices=[x['run_id'] for x in PLAN['runs']], required=True)
    main(parser.parse_args().run_id)
