"""Checkpoint actual original gate acceptance and prospective native control."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';docs=r/'docs/chained-transfer-checkpoint-transport';base='39e9db95506b8cdfa0fea37c3d2716b511651b84'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
at=datetime.now(timezone.utc);date=at.date().isoformat();journal=r/'docs/session-logs'/f'{date}.md'
note='''\n## {at} — transport outcome and next native protocol checkpoint\n\n### What was done (commands, files, features)\n+ffe675 originalremote andlocalcheckpoint gates0 forexactclean39e9;wholeauthenticatedartifact87453bytes/all28members/genuineS3pack+Resume+meta/originalreceipt/sourceandresumeequality/unchangedGitstatus. Prospective2dd807 BEFOREcommon-origin-iccode freezesall20pairedoriginal/classICattempts/sameactualP0/fullFB/RNG/raworigin/sign/differences/allr0..32/independentanswers/allfailures. Scientific1816 full3f52fc730/14CId53e33190native57canonical remainssettled. [pcc:unverified]\n\n### Decisions made (and why)\n+Publishprospectivecommonoriginprotocolbeforecode;transportcapabilityisnowdemonstrated,butnewstatechangesstaleoldreceipt. Nativecorrectnessdevelopment continues;budget/capacity/isolation/fullcosts/referencesstillrequired forexperiments. [pcc:unverified]\n\n### Open threads (unfinished, pick up next time)\n+Normalpublishcurrentprotocol;implementborrowed-Picard compatibilitycrate withonlycontexttype/accessdelta anduntouchedoriginalbaseline;run900sbuild900snative/2GiB/oneunfiltered/warmcache. Preserveall20pairs andactualclasscontrols;writeproofscope/report. Nextcountercoverage/completebeta coordinates/genuinewholecapturehandoffNEWguard08. [pcc:unverified]\n\n### Errors (what went wrong, how it was handled)\n+Allpriornegativecapturesretained;rootfull124/unknowntotals/twoexactclock101 needscapablehost. CI namespacecapability0isnotrootregression. Geometry/logextension/fullcost/mainledger/signing/reviews/conflict/vault/KB gapsremain. [pcc:unverified]\n'''.format(at=at.isoformat()).replace('\n+','\n')
with journal.open('a')as f:f.write(note)
resume='''# Resume: Chained ECDLP Transfers — {at}

## Goal
Continue DLP-preserving transfers,chained Jacobians,prime-field descent and admitted computational comparisons across the workspace. Continue after each rung. [pcc:unverified]

## Lead / hypothesis
ActualnewtargetIC solvesall15publiccases. Nextnativecontrol comparesoriginalsource-boundIC andborrowed-Picard class-inputIC atTHEsameactualrandomFBP0,withthegenuineaffineorigin bridge. No path/counter/costequivalence assumed. [pcc:unverified]

## Spec
COMMON_ORIGIN_IC_PROTOCOL_01.md/2dd807 isprospectiveBEFOREcommon-origin-iccode;all20pairedattempts/public5xFB30,36,48,64/seeds102..105 explicitzeroindices/actualclassr0..32/rawavailableH+T/differences/foreignP0/independentanswers. ONEunfiltered/900build900native/2GiB/warmoutsidecache. Scientific1816/newICe869bd/57partialbindings/reportd1027f/full3f52fc730/14CId53e33190native57canonical settled. [pcc:unverified]

## State
Originalcheckpointtransport ffe675 PASSES forexactclean39e9:43530006697/job132245064560/artifact14087750072/87453bytes/SHA19053dfd/all28members;originalremote gate/readback0,exactoriginalreceipt/matchingcleanlocaloriginalgate0/Gitstatusunchanged. Latermetadatachangesstaleoldreceipt;neworiginalcheckpoint requiredbeforeexperiment. Existingdata-onlyworkflowwillcheckpointnewcommittedhead whenitsdocschange. Genuineolder25objects43d6ba/babda6 complete;new730full/14CI/transportwholecapturesawaitnextgenuinepublication/NEWguard08. [pcc:unverified]

## Next steps
Normalpublishthisprotocolcheckpoint BEFOREnewcratecode,thenimplementcommon-origin-ic/candidatecontexttype+picaccessONLY/literalbodies/originalbaselineunchanged. Usewarmct57cache andfresh /workspace/scratch/ct70-common-origin-native-01 capture/guards. Requireallreportedanswersactualtarget+independentsource andoneCOMMONcorrectsettingperpublicQ;retainall20pairs andallfailures/availabilitycounts. Thenactualoutputs/proofscope/report/checkpoint,countercoverage/completeodddegreecoordinates. RefreshPR1523/root3877/queue3904. [pcc:unverified]

## Runs in flight
No localscientificprocess. Source39e9 ordinaryCIisautomatic;itsoriginalcheckpointdatajobisalreadyterminalsuccess. NewprotocolpublicationmaytriggerrepositoryCI;collectexactsource/workflow IDsfromGitHubwithoutmanualredispatch. Transportcaptureraw /workspace/scratch/ct69-original-checkpoint-transport-01;full /workspace/scratch/ct69-new-target-IC-full-01;ownCI /workspace/scratch/ct69-new-target-IC-own-CI-raw-01. No paidbenchmark. [pcc:unverified]

## Stop and success conditions
Followprospective2dd807 nativeacceptance/literalprovenance/allguards;failuresremain scopedandnextdiagnosed. OriginalS3gatepass forexactstatealone doesnotprovidelivebudget/capacity/isolation/fullcounters/strongestrefs/performanceadmission. Rootfull124/twoexact101clockfailuresrequirescapablehost;actualgeometry/logextension/mainledger/signing/reviews/conflict/vault/KB gapsremain. Continuewhileusefulauthorizedworkavailable. [pcc:unverified]
'''.format(at=at.isoformat())
p=r/'.resume/RESUME.md';p.write_text(resume+'\n---\n\n'+p.read_text())
g=docs/'origin-protocol-governance-01';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
scope=[str(docs.relative_to(r)),str((s/'COMMON_ORIGIN_IC_PROTOCOL_01.md').relative_to(r)),str((s/'evidence/common-origin-prospective-01').relative_to(r)),'pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-13.md','docs/session-logs/'+date+'.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,cmd):
    p=subprocess.run(cmd,cwd=r,capture_output=True);raw=p.stdout+p.stderr;(g/(name+'.txt.xz'if len(raw)>60000 else name+'.txt')).write_bytes(lzma.compress(raw)if len(raw)>60000 else raw);(g/(name+'.exit')).write_text(str(p.returncode)+'\n');print(name,p.returncode,flush=True);assert p.returncode==0,raw[:1700]
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','scripts/checkpoint.sh','.github/workflows',str((s/'native').relative_to(r)),str((s/'new-target-ic').relative_to(r)),str((s/'ci_new_target_ic').relative_to(r))],cwd=r)
run('reference729',['sha256sum','--check','experiments/chained-transfer-public-target/ci_new_target_ic/reference-01.sha256']);run('reportPython',['python3','tools/ci/check_report_graph_python.py']);run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]]);run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate'])
def stage():
    ps=paths();f=Path('/workspace/scratch/ct70-origin-protocol.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
    selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
    for p in ps:
        if p.startswith(b'pcc/claims/'):
            for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
                if proof.get('kind')=='attestation':
                    x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path'];assert x['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode==0,x['path']
    return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(g/'custody.json').write_text(json.dumps(dict(parent=base,actual_transport='ffe675/remoteandlocalORIGINALgate0/exactclean39e9/genuinereadback/receipt/no keyexport/laterstatechangesstale',new_protocol='2dd807 BEFOREcommon-origin-iccode/20pairedattempts/exactP0FB/r0..32/actualraworiginbridge/independentanswers/wholefailures',all729_science_prior15workflows_engines_verifiers_original_checkpoint_unchanged=True,governance='reference729/reportPython/ledger/prose/working+cachedwhitespace/wiring/benchrec/artifact0/allsubjects+staging',next='normalpublishprotocol THENnativecompatibilityimplementation/test/report;operationcoverage/genuinewholecapturepublicationNEW08',scope='unsigned/metadata/transportcapability notperformance/globalroot/mergewaiver'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Originaltransportacceptance/commonoriginprospective governance own39e9:ffe675 genuineoriginalremoteandlocalgate0/exactclean39e9/actualS3readback/originalreceipt/whole28members/no keyexport/laterstatechangesstale. New2dd807 common-originIC protocol BEFOREcratecode/all20pairedattempts/exactactualP0/fullFB+RNG/actualraworigin/sign/differences/r0..32/independentanswers/allfailures. Previous15workflows/729scienceinputs/engines/verifiers/originalcheckpoint unchanged. Originalreference729/reportPython/ledger/prose/working+cachedwhitespace/wiring/benchrec/artifact0/newsubjects hash+staging covered. Scientific1816 full3f52fc730/14CId53e33190native57canonical settled. NormalpublishprotocolTHENimplement;no performance/globalrootgreen/mergewaiver.']
for p in sorted(g.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True);selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: restore original checkpoint transport and freeze origin control'],cwd=r,check=True)
print(subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
