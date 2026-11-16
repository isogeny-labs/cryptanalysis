"""Persist current replay state and normally publish next protocols before code."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='fb9ee1d613eebcd3459c02007b9bce06da218b47'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
def claim(statement,d):
 cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',statement]
 for p in sorted(d.iterdir()):
  if p.is_file():cmd+=['--proof','attestation:'+str(p.relative_to(r))]
 print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
d=s/'evidence/odd-product-refinement-normal-publication-01';d.mkdir();pub=Path('/workspace/scratch/ct66-refinement-source-publication-01');receipt=json.loads((pub/'receipt.json').read_text());assert receipt['head']==base and receipt['original_exit']==0
for p in pub.iterdir():
 if p.is_file():
  if p.suffix=='.log':(d/(p.name+'.xz')).write_bytes(lzma.compress(p.read_bytes()))
  else:shutil.copyfile(p,d/p.name)
claim('Normal nonforce refinement sourcefb9ee1d6/treeb3ed0a15/directc37ad390/134paths/governance3d6caf originalpush0. Actual147b66 transported52kerneltypes/nonefree/matchedwrittenodddegreefactor and identical-sourceAPIall3/public5/55partialbindings/inspectedreport1ca98b. Own12workflow events start automatically;new cleanfull02/703inputs/fouractualadmissioncontrols started separately,not completed. Failedsetup01/74ee4e preserved. No performance/globalrootgreen/mergewaiver.',d)
ad=s/'evidence/odd-product-refinement-full-admission-02';ad.mkdir();o=Path('/workspace/scratch/ct67-odd-product-refinement-full-02')
for name in ['plan.json','fixture-materialization.json','original-fixture-verify.exit','admission/results.json','admission/restoration.json']:shutil.copyfile(o/name,ad/Path(name).name)
assert json.loads((ad/'results.json').read_text())==[dict(name=k,original_exit=2,output_created=False)for k in ['missing-tool','wrong-head','dirty-source','output-in-source']]
claim('Actual corrected refinement full02 admission:newsourcefb9ee/original3d physicalGit siblings,ALL703selectedhashesunchanged,actualmissingtool/wrongHEAD/dirtysource/outputinsource controls each2/nooutput/restored. Whole genuine120752bytefixture read-only copied with originaltoolverify0,notnewremoteread. Originalstrictfull started separately;no terminal native/full/CI success claimed. Failedcaller01 retained74ee4e;originalscience/702CI unchanged.',ad)
kb=s/'evidence/new-target-IC-prior-search-01';kb.mkdir()
for label,query in [('IC','generic plane quartic class input index calculus canonical basepoint descent target solver'),('fixture','original curve25519 f1 targetwalk k20 s0 records artifact authenticated regression fixture')]:
 p=subprocess.run(['scripts/research-kb','search',query],cwd='/workspace/crypto',capture_output=True);(kb/(label+'.log.xz')).write_bytes(lzma.compress(p.stdout+p.stderr));(kb/(label+'.exit')).write_text(str(p.returncode)+'\n');assert p.returncode==127
(kb/'scope.json').write_text(json.dumps(dict(queries=2,original_fallback_exit=127,reason='no research KB executable',sources_read=['native/derived/public_solver.rs','native/original/ic.rs','completed-descent/derived/completed_solver.rs','original plane_quartic_pic.rs/canonical P0','originalFpr.rs/no exposed operation counter','originalrootfixture committed manifest','successful pinned original-tool hydration43508244485'],atlas='vault8edec422 locked/unchanged',inference='no novelty/absence claim'),indent=2)+'\n')
claim('Two fresh original KBfallback queries for generic JacobianIC and authentic rootfixture route each127/noexecutable. Read exact original solver/IC/completed/Picard/FpR APIs and original manifest/successful authenticated hydration instead;source IDs unavailable,atlas vaultlocked,no novelty or absence inference.',kb)
q='''# Current research queue — {at}

Published refinementfb9ee1d6/134paths/treeb3ed0a15/3d6caf normalpush0. Clean physical full02 runs from that exact source/original3d,703guards and FOUR actual controls2/nooutput/restored;whole fixture originalverify0. First setup01 failed before native on a corrupted negative-control revision and is preserved74ee4e. Own12 workflow events are in progress;terminal full/108native55canonical audit pending. [pcc:unverified]

| Priority | Task | Next discriminating action |
| --- | --- | --- |
| 1 | Actual new-target IC | Freeze/publish98c6f0 BEFOREcode;new typed generic class-input originalIC,actualP0/fb0 anchor,all3 x public5 x FB30/36/48/64/all60attempts,actualJacobian and independentoriginalsource checks,no recovery-toECDLP/lookup/witness. Complete costs remain unknown. [pcc:unverified] |
| 2 | Authenticated original root fixture | Freeze/publish708cb8 BEFORE dataonlyworkflow;pinned originaltool/config/manifest,literal2293097byteSHA8970667e fixture,GitHubCIauthenticatedpull/verify/hash and wholeartifact;then originalexacttargetedregression/guards. Globalroot gate remains separate. [pcc:unverified] |
| 3 | Refinement terminal full/CI | Let physical703full02 finish within2100s;collect12sourceworkflows/108native55canonicaldigests/wholelogs,retain failures. No unchanged redispatch. [pcc:unverified] |
| 4 | Whole-data publication and beta coordinates | ct65 full/CI,ct66 native,ct67 failedsetup/full/CI wholecaptures+completeindices through unchanged genuinepublisher;NEWguard07 beforebotFF. Matched global beta13^3/both13 exists written;complete coordinates not implemented. [pcc:unverified] |
| 5 | Admission/formal/merge | Original S3 checkpoint/livebudget/capacity/completecold+online counters/strongest IC/rho references;55partialbindings/signedexecution/actualgeometryopen;mainledger/signing/reviews/conflict/vault/KBecdb remain. [pcc:unverified] |

Native147b66 actual transported d3,2,1/nonefree52/wronguntransportedfalsefree;identical-sourceAPIall3/32odd+zero/public5. Activewritten03f46ce2/3faithfulbindings/55total/report1ca98b inspectedTWO63907-bytePDFpages. Existing702inputs/prior675/engines/verifiers/workflows immutable. Continue after each rung. [pcc:unverified]
'''.format(at=datetime.now(timezone.utc).isoformat())
p=s/'RESEARCH_QUEUE.md';p.write_text(q+'\n---\n\n'+p.read_text())
note='''
## {at} — next solver and authentic-fixture protocols before code

fb9ee source normalpush0. Corrected cleanphysical703full02 is running afterallfouractualadmissioncontrols2/nooutput/restored;fixtureoriginalverify0. Firstsetup01/74ee4e stopsBEFOREnative:helperglobal675-to702 substitutioncorrupts historicalnegativecontrolhash;all703inputs/bothcleansiblings/restoredproducerunchanged. Distinct02 fixesONLYcallerhash;nooriginalscientific/CI/verifierchanges. Own12CIevents4351434...inprogress;terminalfull/108native55digests pending. [pcc:unverified]

New prospective98c6f0 beforeany newtargetICcode:typed arbitrarynewJacobians/publicGQ/classes,actualP0/fb0anchor,originalICrelations/LA/descent preserved,all3xpublic5x4FBsettings60attempts/dualactualtarget+independentoriginalsourcechecks/noECDLPfallback. New708cb8 beforedataonlyworkflow:materiallydifferent authenticatedoriginalfixture hydration with originalpinnedtool/config/manifest and exactliteralhash;wholeGitHubartifact/authenticateddownload/originalverify/targetedoriginalregression;globalgate separate. Scope expands additively to newtargetICcrate/reports/formal/versionedCI and one dataonlyfixtureworkflow;old702/engines/verifiers unchanged. FreshKB2queries127,vaultlocked. [pcc:unverified]
'''.format(at=datetime.now(timezone.utc).isoformat())
for p in [r/'docs/session-logs/2026-11-13.md',r/'.resume/RESUME.md']:
 with p.open('a')as f:f.write(note)
g=s/'evidence/new-target-and-fixture-protocol-governance-01';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
scope=[str(s.relative_to(r)),'pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,cmd):
 p=subprocess.run(cmd,cwd=r,capture_output=True);raw=p.stdout+p.stderr;(g/(name+'.txt.xz'if len(raw)>60000 else name+'.txt')).write_bytes(lzma.compress(raw)if len(raw)>60000 else raw);(g/(name+'.exit')).write_text(str(p.returncode)+'\n');print(name,p.returncode,flush=True);assert p.returncode==0,raw.decode(errors='replace')[:1300]
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','.github/workflows',str((s/'odd-product-refinements').relative_to(r)),str((s/'ci_odd_refinement').relative_to(r))],cwd=r)
run('reference702',['sha256sum','--check',str((s/'ci_odd_refinement/reference-01.sha256').relative_to(r))]);run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]])
run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate'])
def stage():
 ps=paths();f=Path('/workspace/scratch/ct67-next-protocol.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
 selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
 for p in ps:
  if p.startswith(b'pcc/claims/'):
   for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
    if proof.get('kind')=='attestation':
     x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path'];assert x['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode==0,x['path']
 return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(g/'custody.json').write_text(json.dumps(dict(parent=base,protocols='98c6f0/708cb8 BEFOREcode',current_full='703physical02 running;fouractualcontrols2/nooutput/restored;firstsetup74ee preserved',own_CI='12workflow events running;terminal audit pending',all702_original_inputs_and_engines_workflows_verifiers_unchanged=True,governance='ledger/prose/whitespace/cachedwhitespace/wiring/benchrec/artifact0/allsubjects+staging covered',scope='unsigned correctness;no performance/globalrootgreen/mergewaiver'),indent=2)+'\n')
claim('NewtargetIC98c6f0 and authenticfixture708cb8 prospectiveprotocol checkpoint BEFOREcode;publishedfb9ee normalpush0/current703physicalfull02 and12CIevents running,not terminal;fouractualcontrols2/nooutput/restored/failedsetup74ee preserved. All702science/CI inputs/originalengines/workflows/verifiers unchanged. Originalledger/prose/whitespace/cachedwhitespace/wiring/benchrec/artifact0/newPCCsubjects+staging covered. Persistentqueue/resume updated for solver/all60attempts and materiallydifferent authenticatedoriginalfixture route;no performance/globalrootgreen/fullgeometry/mergewaiver.',g)
selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: freeze new-target IC and authenticated fixture protocols'],cwd=r,check=True)
print(subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
