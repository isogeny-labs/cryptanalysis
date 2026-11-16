"""Compile/source/dependency custody only; no research arithmetic."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, lzma, shutil, subprocess
r=Path('/workspace/cryptanalysis'); s=r/'experiments/chained-transfer-public-target'
pkg=s/'original-full-evaluator-01'; raw=Path('/workspace/scratch/ct90-original-full-evaluator-build-01')
e=s/'evidence/original-full-evaluator-compiled-01'; e.mkdir()
for n in ['original','prior-inputs','locked-graph','metadata','inherited-preparation','chain-compile','auditor-compile','final-prior-inputs']:
    assert (raw/(n+'.exit')).read_text().strip()=='0'
for p in (raw/'actual-source').rglob('*'):
    if p.is_file(): assert p.read_bytes()==(pkg/p.relative_to(raw/'actual-source')).read_bytes()
for label in ['chain','auditor']:
    row=json.loads((raw/(label+'-compiled-custody.json')).read_text())
    assert Path(row['copy']).read_bytes()==Path(row['actual_path']).read_bytes()
    shutil.copyfile(raw/(label+'-compiled-custody.json'),e/(label+'-compiled-custody.json'))
for name in ['engine-prepared.json','engine-reused.json','inherited-preparation.json']:
    shutil.copyfile(raw/name,e/name)
for row in json.loads((raw/'engine-prepared.json').read_text())['files']:
    assert Path(row['copy']).read_bytes()==Path(row['actual_path']).read_bytes()
for p in sorted(raw.iterdir()):
    if p.is_file() and p.suffix not in ['.bin','.json']:
        b=p.read_bytes(); compressed=len(b)>60000
        value=lzma.compress(b) if compressed else b
        assert len(value)<65536
        (e/(p.name+'.xz' if compressed else p.name)).write_bytes(value)
for name in ['source-derivation.json','generated/custody.json']:
    shutil.copyfile(pkg/name,e/Path(name).name)
inventory={p.relative_to(raw).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()) for p in sorted(raw.rglob('*')) if p.is_file()}
(e/'whole-build-inventory.json').write_text(json.dumps(dict(root=str(raw),all_members=inventory,future_custody='NEW25; entire actual source/executables/full prepared libraries retained'),indent=2)+'\n')
guards=len((pkg/'frozen-prior-inputs-01.sha256').read_text().splitlines())
(e/'outcome.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),protocol='1539b6 published d4f9d6b before code',accepted_geometry='0976e9 published7e28729',all_prior_guards=guards,all_build_phases=0,exact_dependency_features_target_closure_and_whole_prepared_bytes=True,actual_Cargo_engine_reuse=True,new_engine_preparation=False,source_actual_executable_full_copy_custody=True,native='NOT RUN',whole701_acceptance='pending',proof_and_additive_CI='pending',scope='unsigned compilation and custody only'),indent=2)+'\n')
shutil.copyfile(__file__,e/'original-record-command.py')
statement=f'Original full-group evaluator PhaseB protocol1539b6/d4f9d6b compiled01: {guards} prior hashes, lockedoffline graph/metadata/exact complete fieldengine dependency-feature-target closure/wholeprepared-library equality pass; both unfiltered test and whole701 auditor compile0 on first attempt. ActualCargo enginefresh reuse, no newenginepreparation. Actualsource/test/auditor/fullpreparedRLIB-RMETA retained. Frozen original cases(2,0)/(0,1)/(2,0), D116/39/36, ell2773073/order11092292; all original fullhalving/correction/admission/norm/inverse bodies retained, no prime projection. Knownpoint direct169 andfactored13 share actualcubic polynomialcoefficients beforeR6 conversion; fullsource/curve/order admission andactualtargetnorm/order checks. All701whole records, five actual entire-class omissions, exactruntime/source/binary custody andfreshcheckpoint/immediategate remainrequired. NativeNOTRUN, proof/additiveCI pending. FuturecustodyNEW25; unsignedcompileonly, no signedstanding or costadvantage.'
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',statement]
for p in sorted(e.iterdir()): cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip()
Path('/workspace/scratch/ct90-full-evaluator-compiled01.claim.txt').write_text(claim+'\n');print(claim,flush=True)
state=f'''# Original full-group Phase B compiled; fresh checkpoint18 next

{claim}: first build all0, {guards} frozen prior hashes unchanged, exact field-engine dependency closure and whole prepared-library bytes match; actual Cargo reuse, no new preparation. Native NOT RUN; whole701 acceptance and proof/additive CI pending. [pcc:unverified]

## What was done
Additive original-full-evaluator-01 implements the fixed original-source full-group maps under prospective1539b6/d4f9d6b and accepted geometry0976e9/7e28729. Full halving/correction/admission/norm/inverse retained. The stronger known-point comparator uses actual cubic rational maps with shared coefficients, one prime Phi, actual norm/full-order checks and no scalar witness. All source, actual binaries and full prepared libraries retained in /workspace/scratch/ct90-original-full-evaluator-build-01. [pcc:unverified]

## Decisions made
Publish this compiled source, import exact original checkpoint18 matching clean HEAD/Resume/tool/all28members, then immediate gate0 and one bounded900s/2GiB test via original-full-evaluator-01/run-native-01.sh EXACTHEAD /workspace/scratch/ct90-original-full-evaluator-native-01 /workspace/scratch/ct90-original-full-evaluator-build-01. Require all701whole records, allfive actual class-omission101/nooutput, allprior hashes and actual binary bytes. Keep inverse2 confined to the old public prime controls. [pcc:unverified]

## Open threads
Obtain checkpoint18 and native PhaseB; derive original full-order witnesses and known-point identity, retaining all old conditional roots/hypotheses. Both original Lean gates and exact bindings; inspected report, genuine custodyNEW25 and fresh additive CI. Then continue primitive/setup/reference and prime-field descent leads. [pcc:unverified]

## Errors
No PhaseB compile failure. All prior scientific, infrastructure, proof and source/format failures retained. Genuine24 is fully settled/root0f8203f/consumer7e28729; HOLD24 released and all49753inputs/172links/ownedbytes preserved. Cleanup10 c19c3c removed only unheld rebuildable dependency cache with unchanged scientific executable/source evidence. No calibrated cost, global CI or signed promotion. [pcc:unverified]

---

'''
for p in [r/'.resume/RESUME.md',s/'CHECKPOINT.md',s/'RESEARCH_QUEUE.md']: p.write_text(state+p.read_text())
p=r/'docs/session-logs/2026-11-15.md';p.write_text(p.read_text().rstrip()+'\n\n'+state.split('\n---')[0].rstrip()+'\n')
