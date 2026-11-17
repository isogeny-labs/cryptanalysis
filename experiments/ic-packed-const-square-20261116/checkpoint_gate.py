#!/usr/bin/env python3
"""Use the working local profile through the checkpoint tool's ambient fallback.
Credentials stay only in child environment; no credential values are printed.
"""
import argparse,json,os,subprocess
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
with a.log.open('w') as log:r=subprocess.run(['/bin/bash','scripts/checkpoint.sh','gate'],cwd=ROOT,env=v,stdout=log,stderr=subprocess.STDOUT)
print('checkpoint gate exit',r.returncode);raise SystemExit(r.returncode)
