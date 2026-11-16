"""Commit terminal source validation and prospective transport protocol."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';docs=r/'docs/chained-transfer-checkpoint-transport';base='1816c3b99cb69e2072a7f0a246bdeb98b9f005e8'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
d=docs/'source-and-GitHub-checkpoint-01';d.mkdir()
for source,label in [('/workspace/scratch/ct69-new-target-IC-source-publication-01','consumer-normal-publication'),('/workspace/scratch/ct69-root-final-metadata-publication-01','root-normal-publication')]:
    folder=d/label;folder.mkdir()
    for p in sorted(Path(source).iterdir()):
        if not p.is_file():continue
        raw=p.read_bytes()
        if p.suffix=='.log':(folder/(p.name+'.xz')).write_bytes(lzma.compress(raw))
        else:shutil.copyfile(p,folder/p.name)
for p in sorted(Path('/workspace/scratch').glob('ct69-GitHub-published-*')):
    raw=p.read_bytes();(d/(p.name+'.xz')).write_bytes(lzma.compress(raw))
assert json.loads((d/'consumer-normal-publication/receipt.json').read_text())['original_exit']==0
assert json.loads((d/'root-normal-publication/receipt.json').read_text())['original_exit']==0
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Normalnonforce scientificsource1816c3b9/tree6e2872f8/direct3baa/245paths/58030b push0 BEFOREindependent730full/14CI. Rootfinalmetadata073229fe/tree78ccf900/directe563da1b1/82paths/775838 push0. CompleteGitHubPR1523/root3877/queue3904 body+API checkpoint retainedlossless;that earlier snapshot markedvalidationpending,nowseparateterminal3f52fc/d53e33 establishesfull730/14uniqueCI190native57canonical. No policy/gate/source/verifier/mergewaiver.']
for p in sorted(d.rglob('*')):
    if p.is_file():cmd+=['--proof','attestation:'+str(p.relative_to(r))]
print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
at=datetime.now(timezone.utc).isoformat()
note='''\n## {at} — current IC source independently replayed; transport protocol frozen\n\n### What was done (commands, files, features)\n+Scientific1816 normallypublished0. Independentfull3f52fc:ALL730guards0/nineorderednative+tee0/0/ONEunfilteredtest/ALL82wholeJSONexceptdeclaredrawwalls/bothoriginal2declgates/2canonicalbindings/fouractualadmission2nooutputrestored. OwnCId53e33 ALL14unique workflowsSUCCESS/190native records/57originalcanonicalPCCdigests equal;15eventsincludeextraedited-bodyPCCsuccess/signlegitimatelyskipped. Whole15logs/API/730selectedsourcesretained,largecombined/gluing/productobjectsawaitnextgenuinearchive. [pcc:unverified]\n\n+Prospective16bb06 originalcheckpointtransport docs precedesnewdataonlyworkflow;originalimmutableconsumer3de8tool/gate/SHA3c419216/cleanexactstate+resume/existingCIcredentialsconfinedtrustedstep/genuineS3readback+originalreceipt+matchinglocaloriginalgate0required. No assumedtransportpass orbenchmarkadmission. [pcc:unverified]\n\n### Decisions made (and why)\n+Advance unblockednativecommonorigin/costcoverage whileboundedtransport routeisimplemented. Prior14workflows/729scientificinputs/originalengines/verifiers unchanged. SourceandGitHubcheckpoint API/bodywholecaptureslosslessGit. [pcc:unverified]\n\n### Open threads (unfinished, pick up next time)\n+NormalpublishprotocolBEFOREworkflow;addboundeddataonlyCI/collectactualgate/readback/receipt/localgate. Continuecommonorigin/countercoverage/completebetacoordinates;futurewholedatahandoffNEWguard08 includinglatestfull730/current729/laterwork. [pcc:unverified]\n\n### Errors (what went wrong, how it was handled)\n+Allnative/sourcegovernance/reportdraft/setup/citation/root124/twoexact101clock failuresretained;rootrequirescapablehost. Actualgeometry/global-logextension/costs/admission/mainledger/signing/reviews/conflict/vault/KB gapsremain. [pcc:unverified]\n'''.format(at=at).replace('\n+','\n')
for p in [r/'docs/session-logs/2026-11-13.md',r/'.resume/RESUME.md']:
    with p.open('a')as f:f.write(note)
q='''# Current research queue — {at}

Scientific1816c3b9 is settled:full3f52fc/all730guards/ninephasepairs/82wholeJSONexceptdeclaredwalls/both2gates2bindings/fouractualadmissioncontrols;own14CI d53e33/all190native57canonicaldigests exact/15eventsincludeextraPCCeditedbody. Nativee869bd all15publiccases/60attempts/57partialbindings/reportd1027f/genuinewholedata43d6ba/babda6. [pcc:unverified]

| Priority | Task | Next discriminating action |
| --- | --- | --- |
| 1 | Native common-origin compatibility | Freeze exactorigin/class inputs againstoriginalrandomP0/legacyaffine triples;preserveoriginals,all failures andactualgroup checks. [pcc:unverified] |
| 2 | Complete cost coverage | CoverFpR/extension/source-model/maps/admission/solver/independentverification,bothcoldand online,beforeanyperformancecomparison. [pcc:unverified] |
| 3 | Original checkpoint transport | Prospective16bb06 docs/chained-transfer-checkpoint-transport/PROTOCOL_01.md BEFOREnewworkflow. Normalpublishprotocol;implementoriginaltrustedgate withcurrentCIcredentialsonly/genuineS3readback/exactoriginalreceipt/matchinglocaloriginalgate0. Retainactualfailureorpass;no tokenexport/gate/statehash edits. [pcc:unverified] |
| 4 | Complete beta coordinates | Matched(1,0) globalwritten degree13^3/polarization13/both13/F=2beta;actualcompletecoordinatesopen. [pcc:unverified] |
| 5 | Root/formal/merge | Rootfull124/unknowntotals;633ab0 twoexact101clockinitfailures beforepublicationassertions/requirednamespacefilesabsent. FuturecapableLinuxhost originalregression. Mainledger/signing/reviews/conflict/geometry/logextension/vault/KB gapsremain. [pcc:unverified] |

Wholecurrent730full/14CI capturesawaitnextgenuinewholepublication;older12captures+12indices+wholePDF25objectsalreadygenuine43d6ba/babda6. Guard07historical/released;futureFFfreezeNEW08. OriginalS3/livebudget/capacity/isolation/fullcost/strongestrefs remainindependentadmissionrequirements. Continueaftereachrung. [pcc:unverified]
'''.format(at=at)
p=s/'RESEARCH_QUEUE.md';p.write_text(q+'\n---\n\n'+p.read_text())
g=docs/'protocol-governance-01';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
scope=[str(docs.relative_to(r)),str((s/'evidence/new-target-IC-independent-full-01').relative_to(r)),str((s/'evidence/new-target-IC-own-CI-01').relative_to(r)),str((s/'RESEARCH_QUEUE.md').relative_to(r)),'pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,command):
    p=subprocess.run(command,cwd=r,capture_output=True);raw=p.stdout+p.stderr
    (g/(name+'.txt.xz'if len(raw)>60000 else name+'.txt')).write_bytes(lzma.compress(raw)if len(raw)>60000 else raw);(g/(name+'.exit')).write_text(str(p.returncode)+'\n');print(name,p.returncode,flush=True);assert p.returncode==0,raw[:2000]
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','.github/workflows',str((s/'native').relative_to(r)),str((s/'new-target-ic').relative_to(r)),str((s/'ci_new_target_ic').relative_to(r))],cwd=r)
run('reference729',['sha256sum','--check','experiments/chained-transfer-public-target/ci_new_target_ic/reference-01.sha256']);run('reportPython',['python3','tools/ci/check_report_graph_python.py']);run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]]);run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate'])
def stage():
    ps=paths();f=Path('/workspace/scratch/ct69-checkpoint-protocol.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
    selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
    for p in ps:
        if p.startswith(b'pcc/claims/'):
            for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
                if proof.get('kind')=='attestation':
                    x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path'];assert x['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode==0,x['path']
    return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(g/'custody.json').write_text(json.dumps(dict(parent=base,source_full='3f52fc730guards/ninephasepairs/82wholeJSON/both2gates2bindings/fouractualcontrols',source_CI='d53e33/14uniqueworkflows/15events/190native57canonical',prospective_transport='16bb06 BEFOREnewworkflow/originalconsumer3de8gate/SHA3c419216',old14workflows_729_science_engines_verifiers_unchanged=True,governance='reference729/reportPython/ledger/prose/working+cachedwhitespace/wiring/benchrec/artifact0/allnewsubjects+staging',next='normalpublishprotocol THENdataonlyworkflow/actualoriginalgate/readback/receipt/localgate;nativeorigincompatibility/costcoverage',scope='metadata/unsigned/no assumedadmission/globalrootgreen/mergewaiver'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','CurrentICvalidation/prospectiveoriginalcheckpointtransport governance:source1816 full3f52fc730/9phasepairs/82wholeJSON/both2gates2bindings/fouractualcontrols;own14CI d53e33190native57canonical/15eventswithPCCeditedsuccess. Prospective16bb06 originalconsumer3de8gate protocol BEFOREnewworkflowcode;actualtransportoutcomepending/no assumedpass. Existing14workflows/729scientificinputs/engines/verifiers unchanged. Originalreference729/reportPython/ledger/prose/working+cachedwhitespace/wiring/benchrec/artifact0/newsubjects hash+staging covered. Source/rootnormalpublicationsandGitHubwholebody/API retainedlossless;allfailurespreserved. Nextnormalpublishprotocol THENdataonlyworkflow/actualgate/genuineS3readback/originalreceipt/matchinglocalgate;nativeorigin/costcoverage. Unsigned/no cost/globalrootgreen/mergewaiver.']
for p in sorted(g.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True);selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: checkpoint Jacobian IC replay and original transport protocol'],cwd=r,check=True)
print(subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
