#!/usr/bin/env python3
"""Reversibly move this task's source copy, verifying every file byte."""
from pathlib import Path
import hashlib, json, os, shutil
P = Path(__file__).resolve().parent
src = Path('/tmp/ic-canonical-frozen-source-001')
dst = P / 'local-frozen-source-stash'
assert src.is_dir() and not src.is_symlink() and not dst.exists()
def inventory(root):
    return {str(p.relative_to(root)): ('link', os.readlink(p)) if p.is_symlink() else ('file', p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest()) for p in root.rglob('*') if p.is_symlink() or p.is_file()}
before = inventory(src)
shutil.move(str(src), str(dst))
assert inventory(dst) == before
src.symlink_to(dst, target_is_directory=True)
(P / 'local-source-relocation.json').write_text(json.dumps(dict(status='pass', source=str(src), destination=str(dst), files=len(before), bytes=sum(r[1] for r in before.values() if r[0]=='file'), manifest_sha256=hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(), reason='reclaim internal-volume space; identical source retained with original path symlink'), indent=2) + '\n')
print('Verified reversible source relocation', len(before), 'files')
