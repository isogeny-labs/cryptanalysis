"""Remove unheld pip HTTP download-cache entries only; installed tools and sources remain."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,os,shutil,subprocess
w=Path('/workspace');scratch=w/'scratch';cache=Path('/home/agent/.cache/pip/http-v2')
held=json.loads((scratch/'ct91-whole-closed-science-handoff-25/current-inputs.json').read_text())
assert len(held)==51583
subjects=set()
for repo in ['crypto','cryptanalysis','crypto-autoresearcher']:
 for claim in (w/repo/'pcc/claims').glob('*.json'):
  for proof in json.loads(claim.read_text()).get('proofs',[]):
   if proof.get('kind')=='attestation':
    row=proof.get('subject',proof);p=Path(row['path']);subjects.add(str((p if p.is_absolute() else w/repo/p).resolve()))
rows=[];candidates=[]
for p in sorted(cache.rglob('*')):
 if not p.is_file() or p.is_symlink():continue
 assert str(p) not in held and str(p.resolve()) not in held and str(p.resolve()) not in subjects
 st=p.stat();assert st.st_nlink==1
 rows.append(dict(path=str(p),bytes=st.st_size,allocated_bytes=st.st_blocks*512,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()))
 candidates.append(p)
assert candidates
statuses={repo:subprocess.check_output(['git','status','--porcelain'],cwd=w/repo) for repo in ['crypto','cryptanalysis','crypto-autoresearcher']}
raw=scratch/'ct94-unheld-pip-download-cache-cleanup-13';raw.mkdir()
before=os.statvfs(w)
(raw/'whole-removed-download-cache-inventory.json.xz').write_bytes(lzma.compress((json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),rows=rows,scope='unheld pip HTTP download entries only; no installed package, source, executable, research raw, prepared library or held subject'),indent=2)+'\n').encode()))
for p in candidates:p.unlink()
assert all(subprocess.check_output(['git','status','--porcelain'],cwd=w/repo)==s for repo,s in statuses.items())
after=os.statvfs(w)
out=dict(at=datetime.now(timezone.utc).isoformat(),removed_paths=len(rows),logical_bytes=sum(r['bytes']for r in rows),allocated_bytes=sum(r['allocated_bytes']for r in rows),available_before=before.f_bavail*before.f_frsize,available_after=after.f_bavail*after.f_frsize,all51583_guard_paths_and_all_PCC_subjects_excluded=True,all_three_Git_statuses_unchanged=True,scope='unheld pip HTTP download cache only; installed tools, sources and scientific evidence unchanged')
(raw/'outcome.json').write_text(json.dumps(out,indent=2)+'\n');shutil.copyfile(__file__,raw/'original-command.py');print(json.dumps(out),flush=True)
