"""Physical Git source/fixture custody and literal source edits only."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
BASE='5ac59843a0cc6546b0f007c0bd2f79212d169c43'
PRODUCER='3d49af7f3d0a28e76b79e4825c9d2324e85853d2'
STUDY='experiments/chained-transfer-public-target'
audit=Path(__file__).resolve().parent
consumer,producer,out=map(lambda x:Path(x).resolve(),sys.argv[1:])
assert not out.exists()and not out.is_relative_to(consumer)and not out.is_relative_to(producer)
out.mkdir();original=out/'original-layout';original.mkdir()
def run(label,args,cwd=None,input=None):
 q=subprocess.run(args,cwd=cwd,input=input,capture_output=True);(out/(label+'.txt')).write_bytes(q.stdout+q.stderr);(out/(label+'.exit')).write_text(str(q.returncode)+'\n');assert q.returncode==0,(label,q.stdout[:800],q.stderr[:800]);return q.stdout
refpath=STUDY+'/ci_norm_halving/reference-01.sha256';reference=subprocess.check_output(['git','show',BASE+':'+refpath],cwd=consumer);rows=[x.split('  ',1)for x in reference.decode().splitlines()];assert len(rows)==929
files={'cryptanalysis':{refpath},'crypto':set()}
for digest,path in rows:
 assert len(digest)==64 and not path.startswith('/')
 if path.startswith('../crypto/'):files['crypto'].add(path.removeprefix('../crypto/'))
 else:assert '..'not in Path(path).parts;files['cryptanalysis'].add(path)
support=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--',STUDY+'/arithmetic-audit'],cwd=consumer,text=True).splitlines();files['cryptanalysis'].update(support)
for name,repo,pin in [('cryptanalysis',consumer,BASE),('crypto',producer,PRODUCER)]:
 dest=original/name;run(name+'-worktree',['git','worktree','add','--detach','--no-checkout',str(dest),pin],repo);run(name+'-sparse-init',['git','sparse-checkout','init','--no-cone'],dest);patterns=('\n'.join('/'+p for p in sorted(files[name]))+'\n').encode();run(name+'-sparse',['git','sparse-checkout','set','--no-cone','--stdin'],dest,patterns);run(name+'-checkout',['git','read-tree','-mu','HEAD'],dest)
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=dest,text=True).strip()==pin
c=original/'cryptanalysis';p=original/'crypto'
managed=[STUDY+'/evidence/odd-product-maps-acceptance-02/all-native-records.json.xz',*[f'docs/research-artifacts/chained-transfer/norm-halving-01/{n}'for n in ['expected-native-05.json.xz','report.pdf','selected-calls.png']]]
for i,path in enumerate(managed):
 src=consumer/path;manifest=json.loads((src.parent/'.artifacts.json').read_text())['files'][src.name];assert src.stat().st_size==manifest['bytes']and hashlib.sha256(src.read_bytes()).hexdigest()==manifest['sha256'];run('fixture-verify-'+str(i),['python3','tools/artifacts/artifacts.py','verify',path],consumer);dest=c/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);dest.chmod(0o444)
assert(c/refpath).read_bytes()==reference
for digest,path in rows:assert hashlib.sha256((c/path).read_bytes()).hexdigest()==digest,path
run('base929',['sha256sum','--check',refpath],c)
oldnorm=c/STUDY/'ci_norm_sampling/reference-01.sha256';oldrows=[line.split('  ',1)for line in oldnorm.read_text().splitlines()];assert len(oldrows)==784
old785=[]
for digest,path in oldrows:
 target=c/path;assert hashlib.sha256(target.read_bytes()).hexdigest()==digest
 rel=('crypto/'+path.removeprefix('../crypto/'))if path.startswith('../crypto/')else('cryptanalysis/'+path)
 old785.append(digest+'  ./'+rel+'\n')
old785.append(hashlib.sha256(oldnorm.read_bytes()).hexdigest()+'  ./cryptanalysis/'+str(oldnorm.relative_to(c))+'\n');assert len(old785)==785
(out/'original-785.sha256').write_text(''.join(sorted(old785)))
oldref=c/STUDY/'arithmetic-audit/reference-03.sha256';run('old-arithmetic22',['sha256sum','--check',str(oldref.relative_to(c))],c)
shutil.copytree(audit/'fixture',original/'norm-fixture')
original_inventory={str(q.relative_to(original)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'link':os.readlink(q)if q.is_symlink()else None}for q in sorted(original.rglob('*'))if(q.is_file()or q.is_symlink())and q.name!='.git'}
(out/'original-inventory.json').write_text(json.dumps(original_inventory,indent=2)+'\n')
derived=out/'derived-layout';shutil.copytree(original,derived,symlinks=True)
for name in ['cryptanalysis','crypto']:(derived/name/'.git').unlink()
old=c/STUDY/'arithmetic-audit'
shutil.copytree(audit/'taps',derived/'n4-arithmetic-taps');shutil.copyfile(old/'controls.rs',derived/'arithmetic-controls.rs');shutil.copyfile(old/'scalar-insertions.json',derived/'scalar-insertions.json')
with(old/'literal-hooks.patch').open('rb')as f:run('old-literal-patch',['patch','-p1','--batch','--fuzz=0'],derived,f.read())
pre={str(q.relative_to(derived)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()}for q in sorted(derived.rglob('*'))if q.is_file()};(out/'old-derived-inventory.json').write_text(json.dumps(pre,indent=2)+'\n')
# The new module only inserts literal observer strings and support declarations.
run('new-quadratic-hooks',['python3',str(audit/'patch_quadratic.py'),str(derived),str(out)])
shutil.copytree(audit/'frontend',derived/'norm-census')
post={str(q.relative_to(derived)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'link':os.readlink(q)if q.is_symlink()else None}for q in sorted(derived.rglob('*'))if q.is_file()};(out/'derived-materialized-inventory.json').write_text(json.dumps(post,indent=2)+'\n')
for name,row in original_inventory.items():assert hashlib.sha256((original/name).read_bytes()).hexdigest()==row['sha256']
(out/'custody.json').write_text(json.dumps({'consumer':BASE,'producer':PRODUCER,'base_logical_inputs':930,'old_arithmetic_support_files':support,'managed_objects':managed,'managed_method':'verified read-only local copies of original genuine objects; no new remote read','original_links_preserved':True,'old_patch_fuzz':0,'original_bytes_unchanged':True,'derivative_git_admin_files_removed':True,'scope':'isolated source I/O, no census result'},indent=2)+'\n')
print(json.dumps({'layout':str(out),'base_logical_inputs':930,'original_files':len(original_inventory),'derived_files':len(post),'original_unchanged':True}))
