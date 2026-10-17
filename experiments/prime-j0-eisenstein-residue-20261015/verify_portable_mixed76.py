#!/usr/bin/env python3
"""Build and replay the opt-in 76-tripling arm on frozen portable source."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
PARENT_SHA256 = '0598b16fb66efda38515bc2a3685c9ff38b3c2e797ca66d7e7c0a2451e0a998c'


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def run(argv: list[str], root: Path, env: dict[str, str]) -> str:
    result = subprocess.run(argv, cwd=root, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert result.returncode == 0, (argv, result.stdout)
    return result.stdout.strip()


def main(parent: Path, output: Path) -> None:
    assert digest(parent) == PARENT_SHA256
    with tempfile.TemporaryDirectory(prefix='mixed76-portable-') as temporary:
        root = Path(temporary)
        with tarfile.open(parent, 'r:gz') as archive:
            for member in archive:
                name = Path(member.name)
                assert member.isfile() and not name.is_absolute() and '..' not in name.parts
                data = archive.extractfile(member)
                assert data is not None
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data.read())
        run([sys.executable, str(HERE / 'native_rho_restart_mixed76_overlay.py'),
             str(root)], HERE, os.environ.copy())
        env = os.environ.copy()
        env.pop('EISENSTEIN_ATLAS_DIR', None)
        source = {str(path.relative_to(root)): digest(path)
                  for path in sorted(root.rglob('*')) if path.is_file()}
        rustc = run(['rustc', '--version'], root, env)
        cargo = run(['cargo', '--version'], root, env)
        openssl = run(['openssl', 'version'], root, env)
        run(['cargo', 'build', '--release', '--locked', '--bin',
             'eisenstein_fixed'], root, env)
        binary = root / 'target/release/eisenstein_fixed'
        results = []
        for label, fixture, count in (
            ('frozen', root / 'fixtures/rho-restart-first128-fixture.json', 1),
            ('frozen', root / 'fixtures/rho-restart-first128-fixture.json', 128),
            ('independent', root / 'fixtures/mixed77-independent-fixture.json', 128),
        ):
            stdout = run([str(binary), '--pilot-rho-restart-joint-mixed76',
                          str(fixture), str(count)], root, env)
            expected = json.loads(fixture.read_text())['cases'][count-1]['point_hex']
            assert 'verified=1' in stdout and f'count={count}' in stdout
            assert 'steps=16 triplings=76 mode=joint_mixed76' in stdout
            assert stdout.endswith('point=' + expected)
            results.append({'fixture': label, 'fixture_sha256': digest(fixture),
                            'count': count, 'stdout': stdout,
                            'last_expected_point': expected})
        controls = []
        frozen = root / 'fixtures/rho-restart-first128-fixture.json'
        expected = json.loads(frozen.read_text())['cases'][0]['point_hex']
        for mode, args in (
            ('openssl_nowarm', ['--pilot-rho-restart', 'openssl_nowarm']),
            ('joint_triple81', ['--pilot-rho-restart-joint-triple81']),
            ('joint_triple243', ['--pilot-rho-restart-joint-triple243']),
            ('joint_mixed78', ['--pilot-rho-restart-joint-mixed78']),
            ('joint_mixed77', ['--pilot-rho-restart-joint-mixed77']),
        ):
            stdout = run([str(binary), *args, str(frozen), '1'], root, env)
            assert 'verified=1 count=1' in stdout and stdout.endswith('point=' + expected)
            assert f'mode={mode}' in stdout
            controls.append({'mode': mode, 'stdout': stdout,
                             'expected_point': expected})
        receipt = {
            'schema': 1, 'status': 'portable_exact_output_replay_passed',
            'timing_status': 'diagnostic_only_unisolated',
            'parent_bundle_sha256': PARENT_SHA256,
            'parent_bundle_file_sha256': digest(parent),
            'overlay_sha256': digest(HERE / 'native_rho_restart_mixed76_overlay.py'),
            'verifier_sha256': digest(Path(__file__)),
            'platform': platform.platform(), 'rustc': rustc,
            'cargo': cargo, 'openssl': openssl,
            'rustflags': env.get('RUSTFLAGS', ''),
            'optional_atlas_dir_set': False,
            'source_sha256': source, 'binary_sha256': digest(binary),
            'mixed76_exact_outputs': sum(row['count'] for row in results),
            'control_exact_outputs': len(controls),
            'exact_outputs': sum(row['count'] for row in results) + len(controls),
            'results': results, 'control_results': controls,
        }
        output.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
        print(json.dumps({'status': receipt['status'],
                          'exact_outputs': receipt['exact_outputs'],
                          'binary_sha256': receipt['binary_sha256']}, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--parent-bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    main(args.parent_bundle, args.output)
