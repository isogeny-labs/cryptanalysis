"""Replay the exact new proof driver with sparse original tool worktrees; I/O orchestration only."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,shutil,subprocess
w=Path('/workspace');raw=w/'scratch/ct95-induced-proof-driver-local-01';raw.mkdir()
shutil.copyfile(__file__,raw/'original-command.py')
commands=[]
def run(name,cmd,cwd):
 with(raw/(name+'.txt')).open('xb')as f:q=subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT)
 (raw/(name+'.exit')).write_text(str(q.returncode)+'\n');commands.append(dict(name=name,command=cmd,cwd=str(cwd),actual_exit=q.returncode));print(name,q.returncode,flush=True)
 assert q.returncode==0,(name,q.returncode)
consumer=w/'cryptanalysis';pin=(consumer/'experiments/chained-transfer-public-target/upstream-commit.txt').read_text().strip()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=consumer,text=True).strip()
for name,revision,patterns in [('crypto',pin,['/tools/lean/']),('cryptanalysis',head,['/tools/lean/','/tools/pcc/','/pcc/keyring.json','/pcc/claims/','/experiments/chained-transfer-public-target/original-induced-transfer-01/','/experiments/chained-transfer-public-target/evidence/original-induced-full-transfer-proof-01/','/experiments/chained-transfer-public-target/upstream-commit.txt'])]:
 repo=w/name;dest=raw/name
 run(name+'-worktree',['git','worktree','add','--detach','--no-checkout',str(dest),revision],repo)
 run(name+'-sparse',['git','sparse-checkout','set','--no-cone',*patterns],dest)
 run(name+'-checkout',['git','checkout','--detach',revision],dest)
src=consumer/'experiments/chained-transfer-public-target/ci_induced_transfer';dst=raw/'cryptanalysis'/src.relative_to(consumer)
shutil.copytree(src,dst)
workflow=Path('.github/workflows/chained-transfer-induced-proof.yml');(raw/'cryptanalysis'/workflow).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(consumer/workflow,raw/'cryptanalysis'/workflow)
manifest={str(p.relative_to(raw/'cryptanalysis')):dict(bytes=p.stat().st_size,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest())for p in list(dst.rglob('*'))+[raw/'cryptanalysis'/workflow]if p.is_file()}
(raw/'prospective-local-uncommitted-driver-source.json').write_text(json.dumps(dict(consumer_parent=head,producer_exact_original=pin,source_files=manifest,scope='precommit local driver validation; added driver/workflow files are explicitly untracked at the recorded consumer parent; not GitHub CI acceptance'),indent=2)+'\n')
env=dict(os.environ,PATH='/home/agent/.cargo/bin:/home/agent/.elan/bin:'+os.environ['PATH'])
cmd=['timeout','1500','bash',str(dst/'check-01.sh'),str(raw/'crypto'),str(raw/'whole-output')]
with(raw/'actual-driver.txt').open('xb')as f:q=subprocess.run(cmd,cwd=raw/'cryptanalysis',env=env,stdout=f,stderr=subprocess.STDOUT)
(raw/'actual-driver.exit').write_text(str(q.returncode)+'\n')
(raw/'outcome.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),actual_exit=q.returncode,command=cmd,consumer_parent=head,producer_original_pin=pin,prospective_source_manifest='prospective-local-uncommitted-driver-source.json',preparatory_commands=commands,scope='local complete new proof-driver validation only; no fresh GitHub CI or broader mathematical/program/cost standing'),indent=2)+'\n')
print('actual-driver',q.returncode,flush=True);assert q.returncode==0
