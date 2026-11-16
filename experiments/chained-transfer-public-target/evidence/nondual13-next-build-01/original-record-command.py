"""Build/source/binary custody; does not execute research arithmetic."""
from pathlib import Path
import hashlib,json,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';e=s/'evidence/nondual13-next-build-01';e.mkdir()
rows=[]
for label in ['edge','model']:
 raw=Path('/workspace/scratch/ct77-next-'+label+'-build-01')
 files=['lock.txt','lock.exit','compile.stderr.txt','compile.exit','original-command.sh']
 if label=='edge':files+=['control-compile.stderr.txt','control-compile.exit','actual-binaries.json']
 for name in files:shutil.copyfile(raw/name,e/(label+'-'+name))
 if label=='model':
  artifacts=[json.loads(v)for v in(raw/'compile.jsonl').read_text().splitlines()];bins=[v for v in artifacts if v.get('reason')=='compiler-artifact'and v.get('executable')];assert len(bins)==1
  p=Path(bins[0]['executable']);dst=raw/'actual-test-executable.bin';shutil.copy2(p,dst);v=dict(cargo_artifact=bins[0],actual_copy=str(dst),bytes=dst.stat().st_size,sha256=hashlib.sha256(dst.read_bytes()).hexdigest());(e/'model-actual-binary.json').write_text(json.dumps(v,indent=2)+'\n')
 for p in sorted(raw.rglob('*')):
  if p.is_file():rows.append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(e/'whole-build-index.json').write_text(json.dumps(rows,indent=2)+'\n')
for label,path in [('edge',s/'nondual13-next-preflight'),('model',s/'nondual13-next-preflight/models')]:
 shutil.copyfile(path/'generated/custody.json',e/(label+'-literal-custody.json'))
guard=s/'nondual13-next-preflight/frozen-prior-inputs-01.sha256'
paths=subprocess.check_output(['git','ls-files','-z','--',str(s.relative_to(r)/'nondual13-preflight')],cwd=r).split(b'\0')
entries=[]
for name in sorted(x.decode()for x in paths if x):
 p=r/name;assert p.is_file();entries.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+name+'\n')
guard.write_text(''.join(entries));q=subprocess.run(['sha256sum','--check',str(guard)],cwd=r,capture_output=True);(e/'prior-inputs-guard.txt').write_bytes(q.stdout+q.stderr);(e/'prior-inputs-guard.exit').write_text(str(q.returncode)+'\n');assert q.returncode==0
(e/'scope.json').write_text(json.dumps(dict(protocol='bbfd74 published9038f2b9 BEFORE all new third-edge code',edge='lock/build/test-no-run/control-build0, actual source and both executables captured',model='lock/build/test-no-run0, source and actual executable captured',native='NOT RUN: no E3, new model or new mathematical observation asserted',literal='original engine/previous SecondHop bodies and original model/helper/second-source/second-transport prefixes exact',record_kind_note='new model test retains TWO actual prior-constructor kernel-gate records; future whole comparator must preserve every occurrence, no deduplication',selection='same actual G2, its original smooth/nonsquare unsupported row retained; new G3fixed BEFORE model builder; allsix outcomes',prior_guards=len(entries),scope='unsigned build custody only; no new mathematical, timing, cost or signed execution standing'),indent=2)+'\n')
shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','After prospectivebbfd74/9038f2b9, additive fixed-third-edge and full same-kernel model source compile0, both120sboundedbuilds and actualtest/control executables/sourceclosures retained. Literaloriginalengine/SecondHop/model/source/even/torsion plusprevioussecond appendices exact. Newmiddle169rational/gcd12vs168/control101 and full64/4096/135/E0E1E2parity/allsixcases implemented, nativeNOTRUN; no E3 ormatchedJ3outcome. Prior-sourceguard pins all tracked predecessorpreflightinputs; allold929/21workflows unchanged. Newmodel will print two actual oldconstructor kernelrecords, future strict whole comparator must retain both occurrences. Unsigned buildcustody/no mathematical-computationalgain or novelty.']
for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
