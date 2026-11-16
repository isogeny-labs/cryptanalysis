"""Close refinement evidence and publish bounded data-only fixture hydration."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='2aee9ef59dbd0fc0a8261f40e9abc1a0e6d77203'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
def claim(statement,d):
 cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',statement]
 for p in sorted(d.iterdir()):
  if p.is_file():cmd+=['--proof','attestation:'+str(p.relative_to(r))]
 print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
d=s/'evidence/new-target-and-fixture-protocol-normal-publication-01';d.mkdir();pub=Path('/workspace/scratch/ct67-next-protocol-publication-01');receipt=json.loads((pub/'receipt.json').read_text());assert receipt['head']==base and receipt['original_exit']==0
for p in pub.iterdir():
 if p.is_file():
  if p.suffix=='.log':(d/(p.name+'.xz')).write_bytes(lzma.compress(p.read_bytes()))
  else:shutil.copyfile(p,d/p.name)
claim('Normal nonforce nextprotocol2aee9ef5/tree524f47d0/directfb9ee/52paths/governancedb7ed9 originalpush0 BEFORE newtargetICcode and dataonlyfixtureworkflow. Prospective98c6f0/708cb8,failedsetup74ee preserved,fouractualadmissioncontrols and sourcefb9eenormalpub retained;original702inputs/engines/verifiers unchanged. No performance/globalrootgreen/mergewaiver.',d)
wf=r/'.github/workflows/chained-transfer-original-root-fixture.yml';p=subprocess.run(['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Actual additive data-only original-root-fixture workflow under prospectivelypublished708cb8/2aee:immutableoriginal3dcheckout/tool/config/manifest only,literal2293097byteSHA8970667efile,originalpull/verify/independenthash/size/sourceguards,credentialsonlydatareadstep,no candidatescientificcode;whole exactfile/inputs/API/logs/terminalexits viaoriginalGitHubartifact. Fifteenminute datajob;previous twelve workflows untouched. Actual remoteoutcome pending normalpublication;no availability/globalrootgreen/targettestpass/performance/mergewaiver.','--proof','attestation:'+str(wf.relative_to(r))],cwd=r,capture_output=True,text=True,check=True);print(p.stdout.strip(),flush=True)
q='''# Current research queue — {at}

Refinementfb9ee is settled:clean physical full02/b38c7f ALL703guards/10phasepairs/7wholeJSON/bothoriginal3declgates/3canonicalbindings/fouractualcontrols pass. OwnTWELVE workflows65dd08 ALLSUCCESS/108native55canonicaldigests. First caller setup74ee remains preserved. Standing unsigned,geometrypartial,no computational advantage. [pcc:unverified]

| Priority | Task | Next discriminating action |
| --- | --- | --- |
| 1 | Actual new-target IC | Prospective98c6f0 normallypublished2aee BEFOREcode. Implement typed generic originalIC/class-input/actualP0/fb0anchor;all3 x public5 x FB30/36/48/64/all60attempts/actualJacobian+independentoriginalsource checks. No ECDLPfallback,witness or lookup. [pcc:unverified] |
| 2 | Authenticated original root fixture | Prospective708cb8/2aee before additive dataonlyworkflow. Normalpublishworkflow;collectactual originaltoolpull/verify/exactsizehash/wholeartifact. Ifsuccess,authenticatedwholeartifactdownload/originalverify/exactcachedoriginaltargetedregression120s/guards. Globalroot gate staysseparate. [pcc:unverified] |
| 3 | Whole-data publication | ct65 full/11CI,ct66 native,ct67 failedsetup/full02/12CI and later solver wholecaptures/completeindices through unchanged genuinepublisher. FreezeNEWguard07 includingcurrent702/703/laterwork beforebotFF;old3241guard06 historical/released. [pcc:unverified] |
| 4 | Complete beta coordinates | Matched(1,0) gives globalwritten beta degree13^3/polarization13/both13/F=2beta. Actualcompletequotient/divisor coordinates remainopen;none of current3kernels free52. [pcc:unverified] |
| 5 | Admission/formal/merge | OriginalS3checkpoint/livebudget/capacity/completecold+onlinecounters/strongestICrho references;55partialbindings/actualgeometry/signedexecutionopen. Mainledger/signing/reviews/conflict/vault/KBecdb remain. [pcc:unverified] |

Native147b66/all2514guards;activewritten03f46ce2 and55bindings;report1ca98b/TWO63907-byte finalpagesinspected. Genuine768f4a/0bb0f5 all9captures+2fixtures20objects16S3+4Git;rootcdfce1bbnormalpush0. Allfrozeninputs/priorworkflows/originalengines/verifiers unchanged;continue aftereachoutcome. [pcc:unverified]
'''.format(at=datetime.now(timezone.utc).isoformat())
p=s/'RESEARCH_QUEUE.md';p.write_text(q+'\n---\n\n'+p.read_text())
note='''
## {at} — refinement terminal evidence; authentic-fixture data workflow

Exactfb9ee703physicalfull02 nowterminalb38c7f:all703guards0/fouractualcontrols2/nooutput/restored/tennative+teephasepairs0/ALL7wholeJSON/bothoriginal3declgates/threecanonicalbindings. Own12CI65dd08 allSUCCESS/108native55originalcanonicaldigests;whole12logs/API/703sources retained,largewholeobjects awaitinggenuinepublication. CI collector's earlierfull-running timestamp remains immutable;terminalfull is distinctb38c7f. [pcc:unverified]

2aee nextprotocolnormalpush0 BEFOREnewtargetsolvercode/fixtureworkflow. Actual additive original-root-fixture workflow checksoutonlypinnedoriginal3dtool/config/manifest,credentialsdata steponly,originalpull/verify/literalsizeSHA andwholeartifact;outcomependingnormalpublication. Existingtwelveworkflows/702inputs/engines/verifiers unchanged. Next implementactualnewtargetIC98c6f0/all60attempts whiledatajobruns;authenticateddownload/exactoriginaltargetregression onlyifauthenticbytesreturn. Performance/fullgeometry/globalgate/mainmerge/vault/KB gapsremain. [pcc:unverified]
'''.format(at=datetime.now(timezone.utc).isoformat())
for p in [r/'docs/session-logs/2026-11-13.md',r/'.resume/RESUME.md']:
 with p.open('a')as f:f.write(note)
g=s/'evidence/root-fixture-workflow-governance-01';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
scope=[str(s.relative_to(r)),str(wf.relative_to(r)),'pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,cmd):
 p=subprocess.run(cmd,cwd=r,capture_output=True);raw=p.stdout+p.stderr;(g/(name+'.txt.xz'if len(raw)>60000 else name+'.txt')).write_bytes(lzma.compress(raw)if len(raw)>60000 else raw);(g/(name+'.exit')).write_text(str(p.returncode)+'\n');print(name,p.returncode,flush=True);assert p.returncode==0,raw.decode(errors='replace')[:1300]
changed=set(subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','.github/workflows',str((s/'odd-product-refinements').relative_to(r)),str((s/'ci_odd_refinement').relative_to(r))],cwd=r,text=True).splitlines());assert changed<={str(wf.relative_to(r))},changed
run('reference702',['sha256sum','--check',str((s/'ci_odd_refinement/reference-01.sha256').relative_to(r))]);run('actionlint',['/workspace/scratch/actionlint-bin/actionlint',str(wf.relative_to(r))]);run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]])
run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate'])
def stage():
 ps=paths();f=Path('/workspace/scratch/ct67-fixture-workflow.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
 selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
 for p in ps:
  if p.startswith(b'pcc/claims/'):
   for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
    if proof.get('kind')=='attestation':
     x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path'];assert x['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode==0,x['path']
 return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(g/'custody.json').write_text(json.dumps(dict(parent=base,protocol='708cb8/2aee beforeworkflowcode',new_workflow='immutableoriginal3d dataonly originalpull/verify/sizeSHA/15min/wholeartifact',refinement='b38c7f703full/65dd08own12CI108native55canonical settled',all702_original_inputs_and_engines_verifiers_unchanged=True,previous_twelve_workflows_unchanged=True,governance='ledger/prose/whitespace/cachedwhitespace/wiring/benchrec/artifact/actionlint0/allsubjects+staging covered',scope='unsigned/datajoboutcomepending/no globalrootgreen/performance/mergewaiver'),indent=2)+'\n')
claim('Bounded dataonlyfixtureworkflow governance under708cb8/2aee prospectivebeforecode:immutableoriginal3dtool/config/manifest/credentialssingledatastep/originalpullverify/literalhashsize/wholeartifact. Previous12workflows/all702scienceinputs/originalengines/verifiers unchanged. Refinementsourcefb9ee independent703fullb38c7f/own12CI65dd08108native55canonical settled. Originalledger/prose/whitespace/cachedwhitespace/wiring/benchrec/artifact/actionlint0/newsubjects+staging covered;queue/resume current. Actualdatajoboutcome pendingnormalpublication;no globalrootgreen/performance/mergewaiver.',g)
selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','ci: hydrate authentic root fixture and checkpoint refinement replay'],cwd=r,check=True)
print(subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
