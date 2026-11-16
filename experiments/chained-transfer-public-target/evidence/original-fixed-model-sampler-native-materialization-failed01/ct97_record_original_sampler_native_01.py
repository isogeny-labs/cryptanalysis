"""Inspect all whole sampler results, preserve the stronger-reference finding and complete raw custody."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'original-fixed-model-sampler-01';raw=Path('/workspace/scratch/ct97-original-fixed-model-sampler-native-01');sup=Path('/workspace/scratch/ct97-original-fixed-sampler-native-supervisor-01');analysis=Path('/workspace/scratch/ct97-original-sampler-result-analysis-01');build=Path('/workspace/scratch/ct97-original-fixed-model-sampler-build-01');checkpoint=Path('/workspace/scratch/ct97-current-original-checkpoint-21')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()=='d0b0d41b57a3863279d0390f090613ddc3e72b0a'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=r)
assert(raw/'original.exit').read_text().strip()==(sup/'actual-worker.exit').read_text().strip()=='0'
phases=[dict(zip(['name','expected','actual'],line.split()))for line in(raw/'phases.txt').read_text().splitlines()];assert len(phases)==33 and all(v['expected']==v['actual']for v in phases)
assert len([v for v in phases if v['expected']=='101'])==8
assert 'test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;'in(raw/'native.txt').read_text()
assert(raw/'all-whole-expected.json').read_bytes()==(raw/'all-whole-compared.json').read_bytes()
diag=json.loads((analysis/'complete-record-diagnostics.json').read_text())
for k,n in [('whole_record_count',101),('scalar_pairs',225),('class_triples',1125),('paired_attempts',60),('whole_solver_reports',120),('joint_verified_successful_pairs',45),('verified_successful_reports',90),('shared_rejected_pairs',15),('rejected_reports',30)]:assert diag[k]==n,k
assert diag['all_frozen_comparison_fields_independently_equal']and diag['all_three_derived_sources_exact_independent_known_initial_points']
omissions=[]
for f in sorted(raw.glob('*-entire-actual-records-omitted.txt.xz')):
 tag=f.name.split('-entire-',1)[0];h=hashlib.sha256();size=0;removed=0
 with(raw/'native.txt').open('rb')as original,lzma.open(f,'rb')as actual:
  for line in original:
   if(tag+' ').encode()in line:removed+=1;continue
   b=actual.read(len(line));assert b==line;h.update(b);size+=len(b)
  assert not actual.read(1)
 assert removed>0 and not(raw/(tag+'-must-not-accept.json')).exists()
 omissions.append(dict(tag=tag,whole_lossless_XZ=str(f),compressed_bytes=f.stat().st_size,compressed_sha256=hashlib.file_digest(f.open('rb'),'sha256').hexdigest(),whole_decompressed_bytes=size,whole_decompressed_sha256=h.hexdigest(),removed_matching_records=removed,all_other_original_line_bytes_equal=True,actual_auditor_exit=101,no_accepted_output=True))
assert len(omissions)==8
for line in(p/'frozen-prior-inputs-01.sha256').read_text().splitlines():
 h,n=line.split('  ',1);assert hashlib.file_digest((r/n).open('rb'),'sha256').hexdigest()==h,n
for label in ['chain','auditor']:
 row=json.loads((build/(label+'-compiled-custody.json')).read_text());assert Path(row['actual_path']).read_bytes()==Path(row['copy']).read_bytes()==(raw/('actual-before-native-'+label+'.bin')).read_bytes()
assert json.loads((checkpoint/'observation.json').read_text())['source']=='d0b0d41b57a3863279d0390f090613ddc3e72b0a'
e=s/'evidence/original-fixed-model-sampler-native-01';e.mkdir()
for f in raw.iterdir():
 if f.is_file()and((f.suffix in['.json','.sh','.exit']and f.name not in['all-whole-expected.json','all-whole-compared.json'])or(f.suffix=='.txt'and f.name!='native.txt')):
  if f.stat().st_size<60000:shutil.copyfile(f,e/f.name)
(e/'all-eight-whole-omission-custody.json').write_text(json.dumps(omissions,indent=2)+'\n')
for name in ['complete-record-diagnostics.json','commands.json','compile.txt','compile.exit','actual-run.txt','actual-run.exit','actual-source.rs']:shutil.copyfile(analysis/name,e/name)
for name in ['started.json','finish.json','actual-worker.exit','actual-versioned-driver.sh']:shutil.copyfile(sup/name,e/('supervisor-'+name))
shutil.copyfile(checkpoint/'observation.json',e/'exact-original-checkpoint21.json')
records=json.loads((raw/'all-whole-compared.json').read_text());selected=[v for v in records if v['kind'].startswith('N4_ORIGINAL_FIXED_SAMPLER_')and v['kind']!='N4_ORIGINAL_FIXED_SAMPLER_SETUP'];assert len(selected)==89
(e/'all89-whole-sampler-records-additional-export.json').write_text(json.dumps(selected,separators=(',',':'))+'\n')
inventory={}
for root in [raw,sup,analysis,checkpoint]:
 for f in root.rglob('*'):
  if f.is_file():inventory[str(f)]=dict(bytes=f.stat().st_size,sha256=hashlib.file_digest(f.open('rb'),'sha256').hexdigest())
(e/'whole-unfiltered-local-raw-inventory.json').write_text(json.dumps(dict(all_whole_files=inventory,whole101_decoded_and_native_stream_full_setup_11_constructor_records_retained=True,all89_export_is_additional_only=True,all120_full_reports_and30_rejected_reports_retained=True,future_custody='genuineNEW26 before canonical fixtures/additive native replay; no scientific raw/source/executable/prepared library removed'),indent=2)+'\n')
outcome=dict(at=datetime.now(timezone.utc).isoformat(),source='d0b0d41b57a3863279d0390f090613ddc3e72b0a',prospective='abf432/80631ad BEFOREsource',compiled='033a84/build01',driver_exit=0,supervisor_worker_exit=0,expected_phases=33,whole_records=101,new_sampler_records=90,original_constructor_records=11,scalar_pairs=225,class_triples=1125,paired_attempts=60,whole_solver_reports=120,joint_correct_public_cases=15,joint_verified_successful_pairs=45,verified_successful_reports=90,shared_rejected_FB30_pairs=15,rejected_reports=30,all_frozen_comparison_fields_independently_equal=True,all_three_prepared_sources_equal_independently_known_generator_points=True,strong_reference_finding=diag['strong_reference_finding'],whole_actual_class_omissions=8,source_guards=len((p/'frozen-prior-inputs-01.sha256').read_text().splitlines()),compiled_runtime_test_auditor_wholebytes_equal=True,exact_prepared_closure_full_RLIB_RMETA_and_reuse=True,exact_checkpoint21='43714362619/job132812569740/art14162135329/all28/remote-localgate0',scope='unsigned bounded finite sampler/paired-IC correctness; stronger known-point reference supplies no newly established advantage; actual model-scalar-program bridges, complete primitive/setup/reference costs and live admission remain open; no calibrated ratio, novelty, global/signed standing')
(e/'outcome.json').write_text(json.dumps(outcome,indent=2)+'\n');shutil.copyfile(__file__,e/'original-record-command.py')
(e/'REPORT.md').write_text('''# Complete original-model paired sampler and stronger reference

At exactd0b0d41 under prospectiveabf432/80631ad and compiled033a84/build01,
one unfiltered test and all33 expected phases pass. All225 scalar samples,
1125 triples,60 paired attempts and120 whole reports are retained. All15
public cases have a jointly correct setting;45 pairs provide90 answers
verified in both actual targets and original source. All15 FB30 pairs retain
both rejected reports (30 rejected candidates). Every frozen report field
agrees under the unchanged old comparison projection. [pcc:unverified]

On allthree models, the public norm-prepared source equals the independently
transported already-known generator point. After preparation the sample body
therefore uses the same source point/source scalar/Phi operations as that
stronger known-point reference. This does not establish a new computational
advantage over a reference that already has the original source point.
Preparation, admission, nested decode, FpR, setup and final verification costs
remain unpriced; original partial counters/API entries are diagnostics only.
[pcc:unverified]

The whole101 records retain90 new sampler records and11 original constructor
records, including full setup, every scalar/class/triple, all120 full reports
and both raw timing/counter fields excluded only from comparison. All eight
actual class omissions return101 without accepted output; whole lossless XZ
inputs independently match every retained source line byte. Actual compiled/
runtime binaries, prepared closure/full libraries/reuse, all prior guards and
exact original checkpoint21/all28/remote+localgate0 pass. [pcc:unverified]

Existing three-root NormAssistedSampling proofs and exact20261114 bindings
retain all actual geometry/scalar/Picard/program hypotheses. Actual alternate
P0/allthree foreign-model/omitted-inverse2/noncanonical scalar and class/nonell/
changed-generator/invalid-side-parameter controls pass. Full raw/source/exes/
prepared libraries/all earlier failures remain forNEW26. No calibrated ratio,
new asymptotic result, novelty, ECDLP advantage or signed standing is asserted.
[pcc:unverified]
''')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Originalfixedmodel pairedsamplernative01 atd0b0d41/prospectiveabf432 published80631ad BEFOREsource/compiled033a84-build01: oneunfilteredtest0/all33expectedphases/whole101records90new+11constructor/all225scalarpairs1125triples60pairedattempts120FULLreports/all15jointcorrectpubliccases. Exactly45verifiedsuccesspairs90acceptedreports/all15sharedFB30pairs30rejectedreports retained; independentRustwhole-record aggregation confirmsallfrozencomparisonfields equal, fullrawtiming-and-descentcounterfields nevertrimmed. ALLTHREEpublicnorm-derivedu EXACTindependentlyknowntransportedGsourcepoints; samplebodyafterpreparation matchesstrongerexistingknownpointsource-scalar-Phi path, no newlyestablishedadvantageoverthatreference. ActualdifferentP0/allthreeforeignmodels/omittedinverse2/nonell-malformed-scalar-changedG-invalidside-paramcontrols pass. Eightactualwholeclassomissions101-nooutput/fullXZproduction-CRC-independentwholelinebytehashcustody/allpriorguards/actualtest-auditorbinaries/fullpreparedclosure-RLIB-RMETA-freshreuse/exactoriginalcheckpoint21run43714362619-job132812569740-art14162135329-all28remote-localgate0. BothoriginalconditionalNormAssistedSampling3roots0trusted/threeexact20261114bindingspass. Allsource/raw/binaries/preparedcopies/rejectedreports/failures retainedforNEW26; actualmodel-scalar-programbridges/completeness-cost-liveadmission explicit. Unsignedboundedcorrectnessonly/no calibratedratio-ECDLPadvantage-novelty-globalCI-signedpromotion.']
for f in sorted(e.rglob('*')):
 if f.is_file():cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct97-original-sampler-native01.claim.txt').write_text(cl+'\n');print(cl,flush=True)
state='# Original paired sampler passes; stronger known-point reference limits advantage\n\n'+cl+': exactd0b0d41/prospectiveabf432/compiled033a84-build01; oneunfiltered0/all33phases/whole101records90new11prior/all225samples1125triples60pairs120FULLreports/all15jointpubliccases.45verifiedpairs90answers,15sharedFB30pairs30rejections retained. IndependentRustprojectioncomparisonallfrozenfieldsequal; fulltiming/descentcounterrawneverremoved. [pcc:unverified]\n\nAllthreepublicnorm-derivedpreparedpoints EXACTalreadyknownindependentlytransportedGpoints. Aftersourceprep samplebodymatchesstrongerretainedknownpointsource-scalar-Phi path; no newadvantageestablishedversusthatreference. Fullprimitive/setup/nesteddecode/admission/sourceverify/referencecostsandliveadmission unknown. Eightwholeclassomissions101-nooutput/XZfullbytes/actualbinaries-preparedreuse/allpriorguards/checkpoint21all28remote-localgate0 pass; oldconditional3roots0trusted/threeactual20261114bindingskeepbridgesexplicit. [pcc:unverified]\n\nNextinspectsource-linkedresult/report, registercapacitynegative-and-recovery, normalpublishRootmirrorandGitHubqueue; genuineNEW26wholedata/canonicalfixtures/additiveCI, thencompleteprimitive/setup/strongreferencecensus andpossibleFB30relation-rankdiscriminator. Allscience/raw/exes/fullpreparedcopies/rejections/earlierfailuresretained. TemporaryreadonlyFUSEprobeEPERM; historyinventorytriggeredpromisorfetchandENOSPCBEFOREpacking/removal, allrefsunchanged; onlynewremote180MBcachepackrelocatedwhollytoRAMwithoriginalpathbytesmodes/refHEADstatusstable, recoveryrecipeinscratchct98-remote-cache-relocation-01. UseGIT_NO_LAZY_FETCH=1 andavoidwholehistoryobjectenumeration. [pcc:unverified]\n\nNo calibrated-ECDLPadvantage/novelty/globalCI/signedpromotion. Oldcold12018complete102missing124/root124/clock101/mainledger/vault8edec422locked-KB127/review-signing/liveadmission gapsstayopen. [pcc:unverified]\n\n---\n\n'
for f in [r/'.resume/RESUME.md',s/'CHECKPOINT.md',s/'RESEARCH_QUEUE.md']:f.write_text(state+f.read_text())
f=r/'docs/session-logs/2026-11-15.md';f.write_text(f.read_text().rstrip()+'\n\n'+state.split('\n---')[0].rstrip()+'\n')
