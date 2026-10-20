#!/usr/bin/env python3
"""Independent, fail-closed audit of the multiple-Q Tier 1 closeout panel."""

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

from check_secp256k1_tau_generator import G, N, add, mul
from make_tier1_rho_closeout_panel import HERE, FIXTURES, REPETITIONS

AA = {'cal_before', 'cal_mid', 'cal_after'}
MODES = {'openssl': 'openssl_globalwarm', 'radix81': 'joint_triple81',
         'mixed76': 'joint_mixed76'}
COMPARISONS = ('openssl_vs_81', '81_vs_76', 'openssl_vs_76')


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def regenerate(manifest: dict, rules: dict, bundle: Path,
               fixtures: Path) -> None:
    with TemporaryDirectory(prefix='rho-closeout-audit-') as temporary:
        command = [sys.executable, str(HERE / 'make_tier1_rho_closeout_panel.py'),
                   '--instance-id', rules['instance_id'],
                   '--execution-cpu', str(rules['execution_cpu']),
                   '--binary-sha256', rules['hashes']['binary'],
                   '--libcrypto-sha256', rules['hashes']['libcrypto'],
                   '--libcrypto-path', rules['paths']['libcrypto'],
                   '--remote-root', str(Path(rules['paths']['binary']).parents[2]),
                   '--remote-panels', str(Path(rules['paths']['bundle']).parent),
                   '--provider', manifest['allocation']['provider'],
                   '--bundle-path', str(bundle), '--output-dir', temporary,
                   '--fixtures', str(fixtures)]
        result = subprocess.run(command, text=True, capture_output=True)
        assert result.returncode == 0, result.stdout + result.stderr
        root = Path(temporary)
        assert manifest == json.loads((root / 'tier1-rho-closeout-one-manifest.json').read_text())
        assert rules == json.loads((root / 'tier1-rho-closeout-one-rules.json').read_text())


def replay_first_points(rules: dict, fixtures: Path) -> None:
    receipt = json.loads((fixtures / 'full-verification.json').read_text())
    assert receipt['status'] == 'pass' and receipt['scope'] == 'all_rows'
    assert receipt['rows_verified'] == 4096
    assert receipt['manifest_sha256'] == rules['hashes']['fixture_manifest']
    fixture_manifest = json.loads((fixtures / 'manifest.json').read_text())
    assert len(fixture_manifest['fixtures']) == 32
    for entry in fixture_manifest['fixtures']:
        path = fixtures / entry['path']
        assert digest(path.read_bytes()) == entry['sha256']
        fixture = json.loads(path.read_text())
        q = tuple(int(word, 16) for word in fixture['q_hex'].split(':'))
        assert mul(int(entry['q_scalar_hex'], 16), G) == q
        row = fixture['cases'][0]
        point = add(mul(int(row['a_hex'], 16) % N, G),
                    mul(int(row['b_hex'], 16) % N, q))
        assert point is not None
        expected = ':'.join(f'{coordinate:064x}' for coordinate in point)
        assert expected == row['point_hex'] == entry['first_point_hex']


def interval(cluster_logs: list[float], rules: dict) -> list[float] | None:
    if len(cluster_logs) != 32:
        return None
    plan = rules['bootstrap']
    assert plan['cluster'] == 'Q point'
    assert plan['draws'] == 10000
    randomizer = random.Random(plan['seed'])
    draws = sorted(exp(statistics.median(cluster_logs[randomizer.randrange(32)]
                                          for _ in range(32)))
                   for _ in range(plan['draws']))
    low, high = plan['interval_indices']
    return [draws[low], draws[high]]


