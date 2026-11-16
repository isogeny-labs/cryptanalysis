"""Execute the unchanged conditional checked-answer/log-ratio proofs under both original gates."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,shutil,subprocess
r=Path('/workspace/cryptanalysis');producer=Path('/workspace/crypto');study=r/'experiments/chained-transfer-public-target';raw=Path('/workspace/scratch/ct96-original-model-IC-reused-proof-01');raw.mkdir();shutil.copyfile(__file__,raw/'original-command.py')
source=study/'new-target-ic/lean/NewTargetIC.lean';stage=producer/'target/ct96-original-model-IC-proof-stage-01';stage.mkdir();shutil.copyfile(source,stage/source.name);shutil.copyfile(source,raw/'actual-NewTargetIC.lean')
env=dict(os.environ,PATH='/home/agent/.cargo/bin:/home/agent/.elan/bin:'+os.environ['PATH'])
commands=[('consumer',r,'leanprover/lean4:v4.34.1',source.relative_to(r).as_posix()),('producer',producer,'leanprover/lean4:v4.35.0',(stage/source.name).relative_to(producer).as_posix())]
receipts=[]
for name,repo,toolchain,module in commands:
 cmd=['timeout','120','env','ELAN_TOOLCHAIN='+toolchain,'bash','tools/lean/proof-gate.sh','--out',str(raw/(name+'-proofs')),module]
 with(raw/(name+'.txt')).open('xb')as f:q=subprocess.run(cmd,cwd=repo,env=env,stdout=f,stderr=subprocess.STDOUT)
 (raw/(name+'.exit')).write_text(str(q.returncode)+'\n');print(name,q.returncode,flush=True);assert q.returncode==0
 logs=list((raw/(name+'-proofs')).rglob('audit.log'));assert len(logs)==1
 text=logs[0].read_text();assert 'audited 2 theorems'in text and'0 failing, 0 trusted (native_decide)'in text
 receipts.append(dict(gate=name,command=cmd,actual_exit=q.returncode,declarations=2,trusted=0))
(raw/'outcome.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),reused_source=str(source),source_sha256=hashlib.file_digest(source.open('rb'),'sha256').hexdigest(),original_exact_binding_ids=['PCC-20261113-01efbf','PCC-20261113-671d42'],gates=receipts,scope='reuses existing conditional checked-target soundness and common-offset log-ratio statements only; actual transfer/model/program/order/relation-log bridges remain explicit, no solver completeness or cost proof'),indent=2)+'\n')
