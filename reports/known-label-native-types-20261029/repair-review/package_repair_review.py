"""Package the existing sealed review without changing any review artifact."""
from pathlib import Path, PurePosixPath
import gzip
import hashlib
import io
import json
import tarfile

BASE = Path(__file__).resolve().parent
ROOT = BASE / 'TASK-20261029-b339cc/repair-review'
SEAL = ROOT / 'independent-controls/seal.json'
OUT = BASE / 'repair-review-sealed.tar.gz'
RECEIPT = BASE / 'repair-review-package.json'
assert not OUT.exists() and not RECEIPT.exists(), 'Refusing overwrite'
seal_bytes = SEAL.read_bytes()
seal_hash = hashlib.sha256(seal_bytes).hexdigest()
assert seal_hash == 'db44a1e8339ef98406ec098ddc6b136495c99f3c900f2a7890ac8ff70e3ef5af'
seal = json.loads(seal_bytes)
assert seal['revision'] == '42fb95ed95a6bbf06ea38422b32cc3e22988b08d'
expected = {x['path']: x for x in seal['files']}
assert len(expected) == len(seal['files']) == 840
expected['independent-controls/seal.json'] = {
    'path': 'independent-controls/seal.json', 'sha256': seal_hash, 'bytes': len(seal_bytes)}
total = 0
with OUT.open('xb') as raw:
    with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w|', format=tarfile.USTAR_FORMAT) as archive:
            for name, item in sorted(expected.items()):
                path = PurePosixPath(name)
                assert not path.is_absolute() and '..' not in path.parts
                source = ROOT / name
                assert source.is_file() and not source.is_symlink()
                content = source.read_bytes()
                assert len(content) == item['bytes']
                assert hashlib.sha256(content).hexdigest() == item['sha256'], name
                info = tarfile.TarInfo(name)
                info.size = len(content)
                info.mode = 0o644
                info.uid = info.gid = info.mtime = 0
                info.uname = info.gname = ''
                archive.addfile(info, io.BytesIO(content))
                total += len(content)
seen = set()
with tarfile.open(OUT, 'r:gz') as archive:
    for member in archive:
        assert member.isfile() and member.name in expected and member.name not in seen
        item = expected[member.name]
        stream = archive.extractfile(member)
        assert stream is not None
        content = stream.read()
        assert len(content) == item['bytes'] and hashlib.sha256(content).hexdigest() == item['sha256']
        seen.add(member.name)
assert seen == set(expected)
result = {'schema': 'sealed-review-package/v1', 'reviewed_revision': seal['revision'],
          'original_seal_sha256': seal_hash, 'sealed_review_files': 840,
          'archive_members_including_seal': len(seen), 'uncompressed_bytes': total,
          'archive': OUT.name, 'archive_bytes': OUT.stat().st_size,
          'archive_sha256': hashlib.sha256(OUT.read_bytes()).hexdigest(),
          'verification': 'All original sealed hashes checked before packaging and after reading the archive; no filesystem extraction.',
          'scope': 'Existing independent software repair review only. No native Lean or theorem-fidelity verification added.',
          'original_artifacts_modified': False, 'published': False}
RECEIPT.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
