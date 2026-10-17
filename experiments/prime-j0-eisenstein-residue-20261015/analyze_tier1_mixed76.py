#!/usr/bin/env python3
"""Audit the frozen serial mixed-76 Tier 1 panel without dropping failures."""
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
from make_tier1_mixed76_panel import CASES, HERE

AA = ('cal_before', 'cal_mid', 'cal_after')
COMPARE = tuple(case for case in CASES if case not in AA)
MODES = {
    'cal_before': ('openssl_nowarm', 'openssl_nowarm'),
    'compare76_vs_77': ('joint_mixed77', 'joint_mixed76'),
    'compare76_vs_78': ('joint_mixed78', 'joint_mixed76'),
    'compare76_vs_243': ('joint_triple243', 'joint_mixed76'),
    'compare76_vs_81': ('joint_triple81', 'joint_mixed76'),
    'compare76_vs_openssl': ('openssl_nowarm', 'joint_mixed76'),
    'cal_mid': ('openssl_nowarm', 'openssl_nowarm'),
    'cal_after': ('openssl_nowarm', 'openssl_nowarm'),
}


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def interval(ratios: list[float]) -> list[float]:
    assert len(ratios) == 16
    logs = [log(ratio) for ratio in ratios]
    randomizer = random.Random(20261017)
    draws = sorted(exp(statistics.median(logs[randomizer.randrange(16)]
                                         for _ in range(16)))
                   for _ in range(10000))
    return [draws[250], draws[9749]]


def regenerate(manifest: dict, rules: dict, bundle: Path) -> None:
    with TemporaryDirectory(prefix='mixed76-manifest-audit-') as temporary:
        command = [sys.executable, str(HERE / 'make_tier1_mixed76_panel.py'),
                   '--instance-id', rules['instance_id'],
                   '--execution-cpu', str(rules['execution_cpu']),
                   '--binary-sha256', rules['hashes']['binary'],
                   '--libcrypto-sha256', rules['hashes']['libcrypto'],
                   '--libcrypto-path', rules['paths']['libcrypto'],
                   '--bundle-path', str(bundle), '--output-dir', temporary]
        result = subprocess.run(command, text=True, capture_output=True)
        assert result.returncode == 0, result.stdout + result.stderr
        root = Path(temporary)
        expected_manifest = json.loads((root / 'tier1-mixed76-one-cpu-manifest.json').read_text())
        expected_rules = json.loads((root / 'tier1-mixed76-one-cpu-rules.json').read_text())
        assert manifest == expected_manifest, 'manifest differs from frozen generator'
        assert rules == expected_rules, 'rules differ from frozen generator'


def replay_fixture() -> str:
    fixture = json.loads((HERE / 'rho-restart-first128-fixture.json').read_text())
    row = fixture['cases'][0]
    q = tuple(int(word, 16) for word in fixture['q_hex'].split(':'))
    point = add(mul(int(row['a_hex'], 16) % N, G),
                mul(int(row['b_hex'], 16) % N, q))
    assert point is not None
    expected = ':'.join(f'{coordinate:064x}' for coordinate in point)
    assert expected == row['point_hex']
    return expected


