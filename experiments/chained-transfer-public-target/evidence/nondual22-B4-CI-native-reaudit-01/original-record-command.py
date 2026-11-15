"""Closed native/checkpoint I/O record; the observer04 panel remains live."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
def record(name,raw,statement):
 e=s/'evidence'/name;e.mkdir();shutil.copyfile(__file__,e/'original-record-command.py')
 index={p.relative_to(raw).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(raw.rglob('*')) if p.is_file()};(e/'whole-closed-raw-members.json').write_text(json.dumps(index,indent=2)+'\n')
 for p in sorted(raw.iterdir()):
  if not p.is_file() or p.suffix in ['.bin','.zip']:continue
  b=p.read_bytes();v=lzma.compress(b) if len(b)>60000 else b
  if len(v)<=60000:(e/(p.name+('.xz' if len(b)>60000 else ''))).write_bytes(v)
 cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',statement]
 for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
 print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
raw=Path('/workspace/scratch/ct80-current-original-checkpoint-06');assert json.loads((raw/'observation.json').read_text())['original_local_gate']==0
record('exact-source-checkpoint-06',raw,'Exact clean published77f92af5 original automatic checkpoint43644156535/job132598070915 succeeds: whole245735B artifact14133128098/SHA9342f6eb21eface3eb30eeebfadbdeddc34fb4134a62e55ce3b2179a8f0e012e/all28members, exact source Resume/tool/remote pack-meta readback/original receipt and local status/gate0, Git unchanged. Precedes allthree bounded detached native launchers. Unsigned transport, not mathematical/performance acceptance.')
raw=Path('/workspace/scratch/ct80-twisted-pair-native-01');assert(raw/'native.exit').read_text().strip()=='101'
record('twisted-pair-native-helper-failure-01',raw,'Fixed twisted-pair native01 after exact77 original checkpoint/immediategate0 and actual compiler/runtime source/binary custody/prior981guards0 exits101. Original old kernel constructors execute, then recipe-forward comparison calls the ORIGINAL degree169-only helper with a degree13 map: assertion actual13 versus required169 at generated/lib.rs172. The new degree13-specific helper already exists and is used for signed dual, but the forward call was missed. This is a helper API wiring defect before any new order/generator/model result, not a mathematical negative. Preserve whole source/actual binary/native failure; correct ONLY the forward recipe call,120bound rebuild with same original prepared-engine/cache and rerun under new exact checkpoint. No field/model/budget change or signed claim.')
raw=Path('/workspace/scratch/ct80-B4-new22-CI-native-audit-01');assert(raw/'orchestrator.exit').read_text().strip()=='0'
phases=[x.split() for x in(raw/'phases.txt').read_text().splitlines()];assert len(phases)==10 and all(a==b for _,a,b in phases)
record('nondual22-B4-CI-native-reaudit-01',raw,'Independent local re-audit of actual originalB4 CI147-member artifact after exact clean77 original checkpoint/gate0: TEN original-Rust checks match expected exits, all4/6/5/9 WHOLE ordered native records exact/no masks/no dedup, FOUR actual complete-record omissions101/no output, BOTH actual original backtrack raw records accepted by original data auditors0. Runs retained CI actual Rust binaries with exact bytes, only executable mode restored after artifact transport. SourceB4 CI23successful occurrences/22distinct/signskipped and fullZIP/log preserved5048c2. This is unsigned independent re-audit, not signed execution, global geometry, original fullcold120 or performance acceptance.')
