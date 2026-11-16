"""Gate and compile/run complete-population Rust reporting; Python is I/O only."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,shutil,subprocess
r=Path('/workspace/cryptanalysis');o=Path('/workspace/scratch/ct103-character-summary-native-01');o.mkdir();shutil.copyfile(__file__,o/'original-command.py');source=Path('/workspace/scratch/ct103-character-summary-source-01/summary.rs');shutil.copyfile(source,o/'actual-source.rs')
assert not subprocess.check_output(['git','status','--porcelain'],cwd=r)
env=dict(os.environ,PATH='/home/agent/.cargo/bin:/home/agent/.elan/bin:'+os.environ['PATH'])
def run(label,cmd):
 q=subprocess.run(cmd,cwd=r,env=env,capture_output=True);(o/(label+'.txt')).write_bytes(q.stdout+q.stderr);(o/(label+'.exit')).write_text(str(q.returncode)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0
run('immediate-original-gate',['bash','scripts/checkpoint.sh','gate'])
deps=Path('/dev/shm/ct102-original-relation-rank-target-01/release/deps');libraries=list(deps.glob('libserde_json-*.rlib'));assert len(libraries)==1
command=['timeout','120','rustc','--edition','2021','-O',str(source),'--extern','serde_json='+str(libraries[0]),'-L','dependency='+str(deps),'-o',str(o/'actual-summary.bin')]
run('compile',command);shutil.copy2(o/'actual-summary.bin',o/'before-summary.bin')
input=Path('/workspace/scratch/ct103-original-relation-character-native-01/whole60-source-character-verdict.json')
run('whole-population-summary',['timeout','120',str(o/'actual-summary.bin'),str(input),str(o/'complete-summary.json')])
assert(o/'actual-summary.bin').read_bytes()==(o/'before-summary.bin').read_bytes()
(o/'custody.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),whole_input_sha256=hashlib.sha256(input.read_bytes()).hexdigest(),binary_sha256=hashlib.sha256((o/'actual-summary.bin').read_bytes()).hexdigest(),actual_compile_command=command,reporting_only=True,all60_call_results_consumed=True,scope='unsigned derived reporting from complete already accepted auditor; no new solver or mathematical experiment'),indent=2)+'\n')