def audit(manifest_path: Path, rules_path: Path, raw_path: Path,
          bundle_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    rules = json.loads(rules_path.read_text())
    regenerate(manifest, rules, bundle_path)
    expected_point = replay_fixture()
    assert rules['expected_point_hex'] == expected_point
    assert tuple(case['id'] for case in manifest['cases']) == CASES
    assert rules['case_order'] == list(CASES)
    assert manifest['repetitions'] == rules['repetitions'] == 16
    assert manifest['pair_fields'] == ['count', 'point']
    cases = {case['id']: case for case in manifest['cases']}
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
        expected_pairs = 16 * len(CASES)
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
            rules_path.as_posix(): digest(rules_path.read_bytes()),
        }
        remote_rule = next(path for path in manifest['artifacts']
                           if path.endswith('/tier1-mixed76-one-cpu-rules.json'))
        expected_artifacts[remote_rule] = digest(rules_path.read_bytes())
        expected_artifacts.pop(rules_path.as_posix(), None)
        for path, expected_hash in expected_artifacts.items():
            if artifacts.get(path) != expected_hash:
                structural.append('artifact mismatch: ' + path)
        for path in (manifest['allocation']['receipt'],
                     '/workspace/isolated-bench/panels/host-probe.json'):
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
            if case not in CASES or repeat not in range(16) or variant not in ('reference', 'candidate'):
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
            observations = row.get('tier1_observations', {})
            if 'counter_deltas' not in observations:
                problems.append('missing host counter deltas')
            stdout = read(row['stdout_file'], optional=True) if row.get('stdout_file') else b''
            stderr = read(row['stderr_file'], optional=True) if row.get('stderr_file') else b''
            fields = dict(word.split('=', 1) for word in stdout.decode(errors='replace').split()
                          if '=' in word)
            if fields != row.get('fields'):
                problems.append('stdout fields mismatch')
            if row.get('status') != 'valid' or row.get('issues') or row.get('returncode') != 0 or row.get('timed_out') or stderr:
                problems.append('runner marked arm invalid')
            if case in CASES and variant in ('reference', 'candidate'):
                mode = MODES[case][0 if variant == 'reference' else 1]
                if fields.get('verified') != '1' or fields.get('count') != '1' or fields.get('point') != expected_point or fields.get('mode') != mode:
                    problems.append('incorrect point, count, or mode')
            try:
                online = float(fields['online_ms'])
                assert isfinite(online) and online > 0
                assert abs(online - float(row['online_ms'])) < 0.000001
                if fields.get('mode') == 'openssl_nowarm':
                    assert float(fields['openssl_warmup_ms']) == 0
                else:
                    prep = float(fields['target_preparation_ms'])
                    evaluation = float(fields['restart_eval_ms'])
                    assert prep >= 0 and evaluation >= 0
                    assert abs(online - prep - evaluation) <= 0.00001
                    assert float(fields['graph_plan_ms']) == 0
                    assert int(fields['graph_edges']) + int(fields['direct_seeds']) == int(fields['constructed_q_points'])
            except (KeyError, ValueError, AssertionError):
                problems.append('online phase accounting failed')
            if problems:
                invalid_arms.append({'serial': serial, 'case': case,
                                     'repeat': repeat, 'variant': variant,
                                     'problems': problems,
                                     'stderr_sha256': digest(stderr)})
            if case in CASES and repeat in range(16) and variant in ('reference', 'candidate'):
                arm_valid[(repeat, case, variant)] = not problems
        pair_lookup = {}
        for position, pair in enumerate(pairs):
            key = (pair.get('repeat'), pair.get('case'))
            if key in pair_lookup:
                structural.append('duplicate pair')
            pair_lookup[key] = pair
            if position < expected_pairs:
                expected_key = (position // len(CASES), CASES[position % len(CASES)])
                if key != expected_key:
                    structural.append('pair order mismatch')
        if len(pairs) > expected_pairs:
            structural.append('extra pairs')
        aa_failures = []
        comparisons = {case: [] for case in COMPARE}
        ordered_serials = []
        for repeat in range(16):
            for index, case in enumerate(CASES):
                pair = pair_lookup.get((repeat, case))
                reference = lookup.get((repeat, case, 'reference'))
                candidate = lookup.get((repeat, case, 'candidate'))
                first = 'reference' if (repeat + index) % 2 == 0 else 'candidate'
                second = 'candidate' if first == 'reference' else 'reference'
                arms = {'reference': reference, 'candidate': candidate}
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
                    ratio = float(reference['fields']['online_ms']) / float(candidate['fields']['online_ms'])
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
                    comparisons[case].append(ratio)
        if ordered_serials != list(range(1, len(runs) + 1)):
            structural.append('arm execution order mismatch')
    tier_gate = (preflight.get('ok') and summary.get('status') == 'completed'
                 and summary.get('artifacts_stable') and not structural
                 and not invalid_arms and not aa_failures
                 and len(runs) == 2 * expected_pairs
                 and len(pairs) == expected_pairs)
    results = {}
    for case, ratios in comparisons.items():
        bounds = interval(ratios) if len(ratios) == 16 else None
        if tier_gate and bounds and bounds[0] > 1:
            status = 'qualified_faster'
        elif tier_gate and bounds and bounds[1] < 1:
            status = 'qualified_slower'
        else:
            status = 'unknown_after_tier_gate'
        results[case] = {
            'valid_pairs': len(ratios),
            'descriptive_reference_over_candidate_median':
                statistics.median(ratios) if ratios else None,
            'paired_bootstrap95_by_repeat': bounds,
            'aggregate_status': status,
            'qualified_ratio': statistics.median(ratios)
                               if status.startswith('qualified_') else None,
        }
    return {'schema': 1, 'job_id': job, 'measurement_tier': 'tier1_instance',
            'frozen_point_independently_replayed': expected_point,
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
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = audit(args.manifest, args.rules, args.raw, args.bundle_path)
    except Exception as error:
        receipt = {'schema': 1, 'status': 'audit_error',
                   'error_type': type(error).__name__, 'error': str(error),
                   'raw_archive_sha256': digest(args.raw.read_bytes())}
    args.output.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps(receipt, sort_keys=True, indent=2))
    if receipt.get('status') == 'audit_error':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
