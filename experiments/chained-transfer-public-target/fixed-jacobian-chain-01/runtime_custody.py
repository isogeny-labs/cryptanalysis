"""Check the compiled mathematical source and executable bytes, no arithmetic."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

pkg, build, out = map(Path, sys.argv[1:4])
assert (build / 'original.exit').read_text().strip() == '0'
assert (build / 'geometry-compile.exit').read_text().strip() == '0'
source = build / 'actual-source'
members = {}
for p in sorted(source.rglob('*')):
    if p.is_file():
        relative = p.relative_to(source)
        assert p.read_bytes() == (pkg / relative).read_bytes(), str(relative)
        members[str(relative)] = dict(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
binary = json.loads((build / 'geometry-compiled-binary.json').read_text())
actual = Path(binary['actual_path'])
copy = build / 'geometry-original-compiled-test.bin'
assert actual.read_bytes() == copy.read_bytes()
assert actual.stat().st_size == binary['bytes']
assert hashlib.sha256(actual.read_bytes()).hexdigest() == binary['sha256']
assert json.loads((build / 'engine-reused.json').read_text())['actual_reuse'] is True
shutil.copy2(actual, out / 'actual-before-native-test.bin')
(out / 'test-actual-path.txt').write_text(str(actual) + '\n')
(out / 'runtime-custody.json').write_text(json.dumps(dict(
    compiled_mathematical_source_members=members, compiled_binary=binary,
    all_original_source_members_equal=True, complete_compiled_and_actual_bytes_equal=True,
    scope='The native driver was added after compilation; every compiled source member remains exact.'
), indent=2) + '\n')
