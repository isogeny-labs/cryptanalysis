"""Closed replay/math custody projection; complete bulky raw remains for NEW19."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
def record(name,raw,statement,extra=[]):
 e=s/'evidence'/name;e.mkdir();shutil.copyfile(__file__,e/'original-record-command.py');inventory={}
 for p in sorted(raw.rglob('*')):
  if p.is_file():inventory[p.relative_to(raw).as_posix()]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 (e/'whole-closed-raw-members.json').write_text(json.dumps(inventory,indent=2)+'\n')
 for p in [*sorted(raw.glob('*')),*extra]:
  if not p.is_file() or p.suffix=='.bin':continue
  b=p.read_bytes();encoded=lzma.compress(b) if len(b)>60000 else b
  if len(encoded)>60000:continue
  (e/(p.name+('.xz' if len(b)>60000 else ''))).write_bytes(encoded)
 cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',statement]
 for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
 print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
raw=Path('/workspace/scratch/ct80-nondual22-full-03');assert(raw/'original.exit').read_text().strip()=='0'
phases=[line.split() for line in(raw/'phases.txt').read_text().splitlines()];assert len(phases)==39 and all(a==b for _,a,b in phases)
record('nondual22-physical-replay-03',raw,'Fresh physical03 replay of clean publishedb4e35430/producer3d49 completes39 actual phases with every expected exit, including FOUR whole-record omissions101 and TWO actual old-dual backtracks101. Four unfiltered native preflights and all4/6/5/9 whole ordered records exact/no masks/no dedup. Explicit900bound unchanged-engine preparation and120bound wrappers0, complete actual prepared/current/dependency library bytes equal with fresh reuse, actual compiler/runtime test binaries copied and equal. Both original Lean gates and allthree exact bindings0; original980/final source guards0; original runner0. Exact original automatic checkpoint9b9c7d and immediate gate0 precede launch. D12/D24 negatives stay negative. Projection includes whole raw index; every bulky raw/source/binary preserved for NEW19. Unsigned correctness replay only, no old-full-cold120 satisfaction or computational advantage.',[Path('/workspace/scratch/ct80_run_nondual22_full_03.sh'),Path('/workspace/scratch/ct80-nondual22-immediate-gate-03.txt')])
raw=Path('/workspace/scratch/ct80-observer-validation-02');assert(raw/'math-native.exit').read_text().strip()=='0' and (raw/'math-whole-compare.exit').read_text().strip()=='0' and(raw/'primitive-native.exit').read_text().strip()=='126'
record('observer-storage-math-and-mode-failure-02',raw,'Observer derivative b4e35430 after exact original checkpoint/immediategate0:120bound math wrappercompile0, actual original-engine fresh reuse/full bytes and actual Cargo test executable retained; FOUR unfiltered observer-DISABLED mathematical tests0 and allFOUR complete original native records exact/no masks0. Primitive-control launch then exits126 Permission denied because an I/O binary copy lost executable mode; primitive Rust code did NOT execute, later hook/census phases NOTRUN. Original failed command and copies preserved. This is a packaging failure after mathematical parity, not a semantic control failure or complete census. Correct only copy mode and resume remaining phases under a new exact checkpoint; no need to repeat passing math. Full raw/index/executables retained for NEW19; unsigned.',[])
