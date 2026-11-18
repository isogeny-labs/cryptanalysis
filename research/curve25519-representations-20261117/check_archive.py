"""Archive-integrity self-check. Does not execute producer research entrypoints."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    original = ROOT / 'original'
    expected = {}
    for line in (original / 'SHA256SUMS').read_text().splitlines():
        sha, name = line.split('  ', 1)
        assert Path(name).name == name and len(sha) == 64
        assert name not in expected
        expected[name] = sha
    inventory = json.loads((ROOT / 'pending-artifacts.json').read_text())
    assert inventory['status'] == 'not_uploaded'
    pending = {}
    for item in inventory['files']:
        name = Path(item['path']).name
        assert item['path'] == 'original/' + name
        assert item['remote_location'] is None and item['upload_status'] == 'blocked'
        pending[name] = item
        if name != 'research-bundle.zip':
            assert item['sha256'] == expected[name]
    checked = []
    absent = []
    for name, sha in expected.items():
        file = original / name
        if not file.exists():
            assert name in pending, f'Undeclared missing file: {name}'
            absent.append(name)
            continue
        assert hashlib.sha256(file.read_bytes()).hexdigest() == sha, name
        if name in pending:
            assert file.stat().st_size == pending[name]['size_bytes']
        checked.append(name)
    for file in original.glob('*.py'):
        ast.parse(file.read_text(), filename=str(file))
    print(json.dumps({'scope': 'archive_integrity_self_check_only',
                      'hashed_local_files': len(checked),
                      'declared_pending_files_absent_locally': absent,
                      'artifact_upload_status': 'blocked',
                      'scientific_standing': 'unverified'}, indent=2))


if __name__ == '__main__':
    main()
