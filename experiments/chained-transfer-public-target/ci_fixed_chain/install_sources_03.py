"""Install exact captured derivative bytes; no scientific arithmetic."""
from pathlib import Path, PurePosixPath
import hashlib, json, shutil, sys
ci, study, out = map(Path, sys.argv[1:4])
manifest = json.loads((ci / 'successor-sources-03.json').read_text())
installed = []
for row in manifest['files']:
    relative = PurePosixPath(row['relative_to_study'])
    assert not relative.is_absolute() and '..' not in relative.parts
    assert relative.parts[0] in ['fixed-jacobian-chain-evaluator-02', 'original-prime-chain-01']
    assert relative.parts[1] in ['derived', 'generated']
    source = ci / 'successor-sources-03' / str(relative)
    target = study / str(relative)
    data = source.read_bytes()
    assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256']
    if target.exists():
        assert target.is_file() and not target.is_symlink() and target.read_bytes() == data
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    assert target.read_bytes() == data
    installed.append(row)
(out / 'installed-literal-successor-sources.json').write_text(json.dumps(installed, indent=2) + '\n')
