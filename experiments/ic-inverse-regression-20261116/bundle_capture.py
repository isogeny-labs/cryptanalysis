#!/usr/bin/env python3
"""Lossless bundle and per-file remote pins for completed captures."""
import argparse, gzip, hashlib, io, json, tarfile
from pathlib import Path
P=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('directory');args=p.parse_args()
D=P/args.directory;files=sorted(f for f in D.iterdir() if not f.name.startswith('.'))
assert all(f.is_file() and not f.is_symlink() for f in files)
manifest={f.name:{'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in files}
for row in manifest.values():
 h=row['sha256'];row['s3_uri']=f's3://crypto-autoresearcher/store/sha256/{h[:2]}/{h}'
bundle=P/('raw-'+args.directory+'.tar.gz')
with bundle.open('wb') as target,gzip.GzipFile(fileobj=target,mode='wb',mtime=0) as zipped,tarfile.open(fileobj=zipped,mode='w') as archive:
 for name,data,mode in [('MANIFEST.json',json.dumps(manifest,sort_keys=True,indent=2).encode(),0o644),*[(f.name,f.read_bytes(),0o755 if f.stat().st_mode&0o111 else 0o644) for f in files]]:
  info=tarfile.TarInfo(name);info.size=len(data);info.mode=mode;info.mtime=0;archive.addfile(info,io.BytesIO(data))
with tarfile.open(bundle,'r:gz') as archive:
 assert set(archive.getnames())==set(manifest)|{'MANIFEST.json'}
 for name,row in manifest.items():
  data=archive.extractfile(name).read();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
receipt={'status':'pass','bundle_sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),'manifest':manifest}
(P/(args.directory+'-bundle-receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':'pass','files':len(files),'bundle_bytes':bundle.stat().st_size}))
