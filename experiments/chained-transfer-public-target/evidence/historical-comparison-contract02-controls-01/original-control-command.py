from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
p=Path('/workspace/scratch/ct100-historical-audit-controls-01');p.mkdir();exe=Path('/dev/shm/ct100-original-fixed-IC-CI-layout-01/whole-output-02-build-cache/release/audit-original-fixed-ic-historical');shutil.copyfile(exe,p/'actual-compiled-auditor.bin');assert exe.read_bytes()==(p/'actual-compiled-auditor.bin').read_bytes();rows=[]
def run(n,args,want):
 q=subprocess.run([str(exe),*args],capture_output=True,timeout=120);(p/(n+'.txt')).write_bytes(q.stdout+q.stderr);(p/(n+'.exit')).write_text(str(q.returncode)+'\n');assert q.returncode==want,(n,q.returncode,q.stderr[:500]);rows.append(dict(name=n,command=[str(exe),*args],actual_exit=q.returncode));print(n,q.returncode,flush=True)
for family,expected,fresh in [('original-ic','/workspace/scratch/ct100-original-fixed-IC-CI-local-02/whole-output/original-ic-expected.json','/workspace/scratch/ct100-original-fixed-IC-CI-local-02/whole-output/original-ic-whole-frozen.json'),('original-sampler','/workspace/scratch/ct97-original-fixed-model-sampler-native-01/all-whole-compared.json','/workspace/scratch/ct97-original-fixed-model-sampler-native-01/all-whole-compared.json')]:
 run(family+'-whole-positive',['--compare',family,expected,fresh,str(p/(family+'-whole-positive.json'))],0)
 mutations=p/(family+'-whole-controls');run(family+'-materialize-controls',['--mutations',family,expected,str(mutations)],0)
 for name in ['missing-record-class','changed-scalar','changed-counter','unexpected-report-field','timing-only']:
  accepted=p/(family+'-'+name+'-accepted.json');want=0 if name=='timing-only'else 1;run(family+'-'+name,['--compare',family,str(mutations/(name+'.json')),fresh,str(accepted)],want);assert accepted.exists()==(want==0)
assert exe.read_bytes()==(p/'actual-compiled-auditor.bin').read_bytes()
(p/'outcome.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),published_contract='b5e431/5493385 before source',commands=rows,whole_positive_inputs='IC entire independent fresh02 vs historical100; sampler entire historical101 vs itself, not a fresh sampler execution',whole_timing_only_positives=2,whole_modified_negative_inputs=8,all_negative_exits=1,all_negative_accepted_outputs_absent=True,actual_auditor_sha256=hashlib.file_digest(exe.open('rb'),'sha256').hexdigest(),actual_compiled_before_after_bytes_equal=True,scope='comparison contract controls only; full fresh driver03/GitHubCI still pending'),indent=2)+'\n')
