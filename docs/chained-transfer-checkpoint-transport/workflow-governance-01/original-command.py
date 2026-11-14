"""Checkpoint the prospectively authorized data-only original-gate workflow."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';docs=r/'docs/chained-transfer-checkpoint-transport';base='4c55dddae323425ce5a36272670a449605faf035';wf='.github/workflows/chained-transfer-checkpoint-transport.yml'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
d=docs/'protocol-normal-publication-01';d.mkdir()
for p in Path('/workspace/scratch/ct69-checkpoint-protocol-publication-01').iterdir():
    raw=p.read_bytes()
    if p.suffix=='.log':(d/(p.name+'.xz')).write_bytes(lzma.compress(raw))
    else:shutil.copyfile(p,d/p.name)
assert json.loads((d/'receipt.json').read_text())['head']==base and json.loads((d/'receipt.json').read_text())['original_exit']==0
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Prospectiveoriginalcheckpointtransport16bb06 NORMALpublished4c55ddda/treefdff909f/direct1816/78paths/d88795/originalpush0 BEFOREnewdataonlyworkflowcode. Also checkpoints terminalscientific1816 full3f52fc730/own14CId53e33190native57canonical. No originalgate/uploader/source/oldworkflow change. Newworkflowactualtransportoutcomepending;no performanceadmission/mergewaiver.']
for p in sorted(d.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
print(subprocess.check_output(['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Actualadditivedataonlyoriginalcheckpointworkflow underpublished16bb06/4c55beforecode:immutableconsumer3de8originalcheckpoint.sh/cmp/SHA3c419216/originalgate/cleanexacteventhead+trackedresume+rootignore/fixedbranch/120sbound/10minjob. AWScredentialsONLYtrustedoriginalgate+originalAWSreadback;AWSCLI installbeforecredentials/no candidatescientificcode/no keytokenexport/IAM/gate/statehash edits. Requireexactoriginalreceipt/remotecheckpoint+resume+metareadback/sourceandresume equality;wholeartifactonalloutcomes. Readonlyhostnamespaceprobe iscapabilityonly. Existing14workflows/all729scienceinputs/engines/verifiers unchanged. Actualoutcomependingnormalpublication;no assumedpass/performance/globalrootgreen.','--proof','attestation:'+wf],cwd=r,text=True).strip(),flush=True)
at=datetime.now(timezone.utc).isoformat()
resume='''# Resume: Chained ECDLP Transfers — {at}

## Goal
Continue nontrivial DLP-preserving transfers,chained Jacobians,prime-field descent and admitted computational comparisons across the three repositories. Continue after each rung. [pcc:unverified]

## Lead / hypothesis
Actual class-input IC solves all15 public cases in three transferred Jacobians. Current next scientific obligations are common-origin compatibility and complete operation coverage. Existing CI credentials may restore ORIGINAL S3 checkpoint transport;actual permission/outcome is unknown. [pcc:unverified]

## Spec
Scientific1816c3b9/nativee869bd/written1e65f0/57partialbindings/reportd1027f. Exact-source independentfull3f52fc730guards/ninephasepairs/82wholeJSON/both2gates2bindings/fouractualcontrols;own14CId53e33190native57canonical settled. Prospective16bb06/4c55 published BEFORE the data-only .github/workflows/chained-transfer-checkpoint-transport.yml. Protocol docs/chained-transfer-checkpoint-transport/PROTOCOL_01.md freezes originalconsumer3de8script/SHA3c419216/originalgate/readback/receipt/localgate requirements. [pcc:unverified]

## State
This committed HEAD contains the additive transport workflow and a complete tracked resume. All prior14workflows/729scientificinputs/engines/verifiers remain unchanged. Genuine43d6ba/babda6 all25wholeobjects13S3+12Git complete/guard07historicalreleased/futureFFNEW08. Originalrootfixture restored1ea795;rootfull03 remains124/unknowntotals;633ab0 locates twoexact101failures atmissingmandatorytime-namespacefiles beforepublicationassertions. [pcc:unverified]

## Next steps
NormalpublishthisHEAD. Discover EXACTHEAD workflow Original chained-transfer checkpoint transport;collect whole jobs/API/log/artifact at /workspace/scratch/ct69-original-checkpoint-transport-01. Preserve actualgate/readbackfailure or originalreceipt. Before editing this consumer worktree again,if remote success,require matchingcleanHEAD/originaltool+resume and copy ONLYgenuine originalreceipt toignored .resume/.last-push;run unchanged scripts/checkpoint.sh gate and retain actualexit. Never synthesize statehash/receipt. Then commit result andcontinue common-origin nativebridge/costcoverage/completebeta coordinates. [pcc:unverified]

## Runs in flight
No local scientific process. Next normalpublication triggers bounded10min data-onlyCI/originalgate120s and ordinary repositoryCI. Collect by exactcommitSHA/workflow name;source/runIDs are inGitHub Actions. Keep consumer tracked/untracked state clean until receipt import/originallocalgate evaluation;rawcaptures outside repository in scratch. No paidbenchmark/admittedperformance run. [pcc:unverified]

## Stop and success conditions
Transport requires originalremote gate0/genuineexactS3readback/originalreceipt/matchingcleanlocaloriginalgate0. A failure remains a scoped result;diagnose actualstage andcontinue useful authorized science. Any laterstatechange stalesadmission untilneworiginalcheckpoint. Budget/capacity/isolation/completecounters/strongestrefs,actualgeometry/logextension/mainledger/signing/reviews/conflict/vault/KB gaps remain separate. [pcc:unverified]
'''.format(at=at)
p=r/'.resume/RESUME.md';p.write_text(resume+'\n---\n\n'+p.read_text())
note='''\n## {at} — original-gate data workflow after published protocol\n\n### What was done (commands, files, features)\n+16bb06/4c55 protocolnormallypublished0 BEFOREworkflowcode. Additive originalcheckpointtransport workflow usesimmutableconsumer3de8tool/SHA3c419216/cmp/originalgate/cleancommittedstate+resume+rootignore/fixedbranch/120sbound/10minjob,credentials ONLYtrustedgate+originalAWSreadback. Wholeartifactalloutcomes;actualtransportnotyetobserved. [pcc:unverified]\n\n### Decisions made (and why)\n+Keep originalgate/uploader/statehash/prior14workflows/729scienceinputs/engines/verifiers intact. Prepare AWSCLIbeforecredentialstep. Require genuineremotecheckpoint/wholeResume/meta/originalreceipt then matchingcleanlocaloriginalgate;no assumedadmission orkeyexport. [pcc:unverified]\n\n### Open threads (unfinished, pick up next time)\n+NormalpublishthenbyEXACTHEADcollectdatajob/API/log/wholeartifact. Keepconsumerstateclean untilreceiptimport/localgate;rawoutsideworkspacegit. Afterwardsrecordoutcome andcontinue nativecommonorigin/countercoverage/completebetacoordinates. Scientific1816 full3f52fc/14CId53e33 settled,no manualredispatch. [pcc:unverified]\n\n### Errors (what went wrong, how it was handled)\n+Existinglocalcheckpointcredentials gap andoriginalroot124/twoexact101clockfailuresremain;allnegativecaptures preserved. Actualtransportpermission unknown;no performance/globalroot/mergewaiver. [pcc:unverified]\n'''.format(at=at).replace('\n+','\n')
with(r/'docs/session-logs/2026-11-13.md').open('a')as f:f.write(note)
(docs/'QUEUE.md').write_text('''# Original checkpoint transport queue

Published prospective16bb06/4c55 precedes the additive workflow. NextnormalpublishcurrentHEAD,collectexact-source Original chained-transfer checkpoint transport job/wholeAPI/log/artifact. Keep consumer tracked/untracked state clean until genuine receipt and unchanged local gate are evaluated;rawcaptures in /workspace/scratch/ct69-original-checkpoint-transport-01. ActualS3permission/gate/readback/localoutcome unknown. [pcc:unverified]

Require originalremote gate0/genuineS3checkpoint+Resume+meta/sourceequality/originalreceipt/matchingcleanlocaloriginalgate0. Preserveallfailures;no key/tokenexport/gate/statehash/IAMchange. Science1816full3f52fc730/14CId53e33190native57canonical settled. Then nativecommonorigin/costcoverage/completebetacoordinates;budget/capacity/isolation/references stillrequired beforeperformance. [pcc:unverified]
''')
g=docs/'workflow-governance-01';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
scope=[str(docs.relative_to(r)),wf,'pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,command):
    p=subprocess.run(command,cwd=r,capture_output=True);raw=p.stdout+p.stderr;(g/(name+'.txt.xz'if len(raw)>60000 else name+'.txt')).write_bytes(lzma.compress(raw)if len(raw)>60000 else raw);(g/(name+'.exit')).write_text(str(p.returncode)+'\n');print(name,p.returncode,flush=True);assert p.returncode==0,raw[:1600]
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','scripts/checkpoint.sh',str(s.relative_to(r))],cwd=r)
assert not subprocess.check_output(['git','diff','--name-only',base,'--','.github/workflows'],cwd=r)
run('reference729',['sha256sum','--check','experiments/chained-transfer-public-target/ci_new_target_ic/reference-01.sha256']);run('actionlint',['/workspace/scratch/actionlint-bin/actionlint',wf]);run('reportPython',['python3','tools/ci/check_report_graph_python.py']);run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]]);run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate'])
def stage():
    ps=paths();f=Path('/workspace/scratch/ct69-checkpoint-workflow.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
    selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
    for p in ps:
        if p.startswith(b'pcc/claims/'):
            for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
                if proof.get('kind')=='attestation':
                    x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'];assert x['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode==0
    return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(g/'custody.json').write_text(json.dumps(dict(parent=base,prospective='16bb06/4c55 normallypublishedBEFOREcode',original_tool='consumer3de8checkpoint.sh/SHA3c419216/originalgate',only_new_workflow=wf,prior14_workflows_729science_engines_verifiers_original_checkpoint_unchanged=True,credential_scope='trusted originalgate+originalAWSreadback only;no key/token export;installbeforecredentials',governance='reference729/actionlint/reportPython/ledger/prose/working+cachedwhitespace/wiring/benchrec/artifact0/allsubjects+staging',actual_transport='pendingnormalpublication;unknown;cleanlocalworktree requireduntil genuine receipt import andoriginalgate evaluation',scope='dataonly/unsigned/no performance/globalrootgreen/mergewaiver'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Originalcheckpoint dataworkflow governance underpublished16bb06/4c55 beforecode:originalconsumer3de8checkpoint.sh/SHA3c419216/cmp/originalgate/cleanexacteventsource+resume+rootignore/fixedbranch/120s/10min;AWScredentialsONLYtrustedgate+originalAWSreadback/no scientificcandidatecode/keyexport/IAM/gate/statehash edits. Requiregenuineoriginalreceipt/remotecheckpointResumeMeta/sourceequality/matchinglocaloriginalgate0;wholeartifactalloutcomes/no assumedpass. Previous14workflows/729scienceinputs/engines/verifiers/originalcheckpoint unchanged. Originalreference729/actionlint/reportPython/ledger/prose/working+cachedwhitespace/wiring/benchrec/artifact0/newsubjects hash+staging covered. Keep consumerstatecleanuntilactualreceipt/localgate;scientific1816 full3f52fc/14CId53e33 settled. No performanceadmission/globalrootgreen/mergewaiver.']
for p in sorted(g.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True);selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','ci: checkpoint committed transfer state with the original uploader'],cwd=r,check=True)
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=r)
print(subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
