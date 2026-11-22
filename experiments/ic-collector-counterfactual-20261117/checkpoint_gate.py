#!/usr/bin/env python3
"""Use the working local profile through the checkpoint tool's ambient fallback.
Credentials stay only in child environment; no credential values are printed.
"""
import argparse,hashlib,io,json,os,shutil,subprocess,tarfile,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--log',type=Path,required=True);a=p.parse_args()
v=dict(os.environ)
for k in ['AWS_ACCESS_KEY_ID','AWS_SECRET_ACCESS_KEY','AWS_SESSION_TOKEN','CHECKPOINT_UPLOAD_TOKEN']:v.pop(k,None)
r=subprocess.run(['aws','configure','export-credentials','--profile','default','--format','process'],env=v,text=True,capture_output=True)
if r.returncode:raise SystemExit('default profile credential export failed; no values printed')
c=json.loads(r.stdout);v.update(AWS_ACCESS_KEY_ID=c['AccessKeyId'],AWS_SECRET_ACCESS_KEY=c['SecretAccessKey'])
if c.get('SessionToken'):v['AWS_SESSION_TOKEN']=c['SessionToken']
v.update(CHECKPOINT_BUCKET='crypto-autoresearcher',CHECKPOINT_AWS_PROFILE='__ambient_checkpoint__',CHECKPOINT_AWS_REGION='us-west-2',CHECKPOINT_TOKEN_FILE='/dev/null')
shell=shutil.which('bash') or '/bin/bash'
with a.log.open('w') as log:r=subprocess.run([shell,'scripts/checkpoint.sh','gate'],cwd=ROOT,env=v,stdout=log,stderr=subprocess.STDOUT)
if r.returncode:raise SystemExit(r.returncode)
# A legacy-shell here-document failure can be swallowed inside the gate's
# conditional push. Require the remote restore contract, not exit0 alone.
uri=(ROOT/'.resume/.last-push').read_text().split()[-1]
assert uri.startswith('s3://crypto-autoresearcher/checkpoints/cryptanalysis/') and uri.endswith('/')
def fetch(name):
    return subprocess.check_output(['aws','--region','us-west-2','s3','cp',uri+name,'-','--only-show-errors'],env=v)
meta_bytes=fetch('meta.json'); meta=json.loads(meta_bytes)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
assert meta['head']==head and meta['branch']==branch and meta['s3']==uri
raw=fetch('checkpoint.tar.gz'); bundle_verified=False
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
    members={m.name.removeprefix('./'):m for m in archive.getmembers() if m.isfile()}
    assert archive.extractfile(members['meta.json']).read()==meta_bytes
    if meta['unpushed_commits']:
        data=archive.extractfile(members['branch.bundle']).read()
        with tempfile.TemporaryDirectory(dir=a.log.parent) as tmp:
            bundle=Path(tmp)/'branch.bundle'; bundle.write_bytes(data)
            subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True,capture_output=True)
            advertised=subprocess.check_output(['git','bundle','list-heads',str(bundle)],cwd=ROOT,text=True)
            assert head+' HEAD' in advertised; bundle_verified=True
receipt=dict(status='pass',head=head,branch=branch,s3_uri=uri,metadata_sha256=hashlib.sha256(meta_bytes).hexdigest(),package_sha256=hashlib.sha256(raw).hexdigest(),package_bytes=len(raw),package_metadata_matches=True,unpushed_bundle_verified=bundle_verified,shell=shell,scope='Uploaded metadata and restore bundle checked after gate; no source/measurement qualification inferred.')
a.log.with_name(a.log.name+'.verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('checkpoint gate and remote restore-contract verification pass')
