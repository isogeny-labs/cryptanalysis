"""Compile the exact final conditional proof under both unchanged original gates."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
raw=Path('/workspace/scratch/ct102-rank-proof-gates-01');raw.mkdir();shutil.copyfile(__file__,raw/'original-command.py')
source=Path('/workspace/scratch/ct102-rank-proof-attempt-03/RelationKernel.lean');shutil.copyfile(source,raw/source.name)
assert(source.parent/'original.exit').read_text().strip()=='0'
env=dict(os.environ,PATH='/home/agent/.cargo/bin:/home/agent/.elan/bin:'+os.environ['PATH'])
rows=[]
for name,repo,pin in [('consumer','/workspace/cryptanalysis','leanprover/lean4:v4.34.1'),('producer','/workspace/crypto','leanprover/lean4:v4.35.0')]:
 r=Path(repo);stage=r/'target/ct102-relation-kernel-proof-01';stage.mkdir();shutil.copyfile(source,stage/source.name)
 cmd=['timeout','120','env','ELAN_TOOLCHAIN='+pin,'bash','tools/lean/proof-gate.sh','--out',str(raw/(name+'-proofs')),(stage/source.name).relative_to(r).as_posix()]
 with(raw/(name+'.txt')).open('xb')as f:q=subprocess.run(cmd,cwd=r,env=env,stdout=f,stderr=subprocess.STDOUT)
 (raw/(name+'.exit')).write_text(str(q.returncode)+'\n');print(name,q.returncode,flush=True)
 rows.append(dict(name=name,command=cmd,actual_exit=q.returncode,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
 assert q.returncode==0
(raw/'commands.json').write_text(json.dumps(rows,indent=2)+'\n')
