#!/usr/bin/env python3
"""Assemble, build, and replay mixed-77 without atlas placeholder files."""
import argparse
from hashlib import sha256
import gzip
import io
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


def write_bundle(root: Path, output: Path,
                 source_hashes: dict[str, str]) -> str:
    files = {str(path.relative_to(root)): path.read_bytes()
             for path in sorted(root.rglob('*')) if path.is_file()}
    files['fixtures/rho-restart-first128-fixture.json'] = (
        HERE / 'rho-restart-first128-fixture.json').read_bytes()
    files['fixtures/mixed77-independent-fixture.json'] = (
        HERE / 'mixed77-independent-fixture.json').read_bytes()
    manifest = {'schema': 1, 'source_sha256': source_hashes,
                'fixture_sha256': {
                    name: sha256(data).hexdigest() for name, data in files.items()
                    if name.startswith('fixtures/')},
                'command': ['cargo', 'build', '--release', '--locked',
                            '--bin', 'eisenstein_fixed']}
    files['source-manifest.json'] = (json.dumps(manifest, sort_keys=True,
                                               indent=2) + '\n').encode()
    for name, data in files.items():
        if name.endswith(('.rs', '.toml')):
            assert b'/Volumes/' not in data and b'/private/tmp/' not in data
            assert b'/Users/' not in data
    with output.open('wb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode='w') as archive:
                for name, data in sorted(files.items()):
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    info.mtime = info.uid = info.gid = 0
                    info.mode = 0o644
                    archive.addfile(info, io.BytesIO(data))
    return digest(output)


def main(output: Path, bundle_out: Path | None) -> None:
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
        bundle_sha256 = (write_bundle(root, bundle_out, source_hashes)
                         if bundle_out is not None else None)
        build_env = os.environ.copy()
        build_env.pop('EISENSTEIN_ATLAS_DIR', None)
        rustc = run(['rustc', '--version'], root, build_env)
        cargo = run(['cargo', '--version'], root, build_env)
        openssl = run(['openssl', 'version'], root, build_env)
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
            'openssl': openssl, 'rustflags': build_env.get('RUSTFLAGS', ''),
            'verifier_sha256': digest(Path(__file__)),
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
            'bundle_sha256': bundle_sha256,
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
    parser.add_argument('--bundle-out', type=Path)
    args = parser.parse_args()
    main(args.output, args.bundle_out)
