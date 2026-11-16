"""Closed source/CI/control data projection, preserving all whole raw externally."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
def record(name,raw,statement,selected):
 e=s/'evidence'/name;e.mkdir();shutil.copyfile(__file__,e/'original-record-command.py')
 index={p.relative_to(raw).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(raw.rglob('*')) if p.is_file()}
 (e/'whole-closed-raw-members.json').write_text(json.dumps(index,indent=2)+'\n')
 for p in selected:
  if not p.is_file():continue
  b=p.read_bytes();encoded=lzma.compress(b) if len(b)>60000 else b
  if len(encoded)>60000:continue
  dest=e/p.relative_to(raw);dest=dest.with_name(dest.name+('.xz' if len(b)>60000 else ''));dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(encoded)
 cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',statement]
 for p in sorted(e.rglob('*')):
  if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
 print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
raw=Path('/workspace/scratch/ct80-observer-validation-03')
for label,expected in [('primitive-native',0),('disabled-native',2),('FpR-omission-caller',0),('quadratic-omission-caller',0)]:assert(raw/(label+'.exit')).read_text().strip()==str(expected)
for family in ['actual-FpR-omission','actual-quadratic-omission']:
 for arm,expected in [('positive',0),('negative',101)]:assert(raw/family/(arm+'-native.exit')).read_text().strip()==str(expected)
assert not(raw/'panels/cold-panel.exit').exists() and not(raw/'panels/reused-panel.exit').exists()
successes=[p for p in(raw/'panels').glob('cold-*.exit') if p.name!='cold-panel.exit' and p.read_text().strip()=='0'];assert len(successes)==17
selected=[p for p in raw.rglob('*') if p.is_file() and p.suffix!='.bin' and 'panels' not in p.relative_to(raw).parts]
record('observer-storage-controls-interrupted-panel-03',raw,'Observer continuation03 after exact clean3fad original checkpoint/localgate0 preserves actual Cargo binary modes and prior four-test whole mathematical parity. Primitive controls0, disabled fixture admission2, ACTUAL FpR omitted-hook positive0/negative101 and quadratic omitted-hook positive0/negative101, complete actual compiler/copy custody retained. The original full panel is INTERRUPTED:17 separate cold success receipts, next started process without terminal receipt, NO cold-panel outcome and NO reuse result. Enclosing tool session56906 later returns Unknown process id; exact cause unknown. No124/0 is invented and full census/old-whole-packet acceptance remains unmet. Frozen source/raw/actual executables retained for NEW19. Resume fresh unchanged900+900 stages using a detached bounded supervisor after new exact checkpoint; do not repeat passing math/controls or change workload/bounds. Unsigned only.',selected)
raw=Path('/workspace/scratch/ct80-B4-new22-CI-acceptance-01');members=json.loads((raw/'whole-original-members.json').read_text());m=raw/'members'
assert(m/'original.exit').read_text().strip()=='0'
phases=[x.split() for x in(m/'phases.txt').read_text().splitlines()];assert len(phases)==39 and all(a==b for _,a,b in phases)
for label in ['second-edge','second-model','third-edge','third-model']:
 compiled=json.loads((m/(label+'-compiled-binary.json')).read_text());runtime=json.loads((m/(label+'-runtime-binary.json')).read_text());assert compiled['actual_path']==runtime['actual_path'] and compiled['sha256']==runtime['sha256'] and compiled['bytes']==runtime['bytes']
 for suffix in ['-original-compiled-test.bin','-actual-runtime-test.bin']:
  assert members[label+suffix]==dict(bytes=compiled['bytes'],sha256=compiled['sha256'])
record('nondual22-B4-CI-whole-custody-01',raw,'Original sourceb4 exact CI API collection after50min cadence reports23 successful run occurrences/22 distinct workflows (two pcc-gates; BOTH sign jobs skipped). Corrected22nd run43638366601/job132580094399 success; entire original6660523char API-log representation and34823262B ZIP14130459991/SHA2dcafafd1682141eafccdd7116a3487d09ac90372ecaf41fc52a1ed187880bba/all147members retained. Original artifact has39 matched expected phase exits/runner0, all4 compiler/runtime binary paths+complete hashes match both actual ZIP copies; prepared-library alias receipt retained. This records API/outcome/I/O custody only; independent Rust re-audit of whole CI native records is NOTRUN. No signed standing,23-distinct inflation, originalfullcold120 or performance claim.',[p for p in raw.iterdir() if p.is_file() and p.name!='whole-original-artifact.zip'])
raw=Path('/workspace/scratch/ct80-twisted-pair-build-01');assert(raw/'orchestrator.exit').read_text().strip()=='0'
for label in ['prior981','metadata','original-engine-preparation','prepared-custody','twist-test-compile','test-executable-custody','reused-custody','auditor-compile','auditor-executable-custody','final-prior981']:assert(raw/(label+'.exit')).read_text().strip()=='0',label
record('twisted-pair-source-build-01',raw,'Fixed-pair f10846/3fad prospective source build01 passes original981 guards, locked offline metadata, explicit900bound unchanged-engine LIBRARY preparation in NEW cache, whole prepared library custody/actual fresh reuse and120bound wrapper compile0. ONE comprehensive unfiltered test binary and strict nine-whole-record Rust auditor compile0, full actual Cargo binary bytes/modes/source closures retained; final981 guards0. Literal original helpers/old hops/model constructor/finite-space helpers retained, explicit new generic Hasse certificate and metadata description only in derivative. Existing71014e eight-root proof remains immutable; new inverse-factor proof is separate. NO native ECDLP/new-order/generator/model/preflight result yet. Detached bounded build PID398128 records terminal0; original full cold120 remains unmet. Whole raw/source/binaries for NEW19, unsigned only.',[p for p in raw.iterdir() if p.is_file() and p.suffix!='.bin'])
