"""Reclaim unheld third-party libraries in three closed early build caches; preserve all research evidence."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,os,shutil,subprocess
w=Path('/workspace');scratch=w/'scratch';held=json.loads((scratch/'ct91-whole-closed-science-handoff-25/current-inputs.json').read_text());assert len(held)==51583
subjects=set()
for name in ['crypto','cryptanalysis','crypto-autoresearcher']:
 for claim in(w/name/'pcc/claims').glob('*.json'):
  for proof in json.loads(claim.read_text()).get('proofs',[]):
   if proof.get('kind')=='attestation':
    row=proof.get('subject',proof);p=Path(row['path']);subjects.add(str((p if p.is_absolute()else w/name/p).resolve()))
roots=[scratch/name for name in ['ct54-fp-chain-cli-01-build-cache','ct55-g3-root-regression-01-build-cache','ct56-g3-norm-cli-01-build-cache']]
processes=subprocess.check_output(['ps','-eo','pid,ppid,stat,comm'],text=True)
assert not[line for line in processes.splitlines()if len(a:=line.split())==4 and a[3]in ['cargo','rustc','cc','ld']and not a[2].startswith('Z')]
rows=[];candidates=[]
for root in roots:
 assert root.is_dir()
 for p in sorted(root.rglob('*')):
  if not p.is_file()or p.is_symlink()or p.suffix not in ['.rlib','.rmeta','.so']or not p.name.startswith('lib'):continue
  if p.name.startswith(('libisogeny_algos','libcrypto_lib','libghs','libchained','libdiem','libplane_quartic')):continue
  if str(p)in held or str(p.resolve())in held or str(p.resolve())in subjects:continue
  dep=p.with_name(p.name[3:].rsplit('.',1)[0]+'.d')
  if not dep.is_file():continue
  text=dep.read_text()
  rhs=[line.split(': ',1)[1]for line in text.splitlines()if ': 'in line and not line.startswith('#')]
  if '/.cargo/registry/src/'not in text or not rhs or any('/workspace/'in part for part in rhs):continue
  st=p.stat();assert st.st_nlink==1
  rows.append(dict(path=str(p),bytes=st.st_size,allocated_bytes=st.st_blocks*512,mode=st.st_mode,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),retained_dependency_file=str(dep),dependency_sha256=hashlib.file_digest(dep.open('rb'),'sha256').hexdigest(),classification='thirdparty registry compiler artifact; all parsed source-input sides have no workspace path; target sides are kept distinct'))
  candidates.append(p)
assert rows
retained=[p for root in roots for p in root.rglob('*')if p.is_file()and not p.is_symlink()and p.stat().st_mode&0o111 and p not in candidates]
retained.append(w/'crypto/target/release/deps/crypto_lib-0f5740d1cfe22c09')
before_hashes={str(p):hashlib.file_digest(p.open('rb'),'sha256').hexdigest()for p in retained}
assert '/workspace/scratch/ct55-g3-root-regression-01-build-cache/release/deps/crypto_lib-0f5740d1cfe22c09'in before_hashes
statuses={name:subprocess.check_output(['git','status','--porcelain'],cwd=w/name)for name in ['crypto','cryptanalysis','crypto-autoresearcher']}
raw=scratch/'ct96-unheld-closed-registry-cache-cleanup-14';raw.mkdir();shutil.copyfile(__file__,raw/'original-command.py');before=os.statvfs(w)
(raw/'whole-removed-cache-inventory.json.xz').write_bytes(lzma.compress((json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),rows=rows,retained_executables=before_hashes,all51583_prior_paths_and_all_modern_legacy_PCC_subjects_excluded=True,no_active_compiler=True,scope='unheld registry compiler libraries in three closed ct54-56 caches only; no research source/raw/executable/field-workspace library/fullpreparedcopy/currentct57-80cache'),indent=2)+'\n').encode()))
for p in candidates:p.unlink()
for row in rows:assert hashlib.file_digest(Path(row['retained_dependency_file']).open('rb'),'sha256').hexdigest()==row['dependency_sha256']
assert all(hashlib.file_digest(Path(name).open('rb'),'sha256').hexdigest()==h for name,h in before_hashes.items())
assert all(subprocess.check_output(['git','status','--porcelain'],cwd=w/name)==v for name,v in statuses.items())
after=os.statvfs(w);receipt=dict(at=datetime.now(timezone.utc).isoformat(),removed_paths=len(rows),logical_bytes=sum(v['bytes']for v in rows),allocated_bytes=sum(v['allocated_bytes']for v in rows),available_before=before.f_bavail*before.f_frsize,available_after=after.f_bavail*after.f_frsize,retained_executable_hashes_unchanged=len(before_hashes),both_distinct_diagnostics_retained=True,all_source_dependency_records_unchanged=True,all51583_guard_paths_and_every_PCC_subject_excluded=True,all_three_Git_statuses_unchanged=True,scope='unsigned derived registry compiler cache cleanup only; no scientific or cost acceptance')
(raw/'outcome.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
