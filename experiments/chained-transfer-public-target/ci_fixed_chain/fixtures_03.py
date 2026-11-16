"""Copy or losslessly decompress whole pinned fixtures; no scientific arithmetic."""
from pathlib import Path
import hashlib, json, lzma, shutil, sys
study, out = map(Path, sys.argv[1:3]); rows = []
for package, destination, compressed in [
    ('original-kernel-census-01','original-kernel-fixtures',True),
    ('original-full-geometry-01','original-geometry-fixtures',False),
]:
    dest=out/destination; dest.mkdir()
    for name,pin in json.loads((study/package/'input-pins.json').read_text()).items():
        source=study/pin['source']; value=source.read_bytes()
        assert len(value)==pin['bytes'] and hashlib.sha256(value).hexdigest()==pin['sha256']
        body=value if compressed else lzma.decompress(value)
        target=dest/name;target.write_bytes(body);assert target.read_bytes()==body
        rows.append(dict(source=str(source),source_pin=pin,destination=str(target),bytes=len(body),sha256=hashlib.sha256(body).hexdigest()))
dest=out/'original-prime-fixtures';dest.mkdir()
for label in ['originalE2','originalE3','originalE4']:
    source=study/'evidence/original-prime-alternative-kernel-review-01'/(label+'-whole-six-rows.json.xz')
    body=lzma.decompress(source.read_bytes());target=dest/(label+'-whole-six-rows.json');target.write_bytes(body)
    assert target.read_bytes()==body
    rows.append(dict(source=str(source),destination=str(target),bytes=len(body),sha256=hashlib.sha256(body).hexdigest()))
(out/'whole-successor-fixture-custody.json').write_text(json.dumps(rows,indent=2)+'\n')
