"""Ordinary research-branch fast-forward after the single active ledger checkpoint; no rewrite."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
r=Path('/workspace/cryptanalysis');raw=Path('/workspace/scratch/ct95-single-consumer-ledger-fast-forward-01');raw.mkdir();shutil.copyfile(__file__,raw/'original-command.py')
old='25801fe6aaba49674ef010e814dc7c9a58c28247';new='41e35d8c701484a6ca5406ecbf7bb83278be6073'
original='research/chained-transfer-public-target-20261113';isolated='research/chained-transfer-induced-map-20261115'
def output(cmd):return subprocess.check_output(cmd,cwd=r)
assert not output(['git','status','--porcelain'])
assert output(['git','branch','--show-current']).decode().strip()==isolated
assert output(['git','rev-parse','HEAD']).decode().strip()==new
assert output(['git','rev-parse',original]).decode().strip()==old
subprocess.run(['git','merge-base','--is-ancestor',old,new],cwd=r,check=True)
remote=output(['git','ls-remote','--heads','origin',original]).decode().split();assert remote==[old,'refs/heads/'+original]
before=output(['git','show',old+':pcc/ledger.jsonl']);after=(r/'pcc/ledger.jsonl').read_bytes();assert after.startswith(before)
for name,cmd in [('switch',['git','switch',original]),('normal-fast-forward',['git','merge','--ff-only',isolated])]:
 q=subprocess.run(cmd,cwd=r,capture_output=True);(raw/(name+'.txt')).write_bytes(q.stdout+q.stderr);(raw/(name+'.exit')).write_text(str(q.returncode)+'\n');assert q.returncode==0
assert output(['git','rev-parse','HEAD']).decode().strip()==new
assert(r/'pcc/ledger.jsonl').read_bytes()==after
cmd=['python3','/workspace/scratch/publish_normal_git_checkpoint.py','isogeny-labs/cryptanalysis',old,new,original,str(raw/'normal-publication')]
q=subprocess.run(cmd,cwd=r,capture_output=True);(raw/'normal-publication-caller.txt').write_bytes(q.stdout+q.stderr);(raw/'normal-publication-caller.exit').write_text(str(q.returncode)+'\n');assert q.returncode==0
assert not output(['git','status','--porcelain'])
receipt=dict(at=datetime.now(timezone.utc).isoformat(),old=old,new=new,original_branch=original,isolated_branch=isolated,ordinary_fast_forward=True,normal_publication_exit=0,old_ledger_bytes=len(before),new_ledger_bytes=len(after),old_ledger_sha256=hashlib.sha256(before).hexdigest(),new_ledger_sha256=hashlib.sha256(after).hexdigest(),entire_old_ledger_prefix_preserved=True,no_ledger_append_on_original_before_FF=True,sole_active_ledger_writer_now=original,no_rebase_rechain_force_or_merge=True,scope='normal branch and ledger custody only; fresh workflow execution pending')
(raw/'outcome.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
