"""Closed retrospective native data and original transport custody."""
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
raw=Path('/workspace/scratch/ct80-current-original-checkpoint-08');assert json.loads((raw/'observation.json').read_text())['original_local_gate']==0
record('exact-source-checkpoint-08',raw,'Exact clean4378aef5 original automatic checkpoint43648364070/job132611114516 succeeds: whole257220B ZIP14135500155/SHAfb43c05e283ebc7853f2ee0118d72d3f6fd06a662420541ffbb9d8a2e580adf5/all28members/source Resume-tool-remote pack/meta-original receipt exact/localstatus-gate0/Git unchanged. Precedes retrospective partial diagnostic; unsigned transport only.')
raw=Path('/workspace/scratch/ct80-observer-partial-diagnostic-native-04')
for label in ['immediate-original-gate','compiler-runtime-custody','original-partial-analysis','whole-old-parity','orchestrator']:assert(raw/(label+'.exit')).read_text().strip()=='0',label
assert(raw/'whole-packet-omission.exit').read_text().strip()=='101' and not(raw/'invalid-omission-accepted.json').exists()
v=json.loads((raw/'actual-partial-vectors.json').read_text());assert v['full_cold_population_accepted'] is False and len(v['all_actual_complete_cold_records'])==18 and len(v['all_missing_or_incomplete_cold_records'])==102
record('observer-storage-partial-diagnostic-native-04',raw,'RETROSPECTIVE partial diagnostic after exact clean4378 original checkpoint/immediategate0: preserved original partial Rust analyzer0 validates all18 complete cold packets/output fields/monotone canonical ledgers and102 missing/incomplete, plus BOTH complete60-output reuse streams. New native whole-packet diagnostic0 compares ALL12 actual prior cold and BOTH prior whole60-output reuse packets/every cumulative ledger EXACTLY/no masks/dedup; retains all18 new whole packets and all102 missing/incomplete cases, full_cold_population_accepted=false. ACTUAL complete REUSED_DIRECT packet omission rejects101/no accepted output. Full actual compiler/runtime bytes and original analyzer guard18digest8cce5a91eda7899e7a148ea72b8fae33562944f59372c66e7b66dc0083878619 checked. Original full120 analyzer and full-population parity still101 from actualcold124; no waiver, source-vector price, population mixing, cold extrapolation, benchmark or speedup. Full source/actual executable/raw packet pairs/vectors retained for NEW19, unsigned only.')
