"""Verify the cache artifact, independent rebuild, negative controls and load replays."""
import hashlib
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
POST = json.loads((HERE / 'post_inputs.json').read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(obj):
    return (json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n').encode()


def main():
    for field, name in [('codec_sha256', 'cache_codec.py'),
                        ('builder_sha256', 'build_artifact.py')]:
        assert sha(HERE / name) == PLAN[field]
    for field, name in [('audit_builder_sha256', 'audit_build.py'),
                        ('load_runner_sha256', 'load_replay.py'),
                        ('controls_sha256', 'negative_controls.py')]:
        assert sha(HERE / name) == POST[field]
    assert sha(ROOT / PLAN['source_path']) == PLAN['source_sha256']
    assert sha(ROOT / PLAN['prefix_runner_path']) == PLAN['prefix_runner_sha256']
    assert sha(ROOT / PLAN['shared_runner_path']) == PLAN['shared_runner_sha256']
    assert sha(HERE / 'build-result.json') == POST['build_result_sha256']
    assert (HERE / 'sage-runtime-info.txt').stat().st_size > 0
    build = json.loads((HERE / 'build-result.json').read_text())
    artifact = ROOT / build['artifact_path']
    assert build['status'] == 'COMPLETE'
    assert build['artifact_sha256'] == POST['artifact_sha256'] == sha(artifact)
    assert artifact.name == f"hecke13-{POST['artifact_sha256']}.json"
    raw = artifact.read_bytes()
    assert len(raw) == build['artifact_bytes'] == POST['artifact_bytes']
    assert raw == canonical_bytes(json.loads(raw))
    assert build['function_digest'] == PLAN['expected_function_digest']
    audit = json.loads((HERE / 'audit-build.json').read_text())
    assert audit['status'] == 'PASS' and audit['function_count'] == 28
    assert audit['artifact_sha256'] == POST['artifact_sha256']
    assert audit['function_digest'] == PLAN['expected_function_digest']
    controls = json.loads((HERE / 'negative-controls.json').read_text())
    assert controls['status'] == 'PASS'
    assert {x['control'] for x in controls['results']} == {
        'changed_byte', 'noncanonical_json', 'nonreduced_rational'}
    assert all(x['status'] == 'REJECTED_AS_EXPECTED' for x in controls['results'])
    replays = []
    attempts = []
    for i, p in enumerate(PLAN['load_replay_order'], 1):
        result_path = HERE / f'load-r{i}-p{p}.json'
        data = json.loads(result_path.read_text())
        assert data['status'] == 'PASS' and data['run_number'] == i and data['p'] == p
        assert data['build_invocations'] == 0
        assert data['artifact_sha256'] == POST['artifact_sha256']
        assert data['artifact_bytes'] == len(raw)
        assert data['function_digest'] == PLAN['expected_function_digest']
        assert data['candidate_id'] is None and data['target_online_ms'] is None
        case = data['prime_result']
        frozen_spec = next(x for x in PLAN['cases'] if x['p'] == p)
        frozen_path = ROOT / frozen_spec['prefix_result_path']
        frozen_audit_path = ROOT / frozen_spec['prefix_audit_path']
        assert sha(frozen_path) == frozen_spec['prefix_result_sha256']
        assert sha(frozen_audit_path) == frozen_spec['prefix_audit_sha256']
        frozen = json.loads(frozen_path.read_text())
        frozen_audit = json.loads(frozen_audit_path.read_text())
        assert frozen_audit['status'] == 'PASS'
        assert (case['source_count'], case['candidate_count'], case['search_trials'],
                case['final_rank_qq'], case['final_rank_mod_q']) == (
            frozen['stop_source_count'], len(frozen['candidates']),
            frozen['cumulative_search_trials'], 40, 39)
        assert len(case['sources']) == frozen['stop_source_count']
        assert all((x['source'], x['search_trials'], x['new_candidate_count'],
                    x['rank_qq'], x['rank_mod_q']) ==
                   (y['source'], y['search_trials'], y['new_candidate_count'],
                    y['rank_qq'], y['rank_mod_q'])
                   for x, y in zip(case['sources'], frozen['sources']))
        charged = data['load_wall_ns'] + data['modpoly_wall_ns'] + case['setup_wall_ns'] + sum(
            x['fiber_wall_ns'] + x['search_wall_ns'] + x['rank_wall_ns']
            for x in case['sources'])
        assert 0 <= charged <= data['total_measured_wall_ns']
        replays.append({'run_number': i, 'p': p, 'artifact_load_ms': data['load_wall_ns']/1e6,
                        'prime_setup_ms': case['setup_wall_ns']/1e6,
                        'total_measured_ms': data['total_measured_wall_ns']/1e6,
                        'unallocated_ms': (data['total_measured_wall_ns']-charged)/1e6,
                        'peak_rss_bytes': data['peak_rss_bytes'],
                        'result_sha256': sha(result_path)})
        attempts.append({'stage': 'load_replay', 'run_number': i, 'p': p, 'exit_code': 0,
                         'command': f'gtimeout 1800 ./sage -python experiments/hecke-d79-function-cache-20261027/load_replay.py --run-number {i} --p {p}',
                         'stdout_sha256': sha(HERE / f'load-r{i}-p{p}-stdout.txt'),
                         'stderr_sha256': sha(HERE / f'load-r{i}-p{p}-stderr.txt'),
                         'result_sha256': sha(result_path)})
    attempts[:0] = [
        {'stage': 'build_artifact', 'exit_code': 0,
         'command': 'gtimeout 1800 ./sage -python experiments/hecke-d79-function-cache-20261027/build_artifact.py',
         'stdout_sha256': sha(HERE / 'build-stdout.txt'),
         'stderr_sha256': sha(HERE / 'build-stderr.txt'),
         'result_sha256': sha(HERE / 'build-result.json')},
        {'stage': 'fresh_build_audit', 'exit_code': 0,
         'command': 'gtimeout 1800 ./sage -python experiments/hecke-d79-function-cache-20261027/audit_build.py',
         'stdout_sha256': sha(HERE / 'audit-build-stdout.txt'),
         'stderr_sha256': sha(HERE / 'audit-build-stderr.txt'),
         'result_sha256': sha(HERE / 'audit-build.json')},
        {'stage': 'negative_controls', 'exit_code': 0,
         'command': 'gtimeout 1800 ./sage -python experiments/hecke-d79-function-cache-20261027/negative_controls.py',
         'stdout_sha256': sha(HERE / 'negative-controls-stdout.txt'),
         'stderr_sha256': sha(HERE / 'negative-controls-stderr.txt'),
         'result_sha256': sha(HERE / 'negative-controls.json')},
    ]
    summary = {'schema': 'hecke-d79-function-cache-summary-v1', 'status': 'PASS',
               'artifact_sha256': POST['artifact_sha256'], 'artifact_bytes': len(raw),
               'function_digest': PLAN['expected_function_digest'],
               'build_wall_ms': build['build_wall_ns']/1e6,
               'encode_wall_ms': build['encode_wall_ns']/1e6,
               'roundtrip_wall_ms': build['roundtrip_wall_ns']/1e6,
               'fresh_audit_build_wall_ms': audit['fresh_build_wall_ns']/1e6,
               'fresh_audit_load_wall_ms': audit['load_wall_ns']/1e6,
               'median_artifact_load_ms': median(x['artifact_load_ms'] for x in replays),
               'median_replay_measured_ms': median(x['total_measured_ms'] for x in replays),
               'replays': replays, 'candidate_id': None, 'target_online_ms': None}
    (HERE / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n')
    (HERE / 'ATTEMPTS.json').write_text(json.dumps({'schema': 'hecke-d79-function-cache-attempts-v1',
                                                   'status': 'PASS', 'attempts': attempts,
                                                   'runtime_info_sha256': sha(HERE / 'sage-runtime-info.txt')},
                                                  indent=2, sort_keys=True)+'\n')
    print('FUNCTION_CACHE_PASS', len(replays), POST['artifact_sha256'])


if __name__ == '__main__':
    main()
