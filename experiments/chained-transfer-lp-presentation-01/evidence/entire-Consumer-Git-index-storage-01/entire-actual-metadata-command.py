from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,shutil,subprocess
r=Path('/workspace/cryptanalysis');h=Path('/dev/shm/ct344-Consumer-entire-index-preserved');h.mkdir();env=os.environ.copy();env['GIT_OPTIONAL_LOCKS']='0'
def git(*args):return subprocess.check_output(['git',*args],cwd=r,env=env)
head=git('rev-parse','HEAD').decode().strip();tree=git('rev-parse','HEAD^{tree}').decode().strip();assert head=='6ad0826722e91097cbb6feafcd99d3f625e08304' and not git('diff','--cached','--name-only')
index=r/'.git/index';assert index.is_file() and not index.is_symlink();before=index.read_bytes();(h/'entire-original-index').write_bytes(before);(h/'current-index').write_bytes(before);assert (h/'current-index').read_bytes()==before
shutil.copyfile(r/'.git/config',h/'entire-original-config-private');os.chmod(h/'entire-original-config-private',0o600)
index.unlink();index.symlink_to(h/'current-index');assert index.read_bytes()==before
env['GIT_INDEX_FILE']=str(h/'current-index')
q=subprocess.run(['git','-c','core.splitIndex=true','update-index','--split-index'],cwd=r,env=env,capture_output=True);(h/'actual-split-index.stdout').write_bytes(q.stdout);(h/'actual-split-index.stderr').write_bytes(q.stderr);(h/'actual-split-index.exit').write_text(str(q.returncode)+'\n');assert q.returncode==0
shared=[]
for f in sorted((r/'.git').glob('sharedindex.*')):
 if f.is_file() and not f.is_symlink():
  target=h/f.name;shutil.copyfile(f,target);assert target.read_bytes()==f.read_bytes();info=dict(name=f.name,bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest());f.unlink();f.symlink_to(target);shared.append(info)
assert shared
subprocess.run(['git','config','core.splitIndex','true'],cwd=r,env=env,check=True)
assert git('write-tree').decode().strip()==tree and not git('diff','--cached','--name-only') and git('rev-parse','HEAD').decode().strip()==head
assert index.is_symlink() and index.read_bytes()==(h/'current-index').read_bytes()
receipt=dict(at=datetime.now(timezone.utc).isoformat(),actual_head_before_after=head,actual_staged_tree_before_after=tree,original_entire_index_bytes=len(before),original_entire_index_sha256=hashlib.sha256(before).hexdigest(),actual_split_index_bytes=(h/'current-index').stat().st_size,whole_shared_indices=shared,original_config_held_private=True,whole_hold=str(h),scope='entire Git index/config custody and equivalent split-index representation only; no source/raw/Git object deletion or scientific execution; lost volatile index is reconstructed from published immutable source after preserving working files')
(h/'actual-index-storage-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
g=r/'experiments/chained-transfer-lp-presentation-01/evidence/entire-Consumer-Git-index-storage-01';g.mkdir()
for n in ['actual-index-storage-receipt.json','actual-split-index.stdout','actual-split-index.stderr','actual-split-index.exit']:shutil.copyfile(h/n,g/n)
shutil.copyfile(__file__,g/'entire-actual-metadata-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',f'Proactive storage custody at observed3MiB overlay headroom: whole Consumer original{len(before)}B Git index/config held privately in RAM, canonical index byte-exact symlink then standard split-index conversion0. Complete actual shared-index bytes retained through original-path symlinks; source6ad08267 and exact staged tree unchanged, no staged/source/raw/Git object deletion or native work. Current equivalent index reduced to{receipt["actual_split_index_bytes"]}B; original full index and original config remain immutable. Existing old index/archives/failures/holds not removed. Lost volatile metadata requires preserving working files and reconstructing recorded published index, never scientific rerun. This is metadata storage, not original checkpoint/scientificNEW28/admission or signed standing.' ]
for f in sorted(g.iterdir()):cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,env=env,text=True).strip();print(claim,json.dumps(receipt))
entry='\n---\n\n'+datetime.now(timezone.utc).isoformat()+'\n# Preserve complete Consumer Git index while recovering disk capacity\n\n## What was done\n'+claim+': exact6ad HEAD/staged tree retained; entire old index/config/shared index bytes held inRAM, current standard split index uses byte-exact canonical symlink and substantially smaller current index. No research/raw/object or old-hold deletion. [pcc:unverified]\n\n## Decisions made\nUse RAM alternate source-governor indices and GIT_OPTIONAL_LOCKS=0 reads. Publish finished runtime source/context evidence next. On volatile loss preserve working bytes and rebuild only published Git metadata, never repeat science. [pcc:unverified]\n\n## Open threads\nActual guarded-context source publication/bootstrap, original seven metadata objects/frozen workflow hydration/full scientificNEW28; paid stop remains. [pcc:unverified]\n\n## Errors\nNo failed scientific measurement or index/source loss; proactive response to observed3MiB remaining overlay. [pcc:unverified]\n'
for n in ['docs/session-logs/2026-11-16.md','.resume/RESUME.md']:
 with (r/n).open('a') as f:f.write(entry)
