"""Custody and claim record for the actual bounded native runs, no research math."""
from pathlib import Path
import json,hashlib,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
n=Path('/workspace/scratch/ct77-next-native-01');a=Path('/workspace/scratch/ct77-next-native-audit-01');cp=Path('/workspace/scratch/ct77-next-original-checkpoint-01')
c=s/'evidence/nondual13-next-original-checkpoint-01';c.mkdir()
for name in ['observation.json','original-import-command.py','whole-members.json','original-local-status.log','original-local-status.exit','original-local-gate.log','original-local-gate.exit','before-Git-status.txt','after-Git-status.txt']:
 shutil.copyfile(cp/name,c/name)
e=s/'evidence/nondual13-next-native-01';e.mkdir()
for name in ['original-command.sh','source-head.txt','frozen-source.sha256','original-immediate-gate.txt','original-immediate-gate.exit','prior-source-guards.txt','prior-source-guards.exit','original929-source-guards.txt','original929-source-guards.exit','final-source-guards.txt','final-source-guards.exit']:
 shutil.copyfile(n/name,e/name)
for phase in ['edge','model']:
 for name in ['native.exit','actual-binary-custody.json','start.txt','finish.txt']:
  shutil.copyfile(n/phase/name,e/(phase+'-'+name))
 for name in ['freeze.txt','freeze.exit','compare.txt','compare.exit','omission.txt','omission.exit','omission-custody.json']:
  shutil.copyfile(a/(phase+'-'+name),e/(phase+'-'+name))
 for mode in ['freeze','compare']:
  assert (a/(phase+'-'+mode+'.exit')).read_text().strip()=='0'
 assert (a/(phase+'-omission.exit')).read_text().strip()=='101'
 assert not(a/(phase+'-omission-accepted.json')).exists()
 assert (n/phase/'native.exit').read_text().strip()=='0'
for name in ['actual-old-dual-control.exit']:
 shutil.copyfile(n/'edge'/name,e/name)
assert (n/'edge/actual-old-dual-control.exit').read_text().strip()=='101'
(e/'whole-actual-old-dual-control.txt.xz').write_bytes(lzma.compress((n/'edge/actual-old-dual-control.txt').read_bytes()))
for name in ['control.txt','control.exit','report.txt','report.exit','report-data.json']:
 shutil.copyfile(a/name,e/name)
for name in ['main.rs']:
 shutil.copyfile(a/'actual-source/src'/name,e/'actual-auditor.rs')
shutil.copyfile(a/'actual-source/src/main.rs',s/'nondual13-next-preflight/src/bin/audit_records.rs')
for name in ['edge-all-native-records.json.xz','edge-whole-positive-native.txt.xz','model-all-native-records.json.xz','model-whole-positive-native.txt.xz']:
 p=a/name;(e/(name+'.custody.json')).write_text(json.dumps(dict(workspace_path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),contents='whole ordered JSON or whole stdout; NO masks/deduplication; XZ roundtrip checked',publication='NEW genuine18 required; not yet remotely published'),indent=2)+'\n')
rows=[]
for root in [n,a,cp]:
 for p in sorted(root.rglob('*')):
  if p.is_file():rows.append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
index=json.dumps(rows,indent=2)+'\n'
assert len(index)<64000
(e/'whole-raw-index.json').write_text(index)
(e/'scope.json').write_text(json.dumps(dict(source='f0167e430befd4304b170689e8caebcbdabbc6ad',protocol='bbfd74 published9038f2b9 before third-edge code',checkpoint='original43625626244/job132540664473/artifact14125982634/208396B/SHA889c6532dc5a6d7a6a6f85c03e261b0238f6f424f8c85bf8c86dbf29d0bbd6ae/all28members/sourceResume-tool-receipt-exact/localgate0 before BOTH native phases; source remained clean',native='ONEunfiltered edge and ONEunfiltered model test0, actualsourceguards0/compile-runtimebinariesexact; actualolddual101/gcd168 rejectedgate',whole='all5edge/all9model orderedrecords exact0; TWO actualidentical oldconstructor records retained and jointly crosschecked; actualcompletePUBLIC andMATCHED_MODELS omissions each101/nooutput',result='actual E3a(99,74,32)b(192,90,87); exactmiddle169 both13/curve/separable/gcd12; fullsamekerneltransport matches HLP(0,0), smoothtrue D24 sqrtDnull, supplied-source endpoint againunsupported',interpretation='preserve E2negative12 and E3negative24; smoothquartics exist, no new supplied-source Jacobianmap/retwist/reselection/full2197rational expansion/universalnonexistence/calibratedadvantage/novelty/signedexecution',preparation='I/Ocontrol preparation01 syntax error else101 before invoking auditor; corrected02 actualcontrols. Closed-cache cleanup01 rejected zombiecargo/rustc asactive before deletion;02 explicitly confirms no nonzombie activecompilers and hashes41 derivedlibraries outsideguard17 before reclaiming518033195B. Every actualexecutable/source/raw/sealedB/currentcache kept',next='NEWgenuine18 wholedata/strict22ndreplayCI, inspectednegative report/faithfulproof; advance materiallydifferent primitive-census observer remedy rather than another unregistered edge'),indent=2)+'\n')
shutil.copyfile(__file__,e/'original-record-command.py');shutil.copyfile('/workspace/scratch/ct77_control_next_records_02.py',e/'original-control-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Fixedthirdedgebbfd74 atpublishedf016 after exactoriginal43625626244/job132540664473/28member208396Bart14125982634/localgate0: ONEunfilterededge0/model0/allsourceguards0/actualcompile-runtimebinariesequal. E3a(99,74,32)b(192,90,87), bothsigned13/wholemiddle169/separable/gcd12; actualolddual168gcdreject101. Samefullkernelactual64/4096/135/Frobenius/alloldE0E1E2parity; intermediateE2D12negative preserved. G3fixedBEFOREbuilder uniqueHLP(0,0), smoothtrue D24 sqrtDnull: new supplied-sourceendpointFAILS, no retwist/reselection/newJacobianmap. All5edge+9model orderedwholeJSONexact/NOmasks, botholdconstructoroccurrencesretained/crosschecked; actualcompletePUBLIC/MATCHED_MODELS omissions each101/nooutput. WholeXZ150136/88312/326200/211464B/raw/actualbinaries retained forNEWgenuine18. I/Opreparation syntax andcleanupzombieguard failures distinguished/corrected; no mathsource changed. Unsigned, no full2197rational expansion/universalnonexistence/computationaladvantage/novelty.']
for root in [c,e]:
 for p in sorted(root.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
