"""Verify four shared/separate build replays and emit compact receipts."""
import hashlib
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned(path, expected):
    p = ROOT / path
    assert sha(p) == expected
    return json.loads(p.read_text())


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def main():
    assert sha(HERE / 'run_shared.py') == PLAN['runner_sha256']
    assert sha(ROOT / PLAN['source_path']) == PLAN['source_sha256']
    assert sha(ROOT / PLAN['prefix_runner_path']) == PLAN['prefix_runner_sha256']
    assert (HERE / 'sage-runtime-info.txt').stat().st_size > 0
    digests = set()
    records = []
    attempts = []
    for spec in PLAN['runs']:
        name = spec['run_id']
        path = HERE / f'{name}.json'
        out = json.loads(path.read_text())
        assert out['status'] == 'COMPLETE'
        assert out['mode'] == spec['mode'] and out['order'] == spec['order']
        assert out['candidate_id'] is None and out['target_online_ms'] is None
        assert len(out['builds']) == (1 if spec['mode'] == 'shared' else 2)
        assert [x['p'] for x in out['cases']] == spec['order']
        assert [x['before_p'] for x in out['builds']] == (
            spec['order'][:1] if spec['mode'] == 'shared' else spec['order'])
        assert all(x['wall_ns'] > 0 for x in out['builds'])
        digests.update(x['content_sha256'] for x in out['builds'])
        for case in out['cases']:
            frozen_spec = next(x for x in PLAN['cases'] if x['p'] == case['p'])
            frozen = pinned(frozen_spec['prefix_result_path'],
                            frozen_spec['prefix_result_sha256'])
            audit = pinned(frozen_spec['prefix_audit_path'],
                           frozen_spec['prefix_audit_sha256'])
            assert audit['status'] == 'PASS'
            assert (case['source_count'], case['candidate_count'], case['search_trials'],
                    case['final_rank_qq'], case['final_rank_mod_q']) == (
                frozen['stop_source_count'], len(frozen['candidates']),
                frozen['cumulative_search_trials'], 40, 39)
            assert case['candidate_sha256'] == canonical_hash(frozen['candidates'])
            assert len(case['sources']) == frozen['stop_source_count']
            assert all((x['source'], x['search_trials'], x['new_candidate_count'],
                        x['rank_qq'], x['rank_mod_q']) ==
                       (y['source'], y['search_trials'], y['new_candidate_count'],
                        y['rank_qq'], y['rank_mod_q'])
                       for x, y in zip(case['sources'], frozen['sources']))
            assert all(x['fiber_wall_ns'] > 0 and x['search_wall_ns'] > 0 and
                       x['rank_wall_ns'] > 0 for x in case['sources'])
        stage_ns = out['modpoly_wall_ns'] + sum(x['wall_ns'] for x in out['builds']) + sum(
            c['setup_wall_ns'] + sum(s['fiber_wall_ns'] + s['search_wall_ns'] +
                                     s['rank_wall_ns'] for s in c['sources'])
            for c in out['cases'])
        assert 0 <= stage_ns <= out['total_wall_ns']
        record = {'run_id': name, 'mode': spec['mode'], 'order': spec['order'],
                  'build_count': len(out['builds']),
                  'build_wall_ms': sum(x['wall_ns'] for x in out['builds']) / 1e6,
                  'total_wall_ms': out['total_wall_ns'] / 1e6,
                  'phase_sum_wall_ms': stage_ns / 1e6,
                  'unallocated_wall_ms': (out['total_wall_ns'] - stage_ns) / 1e6,
                  'peak_rss_bytes': out['peak_rss_bytes'],
                  'output_sha256': sha(path)}
        records.append(record)
        attempts.append({'run_id': name, 'exit_code': 0,
                         'command': f'gtimeout 1800 ./sage -python experiments/hecke-d79-shared-build-20261027/run_shared.py --run-id {name}',
                         'stdout_sha256': sha(HERE / f'{name}-stdout.txt'),
                         'stderr_sha256': sha(HERE / f'{name}-stderr.txt'),
                         'result_sha256': sha(path)})
    assert len(digests) == 1
    modes = {mode: [r['total_wall_ms'] for r in records if r['mode'] == mode]
             for mode in ('shared', 'separate')}
    summary = {'schema': 'hecke-d79-shared-build-summary-v1', 'status': 'PASS',
               'candidate_id': None, 'target_online_ms': None,
               'build_content_sha256': next(iter(digests)),
               'build_invocations': {'shared': 1, 'separate': 2},
               'runs': records,
               'exploratory_median_two_prime_total_ms': {k: median(v) for k, v in modes.items()},
               'runtime_info_sha256': sha(HERE / 'sage-runtime-info.txt')}
    (HERE / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    (HERE / 'ATTEMPTS.json').write_text(json.dumps({'schema': 'hecke-d79-shared-build-attempts-v1',
                                                   'status': 'PASS', 'attempts': attempts},
                                                  indent=2, sort_keys=True) + '\n')
    print('SHARED_BUILD_REPLAY_PASS', len(records), next(iter(digests)))


if __name__ == '__main__':
    main()
