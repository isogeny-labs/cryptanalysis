#!/usr/bin/env python3
"""Publish the frozen inventory/report through the scoped working store."""
import hashlib,json,os,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
env=dict(os.environ)
for k in ['AWS_ACCESS_KEY_ID','AWS_SECRET_ACCESS_KEY','AWS_SESSION_TOKEN','ARTIFACTS_AWS_ACCESS_KEY_ID','ARTIFACTS_AWS_SECRET_ACCESS_KEY']:env.pop(k,None)
env.update(AWS_PROFILE='default',AWS_REGION='us-west-2',AWS_DEFAULT_REGION='us-west-2',ARTIFACTS_REMOTE='s3://crypto-autoresearcher/store',ARTIFACTS_CACHE='/tmp/ic-inverse-regression-cache')
plan=json.loads((P/'setup-raw-reference-plan.json').read_text());assert len(set(plan['paths']))==25
keep={'FRESH_SETUP_PROTOCOL.md','SETUP_STATE_PLAN.md','setup-frozen-inputs.json','setup-fresh-identities.json','setup-fresh-generation.json'}
extras=['SETUP_REPORT.pdf','readback-timing-setup-001.json','setup-fresh-snapshot-binding.json','setup-fresh-runner-status.json','setup-timing-launch-metadata.json','incremental-cache-cleanup-timing-001.json','setup-parameter-presence-audit.json']
extras += [name+'.'+ext for name in ['setup-primary','setup-collector','setup-table','setup-aa'] for ext in ['svg','png']]
names=sorted((set(plan['paths'])|set(extras))-keep)
assert all((P/n).is_file() for n in names+sorted(keep))
subprocess.run(['python3','tools/artifacts/artifacts.py','push','--jobs','16',*[str((P/n).relative_to(ROOT)) for n in names]],cwd=ROOT,env=env,check=True)
for name in sorted(keep):
 f=P/name;h=hashlib.sha256(f.read_bytes()).hexdigest();uri='s3://crypto-autoresearcher/store/sha256/'+h[:2]+'/'+h
 subprocess.run(['aws','s3','cp',str(f),uri,'--only-show-errors'],env=env,check=True)
print('Published25raw references and report artifacts; canonical source inputs remain in Git')
