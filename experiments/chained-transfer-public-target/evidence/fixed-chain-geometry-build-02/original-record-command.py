"""Retain the actual failed whitespace gate and corrected-source build."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';old=Path('/workspace/scratch/ct82-fixed-chain-geometry-build-01');raw=old.with_name('ct82-fixed-chain-geometry-build-02')
g=s/'evidence/beta-fixed-chain-phaseA-compiled-source-governance-01'
assert(g/'cached-whitespace.exit').read_text().strip()=='2'
assert(g/'cached-whitespace.txt').read_text()=='experiments/chained-transfer-public-target/fixed-jacobian-chain-01/Cargo.toml:23: new blank line at EOF.\n'
assert(raw/'original.exit').read_text().strip()=='0'
for name in ['prior-inputs','metadata','original-engine-preparation','geometry-compile','final-prior-inputs']:assert(raw/(name+'.exit')).read_text().strip()=='0'
before=old/'actual-source';after=raw/'actual-source';differences=[]
for p in before.rglob('*'):
 if p.is_file()and p.read_bytes()!=(after/p.relative_to(before)).read_bytes():
  assert p.relative_to(before).as_posix()=='Cargo.toml'
  assert p.read_bytes().rstrip()+b'\n'==(after/'Cargo.toml').read_bytes()
  differences.append(dict(path='Cargo.toml',old_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),corrected_sha256=hashlib.sha256((after/'Cargo.toml').read_bytes()).hexdigest(),change='remove only extra EOF blank line; original captured source remains intact'))
assert len(differences)==1
e=s/'evidence/fixed-chain-geometry-build-02';e.mkdir()
for p in sorted(raw.iterdir()):
 if p.is_file()and p.suffix!='.bin':
  b=p.read_bytes();(e/(p.name+'.xz'if len(b)>60000 else p.name)).write_bytes(lzma.compress(b)if len(b)>60000 else b)
members={p.relative_to(raw).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in sorted(raw.rglob('*'))if p.is_file()}
(e/'whole-local-raw-inventory.json').write_text(json.dumps(dict(raw_root=str(raw),all_unfiltered_files=members,explicit_source_changes=differences,source_added_after_original_build=['run-native-01.sh','runtime_custody.py'],previous_failed_gate=str(g.relative_to(r)),scope='Original failed gate and passing build01 retained. Corrected build02 has only manifest EOF change plus added native driver; no mathematical source change. Raw bytes local for NEW22.'),indent=2)+'\n')
shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Retained actual governance cached-whitespace2 at new Cargo manifest EOF; original compiled build01 and failed governance remain intact. Removed only extra EOF blank line, added native driver, and corrected-source build02 prior1060/locked metadata/original-engine preparation/120s test no-run/finalguards all0; exact actual prepared engine reuse and full source/binary bytes retained. No mathematical source changed. NativeNOTRUN; publish corrected compiled source and exact originalcheckpoint next. Unsigned local raw for NEW22, no waiver, complete-Jacobian execution, cost or signed promotion.']
for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
for p in sorted(g.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();print(claim,flush=True)
for p in [r/'.resume/RESUME.md',s/'CHECKPOINT.md',s/'RESEARCH_QUEUE.md']:
 p.write_text('# Corrected compiled manifest; original failed whitespace gate retained\n\n'+claim+': build02 is the current exact compiled source at /workspace/scratch/ct82-fixed-chain-geometry-build-02, all phases0. Only Cargo EOF whitespace correction plus native driver added; original build01 and actual cached-whitespace2 remain preserved. Native NOT RUN. Publish corrected source, obtain exact original checkpoint, then run one unfiltered900s/2GiB PhaseA test. Published5caf67 complete PhaseB-D workload unchanged. [pcc:unverified]\n\n---\n\n'+p.read_text())
p=r/'docs/session-logs/2026-11-15.md';p.write_text(p.read_text().rstrip()+'\n\n'+claim+': preserved actual cached-whitespace2 at Cargo EOF and complete passing build01; corrected manifest EOF only and added native driver. Build02 all phases0, nativeNOTRUN, exact source publication/checkpoint next. No waiver or mathematical source change. [pcc:unverified]\n')
Path('/workspace/scratch/ct82-geometry-build02.claim.txt').write_text(claim+'\n')