def audit(manifest_path: Path, rules_path: Path, raw_path: Path,
          bundle_path: Path, fixtures: Path = FIXTURES) -> dict:
    manifest = json.loads(manifest_path.read_text())
    rules = json.loads(rules_path.read_text())
    regenerate(manifest, rules, bundle_path, fixtures)
    replay_first_points(rules, fixtures)
    case_order = rules['case_order']
    cases = {case['id']: case for case in manifest['cases']}
    assert len(case_order) == len(cases) == 99
    assert list(cases) == case_order
    assert rules['repetitions'] == manifest['repetitions'] == REPETITIONS
    expected_pairs = REPETITIONS * len(cases)
    with tarfile.open(raw_path, 'r:*') as archive:
        roots = {name.split('/')[0] for name in archive.getnames()}
        assert len(roots) == 1
        job = roots.pop()
        assert all(name == job or name.startswith(job + '/')
                   for name in archive.getnames())

        def read(name: str, optional: bool = False) -> bytes:
            try:
                member = archive.extractfile(job + '/' + name)
            except KeyError:
                if optional:
                    return b''
                raise
            if member is None:
                if optional:
                    return b''
                raise ValueError('missing raw member ' + name)
            return member.read()

        assert json.loads(read('manifest.json')) == manifest
        preflight = json.loads(read('preflight.json'))
        summary = json.loads(read('summary.json'))
        runs_bytes = read('runs.jsonl', optional=True)
        pairs_bytes = read('pairs.jsonl', optional=True)
        runs = [json.loads(line) for line in runs_bytes.splitlines()]
        pairs = [json.loads(line) for line in pairs_bytes.splitlines()]
        structural = []
        if summary.get('expected_pairs') != expected_pairs:
            structural.append('expected_pairs mismatch')
        if summary.get('manifest_sha256') != digest(read('manifest.json')):
            structural.append('manifest digest mismatch')
        if summary.get('measurement_tier') != 'tier1_instance':
            structural.append('summary tier mismatch')
        if preflight.get('evidence', {}).get('measurement_tier') != 'tier1_instance':
            structural.append('preflight tier mismatch')
        if preflight.get('evidence', {}).get('allocation', {}).get('instance_id') != rules['instance_id']:
            structural.append('preflight instance mismatch')
        artifacts = summary.get('artifact_sha256', {})
        expected_artifacts = {
            **{path: rules['hashes'][key] for key, path in rules['paths'].items()},
            **{path: rules['hashes']['source_files'][name]
               for name, path in rules['source_paths'].items()},
            manifest['artifacts'][-1]: digest(rules_path.read_bytes()),
        }
        for path, expected_hash in expected_artifacts.items():
            if artifacts.get(path) != expected_hash:
                structural.append('artifact mismatch: ' + path)
        for path in (manifest['allocation']['receipt'],
                     str(Path(rules['paths']['bundle']).parent / 'host-probe.json')):
            if path not in artifacts:
                structural.append('missing host artifact: ' + path)
        lookup = {}
        arm_valid = {}
        invalid_arms = []
        for serial, row in enumerate(runs, 1):
            problems = []
            if row.get('serial') != serial:
                problems.append('serial mismatch')
            case = row.get('case')
            repeat = row.get('repeat')
            variant = row.get('variant')
            if case not in cases or repeat not in range(REPETITIONS) or variant not in ('reference', 'candidate'):
                problems.append('invalid case/repeat/variant')
            else:
                key = (repeat, case, variant)
                if key in lookup:
                    problems.append('duplicate arm')
                lookup[key] = row
                if row.get('command') != cases[case][variant]:
                    problems.append('command mismatch')
                if row.get('binary_sha256') != rules['hashes']['binary']:
                    problems.append('binary hash mismatch')
            if row.get('measurement_tier') != 'tier1_instance':
                problems.append('tier mismatch')
            postflight = row.get('postflight', {})
            if not postflight.get('ok') or postflight.get('evidence', {}).get('allocation', {}).get('instance_id') != rules['instance_id']:
                problems.append('postflight failed')
            if 'counter_deltas' not in row.get('tier1_observations', {}):
                problems.append('missing host counter deltas')
            stdout = read(row['stdout_file'], optional=True) if row.get('stdout_file') else b''
            stderr = read(row['stderr_file'], optional=True) if row.get('stderr_file') else b''
            fields = dict(word.split('=', 1) for word in stdout.decode(errors='replace').split()
                          if '=' in word)
            if fields != row.get('fields'):
                problems.append('stdout fields mismatch')
            if row.get('status') != 'valid' or row.get('issues') or row.get('returncode') != 0 or row.get('timed_out') or stderr:
                problems.append('runner marked arm invalid')
            if case in cases and variant in ('reference', 'candidate'):
                target = rules['case_targets'][case]
                mode = MODES[target[variant]]
                if (fields.get('verified') != '1' or fields.get('count') != '1'
                    or fields.get('point') != cases[case]['expected_result']
                    or fields.get('mode') != mode):
                    problems.append('incorrect point, count, or mode')
            try:
                online = float(fields['online_ms'])
                prep = float(fields['target_preparation_ms'])
                evaluation = float(fields['restart_eval_ms'])
                assert isfinite(online) and online > 0
                assert prep >= 0 and evaluation >= 0
                assert abs(online - prep - evaluation) <= 0.00001
                assert abs(online - float(row['online_ms'])) < 0.000001
                if fields.get('mode') == 'openssl_globalwarm':
                    assert float(fields['openssl_warmup_ms']) > 0
                else:
                    assert float(fields['graph_plan_ms']) == 0
                    assert int(fields['graph_edges']) + int(fields['direct_seeds']) == int(fields['constructed_q_points'])
            except (KeyError, ValueError, AssertionError):
                problems.append('online phase accounting failed')
            if problems:
                invalid_arms.append({'serial': serial, 'case': case,
                                     'repeat': repeat, 'variant': variant,
                                     'problems': problems,
                                     'stderr_sha256': digest(stderr)})
            if case in cases and repeat in range(REPETITIONS) and variant in ('reference', 'candidate'):
                arm_valid[(repeat, case, variant)] = not problems
        pair_lookup = {}
        for position, pair in enumerate(pairs):
            key = (pair.get('repeat'), pair.get('case'))
            if key in pair_lookup:
                structural.append('duplicate pair')
            pair_lookup[key] = pair
            if position < expected_pairs:
                expected_key = (position // len(case_order), case_order[position % len(case_order)])
                if key != expected_key:
                    structural.append('pair order mismatch')
        if len(pairs) > expected_pairs:
            structural.append('extra pairs')
        aa_failures = []
        comparisons = {name: {f'q{i:02d}': [] for i in range(32)}
                       for name in COMPARISONS}
        ordered_serials = []
        for repeat in range(REPETITIONS):
            for position, case in enumerate(case_order):
                pair = pair_lookup.get((repeat, case))
                reference = lookup.get((repeat, case, 'reference'))
                candidate = lookup.get((repeat, case, 'candidate'))
                arms = {'reference': reference, 'candidate': candidate}
                first = 'reference' if (repeat + position) % 2 == 0 else 'candidate'
                second = 'candidate' if first == 'reference' else 'reference'
                ordered_serials.extend(arms[variant]['serial'] for variant in (first, second)
                                       if arms[variant] is not None)
                if pair is None:
                    if case in AA:
                        aa_failures.append({'repeat': repeat, 'case': case,
                                            'reason': 'missing pair'})
                    continue
                serials = {variant: arm['serial'] for variant, arm in arms.items()
                           if arm is not None}
                if pair.get('run_serials') != serials:
                    structural.append('pair serial mismatch')
                ratio = None
                try:
                    ratio = (float(reference['fields']['online_ms']) /
                             float(candidate['fields']['online_ms']))
                    assert isfinite(ratio) and ratio > 0
                except (TypeError, KeyError, ValueError, ZeroDivisionError, AssertionError):
                    pass
                valid = (pair.get('status') == 'valid' and not pair.get('issues')
                         and ratio is not None and reference is not None
                         and candidate is not None
                         and arm_valid.get((repeat, case, 'reference'), False)
                         and arm_valid.get((repeat, case, 'candidate'), False))
                if valid:
                    try:
                        assert abs(float(pair['speedup']) - ratio) <= 0.000001
                    except (KeyError, TypeError, ValueError, AssertionError):
                        structural.append('pair ratio mismatch')
                        valid = False
                if case in AA:
                    low, high = rules['aa_acceptance']
                    if not valid or not low <= ratio <= high:
                        aa_failures.append({'repeat': repeat, 'case': case,
                                            'ratio': ratio, 'status': pair.get('status')})
                elif valid:
                    q, suffix = case.split('_', 1)
                    comparisons[suffix][q].append(ratio)
        if ordered_serials != list(range(1, len(runs) + 1)):
            structural.append('arm execution order mismatch')
    tier_gate = (preflight.get('ok') and summary.get('status') == 'completed'
                 and summary.get('artifacts_stable') and not structural
                 and not invalid_arms and not aa_failures
                 and len(runs) == 2 * expected_pairs
                 and len(pairs) == expected_pairs)
    results = {}
    for name, by_q in comparisons.items():
        clusters = {q: statistics.median(log(ratio) for ratio in ratios)
                    for q, ratios in by_q.items() if len(ratios) == REPETITIONS}
        values = list(clusters.values())
        bounds = interval(values, rules)
        median = exp(statistics.median(values)) if values else None
        primary = name in rules['primary_comparisons']
        if tier_gate and bounds and bounds[0] > 1:
            status = 'qualified_faster' if primary else 'secondary_faster'
        elif tier_gate and bounds and bounds[1] < 1:
            status = 'qualified_slower' if primary else 'secondary_slower'
        else:
            status = 'unknown_after_tier_gate'
        results[name] = {'valid_q_clusters': len(clusters),
                         'valid_pairs': sum(len(ratios) for ratios in by_q.values()),
                         'descriptive_paired_ratio': median,
                         'cluster_bootstrap95': bounds,
                         'aggregate_status': status,
                         'primary': primary,
                         'per_q_median_ratio': {q: exp(value) for q, value in clusters.items()}}
    return {'schema': 1, 'job_id': job, 'measurement_tier': 'tier1_instance',
            'runner_status': summary.get('status'),
            'artifacts_stable': summary.get('artifacts_stable'),
            'completed_arms': len(runs), 'completed_pairs': len(pairs),
            'structural_issues': structural, 'invalid_arms': invalid_arms,
            'aa_failures': aa_failures, 'tier_gate_passed': bool(tier_gate),
            'comparison': results, 'raw_archive_sha256': digest(raw_path.read_bytes()),
            'manifest_sha256': digest(manifest_path.read_bytes()),
            'rules_sha256': digest(rules_path.read_bytes()),
            'runs_sha256': digest(runs_bytes), 'pairs_sha256': digest(pairs_bytes)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--rules', type=Path, required=True)
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--bundle-path', type=Path, required=True)
    parser.add_argument('--fixtures', type=Path, default=FIXTURES)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = audit(args.manifest, args.rules, args.raw, args.bundle_path,
                        args.fixtures)
    except Exception as error:
        receipt = {'schema': 1, 'status': 'audit_error',
                   'error_type': type(error).__name__, 'error': str(error),
                   'raw_archive_sha256': digest(args.raw.read_bytes())}
    args.output.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': receipt.get('status', 'audited'),
                      'tier_gate_passed': receipt.get('tier_gate_passed'),
                      'completed_pairs': receipt.get('completed_pairs'),
                      'aa_failures': len(receipt.get('aa_failures', []))},
                     sort_keys=True))
    if receipt.get('status') == 'audit_error':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
