#!/usr/bin/env python3
"""Freeze the narrow, multiple-Q one-restart Tier 1 bake-off."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import tarfile

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / 'rho-closeout-fixtures'
REMOTE_ROOT = Path('/workspace/bench-sources/rho-closeout')
REMOTE_PANELS = Path('/workspace/isolated-bench/panels')
REPETITIONS = 16


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--instance-id', required=True)
    parser.add_argument('--binary-sha256', required=True)
    parser.add_argument('--bundle-path', type=Path, required=True)
    parser.add_argument('--fixtures', type=Path, default=FIXTURES)
    parser.add_argument('--libcrypto-sha256', required=True)
    parser.add_argument('--libcrypto-path', type=Path,
                        default=Path('/usr/lib/x86_64-linux-gnu/libcrypto.so.3'))
    parser.add_argument('--execution-cpu', type=int, required=True)
    parser.add_argument('--remote-root', type=Path, default=REMOTE_ROOT)
    parser.add_argument('--remote-panels', type=Path, default=REMOTE_PANELS)
    parser.add_argument('--provider', choices=('runpod', 'aws_ec2'), default='runpod')
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    assert re.fullmatch(r'[a-z0-9-]+', args.instance_id)
    for value in (args.binary_sha256, args.libcrypto_sha256):
        assert re.fullmatch(r'[0-9a-f]{64}', value)
    assert args.execution_cpu >= 0
    verification = json.loads((args.fixtures / 'full-verification.json').read_text())
    fixture_manifest = json.loads((args.fixtures / 'manifest.json').read_text())
    assert verification['scope'] == 'all_rows' and verification['status'] == 'pass'
    assert verification['rows_verified'] == 4096
    assert verification['manifest_sha256'] == digest(args.fixtures / 'manifest.json')
    assert len(fixture_manifest['fixtures']) == 32
    from build_rho_closeout_bundle import MIXED76_SHA256
    with tarfile.open(args.bundle_path, 'r:gz') as archive:
        source_manifest_bytes = archive.extractfile('source-manifest.json').read()
    source_manifest = json.loads(source_manifest_bytes)
    assert source_manifest['parent_bundle_sha256'] == MIXED76_SHA256
    assert source_manifest['fixture_manifest_sha256'] == digest(args.fixtures / 'manifest.json')
    for entry in fixture_manifest['fixtures']:
        assert digest(args.fixtures / entry['path']) == entry['sha256']
        name = 'fixtures/rho-closeout/' + entry['path']
        assert source_manifest['source_sha256'][name] == entry['sha256']
    binary = args.remote_root / 'target/release/eisenstein_fixed'
    bundle = args.remote_panels / 'rho-closeout-source-20261017.tar.gz'
    commands = {}
    for entry in fixture_manifest['fixtures']:
        qi = entry['path'][:3]
        fixture = args.remote_root / 'fixtures/rho-closeout' / entry['path']
        commands[qi] = {
            'openssl': [str(binary), '--pilot-rho-restart',
                        'openssl_globalwarm', str(fixture), '1'],
            'radix81': [str(binary), '--pilot-rho-restart-joint-triple81',
                        str(fixture), '1'],
            'mixed76': [str(binary), '--pilot-rho-restart-joint-mixed76',
                        str(fixture), '1'],
        }
    cases = []
    case_targets = {}

    def append_case(case_id: str, qi: str, reference: str, candidate: str) -> None:
        entry = fixture_manifest['fixtures'][int(qi[1:])]
        assert entry['path'].startswith(qi)
        cases.append({'id': case_id,
                      'reference': commands[qi][reference],
                      'candidate': commands[qi][candidate],
                      'expected_fields': {'count': '1'},
                      'expected_result': entry['first_point_hex']})
        case_targets[case_id] = {'fixture': entry['path'],
                                 'fixture_sha256': entry['sha256'],
                                 'q_hex': entry['q_hex'],
                                 'reference': reference, 'candidate': candidate}

    append_case('cal_before', 'q00', 'openssl', 'openssl')
    for index in range(32):
        if index == 16:
            append_case('cal_mid', 'q16', 'openssl', 'openssl')
        qi = f'q{index:02d}'
        comparisons = [('openssl_vs_81', 'openssl', 'radix81'),
                       ('81_vs_76', 'radix81', 'mixed76'),
                       ('openssl_vs_76', 'openssl', 'mixed76')]
        comparisons = comparisons[index % 3:] + comparisons[:index % 3]
        for suffix, reference, candidate in comparisons:
            append_case(qi + '_' + suffix, qi, reference, candidate)
    append_case('cal_after', 'q31', 'openssl', 'openssl')
    assert len(cases) == 99
    boundary = ('One supplied public Q and one frozen (a,b) pair per case. '
        'Fixture loading, Q-independent curve/group initialization, '
        'generator-only OpenSSL warmup, reusable G-table preparation, and '
        'scalar-plan compilation are outside online time. OpenSSL globalwarm '
        'times Q point setup, first target EC_POINT_mul, and affine output. '
        'Joint radix-81 and mixed-76 time Q-table construction, Horner '
        'evaluation, and affine output. Each arm verifies the same point.')
    source_paths = {name: str(args.remote_root / name)
                    for name in sorted(source_manifest['source_sha256'])}
    paths = {'binary': str(binary), 'libcrypto': str(args.libcrypto_path),
             'bundle': str(bundle),
             'source_manifest': str(args.remote_root / 'source-manifest.json'),
             'fixture_manifest': str(args.remote_root /
                 'fixtures/rho-closeout/manifest.json')}
    hashes = {'binary': args.binary_sha256,
              'libcrypto': args.libcrypto_sha256,
              'bundle': digest(args.bundle_path),
              'source_manifest': sha256(source_manifest_bytes).hexdigest(),
              'source_files': source_manifest['source_sha256'],
              'fixture_manifest': digest(args.fixtures / 'manifest.json')}
    rules = {'schema': 1, 'purpose': 'rho-closeout-one-restart',
             'tier': 'tier1_instance', 'instance_id': args.instance_id,
             'execution_cpu': args.execution_cpu,
             'repetitions': REPETITIONS, 'q_count': 32,
             'case_order': [case['id'] for case in cases],
             'case_targets': case_targets, 'aa_acceptance': [0.90, 1.11],
             'bootstrap': {'seed': 20261017, 'draws': 10000,
                           'cluster': 'Q point',
                           'within_cluster': 'median log(reference/candidate) over 16 pairs',
                           'across_clusters': 'median of 32 cluster medians',
                           'interval_indices': [250, 9749]},
             'primary_comparisons': ['openssl_vs_81', '81_vs_76'],
             'secondary_comparisons': ['openssl_vs_76'],
             'comparison_acceptance': ('All exact same-point pairs and three '
                 'bracketing OpenSSL A/A controls per repetition pass; '
                 'cluster bootstrap by Q gives a 95% paired log-ratio '
                 'interval excluding one.'),
             'timing_boundary': boundary, 'paths': paths,
             'source_paths': source_paths, 'hashes': hashes}
    rule_path = args.remote_panels / 'tier1-rho-closeout-one-rules.json'
    manifest = {'schema': 1, 'measurement_tier': 'tier1_instance',
                'allocation': {'provider': args.provider,
                               'instance_id': args.instance_id,
                               'receipt': str(args.remote_panels / 'allocation.json')},
                'isolation': {'cpus': str(args.execution_cpu),
                              'execution_cpu': args.execution_cpu},
                'workdir': str(args.remote_root), 'repetitions': REPETITIONS,
                'outer_repeats': 1, 'timeout_s': 30,
                'measurement_boundary': boundary,
                'pair_fields': ['count', 'point'],
                'comparison_variant': 'rho-closeout-one-restart',
                'cases': cases,
                'artifacts': list(dict.fromkeys([
                    str(args.remote_panels / 'allocation.json'),
                    str(args.remote_panels / 'host-probe.json'),
                    *paths.values(), *source_paths.values(),
                    str(rule_path)]))}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write(args.output_dir / rule_path.name, rules)
    write(args.output_dir / 'tier1-rho-closeout-one-manifest.json', manifest)
    print(json.dumps({'q_count': 32, 'cases': len(cases),
                      'pairs': REPETITIONS * len(cases),
                      'bundle_sha256': hashes['bundle']}, sort_keys=True))


if __name__ == '__main__':
    main()
