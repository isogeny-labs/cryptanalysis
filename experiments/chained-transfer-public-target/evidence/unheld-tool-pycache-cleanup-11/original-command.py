"""Unheld regenerable tool bytecode only; preserve all sources and research data."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,os,subprocess
w=Path('/workspace');scratch=w/'scratch';held=json.loads((scratch/'ct89-whole-closed-science-handoff-24/current-inputs.json').read_text());assert len(held)==49753
subjects=set()
for name in ['crypto','cryptanalysis','crypto-autoresearcher']:
    for claim in (w/name/'pcc/claims').glob('*.json'):
        for proof in json.loads(claim.read_text()).get('proofs',[]):
            if proof.get('kind')=='attestation':
                v=proof.get('subject',proof);p=Path(v['path']);subjects.add(str((p if p.is_absolute() else w/name/p).resolve()))
roots=[scratch/'report-venv',scratch/'ct56-awscli-venv']
processes=subprocess.check_output(['ps','-eo','pid,ppid,stat,comm,args'],text=True)
assert not [line for line in processes.splitlines() if len(a:=line.split(None,4))==5 and a[3] in ['cargo','rustc','aws'] and not a[2].startswith('Z')]
assert not [line for line in processes.splitlines() if len(a:=line.split(None,4))==5 and a[3].startswith('python') and any(str(root/'bin') in a[4] for root in roots)]
statuses={name:subprocess.check_output(['git','status','--porcelain'],cwd=w/name) for name in ['crypto','cryptanalysis','crypto-autoresearcher']}
retained=[w/'crypto/target/release/deps/crypto_lib-0f5740d1cfe22c09',scratch/'ct55-g3-root-regression-01-build-cache/release/deps/crypto_lib-0f5740d1cfe22c09']
retained_hashes={str(p):hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in retained}
before=os.statvfs(w);rows=[];sources={}
for root in roots:
    for p in sorted(root.rglob('*.pyc')):
        if p.is_symlink() or str(p) in held or str(p.resolve()) in held or str(p.resolve()) in subjects or '.cpython-' not in p.name:continue
        source=p.parent.parent/(p.name.split('.cpython-',1)[0]+'.py')
        if not source.is_file() or source.is_symlink():continue
        sources[str(source)]=hashlib.file_digest(source.open('rb'),'sha256').hexdigest()
        st=p.stat();rows.append(dict(path=str(p),bytes=st.st_size,allocated_bytes=st.st_blocks*512,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),mode=st.st_mode,inode=st.st_ino,links=st.st_nlink,regenerable_source=str(source)))
assert rows
raw=scratch/'ct91-unheld-tool-pycache-cleanup-11';raw.mkdir();receipt=raw/'whole-removed-bytecode-inventory.json.xz'
receipt.write_bytes(lzma.compress((json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),rows=rows,all_retained_source_hashes=sources,all49753held_paths_and_every_PCC_subject_excluded=True,no_active_target_tool_or_compiler=True,scope='regenerable .pyc under two task tool venvs only; no scientific source/raw/actual research executable/fullprepared copy/currentct57-ct80 cache removed'),indent=2)+'\n').encode()))
for row in rows:Path(row['path']).unlink()
assert all(hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()==h for p,h in sources.items())
assert all(hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==retained_hashes[str(p)] for p in retained)
assert all(subprocess.check_output(['git','status','--porcelain'],cwd=w/name)==state for name,state in statuses.items())
after=os.statvfs(w)
outcome=dict(at=datetime.now(timezone.utc).isoformat(),removed_paths=len(rows),logical_bytes=sum(row['bytes'] for row in rows),allocated_bytes=sum(row['allocated_bytes'] for row in rows),actual_available_before=before.f_bavail*before.f_frsize,actual_available_after=after.f_bavail*after.f_frsize,whole_receipt=str(receipt),whole_receipt_bytes=receipt.stat().st_size,whole_receipt_sha256=hashlib.file_digest(receipt.open('rb'),'sha256').hexdigest(),all49753_prior_guard_paths_excluded=True,every_PCC_subject_excluded=True,all_retained_python_sources_unchanged=True,both_different_diagnostic_executables_unchanged=retained_hashes,all_three_Git_statuses_unchanged=True,scope='unsigned regenerable tool bytecode cleanup only; no scientific evidence or cold acceptance changed')
(raw/'outcome.json').write_text(json.dumps(outcome,indent=2)+'\n');print(json.dumps(outcome),flush=True)
