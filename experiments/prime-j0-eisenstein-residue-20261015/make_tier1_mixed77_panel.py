#!/usr/bin/env python3
"""Freeze one-target serial Tier 1 pairs for the portable mixed-77 binary."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import tarfile

HERE = Path(__file__).resolve().parent
RECEIPT = HERE / 'triple-mixed77-portable-replay.json'
FIXTURE = HERE / 'rho-restart-first128-fixture.json'
REMOTE_ROOT = Path('/workspace/bench-sources/mixed77-portable')
REMOTE_PANELS = Path('/workspace/isolated-bench/panels')
CASES = ('cal_before', 'compare77_vs_78', 'compare77_vs_243',
         'compare77_vs_81', 'compare77_vs_openssl', 'cal_mid', 'cal_after')


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--instance-id', required=True)
    parser.add_argument('--binary-sha256', required=True)
    parser.add_argument('--bundle-path', type=Path, required=True)
    parser.add_argument('--libcrypto-sha256', required=True)
    parser.add_argument('--libcrypto-path', type=Path,
                        default=Path('/usr/lib/x86_64-linux-gnu/libcrypto.so.3'))
    parser.add_argument('--execution-cpu', type=int, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    assert re.fullmatch(r'[a-z0-9]+', args.instance_id)
    for value in (args.binary_sha256, args.libcrypto_sha256):
        assert re.fullmatch(r'[0-9a-f]{64}', value)
    assert args.execution_cpu >= 0
    source = json.loads(RECEIPT.read_text())
    assert source['status'] == 'portable_exact_output_replay_passed'
    assert source['mixed77_exact_outputs'] == 257
    assert source['control_exact_outputs'] == 4
    assert source['atlas_include_bytes_count'] == 0
    assert source['bundle_sha256'] == (
        '0598b16fb66efda38515bc2a3685c9ff38b3c2e797ca66d7e7c0a2451e0a998c')
    assert digest(args.bundle_path) == source['bundle_sha256']
    with tarfile.open(args.bundle_path, 'r:gz') as archive:
        manifest_bytes = archive.extractfile('source-manifest.json').read()
    source_manifest = json.loads(manifest_bytes)
    assert source_manifest['source_sha256'] == source['source_sha256']
    fixture = json.loads(FIXTURE.read_text())
    expected = fixture['cases'][0]['point_hex']
    binary = REMOTE_ROOT / 'target/release/eisenstein_fixed'
    fixture_remote = REMOTE_ROOT / 'fixtures/rho-restart-first128-fixture.json'
    bundle = REMOTE_PANELS / 'mixed77-portable-source-20261017.tar.gz'
    commands = {
        'openssl': [str(binary), '--pilot-rho-restart', 'openssl_nowarm',
                    str(fixture_remote), '1'],
        'radix81': [str(binary), '--pilot-rho-restart-joint-triple81',
                    str(fixture_remote), '1'],
        'radix243': [str(binary), '--pilot-rho-restart-joint-triple243',
                     str(fixture_remote), '1'],
        'mixed78': [str(binary), '--pilot-rho-restart-joint-mixed78',
                    str(fixture_remote), '1'],
        'mixed77': [str(binary), '--pilot-rho-restart-joint-mixed77',
                    str(fixture_remote), '1'],
    }
    references = {
        'cal_before': 'openssl', 'compare77_vs_78': 'mixed78',
        'compare77_vs_243': 'radix243', 'compare77_vs_81': 'radix81',
        'compare77_vs_openssl': 'openssl', 'cal_mid': 'openssl',
        'cal_after': 'openssl',
    }
    cases = [{'id': case, 'reference': commands[references[case]],
              'candidate': commands['openssl' if case.startswith('cal_')
                                    else 'mixed77'],
              'expected_fields': {'count': '1'},
              'expected_result': expected} for case in CASES]
    assert tuple(case['id'] for case in cases) == CASES
    assert all(case['reference'][-1] == '1' and case['candidate'][-1] == '1'
               for case in cases)
    boundary = ('One previously supplied Q and one frozen scalar pair. '
                'Process launch and fixture loading are outside both online '
                'intervals. OpenSSL nowarm times first EC_POINT_mul and affine '
                'output; joint paths time target Q-table construction, Horner '
                'evaluation, and affine output, excluding reusable G setup '
                'and Q-independent plan compilation. Every arm independently '
                'checks the same expected point.')
    paths = {'binary': str(binary), 'libcrypto': str(args.libcrypto_path),
             'bundle': str(bundle), 'fixture': str(fixture_remote),
             'source_manifest': str(REMOTE_ROOT / 'source-manifest.json')}
    source_paths = {name: str(REMOTE_ROOT / name)
                    for name in sorted(source['source_sha256'])}
    hashes = {'binary': args.binary_sha256,
              'libcrypto': args.libcrypto_sha256,
              'bundle': source['bundle_sha256'], 'fixture': digest(FIXTURE),
              'source_manifest': sha256(manifest_bytes).hexdigest(),
              'source_files': source['source_sha256']}
    rules = {'schema': 1, 'purpose': 'mixed77-one-target-online',
             'tier': 'tier1_instance', 'instance_id': args.instance_id,
             'execution_cpu': args.execution_cpu, 'repetitions': 16,
             'expected_count': 1, 'expected_point_hex': expected,
             'q_hex': fixture['q_hex'], 'case_order': list(CASES),
             'aa_acceptance': [0.90, 1.11],
             'comparison_acceptance': ('all 16 same-point pairs valid; three '
                'bracketing OpenSSL A/A controls within [0.90,1.11]; paired '
                'bootstrap 95% log-ratio interval excludes one'),
             'timing_boundary': boundary, 'paths': paths,
             'source_paths': source_paths, 'hashes': hashes}
    rule_path = REMOTE_PANELS / 'tier1-mixed77-one-cpu-rules.json'
    manifest = {
        'schema': 1, 'measurement_tier': 'tier1_instance',
        'allocation': {'provider': 'runpod', 'instance_id': args.instance_id,
                       'receipt': str(REMOTE_PANELS / 'allocation.json')},
        'isolation': {'cpus': str(args.execution_cpu),
                      'execution_cpu': args.execution_cpu},
        'workdir': str(REMOTE_ROOT), 'repetitions': 16,
        'outer_repeats': 1, 'timeout_s': 30,
        'measurement_boundary': boundary,
        'pair_fields': ['count', 'point'],
        'comparison_variant': 'mixed77-one-target-online',
        'cases': cases,
        'artifacts': [str(REMOTE_PANELS / 'allocation.json'),
                      str(REMOTE_PANELS / 'host-probe.json'),
                      *paths.values(), *source_paths.values(), str(rule_path)],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write(args.output_dir / rule_path.name, rules)
    write(args.output_dir / 'tier1-mixed77-one-cpu-manifest.json', manifest)
    print(json.dumps({'cases': list(CASES), 'pairs': 16 * len(CASES),
                      'bundle_sha256': source['bundle_sha256']}, sort_keys=True))


if __name__ == '__main__':
    main()
