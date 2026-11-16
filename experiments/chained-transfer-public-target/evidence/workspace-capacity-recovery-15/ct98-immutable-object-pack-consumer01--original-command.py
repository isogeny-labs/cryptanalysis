"""Losslessly pack a bounded batch of existing immutable Git objects; preserve every ref and byte."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,os,shutil,stat,subprocess,sys,zlib
repo=Path(sys.argv[1]);label=sys.argv[2];assert repo in [Path('/workspace/crypto'),Path('/workspace/cryptanalysis')]
raw=Path('/workspace/scratch')/('ct98-immutable-object-pack-'+label);raw.mkdir();shutil.copyfile(__file__,raw/'original-command.py')
common=Path(subprocess.check_output(['git','rev-parse','--git-common-dir'],cwd=repo,text=True).strip())
if not common.is_absolute():common=repo/common
objects=common/'objects'
def git(*args,**kw):return subprocess.check_output(['git',*args],cwd=repo,**kw)
before_refs=git('show-ref');before_head=git('rev-parse','HEAD');before_status=git('status','--porcelain');assert not before_status
(raw/'all-before-refs.txt').write_bytes(before_refs);(raw/'before-HEAD.txt').write_bytes(before_head);(raw/'before-Git-status.txt').write_bytes(before_status)
processes=subprocess.check_output(['ps','-eo','pid,ppid,stat,comm'],text=True)
assert not[line for line in processes.splitlines()if len(a:=line.split())==4 and a[3]in ['git','cargo','rustc']and not a[2].startswith('Z')]
names={}
for line in git('rev-list','--objects','--all').decode().splitlines():
 fields=line.split(' ',1)
 if len(fields)==2:names[fields[0]]=fields[1]
rows=[]
for directory in objects.iterdir():
 if len(directory.name)!=2 or not directory.is_dir():continue
 for p in directory.iterdir():
  if not p.is_file()or p.is_symlink()or len(p.name)!=38:continue
  oid=directory.name+p.name
  if any(c not in'0123456789abcdef'for c in oid):continue
  st=p.stat()
  if st.st_nlink!=1 or st.st_size>1024*1024:continue
  with p.open('rb')as f:prefix=zlib.decompressobj().decompress(f.read(4096),256)
  header=prefix.split(b'\0',1)[0];kind,size=header.split(b' ',1);size=int(size)
  if size>8*1024*1024:continue
  name=names.get(oid,'unreferenced-retained')
  if name.endswith(('RESUME.md','CHECKPOINT.md','RESEARCH_QUEUE.md','QUEUE.md','PUBLIC_TARGET_CHECKPOINT.md')):group='00-session-state'
  elif name.endswith('ledger.jsonl'):group='01-complete-ledgers'
  elif '/session-logs/'in name:group='02-session-logs'
  elif '/pcc/claims/'in'/'+name:group='03-claims'
  else:group='04-'+Path(name).name
  rows.append(dict(oid=oid,path=str(p),loose_bytes=st.st_size,loose_allocated=st.st_blocks*512,mode=stat.S_IMODE(st.st_mode),inode=st.st_ino,kind=kind.decode(),body_bytes=size,semantic_path=name,group=group))
rows.sort(key=lambda v:(v['group'],v['semantic_path'],v['oid']))
chosen=[];total=0
for row in rows:
 if total+row['loose_bytes']>8*1024*1024:continue
 chosen.append(row);total+=row['loose_bytes']
assert chosen
free=os.statvfs(repo);available_before=free.f_bavail*free.f_frsize;assert available_before>total+16*1024*1024
ids=''.join(row['oid']+'\n'for row in chosen).encode();(raw/'all-selected-object-ids.txt').write_bytes(ids)
cmd=['git','pack-objects','--compression=9','--window=250','--window-memory=32m','--depth=50',str(objects/'pack/pack')]
q=subprocess.run(cmd,cwd=repo,input=ids,capture_output=True);(raw/'actual-pack.stdout').write_bytes(q.stdout);(raw/'actual-pack.stderr').write_bytes(q.stderr);(raw/'actual-pack.exit').write_text(str(q.returncode)+'\n');assert q.returncode==0
pack_id=q.stdout.decode().strip();assert len(pack_id)==40
pack=objects/'pack'/('pack-'+pack_id+'.pack');index=pack.with_suffix('.idx');assert pack.is_file()and index.is_file()
q=subprocess.run(['git','verify-pack','-v',str(index)],cwd=repo,capture_output=True);(raw/'whole-verify-pack.txt.xz').write_bytes(lzma.compress(q.stdout+q.stderr));(raw/'verify-pack.exit').write_text(str(q.returncode)+'\n');assert q.returncode==0
isolated=raw/'new-pack-only-object-store';(isolated/'pack').mkdir(parents=True)
os.symlink(pack,isolated/'pack'/pack.name);os.symlink(index,isolated/'pack'/index.name)
env=dict(os.environ,GIT_OBJECT_DIRECTORY=str(isolated));env.pop('GIT_ALTERNATE_OBJECT_DIRECTORIES',None)
reader=subprocess.Popen(['git','cat-file','--batch'],cwd=repo,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
 for row in chosen:
  old=Path(row['path']);compressed=old.read_bytes();canonical=zlib.decompress(compressed);header,body=canonical.split(b'\0',1)
  assert header==row['kind'].encode()+b' '+str(row['body_bytes']).encode()
  assert hashlib.sha1(canonical).hexdigest()==row['oid']
  reader.stdin.write((row['oid']+'\n').encode());reader.stdin.flush()
  actual=reader.stdout.readline().decode().split();assert actual==[row['oid'],row['kind'],str(row['body_bytes'])]
  offset=0
  while offset<len(body):
   chunk=reader.stdout.read(min(1048576,len(body)-offset));assert chunk==body[offset:offset+len(chunk)]and chunk
   offset+=len(chunk)
  assert reader.stdout.read(1)==b'\n'
  row['loose_compressed_sha256']=hashlib.sha256(compressed).hexdigest();row['canonical_object_sha256']=hashlib.sha256(canonical).hexdigest();row['whole_original_and_isolated_pack_bytes_equal']=True
 reader.stdin.close();code=reader.wait(timeout=30);err=reader.stderr.read();(raw/'isolated-pack-reader.stderr').write_bytes(err);(raw/'isolated-pack-reader.exit').write_text(str(code)+'\n');assert code==0
except BaseException:
 reader.kill();reader.wait();raise
# No original is removed until every selected complete object was verified in
# the isolated pack-only database. This removes redundant encodings, never data.
for row in chosen:
 p=Path(row['path']);st=p.stat();assert st.st_ino==row['inode']and stat.S_IMODE(st.st_mode)==row['mode'];assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==row['loose_compressed_sha256']
for row in chosen:Path(row['path']).unlink()
assert git('show-ref')==before_refs and git('rev-parse','HEAD')==before_head and git('status','--porcelain')==before_status
for row in chosen:
 q=git('cat-file','-t',row['oid']).decode().strip();assert q==row['kind']
after=os.statvfs(repo)
(raw/'whole-object-migration-inventory.json.xz').write_bytes(lzma.compress((json.dumps(chosen,indent=2)+'\n').encode()))
outcome=dict(at=datetime.now(timezone.utc).isoformat(),repo=str(repo),objects=len(chosen),old_loose_logical_bytes=total,old_loose_allocated_bytes=sum(row['loose_allocated']for row in chosen),new_pack=str(pack),new_pack_bytes=pack.stat().st_size,new_pack_sha256=hashlib.file_digest(pack.open('rb'),'sha256').hexdigest(),new_index_bytes=index.stat().st_size,available_before=available_before,available_after=after.f_bavail*after.f_frsize,all_complete_objects_wholebyte_compared_in_isolated_pack_only_database=True,all_original_object_IDs_and_types_still_readable=True,all_refs_HEAD_and_Git_status_unchanged=True,no_prune_of_reachable_or_unreachable_objects=True,no_checkout_cache_source_raw_executable_or_prepared_library_changed=True,scope='lossless bounded Git object encoding migration only; no history rewrite, reference movement, deleted scientific data or research/cost inference')
(raw/'outcome.json').write_text(json.dumps(outcome,indent=2)+'\n');print(json.dumps(outcome),flush=True)
