#!/usr/bin/env python3
"""Assemble, build, and replay mixed-77 without atlas placeholder files."""
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
ARCHIVE = HERE / 'rho-restart-hybrid-native-provenance.tar.gz'
FIXTURE_ARCHIVE = HERE / 'mixed640-compile-fixtures-20261016.tar.gz'
PREFIX = 'workspace/bench-sources/prime-j0-rho-restart-hybrid/'
SOURCE_MEMBERS = (
    'Cargo.toml', 'Cargo.lock', 'src/bin/eisenstein_fixed.rs',
    'src/bin/eisenstein_fixed/unit_orbit_windows.rs',
    'src/bin/rho_restart_hybrid.rs',
)
FIXTURE_MEMBERS = (
    'mixed640_bench_fixture.json', 'mixed640_stream_fixture.json',
    'mixed640_uniform_fixture.json',
)


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def extract_exact(archive: Path, names: tuple[str, ...], root: Path,
                  prefix: str = '') -> None:
    with tarfile.open(archive, 'r:gz') as tar:
        for name in names:
            data = tar.extractfile(prefix + name)
            assert data is not None, name
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data.read())


def run(command: list[str], cwd: Path, env: dict[str, str]) -> str:
    result = subprocess.run(command, cwd=cwd, env=env, text=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    assert result.returncode == 0, (command, result.stdout)
    return result.stdout.strip()


def main(output: Path) -> None:
    with tempfile.TemporaryDirectory(prefix='mixed77-portable-') as temporary:
        root = Path(temporary)
        extract_exact(ARCHIVE, SOURCE_MEMBERS, root, PREFIX)
        extract_exact(FIXTURE_ARCHIVE, FIXTURE_MEMBERS, root / 'src/bin')
        run([sys.executable, str(HERE / 'native_rho_restart_joint_overlay.py'),
             str(root)], HERE, os.environ.copy())
        run([sys.executable,
             str(HERE / 'native_rho_restart_mixed77_portable_overlay.py'),
             str(root)], HERE, os.environ.copy())
        windows = root / 'src/bin/eisenstein_fixed/unit_orbit_windows.rs'
        assert 'include_bytes!' not in windows.read_text()
        source_hashes = {str(path.relative_to(root)): digest(path)
                         for path in sorted(root.rglob('*')) if path.is_file()}
        build_env = os.environ.copy()
        build_env.pop('EISENSTEIN_ATLAS_DIR', None)
        rustc = run(['rustc', '--version'], root, build_env)
        cargo = run(['cargo', '--version'], root, build_env)
        run(['cargo', 'build', '--release', '--locked', '--bin',
             'eisenstein_fixed'], root, build_env)
        binary = root / 'target/release/eisenstein_fixed'
        results = []
        for label, fixture, count in (
            ('frozen', HERE / 'rho-restart-first128-fixture.json', 1),
            ('frozen', HERE / 'rho-restart-first128-fixture.json', 128),
            ('independent', HERE / 'mixed77-independent-fixture.json', 128),
        ):
            stdout = run([str(binary), '--pilot-rho-restart-joint-mixed77',
                          str(fixture), str(count)], root, build_env)
            expected = json.loads(fixture.read_text())['cases'][count - 1]['point_hex']
            assert 'verified=1' in stdout and f'count={count}' in stdout
            assert 'steps=16 triplings=77 mode=joint_mixed77' in stdout
            assert stdout.endswith('point=' + expected)
            results.append({'fixture': label, 'fixture_sha256': digest(fixture),
                            'count': count, 'last_expected_point': expected,
                            'stdout': stdout})
        receipt = {
            'schema': 1, 'status': 'portable_exact_output_replay_passed',
            'timing_status': 'diagnostic_only_unisolated',
            'optional_atlas_dir_set': False,
            'atlas_include_bytes_count': 0,
            'platform': platform.platform(), 'rustc': rustc, 'cargo': cargo,
            'provenance_archive_sha256': digest(ARCHIVE),
            'compile_fixture_archive_sha256': digest(FIXTURE_ARCHIVE),
            'overlay_sha256': {
                name: digest(HERE / name) for name in (
                    'native_rho_restart_joint_overlay.py',
                    'native_rho_restart_joint243_overlay.py',
                    'native_rho_restart_mixed78_overlay.py',
                    'native_rho_restart_mixed77_overlay.py',
                    'native_rho_restart_mixed77_portable_overlay.py')},
            'source_sha256': source_hashes, 'binary_sha256': digest(binary),
            'exact_outputs': sum(row['count'] for row in results),
            'results': results,
        }
        output.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
        print(json.dumps({'status': receipt['status'],
                          'exact_outputs': receipt['exact_outputs'],
                          'binary_sha256': receipt['binary_sha256']},
                         sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args().output)
