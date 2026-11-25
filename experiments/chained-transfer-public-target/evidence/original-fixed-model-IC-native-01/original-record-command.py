"""Independently inspect and register the complete fixed original-model IC native result."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'original-fixed-model-ic-01'
raw=Path('/workspace/scratch/ct96-original-fixed-model-IC-native-01');supervisor=Path('/workspace/scratch/ct96-original-model-IC-native-supervisor-01');analysis=Path('/workspace/scratch/ct96-original-model-IC-result-analysis-01');build=Path('/workspace/scratch/ct96-original-fixed-model-IC-build-02');checkpoint=Path('/workspace/scratch/ct96-current-original-checkpoint-20')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()=='0cb4ab3ec3435353e3602b521c59f937898a4704'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=r)
assert(raw/'original.exit').read_text().strip()==(supervisor/'actual-worker.exit').read_text().strip()=='0'
phases=[dict(zip(['name','expected','actual'],line.split()))for line in(raw/'phases.txt').read_text().splitlines()]
assert len(phases)==30 and all(v['expected']==v['actual']for v in phases)
assert len([v for v in phases if v['expected']=='101'])==7
assert 'test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;'in(raw/'native.txt').read_text()
assert(raw/'all-whole-expected.json').read_bytes()==(raw/'all-whole-compared.json').read_bytes()
diag=json.loads((analysis/'complete-record-diagnostics.json').read_text());assert diag['whole_record_count']==100 and diag['all_attempts']==60 and diag['verified_successful_attempts']==45 and diag['failed_attempts']==15
assert diag['actual_Rust_scope']['public_cases_solved']==15
omissions=[]
for f in sorted(raw.glob('*-entire-actual-records-omitted.txt.xz')):
 tag=f.name.split('-entire-',1)[0];h=hashlib.sha256();size=0;removed=0
 with(raw/'native.txt').open('rb')as original,lzma.open(f,'rb')as actual:
  for line in original:
   if(tag+' ').encode()in line:removed+=1;continue
   value=actual.read(len(line));assert value==line;h.update(value);size+=len(value)
  assert not actual.read(1)
 assert removed>0 and not(raw/(tag+'-must-not-accept.json')).exists()
 omissions.append(dict(tag=tag,whole_lossless_XZ=str(f),XZ_bytes=f.stat().st_size,compressed_sha256=hashlib.file_digest(f.open('rb'),'sha256').hexdigest(),all_decompressed_bytes=size,whole_decompressed_sha256=h.hexdigest(),omitted_matching_records=removed,all_other_original_line_bytes_equal=True,actual_auditor_exit=101,no_accepted_output=True))
assert len(omissions)==7
for line in(p/'frozen-prior-inputs-01.sha256').read_text().splitlines():
 h,name=line.split('  ',1);assert hashlib.file_digest((r/name).open('rb'),'sha256').hexdigest()==h,name
for label in ['chain','auditor']:
 record=json.loads((build/(label+'-compiled-custody.json')).read_text());assert Path(record['actual_path']).read_bytes()==Path(record['copy']).read_bytes()==(raw/('actual-before-native-'+label+'.bin')).read_bytes()
assert json.loads((checkpoint/'observation.json').read_text())['source']=='0cb4ab3ec3435353e3602b521c59f937898a4704'
e=s/'evidence/original-fixed-model-IC-native-01';e.mkdir()
for name in ['phases.txt','original.exit','start.txt','finish.txt','original-command.sh','runtime-custody.json','whole-closed-positive-and-binary-links.json']:
 shutil.copyfile(raw/name,e/name)
for f in raw.iterdir():
 if f.is_file()and f.suffix in ['.txt','.exit']and f.name!='native.txt'and not f.name.endswith('-entire-actual-records-omitted.txt'):
  if f.stat().st_size<60000:shutil.copyfile(f,e/f.name)
(e/'all-seven-whole-omission-custody.json').write_text(json.dumps(omissions,indent=2)+'\n')
for name in ['complete-record-diagnostics.json','commands.json','compile.txt','compile.exit','actual-run.txt','actual-run.exit','actual-source.rs']:shutil.copyfile(analysis/name,e/name)
for name in ['started.json','finish.json','actual-worker.exit','actual-versioned-driver.sh']:shutil.copyfile(supervisor/name,e/('supervisor-'+name))
shutil.copyfile(checkpoint/'observation.json',e/'exact-original-checkpoint20.json')
records=json.loads((raw/'all-whole-compared.json').read_text())
selected=[row for row in records if row['kind'].startswith('N4_ORIGINAL_MODEL_IC_')and row['kind']!='N4_ORIGINAL_MODEL_IC_SETUP']
(e/'all85-whole-IC-input-attempt-case-control-target-scope-records.json').write_text(json.dumps(selected,separators=(',',':'))+'\n');assert len(selected)==85
inventory={}
for root in [raw,supervisor,analysis,checkpoint]:
 for f in sorted(root.rglob('*')):
  if f.is_file():inventory[str(f)]=dict(bytes=f.stat().st_size,sha256=hashlib.file_digest(f.open('rb'),'sha256').hexdigest())
(e/'whole-unfiltered-local-raw-inventory.json').write_text(json.dumps(dict(all_whole_files=inventory,whole_native_and100_decoded_records_retained=True,all85_compact_IC_records_are_only_an_additional_literal_export=True,all_full_setup_and14_constructor_records_also_retained_in_whole_raw=True,all_failed_candidates_and_compile_failures_retained=True,future_custody='genuineNEW26 before canonical fixtures/additive native CI; no raw/source/executable/fullpreparedcopy removed'),indent=2)+'\n')
outcome=dict(at=datetime.now(timezone.utc).isoformat(),source='0cb4ab3ec3435353e3602b521c59f937898a4704',protocol='3da7fe/7550409 beforeRust',compiled='f9e8c9/03769fb/build02',driver_exit=0,supervisor_worker_exit=0,all_expected_phases=30,one_unfiltered_test_passed=True,whole_records=100,all_new_IC_records=86,prior_constructor_records=14,all_attempts=60,all_public_cases_correct=15,verified_successful_attempts=45,rejected_failed_attempts=15,FB30='all15 candidates rejected by actual final kG=Q check; retained, not accepted answers',FB36_FB48_FB64='all45 attempts accepted with both actual-target and original-source checks',all_actual_whole_class_omissions=7,source_guards=1465,compiler_runtime_test_auditor_wholebytes_equal=True,full_prepared_engine_closure_and_reuse_checked=True,exact_original_checkpoint20='43710462830/job132800676430/art14159918729/all28/remote+localgate0',old_original_solver_wholebytes_unchanged=True,scope='unsigned bounded fixed original-prime IC correctness only; all full data/failures retained; conditional proof/model-program bridges and complete primitive/setup/reference/live admission costs remain explicit; no calibrated advantage, solver completeness, novelty or global/signed standing')
(e/'outcome.json').write_text(json.dumps(outcome,indent=2)+'\n');shutil.copyfile(__file__,e/'original-record-command.py')
(e/'REPORT.md').write_text('''# All fixed original-prime public cases solved by literal IC

At0cb4ab3, prospective3da7fe/7550409 and compiledf9e8c9/build02, the complete
unfiltered test passes. All30 phases have their frozen expected exits. The
whole100 records include all86 new IC records and14 original constructor
records, with complete setup, every report/counter/raw wall and all failures.
All60 attempts finish and all15 public cases have a verified answer.
FB36/48/64 supply45 accepted solutions, each checked in the actual Jacobian
and independent original source. All15 FB30 candidates fail the original
final kG=Q check and remain rejected reports. [pcc:unverified]

The actual opaque full Jacobian chain packets equal independent source-point
transport and prime Phi. The solver receives no scalar witness/source lift/
elliptic DLP fallback; its entire old relation/LA/descent code is literal.
All seven actual whole-class omission inputs return101 without output. Their
full lossless XZ decompressions independently match every retained original
line byte; all whole compressed/uncompressed hashes and omitted-class counts
are recorded. Whole freeze/compare,1465 guards, actual test/auditor bytes,
full prepared libraries/closure/reuse and exact original checkpoint20 pass.
[pcc:unverified]

Existing two-root checked-answer/log-ratio proofs and both exact bindings
retain their conditional model/program/order/log-extension hypotheses; the
new induced proof supplies earlier abstract identities. All45 accepted and15
rejected reports and both first compiler errors are preserved. Complete
primitive/setup/known-point/opaque-input/admission/independent verification/
strong-reference/live admission costs remain unknown. Diagnostic counters
and walls do not establish an ECDLP advantage or calibrated ratio. Genuine
NEW26 and additive whole native replay remain queued. [pcc:unverified]
''')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','FixedoriginalprimeIC native01 at0cb4ab3 underprospective3da7fe published7550409 BEFOREsource/compiledf9e8c9-build02: ALL30phasesexpected0-101/oneunfilteredtest0/whole100records86newIC+14originalconstructors/all60attempts/all15publiccasescorrect. Exactly45verifiedacceptedFB36-48-64/all15FB30candidatesrejectedbyoriginalkG=Q; everywholefailedreportretained. ActualopaqueJacobianchainG-Q equalsindependentsourcepoint-primePhi; solverwholeoldclassbodyliteral/no scalar-witness-lift-DLPfallback. Sevenactualentireclassomissions101-noacceptedoutput/fullXZCRC/independentwholedecompressedlineequality+hashes; wholefreezecompare/1465guards/actualcompiled-runtime-test-auditor/fullpreparedclosure-freshreuse/exactoriginalcheckpoint20run43710462830-job132800676430-art14159918729-all28-remote-localgate0. BothoriginalreusedNewTargetICgates2roots0trusted/twoexactbindings retainedconditional, actualmodel-program-order-logextension/completeness-costbridgesexplicit. Rust-onlywhole100recordaggregation/all12FBgroups/completepartialcounterdiagnostics; allsource/raw/binaries/fullpreparedcopies/rejectedcandidates/compilerfailures retainedforNEW26. Unsignedboundedcorrectnessonly/no calibratedratio-ECDLPadvantage-novelty-globalCI-signedpromotion.']
for f in sorted(e.rglob('*')):
 if f.is_file():cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct96-original-IC-native01.claim.txt').write_text(claim+'\n');print(claim,flush=True)
state='# Original fixed-prime IC passes all15 public cases; preserve15 rejected FB30 reports\n\n'+claim+': exact0cb4ab3/prospective3da7fe/compiledf9e8c9-build02. Oneunfilteredtest0/all30phasesexpected/whole100records(86new+14priorconstructors)/all60attempts/all15publiccasesverified. FB36-48-64all45accepted, FB30all15candidatesrejectedbyactualfinalgroupcheck andwholefailurereportsretained. Sevenactualentireclassomissions101/nooutput/fullwholeXZdecompressedbyteequality; all1465guards/exactbinaries/fullpreparedreuse/checkpoint20all28+remote-localgate0. [pcc:unverified]\n\n## What was done\nActualopaqueJacobianchainpacketsexactindependentpoint-Phi outputs onallfixedmodels/publicinputs. Solverentireexistingclassbodyliteral/contextonlytypeadapter/no runtimescalar-witness-lift-DLPfallback. Rustwhole-recordaggregation/all12settinggroups/partialcounterdiagnostics retained. ConditionalNewTargetIC2roots0trusted/twoexactbindings andpriorInduced21/allninebindings stayexplicitaboutgeometric-model-program-order-logextension/completeness-costbridges. [pcc:unverified]\n\n## Decisions made\nRetainall100wholedecodedrecords/wholeNative/fullsetup/14constructorrecords/all60reports/15rejections/allsource-exes-preparedcopies-firstCargo101failure forNEW26. Additionalall85compactIC-recordexportdoesnotreplacewholedata. Renderandinspectsource-linkedresult, normalpublishandcheckpointGitHub; nextadaptoldnormassistedsamplertoexactsamemodels, preservepairedfailures andcompleteprimitive/setup/knownpoint/strongreferencecensus. [pcc:unverified]\n\n## Open threads\nInspectedresultreport/genuineNEW26wholepublication/canonicalwholefixture/additiveICCI; prospectivepairedsampler/costtask. FullCI43707728514at41successmetadatahasseparateuncollectedfullartifact, olda93f80at258andproofCI39bb46at41 scopesunchanged. Root66bc048/vault8edec422 unchanged. Cold12018complete102missing/124/root124/clock101/global-mainledger/livebudget-capacity-isolation-image/review/signingremainopen. No calibratedratio/ECDLPadvantage/globalCI/signedpromotion. [pcc:unverified]\n\n## Errors\nAll15FB30wrongcandidatesareoriginalsolver-rejected reports, notacceptedwronganswers; no model/kernel/parameterswerereselected. Firstcompiledtypeerrors/alloldprojection-transport-governance-publisher-source-coldnegativeactualprefixes remainintact. [pcc:unverified]\n\n---\n\n'
for f in [r/'.resume/RESUME.md',s/'CHECKPOINT.md',s/'RESEARCH_QUEUE.md']:f.write_text(state+f.read_text())
f=r/'docs/session-logs/2026-11-15.md';f.write_text(f.read_text().rstrip()+'\n\n'+state.split('\n---')[0].rstrip()+'\n')
