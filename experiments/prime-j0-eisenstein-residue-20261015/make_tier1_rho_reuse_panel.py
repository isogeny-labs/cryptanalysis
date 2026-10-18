#!/usr/bin/env python3
"""Freeze the separate 1/8/32/128-restart, 32-Q rho reuse panel."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from make_tier1_rho_closeout_panel import FIXTURES

COUNTS = (1, 8, 32, 128)
REPETITIONS = 8
RULE_NAME = 'tier1-rho-closeout-reuse-rules.json'
MANIFEST_NAME = 'tier1-rho-closeout-reuse-manifest.json'
REMOTE_RULE = '/workspace/isolated-bench/panels/' + RULE_NAME


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    parser = argparse.ArgumentParser()
    for name in ('instance-id', 'binary-sha256', 'bundle-path',
                 'libcrypto-sha256', 'execution-cpu', 'output-dir'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--libcrypto-path',
                        default='/usr/lib/x86_64-linux-gnu/libcrypto.so.3')
    args = parser.parse_args()
    with TemporaryDirectory(prefix='rho-reuse-base-') as temporary:
        base = [sys.executable, str(Path(__file__).with_name(
            'make_tier1_rho_closeout_panel.py')),
            '--instance-id', args.instance_id, '--binary-sha256', args.binary_sha256,
            '--bundle-path', args.bundle_path,
            '--libcrypto-sha256', args.libcrypto_sha256,
            '--libcrypto-path', args.libcrypto_path,
            '--execution-cpu', args.execution_cpu, '--output-dir', temporary]
        subprocess.run(base, check=True, capture_output=True)
        root = Path(temporary)
        manifest = json.loads((root / 'tier1-rho-closeout-one-manifest.json').read_text())
        rules = json.loads((root / 'tier1-rho-closeout-one-rules.json').read_text())
    fixture_manifest = json.loads((FIXTURES / 'manifest.json').read_text())
    binary = rules['paths']['binary']
    cases = []
    targets = {}
    for count in COUNTS:
        for index in range(32):
            qi = f'q{index:02d}'
            entry = fixture_manifest['fixtures'][index]
            fixture = FIXTURES / entry['path']
            value = json.loads(fixture.read_text())
            expected = value['cases'][count - 1]['point_hex']
            remote_fixture = '/workspace/bench-sources/rho-closeout/fixtures/rho-closeout/' + entry['path']
            commands = {
                'openssl': [binary, '--pilot-rho-restart', 'openssl_globalwarm',
                            remote_fixture, str(count)],
                'radix81': [binary, '--pilot-rho-restart-joint-triple81',
                            remote_fixture, str(count)],
                'mixed76': [binary, '--pilot-rho-restart-joint-mixed76',
                            remote_fixture, str(count)]}
            comparisons = [('openssl_vs_81', 'openssl', 'radix81'),
                           ('81_vs_76', 'radix81', 'mixed76'),
                           ('openssl_vs_76', 'openssl', 'mixed76')]
            if index == 0:
                comparisons.insert(0, ('cal_before', 'openssl', 'openssl'))
            if index == 16:
                comparisons.insert(0, ('cal_mid', 'openssl', 'openssl'))
            if index == 31:
                comparisons.append(('cal_after', 'openssl', 'openssl'))
            for suffix, reference, candidate in comparisons:
                case_id = f'n{count:03d}_{qi}_{suffix}'
                cases.append({'id': case_id, 'reference': commands[reference],
                              'candidate': commands[candidate],
                              'expected_fields': {'count': str(count)},
                              'expected_result': expected})
                targets[case_id] = {
                    'fixture': entry['path'], 'fixture_sha256': entry['sha256'],
                    'q_hex': entry['q_hex'], 'count': count,
                    'reference': reference, 'candidate': candidate}
    assert len(cases) == 396
    boundary = ('One supplied public Q and the first N frozen (a,b) pairs '
                'per case, N in {1,8,32,128}. The timed interval charges '
                'target-Q table construction, all N restart evaluations, '
                'and affine output. Generator preparation and scalar-plan '
                'compilation are Q-independent and outside the interval.')
    rules.update({'purpose': 'rho-closeout-reuse', 'repetitions': REPETITIONS,
                  'counts': list(COUNTS), 'case_order': [c['id'] for c in cases],
                  'case_targets': targets, 'timing_boundary': boundary,
                  'comparison_acceptance': ('Report phase and memory medians '
                      'by count and Q. Each count has three bracketing A/A '
                      'controls per repetition. A failed A/A keeps that count '
                      'exploratory; no count may replace the one-restart gate.'),
                  'bootstrap': {'seed': 20261018, 'draws': 10000,
                                'cluster': 'Q point',
                                'within_cluster': 'median log ratio over 8 pairs',
                                'across_clusters': 'median of 32 cluster medians',
                                'interval_indices': [250, 9749]}})
    manifest.update({'repetitions': REPETITIONS, 'cases': cases,
                     'comparison_variant': 'rho-closeout-reuse',
                     'measurement_boundary': boundary,
                     'artifacts': [REMOTE_RULE if x.endswith(
                         'tier1-rho-closeout-one-rules.json') else x
                                   for x in manifest['artifacts']]})
    assert manifest['artifacts'][-1] == REMOTE_RULE
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write(output / MANIFEST_NAME, manifest)
    write(output / RULE_NAME, rules)
    print(json.dumps({'counts': list(COUNTS), 'cases': len(cases),
                      'pairs': len(cases) * REPETITIONS}))


if __name__ == '__main__':
    main()
