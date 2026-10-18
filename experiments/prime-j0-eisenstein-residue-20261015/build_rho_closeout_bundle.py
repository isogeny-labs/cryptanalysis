#!/usr/bin/env python3
"""Rebuild the exact mixed-76 source and add the fair OpenSSL closeout arm."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory

import verify_portable_mixed77 as v77
import verify_portable_mixed76 as v76

HERE = Path(__file__).resolve().parent
MIXED76_SHA256 = 'aa194966c8ce274f53b169c836baf16ff52c5d94ba384cec9994d72f65f02e8b'
FIXTURES = HERE / 'rho-closeout-fixtures'


def command(*args: str) -> None:
    subprocess.run([sys.executable, *args], check=True)


def unpack(archive_path: Path, root: Path) -> None:
    with tarfile.open(archive_path, 'r:gz') as archive:
        for member in archive:
            path = Path(member.name)
            assert member.isfile() and not path.is_absolute() and '..' not in path.parts
            source = archive.extractfile(member)
            assert source is not None
            destination = root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read())


def source_hashes(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob('*'))
            if path.is_file() and path.name != 'source-manifest.json'}


def main(output: Path) -> None:
    verification = json.loads((FIXTURES / 'full-verification.json').read_text())
    manifest_bytes = (FIXTURES / 'manifest.json').read_bytes()
    assert verification['status'] == 'pass' and verification['scope'] == 'all_rows'
    assert verification['rows_verified'] == verification['total_rows'] == 4096
    assert verification['manifest_sha256'] == sha256(manifest_bytes).hexdigest()
    fixture_manifest = json.loads(manifest_bytes)
    assert len(fixture_manifest['fixtures']) == 32
    with TemporaryDirectory(prefix='rho-closeout-bundle-') as temporary:
        temp = Path(temporary)
        parent = temp / 'mixed77'
        v77.extract_exact(v77.ARCHIVE, v77.SOURCE_MEMBERS, parent, v77.PREFIX)
        v77.extract_exact(v77.FIXTURE_ARCHIVE, v77.FIXTURE_MEMBERS,
                          parent / 'src/bin')
        command(str(HERE / 'native_rho_restart_joint_overlay.py'), str(parent))
        command(str(HERE / 'native_rho_restart_mixed77_portable_overlay.py'), str(parent))
        parent_hashes = {str(p.relative_to(parent)): v77.digest(p)
                         for p in sorted(parent.rglob('*')) if p.is_file()}
        parent_bundle = temp / 'mixed77.tar.gz'
        assert v77.write_bundle(parent, parent_bundle, parent_hashes) == v76.PARENT_SHA256

        mixed76 = temp / 'mixed76'
        unpack(parent_bundle, mixed76)
        command(str(HERE / 'native_rho_restart_mixed76_overlay.py'), str(mixed76))
        original_manifest = {'schema': 1,
            'parent_bundle_sha256': v76.PARENT_SHA256,
            'source_sha256': source_hashes(mixed76),
            'command': ['cargo', 'build', '--release', '--locked',
                        '--bin', 'eisenstein_fixed']}
        (mixed76 / 'source-manifest.json').write_text(
            json.dumps(original_manifest, sort_keys=True, indent=2) + '\n')
        mixed76_bundle = temp / 'mixed76.tar.gz'
        assert v76.write_bundle(mixed76, mixed76_bundle) == MIXED76_SHA256

        closeout = temp / 'closeout'
        unpack(mixed76_bundle, closeout)
        command(str(HERE / 'native_rho_closeout_overlay.py'), str(closeout))
        fixture_root = closeout / 'fixtures/rho-closeout'
        fixture_root.mkdir(parents=True)
        for entry in fixture_manifest['fixtures']:
            source = FIXTURES / entry['path']
            assert sha256(source.read_bytes()).hexdigest() == entry['sha256']
            shutil.copyfile(source, fixture_root / entry['path'])
        shutil.copyfile(FIXTURES / 'manifest.json', fixture_root / 'manifest.json')
        shutil.copyfile(FIXTURES / 'full-verification.json',
                        fixture_root / 'full-verification.json')
        closeout_manifest = {'schema': 1, 'parent_bundle_sha256': MIXED76_SHA256,
            'fixture_manifest_sha256': sha256(manifest_bytes).hexdigest(),
            'source_sha256': source_hashes(closeout),
            'command': ['cargo', 'build', '--release', '--locked',
                        '--bin', 'eisenstein_fixed']}
        (closeout / 'source-manifest.json').write_text(
            json.dumps(closeout_manifest, sort_keys=True, indent=2) + '\n')
        output.parent.mkdir(parents=True, exist_ok=True)
        bundle_hash = v76.write_bundle(closeout, output)
        print(json.dumps({'bundle_sha256': bundle_hash,
                          'fixture_manifest_sha256': sha256(manifest_bytes).hexdigest(),
                          'source_count': len(closeout_manifest['source_sha256'])},
                         sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    main(args.output)
