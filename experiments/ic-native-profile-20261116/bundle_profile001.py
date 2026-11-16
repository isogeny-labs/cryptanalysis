#!/usr/bin/env python3
"""Lossless deterministic bundle of every raw output, with per-file SHA pins."""
import gzip,hashlib,io,json,tarfile
from pathlib import Path
P=Path(__file__).resolve().parent;D=P/'profile-001';files=sorted(p for p in D.iterdir() if not p.name.startswith('.'))
assert all(p.is_file() and not p.is_symlink() for p in files)
manifest={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files}
for pin in manifest.values():
 digest=pin['sha256'];pin['s3_uri']='s3://setec-astronomy-artifacts/store/sha256/'+digest[:2]+'/'+digest
bundle=P/'raw-profile-001.tar.gz'
with bundle.open('wb') as f,gzip.GzipFile(fileobj=f,mode='wb',mtime=0) as z,tarfile.open(fileobj=z,mode='w') as t:
 for name,data in [('MANIFEST.json',json.dumps(manifest,sort_keys=True,indent=2).encode()),*[(p.name,p.read_bytes()) for p in files]]:
  info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0;info.mode=0o755 if name=='probe' else 0o644;t.addfile(info,io.BytesIO(data))
with tarfile.open(bundle,'r:gz') as t:
 assert set(t.getnames())==set(manifest)|{'MANIFEST.json'}
 for name,pin in manifest.items():
  data=t.extractfile(name).read();assert len(data)==pin['bytes'] and hashlib.sha256(data).hexdigest()==pin['sha256']
(P/'raw-profile001-bundle-receipt.json').write_text(json.dumps(dict(status='pass',files=len(files),bundle_sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(),manifest=manifest),indent=2)+'\n')
print(json.dumps(dict(status='pass',raw_files=len(files),bundle_bytes=bundle.stat().st_size)))
