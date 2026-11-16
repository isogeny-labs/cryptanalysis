"""Publish an already committed owned checkpoint with a normal Git FF.
Only repository custody:never cryptographic research or a benchmark.
"""
from pathlib import Path
from datetime import datetime,timezone
import os,sys,subprocess,json,base64,re
repo,expected,head,branch,destination=sys.argv[1:]
assert re.fullmatch(r'isogeny-labs/(crypto|cryptanalysis)',repo)
assert all(re.fullmatch(r'[0-9a-f]{40}',x) for x in [expected,head])
assert re.fullmatch(r'research/[A-Za-z0-9_./-]+',branch)
out=Path(destination);out.mkdir();cwd=Path.cwd();ref='refs/heads/'+branch;url='https://github.com/'+repo+'.git'
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==head
assert int(subprocess.check_output(['git','rev-list','--count',expected+'..'+head],text=True).strip())>0
subprocess.run(['git','merge-base','--is-ancestor',expected,head],check=True)
env=os.environ.copy();n=int(env.get('GIT_CONFIG_COUNT','0'));env['GIT_CONFIG_COUNT']=str(n+1);env['GIT_CONFIG_KEY_'+str(n)]='http.https://github.com/.extraheader';env['GIT_CONFIG_VALUE_'+str(n)]='AUTHORIZATION: basic '+base64.b64encode(('x-access-token:'+env['GH_TOKEN']).encode()).decode();env['GIT_TERMINAL_PROMPT']='0'
started=datetime.now(timezone.utc).isoformat();lookup=subprocess.run(['git','ls-remote','--heads',url,ref],env=env,capture_output=True,timeout=60);(out/'expected-head-lookup.log').write_bytes(lookup.stdout+lookup.stderr)
assert lookup.returncode==0 and lookup.stdout.decode().split()[0]==expected,'remoteexpectedheadmismatch;no push attempted'
cmd=['git','push','--no-force','--porcelain',url,head+':'+ref]
try:run=subprocess.run(cmd,env=env,capture_output=True,timeout=180)
except subprocess.TimeoutExpired as e:
 (out/'push.log').write_bytes((e.stdout or b'')+(e.stderr or b''));(out/'receipt.json').write_text(json.dumps(dict(start=started,finish=datetime.now(timezone.utc).isoformat(),original_exit=None,timeout=180,ref_movement_unknown_until_fresh_lookup=True),indent=2)+'\n');raise
(out/'push.log').write_bytes(run.stdout+run.stderr);(out/'receipt.json').write_text(json.dumps(dict(command=cmd,start=started,finish=datetime.now(timezone.utc).isoformat(),original_exit=run.returncode,expected_head=expected,head=head,branch=branch,force=False,authentication='inheritedcredentialinmemoryonly,noargvlogfile',scope='normalGitpackandfastforward'),indent=2)+'\n');print(json.dumps(dict(repo=repo,head=head,original_exit=run.returncode)),flush=True);raise SystemExit(run.returncode)
