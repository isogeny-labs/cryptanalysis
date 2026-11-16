"""Whole compiled-source, engine and executable byte custody; no arithmetic."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

pkg, build, out = map(Path, sys.argv[1:4])
assert (build / 'original.exit').read_text().strip() == '0'
assert (build / 'chain-compile.exit').read_text().strip() == '0'
assert (build / 'auditor-compile.exit').read_text().strip() == '0'
source = build / 'actual-source'
members = {}
for p in sorted(source.rglob('*')):
    if p.is_file():
        relative = p.relative_to(source)
        assert p.read_bytes() == (pkg / relative).read_bytes(), str(relative)
        members[str(relative)] = dict(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
binary = json.loads((build / 'chain-compiled-binary.json').read_text())
actual = Path(binary['actual_path'])
assert actual.read_bytes() == (build / 'chain-original-compiled-test.bin').read_bytes()
assert actual.stat().st_size == binary['bytes']
assert hashlib.sha256(actual.read_bytes()).hexdigest() == binary['sha256']
shutil.copy2(actual, out / 'actual-before-native-test.bin')
(out / 'test-actual-path.txt').write_text(str(actual) + '\n')
auditor = json.loads((build / 'auditor-compiled-custody.json').read_text())
path = Path(auditor['actual_path'])
assert path.read_bytes() == (build / 'actual-compiled-auditor.bin').read_bytes()
assert path.stat().st_size == auditor['bytes']
assert hashlib.sha256(path.read_bytes()).hexdigest() == auditor['sha256']
shutil.copy2(path, out / 'actual-before-native-auditor.bin')
(out / 'auditor-actual-path.txt').write_text(str(path) + '\n')
assert json.loads((build / 'engine-reused.json').read_text())['actual_reuse'] is True
(out / 'runtime-custody.json').write_text(json.dumps(dict(
    compiled_source_members=members, compiled_test=binary, compiled_auditor=auditor,
    all_original_source_members_equal=True, full_actual_compiler_runtime_bytes_equal=True,
    scope='Only README, FullGroupNorm proof and native-driver files were added after Rust compilation; every compiled source member is exact.'
), indent=2) + '\n')
