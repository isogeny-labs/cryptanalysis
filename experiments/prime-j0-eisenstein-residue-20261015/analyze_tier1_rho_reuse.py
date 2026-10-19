#!/usr/bin/env python3
"""Independent exact-output and noise audit for the separate reuse panel."""

import argparse
from hashlib import sha256
import json
from math import exp, isfinite, log
from pathlib import Path
import random
import statistics
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory

from make_tier1_rho_reuse_panel import COUNTS, MANIFEST_NAME, REPETITIONS, RULE_NAME
from make_tier1_rho_closeout_panel import FIXTURES

HERE = Path(__file__).resolve().parent
MODES = {'openssl': 'openssl_globalwarm', 'radix81': 'joint_triple81',
         'mixed76': 'joint_mixed76'}
COMPARISONS = ('openssl_vs_81', '81_vs_76', 'openssl_vs_76')


def digest(data):
    return sha256(data).hexdigest()


def median(values):
    return statistics.median(values) if values else None


def interval(values, seed):
    if len(values) != 32:
        return None
    rng = random.Random(seed)
    draws = sorted(exp(median(values[rng.randrange(32)] for _ in range(32)))
                   for _ in range(10000))
    return [draws[250], draws[9749]]


def audit(manifest_path, rules_path, raw_path, bundle_path,
          fixtures=FIXTURES):
    manifest = json.loads(manifest_path.read_text())
    rules = json.loads(rules_path.read_text())
    peak_rule = rules.get('peak_rss')
    with TemporaryDirectory(prefix='rho-reuse-audit-') as temporary:
        command = [sys.executable, str(HERE / 'make_tier1_rho_reuse_panel.py'),
                   '--instance-id', rules['instance_id'],
                   '--binary-sha256', rules['hashes']['binary'],
                   '--bundle-path', str(bundle_path),
                   '--libcrypto-sha256', rules['hashes']['libcrypto'],
                   '--libcrypto-path', rules['paths']['libcrypto'],
                   '--execution-cpu', str(rules['execution_cpu']),
                   '--output-dir', temporary, '--fixtures', str(fixtures),
                   '--provider', manifest['allocation']['provider']]
        if peak_rule:
            command.append('--peak-rss')
        completed = subprocess.run(command, capture_output=True, text=True)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert manifest == json.loads((Path(temporary) / MANIFEST_NAME).read_text())
        assert rules == json.loads((Path(temporary) / RULE_NAME).read_text())
    fixture_receipt = json.loads((fixtures / 'full-verification.json').read_text())
    assert fixture_receipt['status'] == 'pass'
    assert fixture_receipt['scope'] == 'all_rows'
    assert fixture_receipt['rows_verified'] == 4096
    assert fixture_receipt['manifest_sha256'] == rules['hashes']['fixture_manifest']
    cases = {case['id']: case for case in manifest['cases']}
    assert len(cases) == 396 and list(cases) == rules['case_order']
    assert manifest['repetitions'] == REPETITIONS
    for case_id, target in rules['case_targets'].items():
        path = fixtures / target['fixture']
        assert digest(path.read_bytes()) == target['fixture_sha256']
        fixture = json.loads(path.read_text())
        assert cases[case_id]['expected_result'] == fixture['cases'][
            target['count'] - 1]['point_hex']
    with tarfile.open(raw_path, 'r:gz') as archive:
        roots = {name.split('/')[0] for name in archive.getnames()}
        assert len(roots) == 1
        root = roots.pop()
        def read(name):
            return archive.extractfile(root + '/' + name).read()
        assert json.loads(read('manifest.json')) == manifest
        preflight = json.loads(read('preflight.json'))
        summary = json.loads(read('summary.json'))
        runs_bytes, pairs_bytes = read('runs.jsonl'), read('pairs.jsonl')
        runs = [json.loads(line) for line in runs_bytes.splitlines()]
        pairs = [json.loads(line) for line in pairs_bytes.splitlines()]
        structural = []
        if summary.get('manifest_sha256') != digest(read('manifest.json')):
            structural.append('manifest hash mismatch')
        if peak_rule:
            if (peak_rule.get('method') != 'linux_wait4_ru_maxrss_kib' or
                manifest.get('peak_rss_method') != peak_rule['method'] or
                summary.get('child_peak_rss_method') != peak_rule['method']):
                structural.append('peak RSS method mismatch')
            for key, name in (('runner_sha256', 'run_tier1_rho_reuse_peak.py'),
                              ('dependency_sha256', 'run_tier1_rho_closeout.py')):
                if (summary.get(key if key == 'runner_sha256' else
                                'runner_dependency_sha256') != peak_rule.get(key) or
                    digest((HERE / name).read_bytes()) != peak_rule.get(key)):
                    structural.append(key + ' mismatch')
        elif summary.get('runner_sha256') != digest(
                (HERE / 'run_tier1_rho_closeout.py').read_bytes()):
            structural.append('runner source hash mismatch')
        if summary.get('measurement_tier') != 'tier1_instance':
            structural.append('tier mismatch')
        if preflight.get('evidence', {}).get('allocation', {}).get('instance_id') != rules['instance_id']:
            structural.append('allocation mismatch')
        if summary.get('expected_pairs') != 3168:
            structural.append('expected pair mismatch')
        expected_artifacts = {
            **{path: rules['hashes'][key] for key, path in rules['paths'].items()},
            **{path: rules['hashes']['source_files'][name]
               for name, path in rules['source_paths'].items()},
            manifest['artifacts'][-1]: digest(rules_path.read_bytes()),
        }
        if peak_rule:
            expected_artifacts[peak_rule['runner_path']] = peak_rule['runner_sha256']
            expected_artifacts[peak_rule['dependency_path']] = peak_rule['dependency_sha256']
        for path, expected in expected_artifacts.items():
            if summary.get('artifact_sha256', {}).get(path) != expected:
                structural.append('artifact mismatch: ' + path)
        if not all(path in summary.get('artifact_sha256', {})
                   for path in manifest['artifacts']):
            structural.append('missing artifact receipt')
        lookup = {}
        invalid = []
        mode_phases = {count: {mode: [] for mode in MODES}
                       for count in COUNTS}
        for serial, row in enumerate(runs, 1):
            problems = []
            key = (row.get('repeat'), row.get('case'), row.get('variant'))
            if key in lookup:
                problems.append('duplicate arm')
            lookup[key] = row
            if row.get('serial') != serial or row.get('case') not in cases:
                problems.append('arm identity mismatch')
            elif row.get('command') != cases[row['case']][row['variant']]:
                problems.append('command mismatch')
            if row.get('measurement_tier') != 'tier1_instance':
                problems.append('tier mismatch')
            if row.get('binary_sha256') != rules['hashes']['binary']:
                problems.append('binary hash mismatch')
            if not row.get('postflight', {}).get('ok'):
                problems.append('postflight failed')
            if 'counter_deltas' not in row.get('tier1_observations', {}):
                problems.append('counter deltas absent')
            stdout = read(row['stdout_file'])
            stderr = read(row['stderr_file'])
            fields = dict(word.split('=', 1) for word in
                          stdout.decode(errors='replace').split() if '=' in word)
            if fields != row.get('fields') or stderr:
                problems.append('output receipt mismatch')
            if row.get('status') != 'valid' or row.get('issues') or row.get('returncode') != 0:
                problems.append('runner invalid')
            if row.get('case') in cases:
                target = rules['case_targets'][row['case']]
                mode = target[row['variant']]
                if (fields.get('verified') != '1' or
                    fields.get('mode') != MODES[mode] or
                    fields.get('count') != str(target['count']) or
                    fields.get('point') != cases[row['case']]['expected_result']):
                    problems.append('wrong exact output')
                try:
                    online = float(fields['online_ms'])
                    prep = float(fields['target_preparation_ms'])
                    evaluation = float(fields['restart_eval_ms'])
                    assert all(isfinite(x) and x >= 0 for x in
                               (online, prep, evaluation))
                    assert online > 0 and abs(online - prep - evaluation) <= 0.00001
                    assert abs(online - row['online_ms']) < 0.000001
                    memory = (int(fields['retained_bytes'])
                              if mode == 'openssl' else
                              int(fields['g_table_bytes']) +
                              int(fields['q_table_bytes']) +
                              int(fields['plan_bytes']))
                    assert memory >= 0
                    peak_rss = row.get('child_peak_rss_kib')
                    if peak_rule:
                        assert (isinstance(peak_rss, int) and peak_rss > 0 and
                                row.get('child_peak_rss_method') == peak_rule['method'] and
                                peak_rss * 1024 >= memory)
                    if not problems:
                        phase = {'online_ms': online, 'target_preparation_ms': prep,
                                 'restart_eval_ms': evaluation,
                                 'reported_retained_bytes': memory}
                        if peak_rule:
                            phase['child_peak_rss_kib'] = peak_rss
                        mode_phases[target['count']][mode].append(phase)
                except (AssertionError, KeyError, TypeError, ValueError):
                    problems.append('phase or memory accounting invalid')
            if problems:
                invalid.append({'serial': serial, 'problems': problems})
        aa_failures = {count: [] for count in COUNTS}
        comparisons = {count: {name: {f'q{i:02d}': [] for i in range(32)}
                               for name in COMPARISONS}
                       for count in COUNTS}
        ordered = []
        for position, case in enumerate(
                [c for _ in range(REPETITIONS) for c in manifest['cases']]):
            repeat = position // len(cases)
            case_id = case['id']
            pair = pairs[position] if position < len(pairs) else None
            first = 'reference' if (repeat + position % len(cases)) % 2 == 0 else 'candidate'
            second = 'candidate' if first == 'reference' else 'reference'
            arms = {variant: lookup.get((repeat, case_id, variant))
                    for variant in ('reference', 'candidate')}
            ordered.extend(arms[variant]['serial'] for variant in (first, second)
                           if arms[variant] is not None)
            count = rules['case_targets'][case_id]['count']
            suffix = case_id.split('_', 2)[2]
            ratio = None
            try:
                ratio = (arms['reference']['online_ms'] /
                         arms['candidate']['online_ms'])
                assert ratio > 0 and isfinite(ratio)
            except (TypeError, ZeroDivisionError, AssertionError):
                pass
            valid = (pair is not None and pair.get('case') == case_id and
                     pair.get('repeat') == repeat and pair.get('status') == 'valid' and
                     not pair.get('issues') and ratio is not None and
                     pair.get('run_serials') == {v: arm['serial']
                                                  for v, arm in arms.items()} and
                     abs(pair.get('speedup', 0) - ratio) < 0.000001)
            if suffix.startswith('cal_'):
                if not valid or not 0.90 <= ratio <= 1.11:
                    aa_failures[count].append(
                        {'repeat': repeat, 'case': case_id, 'ratio': ratio})
            elif valid:
                q = case_id.split('_', 2)[1]
                comparisons[count][suffix][q].append(ratio)
            if not valid:
                structural.append('invalid pair: ' + str((repeat, case_id)))
        if ordered != list(range(1, len(runs) + 1)):
            structural.append('arm order mismatch')
    results = {}
    for count in COUNTS:
        gate = bool(preflight.get('ok') and summary.get('status') == 'completed'
                    and summary.get('artifacts_stable') and not structural
                    and not invalid and not aa_failures[count]
                    and len(runs) == 6336 and len(pairs) == 3168)
        by_comparison = {}
        for name, by_q in comparisons[count].items():
            logs = [median([log(ratio) for ratio in by_q[f'q{i:02d}']])
                    for i in range(32)
                    if len(by_q[f'q{i:02d}']) == REPETITIONS]
            bounds = interval(logs, rules['bootstrap']['seed'])
            by_comparison[name] = {
                'valid_q_clusters': len(logs),
                'descriptive_paired_ratio': exp(median(logs)) if logs else None,
                'cluster_bootstrap95': bounds,
                'status': ('qualified_faster' if gate and bounds and bounds[0] > 1
                           else 'qualified_slower' if gate and bounds and bounds[1] < 1
                           else 'unknown_after_tier_gate')}
        phase_keys = ('online_ms', 'target_preparation_ms', 'restart_eval_ms',
                      'reported_retained_bytes')
        if peak_rule:
            phase_keys += ('child_peak_rss_kib',)
        phases = {mode: {key: median([row[key] for row in values])
                         for key in phase_keys}
                  for mode, values in mode_phases[count].items()}
        results[str(count)] = {'tier_gate_passed': gate,
                               'aa_failures': aa_failures[count],
                               'comparison': by_comparison,
                               'median_phase_and_memory': phases}
    return {'schema': 1, 'job_id': root, 'completed_pairs': len(pairs),
            'completed_arms': len(runs), 'structural_issues': structural,
            'invalid_arms': invalid, 'counts': results,
            'raw_archive_sha256': digest(raw_path.read_bytes())}


def main():
    parser = argparse.ArgumentParser()
    for name in ('manifest', 'rules', 'raw', 'bundle-path', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--fixtures', type=Path, default=FIXTURES)
    args = parser.parse_args()
    try:
        result = audit(args.manifest, args.rules, args.raw, args.bundle_path,
                       args.fixtures)
    except Exception as error:
        result = {'status': 'audit_error', 'error_type': type(error).__name__,
                  'error': str(error)}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': result.get('status', 'audited'),
                      'completed_pairs': result.get('completed_pairs'),
                      'gates': {count: value['tier_gate_passed']
                                for count, value in result.get('counts', {}).items()},
                      'structural_issues': len(result.get('structural_issues', []))},
                     sort_keys=True))
    if result.get('status') == 'audit_error':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
