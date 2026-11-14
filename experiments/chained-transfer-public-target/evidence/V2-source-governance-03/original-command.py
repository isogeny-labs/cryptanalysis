"""Owned source/evidence checkpoint through original repository gates."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='68d22cee01126c9a03a2222687b0faf62113489d'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
assert not(s/'completed-descent').exists(),'prospective protocol must publish before candidate source'
d=s/'evidence/V2-source-governance-03';d.mkdir();shutil.copyfile(__file__,d/'original-command.py')
scope=[str(s.relative_to(r)),'.github/workflows/chained-transfer-completed-v2.yml','pcc/claims','pcc/ledger.jsonl','problems/chained-transfer-public-target-destination-bridge.md','problems/q223-prime-field-elliptic-shortcut.md','problems/README.md','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
subprocess.run(['git','add','--sparse','-f','--',str((s/'v2/Cargo.lock').relative_to(r))],cwd=r,check=True)
def paths():
    return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,cmd,expected=0):
    p=subprocess.run(cmd,cwd=r,capture_output=True);raw=p.stdout+p.stderr
    if len(raw)>60000:
        z=lzma.compress(raw);assert lzma.decompress(z)==raw;(d/(name+'.txt.xz')).write_bytes(z)
    else:(d/(name+'.txt')).write_bytes(raw)
    (d/(name+'.exit')).write_text(str(p.returncode)+'\n');print(name,p.returncode,flush=True)
    assert p.returncode==expected,raw.decode()[:1800]
    return raw
now=datetime.now(timezone.utc).isoformat()
current=f'''# Chained ECDLP Transfers: actual q223 V2 and completed-descent candidate next

## Goal
Continue nontrivial DLP-preserving transfers/chained Jacobians/prime-field descent and admitted computational comparisons across crypto,cryptanalysis and vault-locked crypto-autoresearcher. Continue after each rung; never infer a computational advantage from correctness. [pcc:unverified]

## Lead / hypothesis
Original N4/B2 public-Q baseline is implemented, independently replayed and ownCI checked. Actual q223 completed maps now identify S=-I, true nonzero legacy origin and rawkey-delta vs rawGen-two-delta. Next candidate replaces ONLY split-transfer triple rejection in individual descent with actual complete Gen spaces at the same actual P0. More complete maps may cost more; no speed prediction is accepted. [pcc:unverified]

## Spec
Frozen P1 PROTOCOL-01/7e016c/f888 was actually published beforecode. DERIVATION/PROOF_MAP f68241 unchanged. V2_MAPS_01/8d4b0d and inspected2page55543-byte report0085e7 describe actualq223 maps/conditional formal gap. Active prospective COMPLETED_DESCENT_PROTOCOL_02/74e00a must be normallypublished in this checkpoint before creating completed-descent code. Historical01/8d4b0d is byte-exact with2literalprose findings;active02 differs only title/two unverified tags. Originallinter unchanged. No candidatecode exists yet.

## State
Published P1 source68d22ce. Independentfull0267baa2:435guards0,all43orderednative/tee pairs29positive0/0+14intentional2/0;all3native/fiveIC14controls/bothoriginal9+5gates/all14exactbindings. OwnCIa5a143 exact68d run43432174569/job131908108813SUCCESS;all13non-timing native records/all14canonicaldigests match. Oldfull01 caller absolute-pathfailure080841 retained. Rhoe5d852 allfive native+actualCLI recoveredanswers originalindependentenginechecked/2202guards0;outputaccessor ONLY3substitutions. Failedrho01638d96 counter-boundary/timestampdiagnostic intact. [pcc:unverified]

V2 native02a5a4a6 and native03a59e6a:oneunfiltered comprehensive test0/zeroignoredfiltered/all2203guards0;32source8oddx4Sylow/all224Cpointclasses/both2compositions/nonzeroexactell2773073/16splitcomparisons eachcanonical+actuallegacyP0[1,74,153]/100P0additionpairs/12branches4infinities224lineoffsets. Actualnonzerolegacyorigin/subtractgeometric only;fivepublicpoint half-inverses+affine3differencecancellations. Multiplicity3 at[1,1,52] changesnormifomitted;first[1,0,0]null retained. Native03addsfinitezero minusbeta/alpha/fourK3gauges/foreignP0tags. Wholefirst7closedcaptures+7indices genuinelypublished637e1a/20436e via43436165702/job131921734179:11S3objects/3smallGitindices,all2283historicalFFguards0/exact13paths/bot e63 parent38. Rootcurrentguard03 was released then V2test03changed;futureFF MUSTfreeze newversion ratherthan reuse stale2283map. Native03 largewholecapture remains scratchct58-v2-native-03;fullsourcebeforemap+logs/currentJSON committed,nextdatahandoff handleswholearchive. [pcc:unverified]

Prime-field elliptic shortcut:three exactinteger Lean declarations PASSbothoriginal4.35/4.34.1 gates3/0trusted;d8f845/180a3c/7c5dfe exactlocalbindings pass,unsigned. m195..253 cannot divide11092292;actual elliptic/Hasse/inclusion/isogeny-count bridges are standardwritten,notformalobjects. PositiveJac(F223)descent preserved. InitialPCCPATHnotcovered953579 saved;samefirstclaim laterpasses. Two24filewholecaptures30544/30564bytes3809b4/f5d8b9;oneinspected37976-bytePDFpagee1c4bb. Combined17partiallocalbindings,not fullformalgeometry. [pcc:unverified]

New independent V2/rho/primefield driver and separateworkflow implemented under0cb563:468portable inputs347producer+121consumer,17orderedpairs15positive0/0+2intentional2/0;all7V2+5rhoJSON/actualrho5CLI+2controls/bothoriginal3gates/3exactbindings. Wholeprevious7jobworkflow,currentP1workflow/P1reference02/native/verifiers unchanged. Need published-source four actualadmissioncontrols and2100s cleanfull/newownCI;no resultyet. [pcc:unverified]

## Next steps
Normalpublish thissourcecheckpoint on readyPR1523 under1521;refresh PR3877/queue3904. Materialize cleanphysicalGit siblings exactnewHEAD/producer3d fromci_v2/reference01,include manifestitself;fouradmissioncontrols2/nooutput/allrestore,thenfull17phase originalscript under2100s/freshoutsidecache. Capture allsources/guards/wholeCIAPI+logs/all7+5native records/3canonicalverdicts. Whileisolatedfull runs, implement completed-descent derivative ONLYAFTERprotocol74e00a actualnormalpublication;oneunfilteredfivepairedtargettest/original6retrycap/900s2GiB/reusedcachelabel/wholefailures. ContinueactualrootfixtureCIhydration inspection asindependentread-onlyavenue;do notrerun unchanged6330suite orblockedAWS403 path.

## Runs in flight
NONE native. P1full02/rho02/V2native03/primeLean01+02+bindings terminal0. NewV2ownCI/full notyetlaunched. Scratchct58-public-full01/02,rho-unit-cli01/02,v2-native01/02/03,public-ci01 andprime-field-lean01/02 containoriginalcaptures;allcompiler caches areoutside raw. Rootlocal+remote e63db78c6a96b3c0caf63e4eaf00544c03255434;actualpublication637e1a collector uncommittedneedsnormalmetadata checkpoint. Consumerbase68d sourcecheckpointnowbeingcommitted. Next globalroutine17:45UTC unlessconcretepublication/CI signal.

## Stop and success conditions
Continue throughnextunblockedtask. No measuredcomputationaladvantage/admittedperformance experiment exists. OriginalS3checkpoint/livebudget/capacity gate remainsblocked;rootglobalnotgreenmissingauthentic2293097-bytefixture/add561;main3877conflict/frozenledger/signing/reviews unresolved. Parentnorm/full/own7CI/raw settled;doNOTrepoll/redispatcholdscience. Vault8edec422 locked/no key/unlock/read/write;KB/ecdbtools unavailable/prioractual127/sourcefallbacknoabsenceinference. No subagents/force/rebase/rechain/lineagechoice/mergegatebypass. Science Rust/Lean only;Pythoncustody/orchestration/rendering. Preserveallfailed/null evidence andcurrentstate before interruption.
'''
(r/'.resume/RESUME.md').write_text(current)
with(s/'CHECKPOINT.md').open('a')as f:f.write('\n## '+now+' — actual V2, independent P1 and next protocol\n\n'+current.split('## State\n',1)[1])
with(r/'docs/session-logs/2026-11-13.md').open('a')as f:f.write('\n## '+now+' — actual V2 and completed-descent prospective checkpoint (Codex)\n\n'+current.split('## State\n',1)[1])
(s/'STATUS-01.md').write_text('''# Current public-target / actual V2 status — 2026-11-13

All observations unsigned;full formalgeometry andcostadvantage remain open.

| Requirement | Evidence | Next obligation |
| --- | --- | --- |
| P1 public IC | e08eac/9e522f;independentfull67baa2;ownCIa5a143 exact68d | preserve original algorithm and all failed attempts |
| Recovered public rho answers | e5d852 allfive native/actualCLI;output-only3changes/2202guards0 | new ownV2/rhoCI |
| Actual q223 maps/model/origin/P0 | a5a4a6/a59e6a;32source224Cclass/both2compositions;actualnonzerolegacyorigin | independent cleanfull/ownCI on published V2 source |
| Conditional formal statements | existing14 plus3integer exactlocalbindings/0trusted | actualdivisor/Picard/Hasse/solverobjects notformalized |
| Fixedprimefield elliptic shortcut | d8f845/180a3c/7c5dfe;written countcontradiction/e1c4bb report | preserve exactscope;positiveJacdescent retained |
| Raw evidence |637e1a/20436e sevenwholecaptures+sevenindices,11S3/3smallGit | native03/newCI futurewholehandoff |
| Completed-transfer descent | activeprospective protocol74e00a | normalpublication BEFOREimplementation,thenallfivepairedtargetsmoke |
| Computational advantage | unestablished | originalS3checkpoint/livebudget/strongestrefs/completecostadmission |

See CHECKPOINT.md forcommands/sourceIDs/failures;V2_MAPS_01.md forwrittenmath andremainingformalbridges. [pcc:unverified]
''')
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','.github/workflows/chained-transfer-reference.yml','.github/workflows/chained-transfer-public-target.yml','.github/workflows/pcc-gate.yml','experiments/chained-transfer-reference',str((s/'native').relative_to(r)),str((s/'reference-02.sha256').relative_to(r))],cwd=r)
run('parent437',['sha256sum','--check','experiments/chained-transfer-reference/g3-norm-reference-01.sha256'])
run('P1-reference434',['sha256sum','--check',str((s/'reference-02.sha256').relative_to(r))])
run('new-reference468',['sha256sum','--check',str((s/'ci_v2/reference-01.sha256').relative_to(r))])
run('shell',['bash','-n',str(s/'ci_v2/check.sh')])
run('python-syntax',['python3','-m','py_compile',str(s/'ci_v2/replay_io.py'),str(s/'ci_v2/freeze_reference.py')])
run('actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-completed-v2.yml'])
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base])
md=[p.decode() for p in paths()if p.endswith(b'.md')]
allprose=run('all-new-prose',['python3','tools/pcc/pcc.py','lint-prose',*md],1).decode()
historical=str((s/'COMPLETED_DESCENT_PROTOCOL_01.md').relative_to(r))
findings=[x for x in allprose.splitlines() if ': line ' in x]
assert len(findings)==2 and all(x.startswith(historical+': line ')for x in findings)
run('active-new-prose',['python3','tools/pcc/pcc.py','lint-prose',*[p for p in md if p!=historical]])
run('whitespace',['git','diff','--check','--',*scope])
run('wiring',['python3','tools/artifacts/wire_workflows.py','--check'])
run('benchrec',['python3','tools/benchrec.py','gate'])
def stage():
    ps=paths();f=Path('/workspace/scratch/ct58-V2-source.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0')
    subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True)
    subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
    selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
    for p in ps:
        if p.startswith(b'pcc/claims/'):
            for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
                if proof.get('kind')=='attestation':
                    x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
                    assert x['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode==0,x['path']
    return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(d/'custody.json').write_text(json.dumps(dict(base=base,old_native_verifiers_trust_whole7_and_currentP1workflow_reference434_unchanged=True,new_manifest=468,all_source_checks=0,originalledger_activeprose_whitespace_wiring_benchrec_actionlint_artifact=0,historical_protocol01_prose='actual1/twofrozenfindings retained;active02/othernewprose0;notblanketallprose0', prior_governance01='workingwhitespace2 onlymutableproblemindexnewEOFblankline;originaloutputretained,unfrozenindexfixed;no scientificsourcechanged', prior_governance02='cachedwhitespace2 only newadapter/normEOFblanklines;frozenformatcorrection/sourceoriginals preserved;Rusttokens identical' ,all_new_subject_hashes_and_Git_staging=True,actualraw='637e1a/20436e/11largeobjects genuinelypublished;3smallindicesGit',results='67baa2/a5a143/e5d852/a5a4a6/a59e6a/3exactintegerbindings;unsignedpartialformal',reports='0085e7two55543pages/e1c4bbone37976page allinspected',next_candidate='74e00a prospective02/no completed-descent code before actualnormalpublication',new_full_and_CI='pending exactpublishedsource',costadvantage='not established'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','ActualV2 sourcecheckpoint governance own68d:originalparent437/P1434/new468hashes0;originalledger/activeprose/whitespace/wiring/benchrec/actionlint/artifact0/allnewsubjecthashstaging. Wholeold7/currentP1workflow/native/verifier/trust/reference434 unchanged. Historicalfrozencompletedprotocol01 actualprose1/twofindings retained;active02/allothernewprose0,notblanketallprose0. Full67baa2/ownCIa5a143/rhoe5d852/V2a5a4a6-a59e6a/3integer exactbindings partialunsigned;11largewholedataobjects637e1a20436e genuinelypublished/3smallindicesGit. Inspectedreports0085e7/e1c4bb. Prospective74e00a mustnormalpublish BEFOREcandidatecode;newV2ownCI/full pending;no costadvantage/fullformalgeometry claim.']
for p in sorted(d.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True)
subprocess.run(['git','commit','--quiet','-m','research: validate actual q223 Jacobian bridges and prime-field elliptic obstruction'],cwd=r,check=True)
print(claim,subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
