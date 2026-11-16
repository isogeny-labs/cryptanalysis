"""Register literal sampler compilation, reused proof gates and exact native launcher before execution."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'original-fixed-model-sampler-01';raw=Path('/workspace/scratch/ct97-original-fixed-model-sampler-build-01');proof=Path('/workspace/scratch/ct97-original-fixed-sampler-reused-proof-01');e=s/'evidence/original-fixed-model-sampler-compiled-01';e.mkdir()
assert(raw/'original.exit').read_text().strip()=='0'
assert(p/'derived/class_solver.rs').read_bytes()==(s/'norm-assisted-ic/derived/class_solver.rs').read_bytes()
for label in ['consumer','producer']:assert(proof/(label+'.exit')).read_text().strip()=='0'
for name in ['789d94','a9a7af','ed533b']:
 assert(proof/('binding-'+name+'.exit')).read_text().strip()=='0';a=json.loads((proof/('binding-'+name+'.json')).read_text());assert a['verdict']=='pass'and all(v['verdict']=='pass'for v in a['proofs'])
for f in raw.iterdir():
 if f.is_file()and f.suffix in ['.txt','.json','.exit','.sh']:shutil.copyfile(f,e/f.name)
shutil.copytree(raw/'actual-source',e/'actual-compiled-source');shutil.copytree(proof,e/'reused-original-proofs')
for f in [Path('/workspace/scratch/ct97_materialize_original_sampler_01.py'),Path('/workspace/scratch/ct97_materialize_original_sampler_test_01.py')]:shutil.copyfile(f,e/f.name)
for f in(raw/'actual-source').rglob('*'):
 if f.is_file():assert f.read_bytes()==(p/f.relative_to(raw/'actual-source')).read_bytes()
inventory={}
for root in [raw,proof]:
 for f in root.rglob('*'):
  if f.is_file():inventory[str(f)]=dict(bytes=f.stat().st_size,sha256=hashlib.file_digest(f.open('rb'),'sha256').hexdigest())
(e/'whole-build-proof-raw-inventory.json').write_text(json.dumps(dict(all_whole_files=inventory,full_actual_binaries_and_prepared_RLIB_RMETA_retained=True,future_custody='NEW26'),indent=2)+'\n')
guard_count=len((p/'frozen-prior-inputs-01.sha256').read_text().splitlines())
metadata=dict(at=datetime.now(timezone.utc).isoformat(),prospective='abf432/80631ad BEFOREsource',source_parent='80631ad65241cbec113ccf1e1d618a076da3a4d7',build_exit=0,first_attempt=True,old_sampler_class_solver_bytes_unchanged=True,source_context_only_import_constructor_changes=True,old_harness_report_comparison_parameters_and_scalar_list_literal=True,scalar_pairs=225,class_triples=1125,paired_attempts=60,full_reports=120,required_joint_correct_cases=15,strong_known_point_reference='actual public-norm-prepared point compared with independently transported already known generator; outcome pending',actual_alternate_P0_and_allthree_foreign_model_controls=True,all_prior_source_guards=guard_count,native_phases=33,whole_actual_class_omissions=8,whole_omission_inputs_lossless_XZ=True,original_three_root_gates0trusted=True,allthree_exact_original_bindings0=True,original_binding_dates='20261114; initial helper unused20261113 metadata list retained with explicit correction receipt',scope='unsigned compiled source and conditional-proof evidence only; no native result, exactmodel-programbridge or calibrated cost/advantage')
(e/'outcome.json').write_text(json.dumps(metadata,indent=2)+'\n')
(e/'REPORT.md').write_text('''# Paired sampler compiled on the fixed original models

Under prospectiveabf432 published80631ad before source, the release test and
auditor compile0 on the first attempt. The entire old norm-assisted solver
body is literal. Only the surrounding original-geometry imports/constructor
change; old report/comparison/parameter/scalar helpers are literal. All225
samples/1125 triples/60 pairs/120 reports/15 jointly correct case requirements
remain frozen, with actual known-point, alternate-P0 and cross-target controls.
Full engine closure/prepared bytes/fresh reuse and all prior guards pass.
Native acceptance is pending. [pcc:unverified]

Both unchanged original gates audit the old three-root NormAssistedSampling
source0trusted; all three original20261114 bindings pass. An unused helper
metadata list inherited the wrong20261113 date; its original source/outcome
and the explicit actual-path correction receipt are preserved. No proof,
formula, claim, verifier or criterion changed. Complete sources/logs/actual
binaries/prepared libraries are retained forNEW26. [pcc:unverified]

The new33-phase launcher requires the exact clean committed source/original
checkpoint,900s/2GiB test, whole records, all eight actual class omissions101
without accepted output, and final binaries/guards. Whole negative inputs
remain lossless XZ with producer/integrity/full decompressed custody. Existing
conditional geometry/scalar/Picard/program bridges, complete primitive/setup/
known-point/reference costs and live admission remain open. No calibrated
advantage, novelty or signed standing is supplied. [pcc:unverified]
''');shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Originalfixedmodel pairedsamplercompiled01 underprospectiveabf432 published80631ad BEFOREsource: firstattemptrelease test-and-auditorcompile0, entireoldnormassistedclasssolverliteral, onlyoriginalgeometrytype-import-constructorcontext adapted/oldreport-comparison-params-75scalar-RNGhelpersliteral. All225scalarpairs1125triples60pairs120fullreports15jointcases/actualknowninitialpointreference/samequarticactualalternateP0/allthreeforeignpacketcontrols frozen. Fulloldengineclosure-RLIB-RMETA-actualfreshreuse/allpriorguards pass; exactcompiledsource/binaries retained. BothoriginalNormAssistedSamplinggates3roots0trusted/allthreeexactoriginal20261114bindings789d94-a9a7af-ed533bpass; unusedhelper13datelist preservedwithexplicit14pathcorrection/no math-verifier-claimedit. Native33phase900s2GiB/exactcheckpoint/wholedata/eightwholeclassomissions101-nooutput/losslesswholeXZ/finalcustody launcherready, NO nativeoutcome yet. Actualmodel-scalar-programbridges/completeprimitive-setup-knownpoint-referencecost/liveadmission open. Fullsource/raw/exes/preparedcopies forNEW26; unsigned/no calibrated-ECDLP-novelty-globalCI-signedpromotion.']
for f in [*e.rglob('*'),*p.rglob('*')]:
 if f.is_file():cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct97-original-sampler-compiled01.claim.txt').write_text(cl+'\n');print(cl,flush=True)
state='# Fixed-model paired sampler compiled01; full native next\n\n'+cl+': firstattemptcompile0/entireoldclassbodyliteral/originalgeometrycontextonly;225samples1125triples60pairs120fullreports15jointcases frozen. BothoriginalNormAssistedSampling3roots0trusted/allthreeexact20261114bindingspass; helperunusedwrongdatemetadata explicitlycorrectedwithoutmath-claim-verifieredit. New33phasewhole900s2GiB/losslessfullcontrols/eightactualomissions/finalcustody launcherready; nativepending. [pcc:unverified]\n\nProspectiveabf432 published80631ad BEFOREsource; acceptedbaseline7df2ae/reportab5c32 atba1fae2/Root4de29a1 unchanged/all343producer sciencehashes stable. Actualpreparedsource-versus-knowninitialGpoint/samequarticactualalternateP0/allthreecross-target/omittedinverse2 controls required. Allfullsource/raw/exes/preparedcopies/failures awaitNEW26. [pcc:unverified]\n\nNextnormalpublishcompiledsource, exactoriginalcheckpoint21 once, boundedwholepairpanel; preserveanyrealfailure. Workspace~42MiBfree; UVTypst81MBsharesinstalledinode anddoesnotfreedata, Rootunheldregistrycandidateassessment0. Cargoarchivecache28MB/readonlyarchiveview orsafeimmutableGitobjectpacking arecapacityalternatives; no researchdata/source/exe/prepareddeletion. Completeprimitive/setup/knownpoint/strongreference/liveadmission andcold12018complete102missing/124/root124/clock101/globalmainledger/review/signing gaps remain/no calibratedratio-ECDLPadvantage-signedpromotion. [pcc:unverified]\n\n---\n\n'
for f in [r/'.resume/RESUME.md',s/'CHECKPOINT.md',s/'RESEARCH_QUEUE.md']:f.write_text(state+f.read_text())
f=r/'docs/session-logs/2026-11-15.md';f.write_text(f.read_text().rstrip()+'\n\n'+state.split('\n---')[0].rstrip()+'\n')
