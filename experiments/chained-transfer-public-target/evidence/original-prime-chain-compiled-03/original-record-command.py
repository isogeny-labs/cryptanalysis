"""Compiled six-coordinate diagnostic correction; no changed research arithmetic."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';prior=Path('/workspace/scratch/ct86-original-prime-build-02');raw=Path('/workspace/scratch/ct86-original-prime-build-03');e=s/'evidence/original-prime-chain-compiled-03';e.mkdir()
assert(raw/'original.exit').read_text().strip()=='0'
for name in ['prior-inputs','metadata','inherited-preparation','chain-compile','auditor-compile','final-prior-inputs']:assert(raw/(name+'.exit')).read_text().strip()=='0'
diff=[]
for p in(prior/'actual-source').rglob('*.rs'):
 if p.read_bytes()!=(raw/'actual-source'/p.relative_to(prior/'actual-source')).read_bytes():diff.append(p.relative_to(prior/'actual-source').as_posix())
assert diff==['src/tests.rs'],diff
before=(prior/'actual-source/src/tests.rs').read_text();after=(raw/'actual-source/src/tests.rs').read_text();helper='''fn offset_json(p: Pt<ER>) -> Value {
    use chained_n4_paired_fourth_preflight::models::six;
    match p {
        Pt::Inf => Value::Null,
        Pt::Aff(x, y) => json!([six(x), six(y)]),
    }
}
''';assert before.replace('fn two_points(g: &Geometry) -> Vec<Pt<ER>> {',helper+'fn two_points(g: &Geometry) -> Vec<Pt<ER>> {').replace('.map(point_json)','.map(offset_json)')==after
for p in sorted(raw.iterdir()):
 if p.is_file()and p.suffix!='.bin':
  b=p.read_bytes();v=lzma.compress(b)if len(b)>60000 else b;name=p.name+'.xz'if len(b)>60000 else p.name;assert len(v)<65536;(e/name).write_bytes(v)
inv={q.relative_to(raw).as_posix():dict(bytes=q.stat().st_size,sha256=hashlib.sha256(q.read_bytes()).hexdigest())for q in sorted(raw.rglob('*'))if q.is_file()};(e/'whole-unfiltered-raw-inventory.json').write_text(json.dumps(dict(root=str(raw),all_files=inv,future_custody='NEW23'),indent=2)+'\n')
(e/'outcome.json').write_text(json.dumps(dict(native01_failure='e62fb2/48262e0/101 before first source-model diagnostic',all_current_build_phases=0,prior1131_guards=0,unchanged_mathematical_Rust_members=True,only_Rust_source_change='tests.rs: line-offset diagnostic uses all six coefficients and asserts higher slots zero; all other source point formatter calls remain cubic',unchanged_protocol='38b827 models/fields/masks/samples/population/bounds/whole1077/four omissions',original_engine='exact graph and original preparation inherited, no new engine build',native02='NOT RUN; genuine23 must retain oversized whole failure record before compiled-source publication/exact checkpoint/new full attempt'),indent=2)+'\n');shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Original-prime build03 allrecorded1131guards/metadata/inheritedoriginalpreparation/testno-run/auditor/finalguards0. ALLRust members equal priorcompiled02 except exacttest formatter addition and one line-offset mapcall: preserve six degree6 coefficients, assert higherzeros; source cubic pointformatters and EVERY runtime mathematical body/instance/field/kernel/mask/sample/population/bound/whole1077/fourwholeomission criterion unchanged. Original graph/prepared fullbytes inherited, no second enginebuild. Native01 e62fb2/48262e0 failure101/fullcriterionunmet retained. Native02NOTRUN; whole4.4MBcompleted-failure-record subject requires genuineNEW23 original artifact publication before correctedsource checkpoint andnewfullattempt. All source/binaries/preparedcopies/raw retained. Unsigned compiled diagnostic repair only/no primechain outcome,cost,geometric,signedpromotion.']
for p in sorted(e.rglob('*')):
 if p.is_file():cmd+=['--proof','attestation:'+str(p.relative_to(r))]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct86-original-prime-compiled03.claim.txt').write_text(claim+'\n');print(claim,flush=True)
e2=s/'evidence/closed-root-derived-cache-cleanup-09';e2.mkdir()
for n in ['ct86_cleanup_closed_root_dependencies_09.py','ct86-closed-root-dependency-cache-cleanup-09.json.xz']:shutil.copyfile('/workspace/scratch/'+n,e2/n)
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Closed root dependency cache cleanup09: only obsolete unheld Root target/release RLIB/RMETA/object paths removed after excluding ALL44386 genuine22 guard paths/every modern+legacy currentPCCattestation/rootisogeny library, with no active compiler. Exact Root andScratch263MB diagnostic executables and all three Git statuses remainunchanged. Allsource/raw/executables/fullpreparedcopies/currentct57andct80caches retained. Complete digest/inode/size/allocatedbytes inventory retained. Rebuildable dependency cache only; no science/globalCI/cold/signing promotion.']
for p in sorted(e2.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
state='''# Corrected original-prime formatter compiled; genuine23 before native02

'''+claim+''': build03 all1131guards/metadata/inherited preparation/testno-run/auditor/finalguards0. Only Rust change fromcompiled02 is fullsix-coordinate line-offset diagnostic; every runtime formula/field/model/mask/sample/population/criterion unchanged. First nativee62fb2 at48262e0/checkpoint14 fails101 before first source-model record; all eight completed records/raw/binaries retained and whole1077 criterion remains unmet. Native02 NOT RUN. [pcc:unverified]

## What was done
Native01 exposed a diagnostic field-shape error, not a prime-map counterexample. Complete failure record is4.4MB, exceeding ordinary Git artifact policy. Preserve that whole subject through original NEW23 pipeline and transparent genuine canonical alias; do not trim it or weaken subject staging/hash checks. Corrected compiled03/source and all failures, norm-point46008b/reportf8d381, strict25acceptance0f3ea8/all294 ZIPmembers/full15runlogs, seven-root original-prime proofs and proposal remain intact. [pcc:unverified]

## Decisions made
Prepare whole closed scientific custodyNEW23, retaining all44386 prior keys/165 links and current append-only ledger plus ALL pendingconsumer bytes. HOLD all science/raw/source/aliases/ownedbytes/consumerledger until actual original remote replays before actual publisher/exactFF/whole archive reassembly/terminalguards. Exclude only credential-bearing private transport logs from publication while retaining them locally; no scientific source/data/control/negative trimmed. [pcc:unverified]

## Open threads
Genuine23 and exact canonical projection of whole norm-point fixture/stdout and oversized failure record; publish exact compiled03 then originalcheckpoint and full900s2GiB native02 under38b827. Next independent full-kernel compatibility census requires own prospective protocol before computation. Completeprimitive/minimal setup/known-point calibrated reference obligations remain open. [pcc:unverified]

## Errors
All native101/import/CIpath/staging/authoring/cold/rootmain and original D12/D24/D67/oldtwistprime negatives retained. Root unheld derived dependency cleanup09 preserves343source hashes/allraw/exes/fullcopies/current caches and exact263MB diagnostics. No paidlaunch/force/rebase/waiver/novelty/signedpromotion. [pcc:unverified]

---

'''
for p in [s/'RESEARCH_QUEUE.md',s/'CHECKPOINT.md',r/'.resume/RESUME.md',r/'docs/session-logs/2026-11-15.md']:p.write_text(state+p.read_text())
