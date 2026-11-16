"""Closed full-run custody, exact exits, original claim creation; I/O only."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';o=Path('/workspace/scratch/ct74-norm-halving-full-02');d=Path('/workspace/scratch/ct74-norm-halving-driver-02');e=s/'evidence/norm-halving-fresh-full-02';e.mkdir()
assert(o/'native.exit').read_text()=='0\n'and(o/'guard.exit').read_text()=='0\n';assert json.loads((o/'guards.json').read_text())=={'count':930,'changed':[]}
phases=[x.split()for x in(d/'phases.txt').read_text().splitlines()];assert len(phases)==21
for name,want,actual in phases:
 assert want==actual==('101'if name in {'compare-negative','identity-negative'}else'0');assert(d/(name+'.pipe-exits')).read_text()==want+' 0\n'
for n in ['original','phase-caller','final-source-guards']:assert(d/(n+'.exit')).read_text()=='0\n'
for side in ['consumer','producer']:assert '10 thm   0 trusted'in(d/(side+'-proof.txt')).read_text()
assert 'test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;'in(d/'native.txt').read_text();assert sum(n.startswith('binding-')for n,_,_ in phases)==9
assert not(d/'omitted-record-must-not-accept.json').exists()
a=json.loads((o/'binary-custody.json').read_text());b=json.loads((d/'actual-binaries.json').read_text());assert len(a['actual_executable_paths'])==3
for row in a['actual_executable_paths']:assert hashlib.sha256(Path(row['copied']).read_bytes()).hexdigest()==row['sha256']
roots=[]
for raw,label in [(o,'outer'),(d,'driver')]:
 members=[];dest=e/label;dest.mkdir()
 for p in sorted(raw.rglob('*')):
  if p.is_file():
   rel=p.relative_to(raw);members.append({'path':rel.as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
   if p.stat().st_size<=60000 and p.suffix!='.bin':q=dest/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
   elif p.name in ['before.json','after.json']:(dest/(p.name+'.xz')).write_bytes(lzma.compress(p.read_bytes()))
 roots.append({'root':str(raw),'whole_members_no_filter':members})
(e/'whole-capture-index.json').write_text(json.dumps({'roots':roots,'actual_all_three_binaries_copied_and_indexed':True,'cache':str(d)+'-build-cache','cache_is_derived_external_to_both_captured_roots':True,'whole_publication':'pending NEWguard17; preservewholefailed01physicalpreparation aswell'},indent=2)+'\n');shutil.copyfile(__file__,e/'record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Freshphysical published5ac59843 normhalving full02: originalproducer3d49/all929selected+self930logicalguards unchanged/outer native0+guard0/all21orderedphases19zero+TWOactual101/everytee0. FOURunfiltered passes/allFOURwholeJSONexact NOmasks/originalidentity0/0/101/bothunchanged10declarationgates0trusted/NINEexactbindings/finalguards0. Fouractualadmissioncontrols reject2/nooutput/restored ddfec3; priorlayout01resolvealias1 retained6d562c. THREEactualexecutables copiedwhole withmatchingCargo compile-runtimepaths anddoublecustodydigests; wholebothoutputroots indexed/cachedoutside. Source/model/coordinate/cofactor/oldcommonadmission scopes unchanged, fullcostunpriced; wholecapture publication pendingNEWguard17. Unsignedboundeddata, no signedexecution orperformance advantage.' ]
for p in sorted(e.rglob('*')):
 if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct74-norm-halving-full-acceptance.claim').write_text(cl+'\n');print(cl)
