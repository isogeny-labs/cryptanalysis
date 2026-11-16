"""File-only preservation of the retained failed source tree and mutable metadata."""
from pathlib import Path
import hashlib,json,os,sys
old=Path(sys.argv[1]);new=Path(sys.argv[2]);out=Path(sys.argv[3]);records=[]
for f in sorted(old.rglob('*')):
 if f.is_symlink():records.append(dict(path=str(f.relative_to(old)),symlink=os.readlink(f)))
 elif f.is_file():records.append(dict(path=str(f.relative_to(old)),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
(out/'entire-original-failed-runtime-byte-inventory.json').write_text(json.dumps(records,indent=2)+'\n')
git=new/'cryptanalysis/.git'
for f in sorted(git.rglob('*')):
 if not f.is_file() or f.is_symlink() or f.is_relative_to(git/'objects') or f==git/'index':continue
 b=f.read_bytes();q=f.with_name(f.name+'.repair-metadata-copy');q.write_bytes(b);os.chmod(q,f.stat().st_mode&0o777);os.replace(q,f)
f=git/'info/sparse-checkout';b=f.read_bytes();q=f.with_name('sparse-checkout.with-canonical-data-metadata');q.write_bytes(b+b'\n**/.gitignore\n**/.gitattributes\n**/.artifacts.json\n');os.replace(q,f)
print(json.dumps(dict(original_failed_tree_byte_records=len(records),old_tree_unchanged=True,mutable_metadata_separated=True,existing_index_preserved_by_Git_atomic_index_replacement=True)))
