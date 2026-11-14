"""Publish actual IC source after genuine whole-data publication; original gates."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,os,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
base='3baa6d0a44973ecbb5dd1db0b5a724e235727e78'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
wf='.github/workflows/chained-transfer-new-target-ic.yml'
note='''
## {at} — actual new-target IC source and genuine whole data

### What was done (commands, files, features)
Prospective98c6f0/2aee published BEFOREcode. Nativee869bd:oneunfilteredtest0/all2543guards0/ALL60attempts/82wholeJSON/ALL15publiccases onall3 actualJacobian targets;every reported answer actualtarget+independentoriginalsourcechecked. Typed class-input solver reuses originalrelation/LA/innerdescent withactualP0/fb0anchor andR,R+G,R+Q;no scalarwitness/ECDLPfallback. Written1e65f0/twofaithfulbindings01efbf671d42/bothoriginalgates2/57total/whole636aec377526;finalreportd1027f/TWO69377-bytePDFpages ALLinspected. [pcc:unverified]

Actual43525890255/job132231419911 pull_request_targetSUCCESS/THIRTEENremote byte replays BEFOREe563da1b1/direct4125274f/EXACT15paths. TWELVEwholeclosedcaptures+TWELVEwholeindices+ONEwholefinalPDF25objects:13genuineS3+12smallwholeGit. Root43d6ba/consumerbabda6/normalFF/artifact/wiring0/all3455guard07+BOTHereposdirtybytes+PDFlinktype/target unchanged;hold07 RELEASEDafterterminal. Whole434959-byteUTF8log/allAPI losslessXZ/push/FF/manifests direct/no recursivearchive. FinalPDFcanonicaldocsdata+researchrelativesymlink preserveoriginalPCCdocs hydration;originalartifactverify0/PCCreport2notcovered/no perproof failures/all729CIinputs0;negativecopies2good1missing1substituted2restored714529. No policythreshold/verifier/trust change. [pcc:unverified]

Newstrict729portable/348producer+self730/ninepositivephasepairs/oneunfilteredtest/ALL82wholeJSON exceptONLYdeclared rawwallfields/bothoriginal2declgates/2canonicalbindings adds14thworkflow. Prior13workflows/702scienceinputs/originalengines/verifiers unchanged. Ownpublished-source independent730full/fouractualadmissioncontrols and14CI190native57digests are NEXT,pending. [pcc:unverified]

### Decisions made (and why)
Preserveall60attempts/failedrelationcontrols/fullraw/reportdraft/citation+setupfailures. GenuinewholePDFdata precedes sourcecommit;69KBPDFneverstagedasGitblob. Same-origin nativecompatibility/globalrelationlogextension/completeFpR/model/maps/admission/verification costs remainopen;raw counters/walls diagnostic only. [pcc:unverified]

### Open threads (unfinished, pick up next time)
Normalpublishnewsource;freshphysicalGit siblings+original3d+genuinefixture readonlyverify0/all730guards/fouractual2nooutput controls/2100sfull;collectall14sourceworkflowjobs/190native57canonicaldigests. Then common-origin nativebridge/countercoverage,completeodddegreebeta coordinates andmateriallydifferent originalS3checkpointuploaderCIroute. Sourcequeue/GitHub3904 current;continueaftereachoutcome. [pcc:unverified]

### Errors (what went wrong, how it was handled)
Rootoriginalfull03 remains124/1800s/all2137guards0/unknowntotals. Actual633ab0 SAMEbinarytwoexactdiagnostics EACH101 beforepublicationassertions:containerlacks originalmandatory/proc/self/ns/time and/proc/self/timens_offsets;bootidread0/namespacereads1. FutureoriginalregressionrequirescapableLinuxhost;no unchangedwhole retry/clockcheck weakening. OriginalS3checkpoint/livebudget/capacity/completecosts/strongestrefs/mainledger/signing/reviews/conflict/fullgeometry/vaultlocked/KB gapsremain. [pcc:unverified]
'''.format(at=datetime.now(timezone.utc).isoformat())
for p in [r/'docs/session-logs/2026-11-13.md',r/'.resume/RESUME.md']:
    with p.open('a')as f:f.write(note)
q='''# Current research queue — {at}

Actualnew-targetICe869bd all15publiccases/all60attempts/82wholeJSON/2543guards,written1e65f0/twofaithfulbindings/57total/reportd1027f finalTWO69377-bytepages inspected. Genuine43d6ba/babda6 covers12wholecaptures+12wholeindices+wholePDF25objects13S3+12Git;hold07 releasedafterexactFF/all3455guards+linktypes. Newsource/checkpointnowprepared;normalpublication/full730/14CIpending. [pcc:unverified]

| Priority | Task | Next discriminating action |
| --- | --- | --- |
| 1 | Independent current-source replay | Normalpublishsource;cleanphysical730full/fouractualadmission2/nooutput/restored/ninephasepairs/oneunfilteredtest/all82wholeJSON exceptdeclaredrawwalls/both2declgates/2canonicalbindings;collectALL14workflows190native57digests. [pcc:unverified] |
| 2 | Same-origin compatibility and costs | Freshnativebridge against originalrandomP0/legacy affine triple;alloriginals/failures retained. Cover FpR,source/model/maps/admission/verification and cold+online allphases before measuring. [pcc:unverified] |
| 3 | Original S3 checkpoint admission | Materiallydifferent dataonlyCI runs ORIGINALpinneduploader oncleancommittedstate/actualresume with credentialsonlytrustedstep;retain success/IAMdenial. Restore onlygenuine exactstate receipt and let ORIGINALgate decide. No tokenexport/gateedit;budget/capacity/references stillrequired. [pcc:unverified] |
| 4 | Complete odddegree coordinates | Matched(1,0) globalwrittenbeta degree13^3/polarization13/both13/F=2beta;completecoordinate/divisor map remainsopen. All3current52kernels nonfree C52^3. [pcc:unverified] |
| 5 | Original root and merge/formal | Rootfull124/unknowntotals;633ab0 identifies twoexact101failures atmissingmandatorynamespacefiles beforepublicationassertions. Futureoriginalregression oncapableLinuxhost;no unchangedwhole retry. Mainledger/signing/reviews/conflict/actualgeometry/vaultlocked/KBecdb remain. [pcc:unverified] |

Refinementfb9ee fullb38c7f703/own12CI65dd08108native55digests settled;actualJacobian52 source45ee full417921676/11CI0ba3a0101native52digests settled. No settledscience redispatch. Actualrootfixture restored1ea795/67ef1d/2293097bytes/SHA8970667e/originalverify0/samebinarytargetedpass. Originalbenchmarkadmission separate;no measuredcostoradvantageclaim. [pcc:unverified]
'''.format(at=datetime.now(timezone.utc).isoformat())
p=s/'RESEARCH_QUEUE.md';p.write_text(q+'\n---\n\n'+p.read_text())
p=r/'problems/README.md';text=p.read_text();row='| [Actual new-target IC compatibility and complete cost coverage](chained-transfer-new-jacobian-ic-cost-coverage.md) | open; native compatibility/cost/formal gaps | Same-origin original-IC bridge and complete cold+online FpR/model/map/admission/verification coverage | e869bd all15cases/60attempts;57partialbindings/finalreport inspected;genuinewholedata complete;next independent730full/14CI then native compatibility/cost coverage. [pcc:unverified] |\n'
assert 'chained-transfer-new-jacobian-ic-cost-coverage.md'not in text
anchor='| [Transported52 kernels';idx=text.index(anchor);p.write_text(text[:idx]+row+text[idx:])
g=s/'evidence/new-target-IC-source-governance-01';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
scope=[str(s.relative_to(r)),wf,'docs/research-artifacts/chained-transfer/new-target-IC-01','pcc/claims','pcc/ledger.jsonl','problems/chained-transfer-new-jacobian-ic-cost-coverage.md','problems/README.md','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,cmd,expected=0):
    p=subprocess.run(cmd,cwd=r,capture_output=True);raw=p.stdout+p.stderr
    (g/(name+'.txt.xz'if len(raw)>60000 else name+'.txt')).write_bytes(lzma.compress(raw)if len(raw)>60000 else raw);(g/(name+'.exit')).write_text(str(p.returncode)+'\n')
    print(name,p.returncode,flush=True);assert p.returncode==expected,raw.decode(errors='replace')[:1800]
    return p
before=json.loads(Path('/workspace/scratch/ct68-new-target-IC-native-01/before.json').read_text());assert len(before)==2543 and all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in before.items())
changed=set(subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','.github/workflows','experiments/chained-transfer-reference',str((s/'native').relative_to(r)),str((s/'odd-product-models').relative_to(r)),str((s/'odd-product-maps').relative_to(r)),str((s/'odd-product-refinements').relative_to(r)),str((s/'ci_odd_refinement').relative_to(r))],cwd=r,text=True).splitlines())
assert changed<={wf},changed
run('reference729',['sha256sum','--check',str((s/'ci_new_target_ic/reference-01.sha256').relative_to(r))])
run('shell',['bash','-n',str(s/'ci_new_target_ic/check.sh')]);run('actionlint',['/workspace/scratch/actionlint-bin/actionlint',wf])
run('format',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',str(s/'new-target-ic/src/lib.rs'),str(s/'new-target-ic/src/tests.rs')])
run('reportPython',['python3','tools/ci/check_report_graph_python.py']);run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]])
run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate'])
subprocess.run(['git','add','--sparse','-f','--',str((s/'new-target-ic/Cargo.lock').relative_to(r))],cwd=r,check=True)
def stage():
    ps=paths();f=Path('/workspace/scratch/ct69-new-target-IC-source.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0')
    subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
    selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
    for p in ps:
        if p.startswith(b'pcc/claims/'):
            for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
                if proof.get('kind')=='attestation':
                    x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
                    assert x['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode==0,x['path']
    pdf='docs/research-artifacts/chained-transfer/new-target-IC-01/report.pdf'
    assert pdf.encode()not in selected and subprocess.run(['git','check-ignore','-q',pdf],cwd=r).returncode==0
    alias='experiments/chained-transfer-public-target/reports/new-target-IC-01/report.pdf'
    assert subprocess.check_output(['git','ls-files','--stage','--',alias],cwd=r,text=True).startswith('120000 ')
    assert (pdf.rsplit('/',1)[0]+'/.artifacts.json').encode()in selected
    return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(g/'custody.json').write_text(json.dumps(dict(base=base,native='e869bd/all2543unchanged/oneunfiltered/82wholeJSON/60attempts/15publiccases',written='1e65f0/conditionalglobal-log and genuine-leftinverse bridges explicit',formal='2faithfulexact/bothoriginalgates2/57total/partialunsigned',report='d1027f/TWO69377-byte finalPDFpages ALLinspected/genuinecanonicaldata+transparentrelativeGitlink',genuine_publication='43d6ba/babda6/43525890255/13remotereplays/e563da1b1/15paths/all3455guards+linktypes hold07released',new_CI='729portable348producer/730outer/ninephasepairs/oneunfiltered82wholeJSONexceptdeclaredrawwalls/both2gates2bindings/new14thworkflow',previous13workflows_and_original702science_engines_verifiers_unchanged=True,governance='ledger/prose/working+cachedwhitespace/wiring/benchrec/artifact/format/actionlint/shell/reportPython0/allnewsubjects+staging/genuinecanonicalPDFnotGitblob',next='normalpublish/730independentfull/fouractualcontrols/14CI190native57digests/commonorigin/costcoverage/originalS3uploaderCI/betacoordinates',scope='unsigned/correctness/not globalrootgreen/computationaladvantage/mergewaiver'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','ActualnewtargetIC source governance underpublished98c6f0/2aee beforecode:oneunfiltered nativee869bd/2543unchanged/ALL60attempts/82wholeJSON/ALL15publiccases actualtarget+independentoriginalsourcechecked. Written1e65f0/twofaithfulbindings01efbf671d42/bothoriginalgates2/57partialunsigned/reportd1027f TWO69377-bytefinalpagesinspected. Genuine43d6ba/babda6/13remote replays/e563da1b1/25wholeobjects13S3+12Git/all3455guards+linktypes preserved/hold07released. WholePDFcanonicaldocsS3+relativeGitlink/originalPCC negativecontrols/unchangedhydration;PDFnotGitblob/no policythreshold/trust change. Newstrict729portable+self730/ninephasepairs/14thworkflow/82JSONexceptdeclaredrawwalls/twobindings prepared;ownfull/fourcontrols/14CI190native57digests pending. Prior13workflows/702science/originalengines/verifiers unchanged. Originalledger/prose/whitespace/cachedwhitespace/wiring/benchrec/artifact/format/actionlint/shell/reportPython0/newsubjects+staging covered. Compatibility/cost/geometry/admission/root124/mainmerge gaps explicit;no computationaladvantage or waiver.']
for p in sorted(g.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();print(cl,flush=True)
selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: solve public logarithms on three transferred Jacobians'],cwd=r,check=True)
print(subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
