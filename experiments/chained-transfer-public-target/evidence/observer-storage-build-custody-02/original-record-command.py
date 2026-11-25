"""I/O-only closed checkpoint/unit/build evidence; live panels remain untouched."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
def record(name,statement,files):
 e=s/'evidence'/name;e.mkdir();shutil.copyfile(__file__,e/'original-record-command.py')
 for label,p in files:
  b=p.read_bytes();(e/(label+('.xz' if len(b)>60000 else ''))).write_bytes(lzma.compress(b) if len(b)>60000 else b)
 cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',statement]
 for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
 print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
o=Path('/workspace/scratch/ct80-current-original-checkpoint-04')
assert json.loads((o/'observation.json').read_text())['original_local_gate']==0
record('exact-source-checkpoint-04','Exact clean b4e35430 original automatic checkpoint43638366539/job132580093749 succeeds: complete232771B artifact14131252028/SHA9d90176fd1a29531864ce2b367889cbcf62426bfc7da87c0258b29e590c2ad28/all28members, exact source Resume/tool/remote pack-meta readback and original receipt imported, original local status/gate0 and unchanged Git state. No manual dispatch occurred. Initial connector filter returned0 then all-events query1 before remaining automatic jobs appeared; unsupported specific-workflow connector400 and direct-urllib401 are retained outside raw checkpoint root. This is unsigned checkpoint transport, not native or performance acceptance.',[(p.name,p) for p in sorted(o.iterdir()) if p.is_file() and p.name not in ['whole-original-GitHub-artifact.zip']])
o=Path('/workspace/scratch/ct80-observer-unit-native-03');assert(o/'native.exit').read_text().strip()=='0'
record('observer-storage-unit-03','Observer-storage source b4e35430 ONE unfiltered enabled native unit test0/1passed0filtered after exact current original checkpoint and immediate localgate0. Complete actual Cargo compiler/runtime bytes and compiled source equal; local zero/collision/overflow and foreign first-entry zero/phase/scope/snapshot controls retained inside the original comprehensive test. All original24source guards0. Mathematical parity/real hook controls/full cold census/whole-old-packet parity remain pending; no signed execution or performance claim.',[(p.name,p) for p in sorted(o.iterdir()) if p.is_file() and p.suffix!='.bin'])
o=Path('/workspace/scratch/ct80-observer-storage-build-02')
record('observer-storage-build-custody-02','Observer derivative sourceb4: unchanged-engine package preparation900bound compile0, frontend120bound compile0. Original custody helper then fails1 because expected3 executables while unchanged frontend actually defines2. Exact failure retained, no native execution in that build command. Post-failure I/O supplement captures BOTH actual complete compiler binaries and validates actual fresh engine profile/source/whole-library-byte reuse0 without recompilation. Whole build/raw/libraries/executables retained for NEW19; not a native or benchmark pass.',[(p.name,p) for p in sorted(o.iterdir()) if p.is_file() and p.suffix!='.bin'])
