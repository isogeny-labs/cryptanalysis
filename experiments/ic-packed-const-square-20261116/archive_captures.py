#!/usr/bin/env python3
"""Lossless bundles plus per-file content-addressed custody; never delete captures."""
import argparse,hashlib,json,os,subprocess,tarfile
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
a=argparse.ArgumentParser();a.add_argument('directories',nargs='+');args=a.parse_args()
env=dict(os.environ)
for key in ['AWS_ACCESS_KEY_ID','AWS_SECRET_ACCESS_KEY','AWS_SESSION_TOKEN','ARTIFACTS_AWS_ACCESS_KEY_ID','ARTIFACTS_AWS_SECRET_ACCESS_KEY']:env.pop(key,None)
env.update(AWS_PROFILE='default',AWS_REGION='us-west-2',AWS_DEFAULT_REGION='us-west-2',ARTIFACTS_REMOTE='s3://crypto-autoresearcher/store',ARTIFACTS_CACHE='/tmp/ic-inverse-regression-cache')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[]
for name in args.directories:
 d=P/name;assert d.is_dir() and d.parent==P
 captures=sorted(p for p in d.rglob('*') if p.is_file() and p.name not in ['.artifacts.json','.gitignore'])
 assert captures and all(not p.is_symlink() for p in captures)
 inventory=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)) for p in captures]
 for row in inventory:row['s3_uri']='s3://crypto-autoresearcher/store/sha256/'+row['sha256'][:2]+'/'+row['sha256']
 bundle=P/('raw-'+name+'.tar.gz');receipt=P/(name+'-bundle-receipt.json')
 assert not bundle.exists() and not receipt.exists(),'immutable bundle already exists'
 with tarfile.open(bundle,'w:gz') as tar:
  for p in captures:tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
 h=sha(bundle);receipt.write_text(json.dumps(dict(schema='ic-raw-bundle/v1',files=inventory,bundle=dict(path=str(bundle.relative_to(ROOT)),bytes=bundle.stat().st_size,sha256=h,s3_uri='s3://crypto-autoresearcher/store/sha256/'+h[:2]+'/'+h)),indent=2)+'\n')
 files.extend([*captures,bundle,receipt])
subprocess.run(['python3','tools/artifacts/artifacts.py','push','--jobs','16',*[str(p.relative_to(ROOT)) for p in files]],cwd=ROOT,env=env,check=True)
print(json.dumps(dict(status='uploaded',objects=len(files))))
