"""Source/evidence governance; native arithmetic and original verifiers unchanged."""
from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,hashlib,shutil,lzma
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-reference';base='c3b8d74cb356be7a1a10ae8778831f1661d506cc'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
status='''# Current canonical norm checkpoint — native, CLI and partial formal component

Protocolac58df/sourcec3b8d74c was ACTUALLYpublished beforecode/readyPR1521 under1520,424a30. New Rustg3-norm-checker uses original field/poly/elliptic/Picard engines;no original arithmetic source edit. Unit01c19a2e/fullunit02 75275f FOURpass/ZEROfailedignoredfiltered/all359guards unchanged. Independently counted C(q,q²,q³) triples(6,26,192),(8,50,380),(12,122,1308),RR+Newton/BFS orders148,356,1324. ALLsource/Jac both2compositions,all740/2492/14564 generatingedges/odd37,89,331scalars/recovery pass. Normkernel2 each;nonreduced/exceptional/explicitfourinfinities+fouru0branches percase/actualwrongplaneorigin/offcurve/tripleroot controls pass. [pcc:unverified]

CLIaf3d78/wholef459a6:THREErequests/nineclasses,TWELVEactualexit2processcontrols/372guards0/overwritebytesunchanged. Formalscopec88b36:13 SAMEdeclarations pass both ORIGINALproducer4.35 andconsumer4.34.1 gates0trusted;ALL13exact originalconsumerPCCbindings localpass. Writtenfbfa81 derivation/proofmap retains allactualgeometrybridges;formalizationpartial. Generalchart independence written;nativealternatecontrols8typicalclasses perfield,notexhaustivepairs. Native report16c9f6 THREEfinal48,914-bytePDFpages ALLvisuallyinspected,editablefigures/recordeddata/fullmodeltags. [pcc:unverified]

Everyfailedstatic/Lean/compatibility attempt preservedwhole with frozen4710c0/2b2a5e/e14270 corrections. ALLSIXnativearchives ACTUALLYpublished48e581 atcanonicalroot5c527/directparent5fff:43398333803/job131794658518 SIXremote replays beforeexact8pathbot. Genuinemanifestprojection7cd6ea toEXACTconsumerpaths preservesphysicalwholebytes;no newPCCarchive hydration/verifier change. ProducerownCI27e47f andprior4+8+5publications complete. FirstFFstaleoldworkflowguard failure andfrozen8b570c/current2175FFguard correction retained upstream;old2132source hashes+WHOLEold6prefix retained. [pcc:unverified]

Integration planb4cd92:pinproducer3d49af7f3d0a28e76b79e4825c9d2324e85853d2,physicalCargo siblings/cleanprotectedinputs/freshoutsideoutput+cache/437portablehashes. Originalproducer20pairs plus23outerpairs:producer,new4tests/9CLIclasses/two13declarationgates/13exactbindings. Wholeold20,796-byteSIXjobprefix unchanged;distinctSEVENTHjob appended. Metadataactionlint/bashsyntax/437hashes pass. Sourcecommit/publication,admissioncontrols andfull2100s cleanreplay/ownexacthead7CI remainNEXT,notaccepted yet. [pcc:unverified]

ROOTglobal NOTgreen:twooriginaltimeouts/missingcanonicalecbenchfixture2364e3;originalAWSCLI installedbutpull2 unablecredentials/anonymousread1 HeadObject403/add561. No fabricatedfixture/sourcepricing/testedit. Mainconflict/frozenledger/signing/reviews remain;routineglobalnext09:44UTC. OlderC0/T20full147b9f/ALL6CIf507c9/ALL4raw andolderroot/consumerCIs settled;do notrepoll. KB127/sourcefallback/vault8edec422locked/no subagents/no paidbenchmarkadmission. No measuredcomputationaladvantage. Continue nextunblockedresearch afterfullreplay.
'''
(s/'G3_NORM_CHECKPOINT.md').write_text(status)
(r/'.resume/RESUME.md').write_text(status+'\n---\n\n'+(r/'.resume/RESUME.md').read_text())
with (r/'docs/session-logs/2026-11-13.md').open('a') as f:f.write(f'''\n## {datetime.now(timezone.utc).isoformat()} — complete local canonical norm component checkpoint (Codex)

### What was done (commands, files, features)
- Unit02 75275f/whole0e2cd4 FOURpass/full148,356,1324source+Jac/both2compositions/437newportableintegrationinputs planned;native359guards0. CLIaf3d78/372guards0/nineclasses12processcontrols. Writtenfbfa81/13exactbindings/twooriginal13declarationgates0trusted,c88b36. Native16c9f6 THREE48,914-bytePDFpages ALLinspected/editable. ActualSIXrawpublication48e581/genuinemanifests7cd6ea;failedstatic/Lean/compatibility preserved. WholeoldSIXjobprefix unchanged,seventhjob+thinoriginalengine replay. [pcc:unverified]

### Decisions made (and why)
- Commit/publish scientific component before cleanindependent replay/ownCI;do not infer completeintegration from unitpass. Protectexact437inputhashes/producer3d/physicalsiblings/freshcache. Generaladmissiblechart invariance written;nativealternate8perfieldscope explicit. No sourceengine/verifier/trust edits orbenchmark claim.

### Open threads (unfinished, pick up next time)
- Sourcepublication/readyPR1521refresh,fouradmissioncontrols/cleanfull2100s/ownSEVENjobCI;then destinationICpipeline and admittedchargedcomparisons. Rootmissingfixture andmainledger/signing/conflict/review gates separate.

### Errors (what went wrong, how it was handled)
- API-name static01,proofbodyLean01,oldauditorcompatibilityLean02 preserved withfrozenbeforeedit corrections;no criteriaweakened. Rootauthenticfixturepull2/no credentials andanonymous403 remainactualaccessgap,notmathematicalobstruction. OldstaleFFguard bookkeeping failure8b570c retained upstream;actual6publication nowcomplete.
''')
d=s/'evidence/g3-norm-source-governance-01';d.mkdir();shutil.copyfile(__file__,d/'original-command.py')
scope=[str(s.relative_to(r)),'.github/workflows/chained-transfer-reference.yml','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,cmd,allowed=(0,)):
 p=subprocess.run(cmd,cwd=r,capture_output=True);v=p.stdout+p.stderr
 if len(v)>60000:z=lzma.compress(v,format=lzma.FORMAT_XZ);assert lzma.decompress(z)==v;(d/(name+'.txt.xz')).write_bytes(z)
 else:(d/(name+'.txt')).write_bytes(v)
 (d/(name+'.exit')).write_text(str(p.returncode)+'\n');print(name,p.returncode,flush=True);assert p.returncode in allowed,v.decode(errors='replace')[:1600];return p
refs=json.loads((s/'evidence/g3-norm-primary-01/upstream-current-inputs.json').read_text());assert len(refs)==343 and all(hashlib.sha256((Path('/workspace/crypto')/p).read_bytes()).hexdigest()==h for p,h in refs.items())
old=(s/'evidence/g3-norm-primary-01/six-original-jobs.yml').read_bytes();assert len(old)==20796 and (r/'.github/workflows/chained-transfer-reference.yml').read_bytes().startswith(old)
native=json.loads(Path('/workspace/scratch/ct56-g3-norm-unit-02/before.json').read_text());changed=[p for p,h in native.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h];assert changed==[str(r/'.github/workflows/chained-transfer-reference.yml')],changed
subjects=[]
for p in paths():
 if p.startswith(b'pcc/claims/'):
  for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
   if proof.get('kind')=='attestation':
    x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path'];subjects.append(x['path'])
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode() for p in paths() if p.endswith(b'.md')]])
run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-reference.yml']);run('driver-syntax',['bash','-n',str((s/'check-g3-norm.sh').relative_to(r))]);run('portablehashes',['sha256sum','--check',str((s/'g3-norm-reference-01.sha256').relative_to(r))]);run('benchrec',['python3','tools/benchrec.py','gate'],(0,1))
subprocess.run(['git','add','--sparse','-f','--',str((s/'g3-norm-checker/Cargo.lock').relative_to(r))],cwd=r,check=True)
def stage():
 ps=paths();f=Path('/workspace/scratch/ct56-norm-source.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True);selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
 for p in subjects:assert subprocess.run(['git','cat-file','-e',base+':'+p],cwd=r,capture_output=True).returncode==0 or p.encode() in selected,p
 for line in (s/'g3-norm-reference-01.sha256').read_text().splitlines():
  p=line.split('  ',1)[1]
  if not p.startswith('../crypto/'):assert subprocess.run(['git','cat-file','-e',base+':'+p],cwd=r,capture_output=True).returncode==0 or p.encode() in selected,p
 return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(d/'custody.json').write_text(json.dumps(dict(base=base,scopedledger_prose_whitespace_wiring_actionlint_syntax_hashes_artifact=0,producer343_unchanged=True,unit02_Rust_inputs_unchanged=True,only_changed_unit_guard='authorizedold6workflow→7append;whole20796prefixbyteexact',portable_inputs=437,whole6raw_actualpublication='48e581/7cd6ea',all_new_subject_hashes_and_input_staging=True,own_lock_forcestaged=True,source='native+CLI+partialformal report component;fullindependent/ownCI pending',no_verifier_trust_originalengine_or_benchmark_change=True),indent=2)+'\n')
c=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','G3norm sourcegovernance:ownc3bledger/prose/workingcachedwhitespace/wiring/actionlint/bash/437portablehashes/artifact0,all343producerhashes/newsubjects/inputstaging/ownCargo.lock covered. Unit02Rustinputs unchanged;ONLYselectedworkflowguardchangesbyauthorized7thappend,wholeold20796SIXprefix byteexact. Actualnative75275f/CLIaf3d78/partialformal13+13bindings/THREE48,914-byteinspectedPDFpages/ALL6raw48e581+genuine7cd6ea. No originalengine/verifier/trust/benchmarkedit;globalroot remainsmissingfixture. Fullcleanreplay/own7CI pending sourcepublication,not inferredfromlocalpass.']
for p in sorted(d.iterdir()):c+=['--proof','attestation:'+str(p.relative_to(r))]
cl=subprocess.check_output(c,cwd=r,text=True).strip();Path('/workspace/scratch/ct56-norm-source-governance.claim').write_text(cl+'\n')
selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: implement independent canonical-class genus-three norm'],cwd=r,check=True)
print(cl,subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
