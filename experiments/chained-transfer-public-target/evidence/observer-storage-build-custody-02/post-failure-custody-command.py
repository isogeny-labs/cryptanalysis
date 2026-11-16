"""Post-failure I/O supplement: the unchanged frontend defines TWO binaries."""
from pathlib import Path
import hashlib,json,shutil,subprocess
o=Path('/workspace/scratch/ct80-observer-storage-build-02');layout=Path('/workspace/scratch/ct80-observer-storage-layout-02/derived-layout')
assert (o/'original-engine-preparation.exit').read_text().strip()=='0' and (o/'observer-compile.exit').read_text().strip()=='0'
rows=[json.loads(x) for x in(o/'observer-compile.txt').read_text().splitlines()];records=[]
for x in rows:
 if x.get('reason')=='compiler-artifact' and x.get('executable'):
  p=Path(x['executable']);q=o/(x['target']['name']+'.bin');assert q.read_bytes()==p.read_bytes()
  records.append(dict(Cargo_artifact=x,actual_copy=str(q),bytes=q.stat().st_size,sha256=hashlib.sha256(q.read_bytes()).hexdigest()))
assert {x['Cargo_artifact']['target']['name'] for x in records}=={'norm-halving-arithmetic-census','analyze'}
(o/'actual-executables-supplement.json').write_text(json.dumps(records,indent=2)+'\n')
q=subprocess.run(['python3',str(o/'capture-observer-engine.py'),str(o),str(layout/'crypto'),'reused'],capture_output=True)
(o/'post-failure-engine-reuse.txt').write_bytes(q.stdout+q.stderr);(o/'post-failure-engine-reuse.exit').write_text(str(q.returncode)+'\n');assert q.returncode==0
shutil.copyfile(__file__,o/'post-failure-custody-command.py')
(o/'post-failure-scope.json').write_text(json.dumps(dict(original_runner_exit=1,engine_compile=0,frontend_compile=0,original_expected_bin_count=3,actual_unchanged_frontend_bin_count=2,post_failure_whole_compiler_binary_copies=True,post_failure_actual_engine_reuse=0,recompiled=False,native='NOTRUN',scope='correct the custody-helper expectation only; original failed command and complete compiled bytes preserved'),indent=2)+'\n')
print('I/O supplement0; original helper failure retained; two actual executables; full engine reuse bytes equal')
