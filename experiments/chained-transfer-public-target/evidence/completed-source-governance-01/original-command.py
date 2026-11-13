"""Continuous owned source/evidence checkpoint via original repository gates."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='093134ba9fbdaa4fdb50fe4bc53cd29d809500d0'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
d=s/'evidence/completed-source-governance-01';d.mkdir();shutil.copyfile(__file__,d/'original-command.py')
scope=[str(s.relative_to(r)),'pcc/claims','pcc/ledger.jsonl','problems/chained-transfer-public-target-destination-bridge.md','problems/README.md','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
subprocess.run(['git','add','--sparse','-f','--',str((s/'completed-descent/Cargo.lock').relative_to(r))],cwd=r,check=True)
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,cmd):
    p=subprocess.run(cmd,cwd=r,capture_output=True);raw=p.stdout+p.stderr
    if len(raw)>60000:z=lzma.compress(raw);assert lzma.decompress(z)==raw;(d/(name+'.txt.xz')).write_bytes(z)
    else:(d/(name+'.txt')).write_bytes(raw)
    (d/(name+'.exit')).write_text(str(p.returncode)+'\n');print(name,p.returncode,flush=True);assert p.returncode==0,raw.decode()[:1600]
guards=json.loads(Path('/workspace/scratch/ct58-completed-descent-unit-01/before.json').read_text());assert len(guards)==2307 and all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in guards.items())
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','.github/workflows',str((s/'native').relative_to(r)),str((s/'v2').relative_to(r)),str((s/'rho-accessor').relative_to(r)),str((s/'prime-field').relative_to(r)),str((s/'ci_v2').relative_to(r)),'experiments/chained-transfer-reference',str((s/'COMPLETED_DESCENT_PROTOCOL_02.md').relative_to(r)),str((s/'V2_MAPS_01.md').relative_to(r))],cwd=r)
now=datetime.now(timezone.utc).isoformat();entry=f'''\n## {now} — completed-descent candidate locally checked, source checkpoint\n\nActual prospective74e00a published093 BEFOREcode/7823d2. Candidate5ff070 originalcompile/native0/oneunfilteredpass0failignoredfiltered/all2307guards0. AllFIVEcandidate andbaseline publictargetanswers ORIGINALindependentenginechecked;TENpairedattempts retainfivefirst26row30columnfailures EACHthenfiveFB36successes EACH. WholederivativeONLY6literal argument/map substitutions;originalrelationLA/descentwalk/recovery/rhobytes unchanged/no genericDLPfallback. ActualP0/nonzeroorigin/32complete16split/fivepointinverse+affinecontrols pass. Reusedoutsidecache;originalcounters omit separatecompletedenginearith/noS/ratio/advantage. TWO52101bytePDFpages ALLinspected. [pcc:unverified]\n\nParentV2 full0815f7 exact093/469guards/all17pairs0orintentional2 andBOTHscientificCIb6c1db run43440225770/job131935606787 +43440225517/job131935606265 SUCCESS. All25nativeJSON match originals (P1ONLYrecordedwall/walltotalexcluded),all17canonicalPCCdigests match. Partialcollector01 digit2regexfault preserved7176d7,complete02 rawat /workspace/scratch/ct58-V2-own-CI-raw-02;no native/verifier change. CIstandaloneexitfiles/ZIPnotdownloaded,originalmarkers+successfulstepscopeexplicit. [pcc:unverified]\n\nNEXT normalpublishthiscandidate source,thenfreezeimplementowncandidateCI/independentdriver/freshphysicalfull/fouradmissioncontrols. Whole Native03,V2full,partial+completeCI andcandidate01 captures neednextgenuine datahandoff. No nativeprocess in flight;allterminalguards0. SourceparentCI468/nativecore/old7/currenttwo workflows/verifiers immutable. Root237230b3 normalpublish0/eeb056;stale2283historicalguard MUSTNOTbeusedforfutureFF;currentcandidate2307beforemap canseednewguard afteranynewintegration additions. [pcc:unverified]\n\nAftercandidateindependentreplay,inspect actualJacobian2-primarystructure/availablegenus3isogenymachinery before proposingnondualchain;avoidreportingnormPhi2backtrackingasnewadvantage. Rootauthenticfixture/nativeglobalnotgreen;read-onlycompile/tool-policyCIinspection foundnohydrationforthatfixture. S3checkpoint/livebudget/strongestrefs/completecostadmission/mainfrozenledger/signing/reviews/vault8edec422/KBtoolabsenceremain. Nextglobalroutine17:45UTCunlessconcretesignal. Continueaftereachrung. [pcc:unverified]\n'''
for p in [s/'CHECKPOINT.md',r/'.resume/RESUME.md',r/'docs/session-logs/2026-11-13.md',r/'problems/chained-transfer-public-target-destination-bridge.md']:
    with p.open('a')as f:f.write(entry)
run('parent437',['sha256sum','--check','experiments/chained-transfer-reference/g3-norm-reference-01.sha256'])
run('P1-reference434',['sha256sum','--check',str((s/'reference-02.sha256').relative_to(r))])
run('V2-reference468',['sha256sum','--check',str((s/'ci_v2/reference-01.sha256').relative_to(r))])
run('own-format',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',str(s/'completed-descent/src/lib.rs'),str(s/'completed-descent/src/tests.rs')])
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base])
run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]])
run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate'])
def stage():
    ps=paths();f=Path('/workspace/scratch/ct58-completed-source.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0')
    subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
    selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
    for p in ps:
        if p.startswith(b'pcc/claims/'):
            for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
                if proof.get('kind')=='attestation':
                    x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256']
                    assert x['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode==0,x['path']
    return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(d/'custody.json').write_text(json.dumps(dict(base=base,all2307_actual_native_inputs_unchanged=True,parent437_P1434_V2468_unchanged=True,all_original_engines_verifiers_workflows_protocols_unchanged=True,original_ledger_prose_whitespace_wiring_benchrec_artifact_format=0,all_subject_hashes_and_staging=True,candidate='5ff070 all5/TENpairs/6literals/noadvantage',parent_full_CI='0815f7/b6c1db/25native17digests',report='two52101pages allinspected',candidate_full_CI_and_new_whole_data_publication='next,not acceptedyet'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Completed-descent sourcecheckpoint governanceown093:all2307nativehashes/parent437/P1434/V2468unchanged;alloriginalengines/verifiers/workflows/protocols unchanged. Originalledger/prose/workingcachedwhitespace/wiring/benchrec/artifact/ownformat0/allnewsubjecthashstaging. Candidate5ff070 allfivepairedanswers/TENretries/6literalmap changes atactualP0,independentparentfull0815f7/CIb6c1db25native17canonicaldigests;inspectedtwo52101PDFpages. CandidateownfullCI andnewwholedata publication next;no cost/S/ratio/advantage orfullformalgeometry.']
for p in sorted(d.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: replace N4 split-transfer admission with completed divisor spaces'],cwd=r,check=True)
print(claim,subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
