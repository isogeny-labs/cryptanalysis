"""Literal whole native outcome and terminal source/binary custody."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
raw=Path('/workspace/scratch/ct90-original-full-evaluator-native-02');supervisor=Path('/workspace/scratch/ct90-original-full-evaluator-native-supervisor-02')
e=s/'evidence/original-full-evaluator-native-02';e.mkdir()
assert (raw/'original.exit').read_text().strip()=='0' and (supervisor/'worker.exit').read_text().strip()=='0'
phases=[]
for line in (raw/'phases.txt').read_text().splitlines():
    name,want,actual=line.split();assert want==actual
    phases.append(dict(name=name,expected_exit=int(want),actual_exit=int(actual)))
assert len(phases)==14
assert not list(raw.glob('*must-not-accept.json'))
assert (raw/'all701-compared.json').read_bytes()==(raw/'all701-expected.json').read_bytes()
rows=json.loads((raw/'all701-compared.json').read_text());assert len(rows)==701
records={x['kind']:x['data'] for x in rows}
for tag,name in [('N4_FIXED_CHAIN_SELECTED_CALL_VECTORS','literal-all48-opaque-vectors.json'),('N4_ORIGINAL_FULL_KNOWN_POINT_VECTORS','literal-all48-known-point-vectors.json'),('N4_ORIGINAL_FULL_ORIGINAL_PUBLIC','literal-all15-original-public-controls.json'),('N4_FIXED_CHAIN_FULL_POPULATION','literal-full-population.json'),('N4_FIXED_CHAIN_ACTUAL_REJECTIONS','literal-actual-rejections.json')]:
    value=(json.dumps(records[tag],indent=2)+'\n').encode();assert len(value)<1024*1024
    (e/name).write_bytes(value)
for p in sorted(raw.iterdir()):
    if p.is_file() and p.suffix not in ['.bin','.json'] and p.name!='native.txt' and 'entire-actual-records-omitted' not in p.name:
        value=p.read_bytes();compressed=len(value)>60000 or value.endswith(b'\n\n')
        if compressed:value=lzma.compress(value)
        if len(value)<65536:(e/(p.name+'.xz' if compressed else p.name)).write_bytes(value)
shutil.copyfile(raw/'runtime-custody.json',e/'runtime-custody.json')
for p in supervisor.iterdir():shutil.copyfile(p,e/('supervisor-'+p.name))
shutil.copyfile('/workspace/scratch/ct90-current-original-checkpoint-19/observation.json',e/'exact-original-checkpoint19.json')
shutil.copyfile('/workspace/scratch/ct90-native02-closed-dedup-01.json',e/'whole701-closed-dedup.json')
inventory={p.relative_to(raw).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()) for p in sorted(raw.rglob('*')) if p.is_file()}
(e/'whole-unfiltered-raw-inventory.json').write_text(json.dumps(dict(root=str(raw),all_members=inventory,future_custody='NEW25; every whole701/native/five actualomission file/source/executable/fullprepared copy retained'),indent=2)+'\n')
(e/'outcome.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),prospective='1539b6 published d4f9d6b beforecode',source='c8490c73db4cd3518435efd0ad8f60282d09ab56',build='03/ba9700',original_checkpoint=dict(run=43695832128,job=132756029535,artifact=14153914871,all28matching=True,immediate_gate=0),one_unfiltered_native=0,worker=0,supervisor=0,all14phases=phases,whole_ordered_records=701,entire_freeze_compare_byte_equal=True,five_entire_class_omissions='actual101/noacceptedoutput',all1270_prior_hashes=0,actual_compiler_runtime_test_auditor_bytes_equal=True,full_population=records['N4_FIXED_CHAIN_FULL_POPULATION'],all48opaque_all48knownpoint_all15originalpublic=True,original_inverse13=3413013,original_inverse169=9648325,prime_source_CRT_recovery_scalar=9705756,knownpoint_carrier='allfourE2 presentations; duplicateJacobianimages retained; notallJacobcofactorsectors assertedcovered',failures_preserved=['99d448 native01/693whole','b3ef84 literalhelperwhitespace','9ada47 literalpanicwhitespace','checkpoint18 importer source failures','CRTproducer launch race'],conditional_proofs='7b5f49 nineteen roots +da2fe7 two roots; bothoriginalgates0trusted/all21localbindingspass',field_engine='exact completeclosure/preparedRLIB-RMETA reuse, no newpreparation',scope='unsigned finite full-cofactor original-source chain; actual field/HLP/geometry/Frobenius/Picard/program/order bridges explicit; selected calls unpriced, no calibrated/ECDLP advantage; fresh additive CI pending'),indent=2)+'\n')
shutil.copyfile(__file__,e/'original-record-command.py')
statement='Original full-group PhaseB underprospective1539b6/d4f9d6b atpublishedc8490c7/build03/ba9700/exactoriginalcheckpoint19 run43695832128/job132756029535/artifact14153914871/all28matching/immediategate0: oneUNFILTEREDnative0/worker0/supervisor0/all14phases expected; ALL701wholeorderedrecords freeze-comparebyteequal; FIVE actual entireexceptional-summary-public-opaquevector-knownvector omissions101/nooutput, all1270priorhashes andactualtest-auditorbytes exact0. Frozenoriginalcases2,0-0,1-2,0/D116-39-36/ell2773073/order11092292, all672descriptors/bothoutgoing/allfourhalves/duplicatecorrections/228cofactorattempts-domain/fourcofactorsectors/144mixed120public/96additions-pair/48opaquevectors/48knownpointvectors/15unchangedoriginalpubliccontrols pass. Actual13-169reverse norms/fullcofactorinverse recovery usesoriginal3413013/9648325; independentprime-source CRToracle9705756 repairedonlyoldtestliterals afterpreserved99d448 failure. Knownpointcubicdirect169/factored13 sharepreparedcoefficients andproduceidenticalwholeoutputs withopaquePhi(P+T), fullpointadmission/actualtargetnorm-order retained; duplicatesretained, notallJacobiancofactorsectors assertedcovered. Strongretainedellipticlift comparator retained andallselectedcalls unpriced. Conditional7b5f49 nineteenroots andda2fe7 twoCRT roots bothoriginalgates0trusted/all21localbindingspass; actualfield/HLP/geometric/Frobenius/Picard/program/order bridges explicit. Fullraw/source/executables/fullpreparedcopies retainedforNEW25; report/genuinepublication/freshadditiveCI pending. Unsignedfinitecorrectness, no calibrated/ECDLP advantage orsignedpromotion.'
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',statement]
for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct90-full-native02.claim.txt').write_text(claim+'\n');print(claim,flush=True)
state=f'''# Original full-group chain native02 passes; report/custody/additive CI next

{claim}: sourcec8490c7/build03/ba9700/exactoriginalcheckpoint19/all28/immediategate0. Oneunfilterednative0/worker0/supervisor0/all14phases, whole701orderedrecords byteequal, fiveactualwholeclass omissions101-nooutput, all1270hashes/actualbinaries exact. [pcc:unverified]

## What was done
Complete frozenoriginal full-cofactor chain atcases(2,0)/(0,1)/(2,0),D116/39/36,ell2773073/order11092292 passes672exceptionals/bothoutgoing/allfourhalves/duplicatecorrections/all228cofactorattempts-domain/foursectors/144mixed120public/96additions-pair/48opaquevectors. Direct169/literalJacobianchain/strongretainedlift wholeoutputs agree. All48knownpoint cubicdirect169/factored13 routes sharepreparedcoefficients andmatchactualopaquePhi(P+T), withallfourE2presentations andduplicates retained; notallJacobiancofactorsectors covered bythosepresentations. All15unchangedoriginalpublicendpointcontrols recoverE0. [pcc:unverified]

## Decisions made
Use7b5f49 nineteen-root conditionalproof plusda2fe7 two-rootCRTproof, bothoriginalgates0trusted/all21bindingspass. ActualHLP/field/geometric/Frobenius/Picard/program/order bridges remainexplicit; selectedcalls unpriced. Preserve99d448failed693/fullsource/raw andalloldnegatives. Nativewhole701expected/compared independentbytecomparison precedestransparentclosedlink, bothpathsfullbytesretained. [pcc:unverified]

## Open threads
Inspected combinedA/Bresultvisual, commit/publish result/rootmirror/GitHubqueue; genuinewholecustodyNEW25 andcanonicalpositive701fixture onlyafteractualoriginalpublication, thenfreshadditiveCI withallnewworkloads/proofs andoldimmutableworkflows/references. Nextstrongprimitive/setup/reference study andprime-field IC/descent usingexistingnew-target IC/norm-assistedsamplerasbaseline. [pcc:unverified]

## Errors
Native01failure99d448 retains693whole/672exceptionals andoldtestscalar1385856; narroworiginalCRT9705756repair passeswithoutchangingruntime/maps/models/populations. Bothliteralwhitespacefailures/importer/launchfailures preserved. No native02failure, calibratedcost/globalCI/signedpromotion. [pcc:unverified]

---

'''
for p in [r/'.resume/RESUME.md',s/'CHECKPOINT.md',s/'RESEARCH_QUEUE.md']:p.write_text(state+p.read_text())
p=r/'docs/session-logs/2026-11-15.md';p.write_text(p.read_text().rstrip()+'\n\n'+state.split('\n---')[0].rstrip()+'\n')
