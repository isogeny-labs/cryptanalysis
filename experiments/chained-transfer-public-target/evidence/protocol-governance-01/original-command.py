"""Owned prospective protocol checkpoint; original repository gates only."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,hashlib,shutil
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='1e4f1292d473a9c01821d946c0ec846b17f8ae1a'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
d=s/'reports/proposal-01'
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Prospective publictarget source-review report ONEfinal35418-bytePDFpage visuallyinspected;editableDOT/SVG/Typst/JSON/renderer retained. Protocol7e016c precedes newcasegeneration/nativeimplementation. ExistingcompleteN4/B2/publicQderivative/fivefixedcorrectnesstargets/additiveV2bridges proposed,notexecuted;candidate_idnull/no exactnewcurveidentityyet. Preservewithdrawnsubgroupenumeration/costadmission/vaultKBscope;canonicalmathedgesunchanged,dashededgesproposal.']
for p in sorted(d.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
report=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct57-proposal-report.claim').write_text(report+'\n');print('report',report,flush=True)
index=r/'problems/README.md';text=index.read_text();anchor='| [Independent chained-transfer input closure]';at=text.index(anchor);text=text[:at]+'| [Public-target chained-transfer destination bridge](chained-transfer-public-target-destination-bridge.md) | open | public-Q IC solver and explicit completed map/basepoint bridge after the canonical norm | prospective public-target protocol P1/P2, five independently checked solves, faithful original-gate proofs; cost admission separate |\n'+text[at:];index.write_text(text)
checkpoint=f'''# Public-target destination calculus — protocol checkpoint

## Goal
Continue ChainedECDLPTransfers across crypto/cryptanalysis/vaultlockedcrypto-autoresearcher;nontrivialDLP-preservingmaps,prime-fielddescent andcompletecostadvantage remainobjective. Currentboundedrung: public-Q N4/B2 API andadditiveV2bridges,notnewsolvername orspeedclaim.

## Lead / hypothesis
OriginalN4/B2 alreadycomplete;itsk_true onlyconstructsQinsidecountedbody. Reusewholeoriginalalgorithmwithpublictarget input,thencheckfield/model/basepoint/completedmapbridges. Preserveoldwithdrawnsubgroupenumerationandlegacycostscope. Primaryb992d8/actual5327f4,12wholeoriginalcataloghashes match. CurrentKBabsent/prior127fallback receipts;vault8edec422locked/no unlock/write/subagents. [pcc:unverified]

## Spec
experiments/chained-transfer-public-target/PROTOCOL-01.md, prospective7e016c;sourcecatalog/evidence/primary-01;proposalreport{report}/ONE35418bytePDFpageALLinspected. Parentready1521/source069/metadata1e4f1292. Newbranchresearch/chained-transfer-public-target-20261113 MUSTnormallypublish/openreadychildunder1521 BEFOREnewcases/code. candidate_idnull. Frozenoriginalbuilderq223seed1/max200000;fiveknownanswerwitnesses outsideactualpublicinputs;originalsixB2retrycaps;all5mustsolveforacceptance. [pcc:unverified]

## State
No newnativeimplementation/casegeneration/solve/proof attempted. ParentnormFULL7b231c/own7CI168c99 settled/all36JSON+24canonicalbindingsmatch;rawgenuinecfbe78/f5c83d. Parentconsumer1e4f1292/907161/normalpush0. Rootfinalmetadata1a47c84e/9249cc/normalpush0 aftercanonicalaef7;cachedwhitespace2 onoriginalpushlog preserved9b10d2,losslessencodingcorrectionandoriginalgates0. Rootglobal NOTgreen/missingauthenticfixture/originalpull2credentials/anonymous403/add561;mainledger/signing/conflict/review requirements separate. CIandraw settled:no repoll/redispatch. [pcc:unverified]

## Next steps
Normalpublish protocolcommit/newbranch/openreadychildunder1521. Thenimplement P1 ORIGINAL-body publicQ derivative andstrictCLI;freezeplan/source+commands BEFOREboundedstatic/unit/proofchecks. Separateoriginalsourceverification;recordEVERYattempt/failure;no genericDLPfallback. ThenP2additiveV2constructor/model/basepoint/completefibre/normbridge andfeasibleLean. ComparativeexperimentneedsoriginalS3checkpointgate/livebudget/capacity;notadmitted.

## Runs in flight
NONE native. Onlythismetadata governance/publication. No backgroundexperimentpromised. Scratchwholepreviousraw andbuildcaches outsideevidence retained;rootdiagnosticbinaryneededonceauthenticfixtureavailable. Workspace~5GiBfreeatlastread.

## Stop and success conditions
Do notstopatprotocolornegativeattempt;continue nextunblockedresearch. P1all5publicICsolves+strictcontrols/derivativediff/originalverification required. P2fullbridge/compositions/actualoddsubgroup/written+faithfulpartialLean required. Costadvantage requiresactualadmittedcompletecomparison. Preservefailures,wholearchives/memberhashes/genuineremotepublication andnewversionedcorrections. No force/rebase/rechain/lineageselection;nextglobalroutine13:45unlessconcretesignal.
'''
(s/'CHECKPOINT.md').write_text(checkpoint);(r/'.resume/RESUME.md').write_text(checkpoint)
with (r/'docs/session-logs/2026-11-13.md').open('a') as f:f.write('\n## '+datetime.now(timezone.utc).isoformat()+' — prospective public-target destination continuation (Codex)\n\n### What was done (commands, files, features)\n\nProtocol7e016c/sourcecatalog12wholeoriginalshashmatch/ONE35418-byteproposalPDFpageALLinspected/'+report+';newreadychildbranchunder1521beforeANYnewcase/code. ParentnormCI/rawsettled;rootfinalmetadata1a47 normalpush0. [pcc:unverified]\n\n### Decisions made (and why)\n\nReuseexistingcompleteN4/B2 via literalpublicQ derivative;unknownwitnessdenied/no genericDLPfallback. Originalconstructorq223seed1 and5target/sixretrycaps frozen;allfive mustsolveforacceptance. AdditiveV2 preservesV1privateorigin/normalforms andoldcontrols. AccountingaloneisNOTalgorithmicgain.\n\n### Open threads (unfinished, pick up next time)\n\nNormallypublishprotocol/openreadychild,thenimplement/test/proveP1/P2;no newnativeattemptyet. KB unavailable:currenttoolcatalogabsent;prior6actual127fallback receipts anddirectprimaryb992read. Vault8edec422locked. Mainmerge/fixture/costadmission separate. [pcc:unverified]\n\n### Errors (what went wrong, how it was handled)\n\nNo newnativeattemptyet. Parentcollectorcanonicaldigest,optionalZIP403 androotpushlogwhitespace encodingfailuresretained;no scientificcriteriaweakened. [pcc:unverified]\n')
g=s/'evidence/protocol-governance-01';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
scope=[str(s.relative_to(r)),'problems/chained-transfer-public-target-destination-bridge.md','problems/README.md','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,cmd):
    v=subprocess.run(cmd,cwd=r,capture_output=True);(g/(name+'.txt')).write_bytes(v.stdout+v.stderr);(g/(name+'.exit')).write_text(str(v.returncode)+'\n');print(name,v.returncode,flush=True);assert v.returncode==0,(v.stdout+v.stderr).decode()[:1800]
run('parent437',['sha256sum','--check','experiments/chained-transfer-reference/g3-norm-reference-01.sha256'])
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','.github','experiments/chained-transfer-reference'],cwd=r)
assert not any(p.endswith((b'.rs',b'.lean')) for p in paths())
subjects=[]
for p in paths():
    if p.startswith(b'pcc/claims/'):
        for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
            if proof.get('kind')=='attestation':
                x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'];subjects.append(x['path'])
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode() for p in paths() if p.endswith(b'.md')]]);run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate'])
def stage():
    ps=paths();f=Path('/workspace/scratch/ct57-protocol.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True);selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
    for p in subjects:assert subprocess.run(['git','cat-file','-e',base+':'+p],cwd=r,capture_output=True).returncode==0 or p.encode() in selected,p
    return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(g/'custody.json').write_text(json.dumps(dict(base=base,all437_parent_inputs_unchanged=True,whole_old7workflow_and_producer_workflow_unchanged=True,no_new_Rust_Lean_native_case=True,own_ledger_prose_whitespace_wiring_benchrec_artifact=0,all_new_attestation_hashes_and_subject_staging_covered=True,protocol='7e016c prospective, publish BEFORE newcases/code',report=report,benchmark_admission=False),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Publictarget pre-codeprotocol governance:own1e4ledger/prose/workingcachedwhitespace/wiring/benchrec/artifact0;all437parentnativeinputs/whole7workflow unchanged/no newRustLean orcasegeneration. Allnewsubjecthash/stagingcoverage;prospective7e016c andONE35418inspectedproposalPDF. Readychild/normalpublication requiredBEFOREimplementation. No benchmark admission/verifier/trust/policy edits.']
for p in sorted(g.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct57-protocol-governance.claim').write_text(cl+'\n');selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: freeze public-target N4 continuation before implementation'],cwd=r,check=True);print(cl,subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
