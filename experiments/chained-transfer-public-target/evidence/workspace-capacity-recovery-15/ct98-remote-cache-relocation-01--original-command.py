"""Relocate only newly fetched promisor cache packs to RAM, preserving all original paths and bytes."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,shutil,stat,subprocess
repo=Path('/workspace/cryptanalysis');objects=repo/'.git/objects';old_attempt=Path('/workspace/scratch/ct98-immutable-object-pack-consumer01');threshold=(old_attempt/'original-command.py').stat().st_ctime
raw=Path('/dev/shm/ct98-remote-cache-relocation-01');raw.mkdir();shutil.copyfile(__file__,raw/'original-command.py');store=raw/'whole-pack-bytes';store.mkdir()
rows=[line.split()for line in subprocess.check_output(['ps','-eo','pid,ppid,stat,comm'],text=True).splitlines()[1:]]
assert not[a for a in rows if a[3]in ['git','cargo','rustc']and not a[2].startswith('Z')]
env=dict(os.environ,GIT_NO_LAZY_FETCH='1');before_refs=subprocess.check_output(['git','show-ref'],cwd=repo,env=env);before_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,env=env);before_status=subprocess.check_output(['git','status','--porcelain'],cwd=repo,env=env);assert not before_status
(raw/'all-before-refs.txt').write_bytes(before_refs);(raw/'before-HEAD.txt').write_bytes(before_head)
candidates=[]
for p in(objects/'pack').glob('pack-*.pack'):
 if p.is_symlink()or not p.with_suffix('.promisor').is_file():continue
 st=p.stat()
 if st.st_ctime>=threshold and st.st_size>=1024*1024:candidates.append(p)
assert candidates,'no newly fetched complete promisor packs; do not touch existing data'
def digest(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def equal(a,b):
 with a.open('rb')as x,b.open('rb')as y:
  while True:
   u,v=x.read(1048576),y.read(1048576)
   if u!=v:return False
   if not u:return True
receipts=[];before=os.statvfs(repo);available_before=before.f_bavail*before.f_frsize
for original in sorted(candidates,key=lambda p:p.stat().st_size,reverse=True):
 st=original.stat();dest=store/original.name;shutil.copy2(original,dest)
 assert equal(original,dest)and stat.S_IMODE(dest.stat().st_mode)==stat.S_IMODE(st.st_mode)
 h=digest(original);assert digest(dest)==h
 row=dict(original_path=str(original),whole_RAM_cache_path=str(dest),bytes=st.st_size,old_allocated_bytes=st.st_blocks*512,mode=stat.S_IMODE(st.st_mode),sha256=h,whole_bytes_and_modes_compared_before_relocation=True,remote_promisor_marker=str(original.with_suffix('.promisor')),new_fetch_ctime=st.st_ctime,failed_inventory_start_ctime=threshold)
 receipts.append(row);(raw/'in-progress-whole-cache-manifest.json').write_text(json.dumps(receipts,indent=2)+'\n')
 # This is a duplicate encoding of a newly fetched remote cache object, not a
 # checkout/source/scientific file. Its full verified bytes already exist in RAM.
 original.unlink();os.symlink(dest,original)
 assert original.is_file()and original.is_symlink()and digest(original)==h
 f=os.statvfs(repo);free=f.f_bavail*f.f_frsize;print('whole remote pack relocated',original.name,st.st_size,'available',free,flush=True)
 if free>=256*1024*1024:break
assert subprocess.check_output(['git','show-ref'],cwd=repo,env=env)==before_refs
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,env=env)==before_head
assert subprocess.check_output(['git','status','--porcelain'],cwd=repo,env=env)==before_status
after=os.statvfs(repo)
out=dict(at=datetime.now(timezone.utc).isoformat(),repo=str(repo),whole_packs=receipts,all_original_paths_bytes_modes_preserved=True,all_refs_HEAD_status_unchanged=True,no_existing_source_or_scientific_data_changed=True,only_remote_promisor_packs_fetched_after_failed_inventory_selected=True,available_before=available_before,available_after=after.f_bavail*after.f_frsize,RAM_cache_recovery='RAM remains available for this workspace session. If the environment is replaced, these are regenerable remote promisor cache encodings: remove only the listed broken pack links and their associated idx/rev/promisor cache metadata, then let the existing partial clone refetch immutable objects. Never remove local/nonpromisor objects, refs, actual research raw or checkout files.',scope='whole-byte remote download-cache relocation only; no history rewrite, pruning, research deletion or mathematical/cost standing')
(raw/'outcome.json').write_text(json.dumps(out,indent=2)+'\n')
persist=Path('/workspace/scratch/ct98-remote-cache-relocation-01');persist.mkdir()
for f in raw.iterdir():
 if f.is_file():shutil.copyfile(f,persist/f.name)
print(json.dumps({k:v for k,v in out.items()if k!='whole_packs'}),flush=True)
