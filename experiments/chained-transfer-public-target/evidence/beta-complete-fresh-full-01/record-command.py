"""Whole-file custody and original claim creation, no research computation."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
o=Path('/workspace/scratch/ct73-complete-full-01');d=Path('/workspace/scratch/ct73-complete-driver-01')
e=s/'evidence/beta-complete-fresh-full-01';e.mkdir()
assert(o/'native.exit').read_text().strip()=='0'and(o/'guard.exit').read_text().strip()=='0'
assert json.loads((o/'guards.json').read_text())==dict(count=882,changed=[])
phases=[x.split()for x in(d/'phases.txt').read_text().splitlines()];assert len(phases)==20
negatives={'compare-negative','identity-negative','legacy-count-negative'}
for name,want,actual in phases:
 assert want==actual==('101'if name in negatives else'0')
 assert(d/(name+'.pipe-exits')).read_text()==want+' 0\n'
for name in ['original','phase-caller','final-source-guards']:assert(d/(name+'.exit')).read_text().strip()=='0'
for side in ['consumer','producer']:
 raw=(d/(side+'-proof.txt')).read_text();assert '44 thm   0 trusted'in raw and'1 thm   0 trusted'in raw
assert 'test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;'in(d/'native.txt').read_text()
assert sum(name.startswith('binding-')for name,_,_ in phases)==7
for name in ['plan.json','fixture-materialization.json','original-fixture-verify.exit','native.exit','guard.exit','guards.json','original-command.sh','binary-custody.json','start.txt','finish.txt']:shutil.copyfile(o/name,e/name)
for name in ['phases.txt','consumer-proof.txt','producer-proof.txt','compare.txt','accounting-change-audit.json','identity-negative.txt','legacy-count-negative.txt','compare-negative.txt']:shutil.copyfile(d/name,e/name)
for name in ['native.txt','before.json','after.json']:(e/(name+'.xz')).write_bytes(lzma.compress((o/name).read_bytes()))
indices=[]
for root in [o,d]:
 files=[dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in sorted(root.rglob('*'))if p.is_file()]
 indices.append(dict(root=str(root),members=files,all_files_no_filter=True))
(e/'whole-capture-index.json').write_text(json.dumps(dict(roots=indices,derived_build_cache=str(d)+'-build-cache',derived_cache_outside_both_captured_roots=True,actual_executables_copied_and_indexed=True,whole_archive_pending='NEWguard13 unchanged genuine publisher'),indent=2)+'\n')
shutil.copyfile(__file__,e/'record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Fresh physical published-b691714c complete rational beta replay: unchanged producer3d49,881selected+self882guards unchanged; outer native0/guard0; all20ordered phases17expected0 and THREEactual101 controls/alltee0; THREEunfiltered passes/allTHREEwholeJSONexact NO masks plus exact3-path accounting-only full-tree audit; originalIDC0/0/101; both originalproofgates44+1 declarations0trusted/sevenexactbindings pass/finalguards0. Fouractual admission controls exit2/nooutput/restored. Five actually executed binaries copied using matching Cargo paths; entire two outputroots indexed without pruning and derivedcache outside. Full custody pending NEWguard13. Unsigned data, no signed execution/corpus standing or performance.']
for p in sorted(e.rglob('*')):
 if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct73-complete-full-acceptance.claim').write_text(claim+'\n');print(claim)
