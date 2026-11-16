"""Preserve failed and corrected compiled sources before native execution."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
old=Path('/workspace/scratch/ct82-fixed-chain-evaluator-build-01');new=old.with_name('ct82-fixed-chain-evaluator-build-02')
assert(old/'chain-compile.exit').read_text().strip()=='101'and(old/'original.exit').read_text().strip()=='1'
errors=[]
for line in(old/'chain-compile.txt').read_text().splitlines():
 try:v=json.loads(line)
 except json.JSONDecodeError:continue
 if v.get('reason')=='compiler-message'and v['message']['level']=='error':errors.append(v['message'])
assert len(errors)==4 and all(v['code']['code']=='E0599'and 'unwrap'in v['message']for v in errors)
assert(new/'original.exit').read_text().strip()=='0'
for label in ['prior-inputs','metadata','original-engine-preparation','chain-compile','auditor-compile','final-prior-inputs']:assert(new/(label+'.exit')).read_text().strip()=='0'
differences=[]
for p in(old/'actual-source').rglob('*'):
 if p.is_file()and p.read_bytes()!=(new/'actual-source'/p.relative_to(old/'actual-source')).read_bytes():
  relative=p.relative_to(old/'actual-source').as_posix();assert relative=='src/tests.rs';differences.append(relative)
assert differences==['src/tests.rs']
e=s/'evidence/fixed-chain-evaluator-build-02';e.mkdir()
for tag,raw in [('failed01',old),('corrected02',new)]:
 d=e/tag;d.mkdir()
 for p in sorted(raw.iterdir()):
  if p.is_file()and p.suffix!='.bin':
   b=p.read_bytes();(d/(p.name+'.xz'if len(b)>60000 else p.name)).write_bytes(lzma.compress(b)if len(b)>60000 else b)
 members={p.relative_to(raw).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in sorted(raw.rglob('*'))if p.is_file()}
 (d/'whole-local-raw-inventory.json').write_text(json.dumps(dict(raw_root=str(raw),all_unfiltered_files=members,future_custody='NEW22; full raw/source/executable/library copies retained'),indent=2)+'\n')
shutil.copytree('/workspace/scratch/ct82-chain-descent-proof-01',e/'earlier-proof01-gates');shutil.copyfile('/workspace/scratch/ct82-ChainDescent-01.lean',e/'earlier-seven-lemma-source.lean')
for name in ['ct82-chain-descent-producer-caller-01.txt','ct82-chain-descent-consumer-caller-01.txt','ct82-chain-descent-producer-caller-01.exit','ct82-chain-descent-consumer-caller-01.exit']:shutil.copyfile('/workspace/scratch/'+name,e/name)
shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Full fixed-chain evaluator compiled-source boundary: original build01 actual test compile101/worker1 with exactly FOUR E0599 unwrap-on-Pt test-helper errors, all raw/source preserved. Corrected only those test API return handling calls, no instances/masks/populations/criterion changed. Build02 original prior1080/lockedoffline metadata/declared engine preparation/test no-run/auditor compilation/finalguards all0; whole actual prepared library reuse and actual compiled source/test/auditor bytes retained. Runtime implements allsix directions/full169composites/fullgroupinverses, full695record/672exceptional-two-outgoing/four-half-cofactor-public-mixed-addition population plus direct/literal-chain/strongretained-lift comparison. Production combined-lift formula is checked against published fullsum in allfourdiagnostics. NativeNOTRUN; publish exact compiledsource then originalcheckpoint before one900s2GiB attempt. Earlier proof01 producer7roots0trusted and consumer absolute-path FAIL_build retained; successor02both8roots and13combined exactbindings are separate. PhaseD complete primitive census and calibrated benchmark admission remain open. Unsigned/no fullnative/cost/signed promotion.']
for p in sorted(e.rglob('*')):
 if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();print(claim,flush=True);Path('/workspace/scratch/ct82-evaluator-build.claim.txt').write_text(claim+'\n')
state='# Three fixed Jacobian models accepted; full evaluator compiled, native next\n\n'+claim+': full evaluator build02 compiles after preserved build01 fourE0599 test-return errors. PhaseA f81cbf on published70ec53e5/exact checkpoint11 passes oneunfilteredtest/allthree actual generic geometries,224lineorigins each/separatequadratic origins/allfourE2/two-two-pointcorrectionfibres/actualrejections. Fullchain native is NOT RUN. [pcc:unverified]\n\n## What was done\nBoth original gates/ALL13 exact local bindings pass across ChainDescent8roots/e89f97 and FullGroupNorm5roots/3805e2, zero trusted assumptions. Rational correction completeness, half-choice and Frobenius-fixed output are derived from explicit kernel/Frobenius inputs; no desired beta assumed. Full-group inverse witnesses13→5117005 and169→7216289 modulo11086844 and retained-lift comparison proved conditionally. Additive24 CI ab17f7: own43663258742/job132657012367SUCCESS/whole35654567BZIP182members/all37phases/all1077guards/both20rootgates/all20bindingverdicts/full8972686Bjoblog/all15runlogmembers and actualCI Rustauditor0/twoentireomissions101/wholefivecontrol0. Original23 unchanged. [pcc:unverified]\n\n## Decisions made\nFixed5caf67 source/mask/population preserved. Native must keep ALL672exceptionaldescriptors underBOTHoutgoingmaps/all4halves/all4cofactorsectors/144mixed/120public/96additionpairs perundirectedpair/fullgroupnorm-inverses/independentellipticchecks/all695wholeorderedrecords. Retain completed descriptor streaming before domainwholepacket. Compare direct169 with BOTHliteralJacchain and STRONGERretainedellipticlift chain, sharingoneexternaladmission/finalnorm+orderchecks. Record48unpricedSELECTEDcallvectors; completeprimitivecensus remainsopen. [pcc:unverified]\n\n## Open threads\nPublish exactcompiledsource/currentmetadata, collect ORIGINALcheckpoint12, then run fixed-jacobian-chain-evaluator-01/run-native-01.sh at that exactcleanhead with /workspace/scratch/ct82-fixed-chain-evaluator-build-02; one900s/2GiBunfilteredtest. Fullraw/archive/binaries/logs/failures/proofs/reports toNEW22; no canonicalnewfixture/replayCI before genuine22. Afterattempt retain outcome, improve implementation oradvance original-prime anti-Frobenius primaryreview; no modelreselection. [pcc:unverified]\n\n## Errors\nRetained EOFcached-whitespace2/oldproofabsolute-pathFAIL_build/fourE0599compile101. CI logconnectorTransportClosed twice andjobredirect403 preservedsafely; run-logZIP endpoint0 recoveredWHOLEjoblog. Exactclosedrawhardlinkdedup preservesbytes andmodes; obsolete root thirdpartyrmeta-only cleanup outsideall42866guards+PCCsubjects, currentct57/ct80/raw/exes/preparedcopies retained. Earlier ct54/ct56 release-path probe failed before mutation (they are debug). Historicalscientific/root-main/coldcensus negatives, signing/ledger/reviews/conflicts/livebenchmarkadmission/KB/vault gaps remainopen. [pcc:unverified]\n\n---\n\n'
for p in [r/'.resume/RESUME.md',s/'CHECKPOINT.md',s/'RESEARCH_QUEUE.md']:p.write_text(state+p.read_text())
p=r/'docs/session-logs/2026-11-15.md';p.write_text(p.read_text().rstrip()+'\n\n'+state.split('\n---')[0].rstrip()+'\n')
