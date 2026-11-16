"""Retain both actual compiler attempts and reused conditional proof receipts before native execution."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'original-fixed-model-ic-01';e=s/'evidence/original-fixed-model-IC-compiled-02';e.mkdir()
bad=Path('/workspace/scratch/ct96-original-fixed-model-IC-build-01');good=Path('/workspace/scratch/ct96-original-fixed-model-IC-build-02');proof=Path('/workspace/scratch/ct96-original-model-IC-reused-proof-01')
assert(bad/'original.exit').read_text().strip()=='1'and(bad/'chain-compile.exit').read_text().strip()=='101'
assert(good/'original.exit').read_text().strip()=='0'
reuse=json.loads((good/'engine-reused.json').read_text());assert reuse['actual_reuse']is True and reuse['Cargo_artifact']['fresh']is True
for name in ['binding-01efbf','binding-671d42']:
 assert(proof/(name+'.exit')).read_text().strip()=='0'
 row=json.loads((proof/(name+'.json')).read_text());assert row['verdict']=='pass'and all(v['verdict']=='pass'for v in row['proofs'])
for name,root in [('compiler-failed01',bad),('compiler-corrected02',good)]:
 d=e/name;d.mkdir()
 for f in root.iterdir():
  if f.is_file()and f.suffix in ['.txt','.json','.exit','.sh']:shutil.copyfile(f,d/f.name)
 shutil.copytree(root/'actual-source',d/'actual-source')
shutil.copytree(proof,e/'reused-original-proofs')
for f in [Path('/workspace/scratch/ct96_materialize_original_IC_support_01.py'),Path('/workspace/scratch/ct96-original-IC-build-caller01.txt'),Path('/workspace/scratch/ct96-original-IC-build-caller02.txt')]:shutil.copyfile(f,e/f.name)
assert(p/'derived/class_solver.rs').read_bytes()==(s/'new-target-ic/derived/class_solver.rs').read_bytes()
for f in(good/'actual-source').rglob('*'):
 if f.is_file():assert f.read_bytes()==(p/f.relative_to(good/'actual-source')).read_bytes(),str(f)
inventory={}
for root in [bad,good,proof]:
 for f in root.rglob('*'):
  if f.is_file():inventory[str(f)]=dict(bytes=f.stat().st_size,sha256=hashlib.file_digest(f.open('rb'),'sha256').hexdigest())
(e/'whole-build-and-proof-raw-inventory.json').write_text(json.dumps(dict(whole_files=inventory,full_prepared_RLIB_RMETA_and_actual_test_auditor_binaries_retained_locally=True,all_failed_source_and_Cargo_diagnostics_retained=True,future_custody='NEW26'),indent=2)+'\n')
(e/'failure-and-correction.json').write_text(json.dumps(dict(first_build_actual_driver_exit=1,actual_Cargo_compile_exit=101,errors=['EncodedClass has no PartialEq; whole field/model/key tuple must be compared explicitly','PairedFourth constructor takes the existing TwistedPair; ThirdHop is a different map object'],narrow_correction=['compare all three packet fields without changing either external type','construct the same TwistedPair already used by FixedGeometry and pass it to PairedFourth'],literal_IC_solver_unchanged=True,no_native_math_executed=True,corrected_build_exit=0,corrected_build_whole_supervisor_seconds=900,individual_compile_bound_seconds=120),indent=2)+'\n')
(e/'REPORT.md').write_text('''# Fixed original-model IC compiled source before native

Protocol3da7fe was published at7550409 before source. The complete literal
existing class solver is unchanged. Failed build01/Cargo101 identified two
new harness type errors; all source and diagnostics remain intact. Corrected
build02 exits0 under the whole900s bound, with individual120s compiler bounds.
It compares the entire packet field/model/key tuples and uses the existing
TwistedPair for the fourth map constructor. Formulae, models, populations and
acceptance criteria are unchanged. No native experiment has run yet.
[pcc:unverified]

Actual optimized test4,799,976 bytes and I/O auditor640,792 bytes are retained.
Complete field-engine dependency/features/targets closure equals the previous
full original build; full prepared RLIB/RMETA bytes and actual fresh reuse
match. Every1465 old/proof/protocol guard passes. Whole source/Cargo/runtime
custody metadata and prepared copies are retained forNEW26.
[pcc:unverified]

Both unchanged original proof gates recheck the existing conditional two-root
NewTargetIC source with zero trusted assumptions. Both exact original local
bindings01efbf/671d42 pass. PROOF_MAP.md keeps model/program/order/relation-log
bridges and completeness/cost obligations explicit. This is unsigned compiled
source and conditional-proof evidence; full native acceptance remains pending.
[pcc:unverified]
''')
shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','OriginalfixedmodelIC compiled02 underprospective3da7fe publishedd7550409 BEFOREsource: literalexistingclasssolver wholebytesunchanged; exactD116-D39-D36context/actualopaquechaininputversusindependentpoint-Phi checks/full60attempt15case panel+controls+wholeRustrecordauditor implemented. Failedbuild01driver1/Cargo101 twonewharnesstypeerrors preservedwithwholefailedsource; narrowwholepacketfieldcomparison andexistingTwistedPairconstructortype correction only. Correctedbuild02whole900s/individual120s driver0; actualoptimizedtest4799976B/auditor640792B/fullpreparedRLIB-RMETA/exactdependency-feature-targetclosure/actualCargofreshreuse/all1465guards pass. BothoriginalLean434-435reusedNewTargetICgates2roots0trusted/originaltwoexactbindings01efbf-671d42pass; actualmodel-program-order-logextension/completeness-cost bridgesexplicit. No nativeexecutionoroutcome yet. Fullsource/diagnostics/exes/fullpreparedcopies retainedforNEW26; unsigned/nocalibrated-ECDLPadvantage-globalCI-signedpromotion.']
for f in [*e.rglob('*'),*p.rglob('*')]:
 if f.is_file():cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct96-original-IC-compiled02.claim.txt').write_text(claim+'\n');print(claim,flush=True)
state='# Fixed original-prime IC compiled02; native experiment next\n\n'+claim+': prospective3da7fe published7550409 BEFOREnewRust; entireoldclasssolver literalunchanged/fixedD116-39-36context/all60attempts15cases/actualopaquechainindependentpoint-Phi equality/controls/wholeRustI-Oauditor. Build02driver0/test4799976B/auditor640792B/exactoldpreparedclosure-fullbytes-freshreuse/1465guards. BothoriginalreusedNewTargetICgates2roots0trusted/twooriginalbindings01efbf-671d42pass. No nativeexperimenthasrun. [pcc:unverified]\n\n## What was done\nPreservedwholefailedbuild01/Cargo101typeerrors andcorrectedonlypacketfieldcomparison/TwistedPairconstructortype. Allmathematicalmodels/solver/criteria unchanged. ProofCI39bb46 accepts41/all50files/both21declarations0trusted/allninebindings; FFb6bcac recordsentireledgerprefix/ordinary258→41 advance. Root66bc048 mirror/343sciencehashesunchanged; vault8edec422 lockedclean/KB127. [pcc:unverified]\n\n## Decisions made\nPublishthiscompiledsourcecheckpoint withoriginalgovernance andnewrustfmt-shell-priorguards; obtainexactoriginalcheckpointtransport beforebounded900s2GiBserialunfilterednative. Retainall60attempts/failures; requireall15verifiedcases. Recordallactualwholeclassomissions101-nooutput/sourceguards/actualcompiled-runtimebinaries. [pcc:unverified]\n\n## Open threads\nNativeIC/wholedataaudits/inspectedresult/proofscope/additiveCI/genuineNEW26, thenadaptoldnormassistedsampler andcompleteprimitive/setup/knownpoint/strongmatchedreferencecensus. CollectfreshfullCI43707728514at41withoutunobservedconclusion; new755CIseparate. Cold12018complete102missing/124/root124/clock101/global-mainledger/livebudget-capacity-isolation-image/review/signingremainopen; no calibrated/ECDLPadvantage/signedstanding. [pcc:unverified]\n\n## Errors\nFirstbuildtypefailurenotmathematicalcounterexample; failedfullsource/Cargodiagnostics/real101anddriver1 retained. Everypriorcustody/proof/transport/governance/literal-logwhitespace/publisher/clock/coldnegative intact. Neitherdesiredtransferidentity norwrongsourceorder wasaddedtorepairaresult. [pcc:unverified]\n\n---\n\n'
for f in [r/'.resume/RESUME.md',s/'CHECKPOINT.md',s/'RESEARCH_QUEUE.md']:f.write_text(state+f.read_text())
f=r/'docs/session-logs/2026-11-15.md';f.write_text(f.read_text().rstrip()+'\n\n'+state.split('\n---')[0].rstrip()+'\n')
