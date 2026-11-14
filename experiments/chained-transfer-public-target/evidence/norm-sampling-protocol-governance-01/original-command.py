"""Ordinary metadata/prospective checkpoint; no new scientific source yet."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='39b932dddb9d655d7d35b058aa796af5c6941b8c';at=datetime.now(timezone.utc).isoformat()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
assert not(s/'norm-assisted-ic').exists()
text=f'''# Resume: Chained ECDLP Transfers — {at}

## Goal
Continue DLP-preserving transfers,chained Jacobian maps,prime-field descent and admitted computational comparisons;advance after each rung. [pcc:unverified]

## Lead / hypothesis
Prospective4a6745 freezes a publicG-only norm-assisted scalar sampler:u=[1386537]NormNew(G),R=Phi([r]u). Actual Phi(u)=G admission and exact original Picard[r]G controls are mandatory. This proposes same-output arithmetic,not a DLP fallback or speed conclusion. [pcc:unverified]

## Spec
NORM_ASSISTED_SAMPLING_PROTOCOL_01.md BEFOREnewcratecode;225scalarpairs/1125triples/all60ICpairs120reports/all3models/public5/FB30,36,48,64/seeds102..105. ONLYcontexttype+oneRexpression derivative;allotherbodies/RNG/finalORIGINALPicardcheck literal. 900build900native/2GiB/oneunfiltered/warmoutsidecache. ARITHMETIC_COVERAGE_INVENTORY_01.md names completecost obligations. [pcc:unverified]

## State
Source39b compatibility native8a77f3 settled;independentfull82290d all755guards/ninephasepairs/51wholeJSON/both2gates/2existingbindings/fouractualcontrols0or2asfrozen. Own16CI11815a all241native/57uniqueoriginalcanonicaldigests/59actualchecks(twoexistingreusedtwice). Originalcheckpointb08916 remote+localORIGINALgate0 exactCLEAN39b/genuine233Breceipt/101732BZIP/all28members;THISmetadatachangesstaleit. Root8a85ba2 normalpub0,genuinepreviousdataf5a805/4fda8d complete,guard08 historicalreleased. [pcc:unverified]

## Next steps
NormalpublishTHISprospectivecheckpoint BEFOREcreating norm-assisted-ic. Then source-only additivecrate and literal provenance,oneboundedunfilterednativepanel;savewhole /workspace/scratch/ct71-norm-assisted-native-01 withguards. Preserveallfailures. Written/faithfulconditionalproof/report/strictindependentreplay;thenisolatedarithmetic taps/completeadmission/matchedreference work. Closedct70full755/16CI/currenttransport wholecaptures need nextgenuinepublisherandNEWguard09. Neverincludeprivate temporarydownloadreference inpublicarchive. [pcc:unverified]

## Runs in flight
NONE local scientific. Source39b all16CI terminalsuccess;do not manuallyredispatch. Newmetadata publicationmaytrigger ordinaryautomaticCI. Currentfull /workspace/scratch/ct70-common-origin-full-01,CI /workspace/scratch/ct70-common-origin-own-CI-raw-01,transport /workspace/scratch/ct70-current-original-checkpoint-01. No newcandidatecode ornativeprocess beforeactualprospectivepublication. [pcc:unverified]

## Stop and success conditions
Require exactclasses,nontimingstats/failures/answers/non-descentcounters andallcontrols/guards. Preparationortransferfailures stayfailures;nofallback. CompleteFpR/model/map/admission/verification/cold+online coverage beforepricing. Freshoriginalcheckpoint/livebudget/capacity/isolation/strongestICrho references forperformance. Root124/two clock101 failures633ab0 requirecapablehost;conditionalgeometry/logextension/mainledger/signing/reviews/conflict/vault8edec422/KB absent remain. Continue usefulauthorizedwork. [pcc:unverified]
'''
p=r/'.resume/RESUME.md';p.write_text(text+'\n---\n\n'+p.read_text())
note=f'''\n## {at} — prospective norm-assisted exact-class sampling\n\n### What was done (commands, files, features)\n+Prospective4a6745 BEFOREnorm-assisted-iccode fixespublicG-onlyu=1386537NormNew(G)/actualPhi(u)=G/225scalarpairs1125triples/all60pairedICattempts/all3models/public5/strictsameoutputs/independentanswers/negativecontrols/900build900native2GiB/ONEunfiltered. Addedstatic ARITHMETIC_COVERAGE_INVENTORY_01.md;no newcosttotals. PrimaryHLPsection4.1pp23-24/Tiansections1+4/EFDformulas+Jacobiancoordinates actuallyread;localactualsourceshashed. KB MCPabsent/wrapperstatus+4queries127/conductor127/noabsenceor noveltyinference/vaultuntouched. [pcc:unverified]\n\n### Decisions made (and why)\n+Establish the sampler's exact-output correctness before investing in completepricing. It changes public groupmultiplication only;original relationoracle/descentlogic/finalPicardcheck remainliteral. Any smalleroldcounter is incompleteandcannotbe a stagewin. Publishthisprotocolnormally beforecandidatecode. [pcc:unverified]\n\n### Open threads (unfinished, pick up next time)\n+Normalpublishthischeckpoint;implementnativecandidate andliteralprovenance;runboundedpanel andretainfailures;thenwrittenfaithfulproof/report/strictreplay/completearithmetic coverage. Nextgenuinewholedata publication requiresNEWguard09;closedct70full/CI/transportcapturessaved. [pcc:unverified]\n\n### Errors (what went wrong, how it was handled)\n+Originaltransportb08916wascurrentatclean39b;thismetadata stalesit. No freshperformanceadmission orcostclaim. Root124/clock101/main/formal/KB/vault gapsremain;do not repeatunchangedfailedcommands or weaken gates. [pcc:unverified]\n'''.replace('\n+','\n')
with(r/'docs/session-logs/2026-11-14.md').open('a')as f:f.write(note)
g=s/'evidence/norm-sampling-protocol-governance-01';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
scope=[str(s.relative_to(r)),'docs/chained-transfer-checkpoint-transport','pcc/claims','pcc/ledger.jsonl','problems/chained-transfer-new-jacobian-ic-cost-coverage.md','docs/session-logs/2026-11-14.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,cmd):
 p=subprocess.run(cmd,cwd=r,capture_output=True);raw=p.stdout+p.stderr;(g/(name+'.txt.xz'if len(raw)>60000 else name+'.txt')).write_bytes(lzma.compress(raw)if len(raw)>60000 else raw);(g/(name+'.exit')).write_text(str(p.returncode)+'\n');print(name,p.returncode,flush=True);assert p.returncode==0,raw[:1500]
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','scripts/checkpoint.sh','.github/workflows',str((s/'native').relative_to(r)),str((s/'new-target-ic').relative_to(r)),str((s/'ci_common_origin').relative_to(r)),str((s/'common-origin-ic').relative_to(r))],cwd=r)
run('reference754',['sha256sum','--check','experiments/chained-transfer-public-target/ci_common_origin/reference-01.sha256']);run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]]);run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate'])
def stage():
 ps=paths();f=Path('/workspace/scratch/ct71-sampling-protocol.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
 selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
 for p in ps:
  if p.startswith(b'pcc/claims/'):
   for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
    if proof.get('kind')=='attestation':
     x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path'];assert x['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode==0,x['path']
 return selected
stage();run('reportPython',['python3','tools/ci/check_report_graph_python.py']);run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(g/'custody.json').write_text(json.dumps(dict(base=base,settled='82290d755full/11815a16CI241native57unique59actualchecks/b08916originalgate0exact39b',prospective='4a6745 BEFOREnorm-assisted-iccode;normalpublicationrequired',prior754_inputs_engines_workflows_verifiers_unchanged=True,governance='reference754/ledger/prose/working+cachedwhitespace/wiring/benchrec/reportPython/artifact0/allnewsubjects hash+staging',genuine_pending='closedct70full/16CI/transport wholearchive;NEWguard09 beforefutureFF',scope='unsigned/metadata+prospective/no sciencecode/performance/rootglobal/mergewaiver'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Common-originsettlement andprospective sampling governance own39b:82290d755full/11815a16CI241native57unique59actualreusechecks/b08916ORIGINALremote+localgate0exactclean39b acceptedunsigned. New4a6745 prospectivenorm-assistedpublicG-onlysampler BEFOREcode/225scalarpairs1125triples60ICpairs120reports/exactnonwalloutputs/independentanswers/strictnegatives/literalR-onlyderivative. Completecostinventory/primarysourceandKB127receipts retained/no noveltyspeedclaim. Original754inputs/engines/workflows/verifiers unchanged/reference754/ledger/prose/working+cachedwhitespace/wiring/benchrec/reportPython/artifact0/newsubjects hash+staging. Wholeclosedct70capturespendingnextgenuinepublication/NEWguard09;private temporarydownloadreference staysprivate. No benchmark/rootglobalgreen/mainmergewaiver;normalpublishbeforecode.']
for p in sorted(g.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct71-protocol-governance.claim').write_text(cl+'\n');selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: settle exact-origin replay and freeze norm-assisted sampling'],cwd=r,check=True)
print(cl,subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
