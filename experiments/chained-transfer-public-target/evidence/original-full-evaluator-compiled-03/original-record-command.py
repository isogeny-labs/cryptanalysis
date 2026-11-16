"""Compile/source/dependency custody only; no research arithmetic."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, lzma, shutil, subprocess
r=Path('/workspace/cryptanalysis'); s=r/'experiments/chained-transfer-public-target'
pkg=s/'original-full-evaluator-01'; raw=Path('/workspace/scratch/ct90-original-full-evaluator-build-03')
e=s/'evidence/original-full-evaluator-compiled-03'; e.mkdir()
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
statement=f'Original full-group PhaseB correctedcompiled03 underprospective1539b6: all{guards}frozenprior hashes andbuildphases0, bothactualtest-auditor compile0, exactcompleteengine dependency-features-targetclosure/wholepreparedRLIB-RMETA equality andactualCargo reuse0, no newenginepreparation. Native01failure99d448 retained693whole/672exceptionals; onlytwo stale nu12testoracle literals replaced by4*inverse_original_prime(8), mod4/inverse2modELL assertions. Runtimehalving/correction/admission/norm/fullinverse andallmodels/populations/criteria unchanged. Wholeactualsource/executables/fullpreparedcopies retained. BothoriginalLean chain gates19roots0trusted/all19bindings7b5f49; separateCRTproofda2fe7 bothgates2roots0trusted/bothbindingspass. Sourceonlynumericprovenance metadata compacted, whole11,799,146B setupfile preserved inraw/build02; noRust/proof/binarybytes changed; freshbuild03sourceinventory0. Native02NOTRUN/whole701pending; publish exactcompiledsource/freshcheckpoint19/immediategate first. FuturecustodyNEW25; unsignedcompileonly, no signedstanding orcostadvantage.'
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',statement]
for p in sorted(e.iterdir()): cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip()
Path('/workspace/scratch/ct90-full-evaluator-compiled03.claim.txt').write_text(claim+'\n');print(claim,flush=True)
state=f'# Corrected original full-group evaluator compiled03; fresh checkpoint19 next\n\n{claim}: all{guards}prior hashes/buildphases0, exact field-engine closure/fullpreparedbytes equal andactualCargo reuse, no new preparation. Onlytwo test-oracle literals changed afterfailednative99d448; allfullruntime/model/population criteria unchanged. Native02 NOT RUN; whole701pending. [pcc:unverified]\n\n## What was done\nNative01 atpublished e633524/build01/exact originalcheckpoint18/all28/immediategate0 failed101/worker1 after693whole records, including672exceptionals/bothoutgoing/all4halves/duplicatecorrections/full13-169inverse. Stale nu12 scalar1385856 failed independentprime-source test recovery. Fullraw/693whole/source/binaries retained under99d448; postfailure1270hashes/binaries0. Correctoracle derives4*inverse_original_prime(8), kills4cofactor andinverts2modoriginalell; bothoriginalCRTproofgates2roots0trusted. [pcc:unverified]\n\n## Decisions made\nThe19-root proof7b5f49 retains8ChainDescent+5FullGroupNorm+3NormPointReuse unchanged andderives knownpoint p/zero representation pluskerneltransport choiceindependence; original inverses13=3413013/169=9648325 androots89/40/6 kernelchecked, all19localbindingspass. Actualfield/HLP/geometry/Frobenius/Picard/program/order bridges remainexplicit. Publishcorrected source, originalcheckpoint19 exactcleanHEAD/Resume/tool/28members/immediategate0, then run one900s2GiB native02 with120sauditors. [pcc:unverified]\n\n## Open threads\nRun original-full-evaluator-01/run-native-01.sh EXACTHEAD /workspace/scratch/ct90-original-full-evaluator-native-02 /workspace/scratch/ct90-original-full-evaluator-build-03 onlyafterfreshcheckpoint19. Require701whole/fiveactualwholeclassomissions101-nooutput/all1270hashes/actualbinaries; inspectedreport, genuinecustodyNEW25, freshadditiveCI. Thenprimitive/setup/strongreferences andprime-field descent leads. [pcc:unverified]\n\n## Errors\nNativefailure99d448 andall693whole records retained. Literal-source whitespacefailureb3ef84 fixedonlyexactattributes; alloldsourcebytes retained. Firstcheckpoint18 importer filenameprojection failedbeforeimport, correctedimport all28/localgate0; originalsourceunchanged. FirstproducerCRTgate shelllaunch race failedbeforegate, secondactualgatepasses. Allhistoricalnegatives preserved; no calibratedperformance/globalCI/signingpromotion. [pcc:unverified]\n\n---\n\n'
for p in [r/'.resume/RESUME.md',s/'CHECKPOINT.md',s/'RESEARCH_QUEUE.md']: p.write_text(state+p.read_text())
p=r/'docs/session-logs/2026-11-15.md';p.write_text(p.read_text().rstrip()+'\n\n'+state.split('\n---')[0].rstrip()+'\n')
