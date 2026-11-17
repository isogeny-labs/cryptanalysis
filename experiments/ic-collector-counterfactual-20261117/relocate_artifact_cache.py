#!/usr/bin/env python3
"""Preserve the goal's exact content cache while freeing internal disk."""
import hashlib,json,os,shutil
from pathlib import Path
P=Path(__file__).resolve().parent
src=Path('/tmp/ic-inverse-regression-cache'); dst=P/'local-artifact-cache'
assert src.is_dir() and not src.is_symlink() and not dst.exists()
def inventory(root):
    return {str(p.relative_to(root)):('link',os.readlink(p)) if p.is_symlink() else ('file',p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()) for p in root.rglob('*') if p.is_symlink() or p.is_file()}
before=inventory(src); shutil.move(str(src),str(dst)); assert inventory(dst)==before
src.symlink_to(dst,target_is_directory=True)
(P/'cache-relocation.json').write_text(json.dumps(dict(status='pass',source=str(src),destination=str(dst),files=len(before),bytes=sum(v[1] for v in before.values() if v[0]=='file'),manifest_sha256=hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),scope='Reversible move of this goal\'s own content cache; no database files, credentials or other build directories changed.'),indent=2)+'\n')
print('Content cache moved and every file verified',len(before))
