"""Preserve the first whole native attempt and its diagnostic field-shape failure."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';raw=Path('/workspace/scratch/ct86-original-prime-native-01');e=s/'evidence/original-prime-native-failure-01';e.mkdir();text=(raw/'native.txt').read_text()
assert(raw/'native.exit').read_text().strip()=='101'and(raw/'original.exit').read_text().strip()=='1';assert Path('/workspace/scratch/ct86-original-prime-native-supervisor-01.exit').read_text().strip()=='1'
assert 'assertion failed: x[3..].iter().all(|&v| v == 0)'in text and '0 passed; 1 failed'in text
rows=[]
for line in text.splitlines():
 if'N4_'in line:
  kind,body=line[line.index('N4_'):].split(' ',1);rows.append(dict(kind=kind,data=json.loads(body)))
assert len(rows)==8 and rows[-1]['kind']=='N4_ORIGINAL_PRIME_SETUP'
for n in ['immediate-original-gate','runtime-custody','initial-prior']:assert(raw/(n+'.exit')).read_text().strip()=='0'
for name in ['freeze1077.exit','compare1077.exit','all1077-expected.json','all1077-compared.json']:assert not(raw/name).exists()
for name,cmd in [('postfailure-terminal-prior',['sha256sum','--check',str(s/'original-prime-chain-01/frozen-prior-inputs-01.sha256')]),('postfailure-test-bytes',['cmp',(raw/'chain-actual-path.txt').read_text().strip(),str(raw/'actual-before-native-chain.bin')]),('postfailure-auditor-bytes',['cmp',(raw/'auditor-actual-path.txt').read_text().strip(),str(raw/'actual-before-native-auditor.bin')])]:
 q=subprocess.run(cmd,cwd=r,capture_output=True);(raw/(name+'.txt')).write_bytes(q.stdout+q.stderr);(raw/(name+'.exit')).write_text(str(q.returncode)+'\n');assert q.returncode==0
for q in sorted(raw.iterdir()):
 if q.is_file()and q.suffix!='.bin'and q.name not in ['old-sixteen.json']:
  b=q.read_bytes();v=lzma.compress(b)if len(b)>60000 else b;name=q.name+'.xz'if len(b)>60000 else q.name
  if len(v)<65536:(e/name).write_bytes(v)
for n in ['start','finish','exit','txt']:shutil.copyfile('/workspace/scratch/ct86-original-prime-native-supervisor-01.'+n,e/('supervisor.'+n))
(e/'completed-whole-records.json').write_text(json.dumps(rows,indent=2)+'\n')
inv={q.relative_to(raw).as_posix():dict(bytes=q.stat().st_size,sha256=hashlib.sha256(q.read_bytes()).hexdigest())for q in sorted(raw.rglob('*'))if q.is_file()};(e/'whole-unfiltered-raw-inventory.json').write_text(json.dumps(dict(root=str(raw),all_files=inv,future_custody='NEW23; actual failure/input/source/executable/checkpoint/prepared bytes retained'),indent=2)+'\n')
(e/'outcome.json').write_text(json.dumps(dict(source='48262e0a83edc271e78e2a2eee90f510de335757',build='02',checkpoint='14/all28/immediate originalgate0',native=101,worker=1,supervisor=1,completed_records=8,completed='all seven original constructor records and whole setup; first source-model record not emitted',observed='cubic-coordinate formatter receives degree6 line-offset encoding; original NormNew uses degree6 field and original PhaseA point_json preserves six coefficients',classification='diagnostic serialization/program failure before full population; not a counterexample to prime-group algebra',whole1077_parity=False,omission_controls='NOT RUN',all_postfailure1131_guards_and_binary_bytes=0,next='retain full six line-offset coordinates with original shape, preserving all models/fields/masks/samples/counts/math/criteria; new compiled source and exact checkpoint before a new full attempt'),indent=2)+'\n')
shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Original-prime first UNFILTERED native attempt atpublished48262e0/build02/exactoriginal checkpoint14/all28/immediate gate0 fails101, worker/supervisor1. Whole eight completed records retain seven original constructors and setup; first source-model diagnostic serialization calls cubic three() on actual degree6 NormNew line-offset coordinates and asserts trailingzero. Original NormNew field and PhaseA six-coordinate point formatter identify the shape mismatch. Whole1077 parity is FALSE/notcompleted; freeze/compare/omission controls NOTRUN, no acceptedfixture. Whole failure/stdout/inputs/source/executables preserved; postfailureall1131guards and bothactual binaries exact0. Repair must preserve six diagnostic coordinates only, with every source/model/field/mask/sample/population/math/criterion fixed; publish newlycompiled source and newexactcheckpoint before onefullattempt. Unsigned observed program/diagnostic failure, not mathematical impossibility or successful prime chain.']
for p in sorted(e.rglob('*')):
 if p.is_file():cmd+=['--proof','attestation:'+str(p.relative_to(r))]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct86-original-prime-native-failure.claim.txt').write_text(claim+'\n');print(claim,flush=True)
