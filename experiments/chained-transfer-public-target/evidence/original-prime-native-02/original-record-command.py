"""Record literal native output and byte custody; no mathematical computation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, lzma, shutil, subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
raw=Path('/workspace/scratch/ct87-original-prime-native-02');e=s/'evidence/original-prime-native-02';e.mkdir()
assert (raw/'original.exit').read_text().strip()=='0'
supervisor=Path('/workspace/scratch/ct87-original-prime-native02-supervisor-01')
assert Path(str(supervisor)+'.exit').read_text().strip()=='0'
phases=[]
for line in (raw/'phases.txt').read_text().splitlines():
 name,want,actual=line.split();assert want==actual
 phases.append(dict(name=name,expected_exit=int(want),actual_exit=int(actual)))
assert len(phases)==13
tags=['N4_ORIGINAL_PRIME_EXCEPTIONAL_CASE','N4_ORIGINAL_PRIME_PUBLIC_CASE','N4_ORIGINAL_PRIME_SOURCE_MODEL','N4_ORIGINAL_PRIME_SELECTED_VECTORS']
for tag in tags:assert not(raw/(tag+'-must-not-accept.json')).exists()
rows=json.loads((raw/'all1077-compared.json').read_text());assert len(rows)==1077
assert (raw/'all1077-compared.json').read_bytes()==(raw/'all1077-expected.json').read_bytes()
selected=next(x['data']for x in rows if x['kind']=='N4_ORIGINAL_PRIME_SELECTED_VECTORS')
population=rows[-1]['data'];assert rows[-1]['kind']=='N4_ORIGINAL_PRIME_FULL_POPULATION' and len(selected['all12'])==12
(e/'literal-selected-vectors.json').write_text(json.dumps(selected,indent=2)+'\n')
(e/'literal-full-population.json').write_text(json.dumps(population,indent=2)+'\n')
for p in sorted(raw.iterdir()):
 if p.is_file() and p.suffix not in ['.bin','.json'] and p.name!='native.txt' and 'entire-actual-records-omitted'not in p.name:
  b=p.read_bytes();name=p.name+'.xz'if len(b)>60000 else p.name;value=lzma.compress(b)if len(b)>60000 else b
  if len(value)<65536:(e/name).write_bytes(value)
shutil.copyfile(raw/'runtime-custody.json',e/'runtime-custody.json')
for suffix in ['start','finish','exit','txt']:shutil.copyfile(str(supervisor)+'.'+suffix,e/('supervisor.'+suffix))
inventory={p.relative_to(raw).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest())for p in sorted(raw.rglob('*'))if p.is_file()}
(e/'whole-unfiltered-raw-inventory.json').write_text(json.dumps(dict(root=str(raw),all_members=inventory,future_custody='NEW24; every raw input/output/omission and actual compiler/runtime byte retained'),indent=2)+'\n')
shutil.copyfile('/workspace/scratch/ct87-current-original-checkpoint-15/observation.json',e/'exact-original-checkpoint15.json')
shutil.copyfile(__file__,e/'original-record-command.py')
outcome=dict(at=datetime.now(timezone.utc).isoformat(),source='2a1a8e58468201f72933f66b0d9b888037bc05f2',compiled_claim='a3c6eb',prospective_protocol='38b827 published at bd603d0981653797e6cc0b9d50f50dcec2314ac1 before code',original_checkpoint=dict(run=43684688854,job=132722574569,artifact=14149624251,all28_members=True,remote_gate=0,immediate_local_gate=0),native_unfiltered_exit=0,worker_exit=0,supervisor_exit=0,all13_phases=phases,whole_ordered_records=1077,entire_freeze_and_compare_bytes_equal=True,all12_selected_vectors=12,actual_whole_record_omissions='four classes reject101 with no accepted output',all1131_prior_guard_hashes=0,actual_compiler_runtime_test_and_auditor_bytes_equal=True,whole_population_literal=population,proof_scope='seven conditional PrimeReprojection roots; actual HLP/field/geometry/Picard/Frobenius/program bridges remain explicit',cost_scope='five routes agree; selected source calls unpriced. Known initial elliptic point avoids the initial norm/inverse-two. Correctness footer is not a benchmark.',preserved_failure='native01 e62fb2 actual101 after eight records; corrected03 only changes Fp6 diagnostic formatter; no mathematical field/kernel/sample/bound change',scope='unsigned finite correctness of separate original-prime reprojection; not full-group kernel-compatible geometric descent')
(e/'outcome.json').write_text(json.dumps(outcome,indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Original-prime reprojection protocol38b827 publishedbd603d0 BEFOREcode: full native02 atpublished2a1a8e5/build03/exact originalcheckpoint15 run43684688854/job132722574569/artifact14149624251/all28 matching members/immediate gate0. One UNFILTERED native test0/worker0/supervisor0, all13phases expected, entire1077 ordered records freeze/compare byteequal. Four actual entire exceptional/public/model/vector class omissions reject101 with NOacceptedoutput; all1131prior hashes and actual compiler/runtime test-auditor bytes exact. All18oldrows/three fixed original-source models/all672 explicitly4-projected exceptionals underbothoutgoing/384publicpoints/all228cofactorattempts-domain/all4classes-strictcofactorrejection/64additionpairs-pair/15originalpublic endpointtransfers/12vectors-five-whole-equalroutes passed actual native assertions. Norm13/169 and inverse recovery hold in the tested originalell2773073 subgroup, with explicit inverse-two; no original log transported by twisting. Known-initial-point route avoids initial norm/inverse-two; allselectedcalls unpriced. Sevenconditionalproofroots remain6d8c42; actualgeometry/programbridges open. Full native01failuree62fb2 retained; diagnostic-only compiled03a3c6eb fixed six-coordinate formatter without changing arithmetic/population/bounds. Everyraw/source/binary/preparedcopy retained forNEW24. Unsigned finite correctness, no full-group geometric transfer, calibrated performance or signed promotion.']
for p in sorted(e.iterdir()):
 assert p.is_file()and p.stat().st_size<262144
 cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct87-original-prime-native02.claim.txt').write_text(claim+'\n');print(claim,flush=True)
state='# Original-prime native02: complete finite reprojection checks passed\n\n'+claim+': source2a1a8e5/build03 and exact original checkpoint15. One unfiltered native test and worker/supervisor return0. All13 phases have their required exits. All1,077 ordered records freeze and compare whole; four actual entire-class omissions reject101 without accepted output. All1,131 prior hashes and actual test/auditor bytes remain exact. [pcc:unverified]\n\n## What was done\nThe original ell2,773,073/order11,092,292 instance passes the frozen18-row, three-model,672 projected exceptional,384 public-point, cofactor, addition, original-public-control and12-vector/five-route population. The previously failed run e62fb2 is retained; build03 changes only the degree6 diagnostic formatter. Seven conditional proof roots remain6d8c42, with explicit geometric and program bridges. The known initial elliptic point avoids the initial norm and inverse-two; selected source counters remain unpriced. [pcc:unverified]\n\n## Decisions made\nPublish the result and an inspected visual report. Preserve all raw/source/executable/full prepared-copy/checkpoint bytes, with future large custody NEW24. Next publish a prospective finite census of18 model vertices,72 adjacent candidate pairs and216 triples before computing new transported masks. Preserve the fixed D12/D24/D67 negative results and the frozen prime-only choices. [pcc:unverified]\n\n## Open threads\nResult report and normal publication; then the full-group kernel-compatibility census, complete primitive/setup/known-point comparison and prime-field descent leads. Sources checked for the next census: HLP math/9809210v1 section4.1/Lemma13/Propositions14-15 and field qualification; original full18-row/64-coordinate/4096-pair tables. KB status and three searches exit127; vault remains locked and unchanged. [pcc:unverified]\n\n## Errors\nNative01 diagnostic101 and all prior implementation/infrastructure/mathematical negatives remain recorded. A metadata inspection command had a syntax error before I/O and was corrected. No new calibrated performance or signed standing is asserted. [pcc:unverified]\n\n---\n\n'
for p in [r/'.resume/RESUME.md',s/'CHECKPOINT.md',s/'RESEARCH_QUEUE.md']:p.write_text(state+p.read_text())
p=r/'docs/session-logs/2026-11-15.md';p.write_text(p.read_text().rstrip()+'\n\n'+state.split('\n---')[0].rstrip()+'\n')
