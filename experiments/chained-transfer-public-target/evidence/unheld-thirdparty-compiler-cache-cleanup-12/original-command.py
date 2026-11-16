"""Remove only unheld third-party compiler cache, preserving all research bytes."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,os,shutil,subprocess
w=Path('/workspace');scratch=w/'scratch';held=json.loads((scratch/'ct91-whole-closed-science-handoff-25/current-inputs.json').read_text());assert len(held)==51583
subjects=set()
for name in ['crypto','cryptanalysis','crypto-autoresearcher']:
    for claim in (w/name/'pcc/claims').glob('*.json'):
        for proof in json.loads(claim.read_text()).get('proofs',[]):
            if proof.get('kind')=='attestation':
                row=proof.get('subject',proof);p=Path(row['path']);subjects.add(str((p if p.is_absolute()else w/name/p).resolve()))
roots=[Path('/tmp')/name for name in ['chained-proper-build.jpqlRHnW','chained-proper-build.v6rBFA1d','chained-prime-norms-build.lkWIdPv7','chained-fp-chain-build.xWW3FiFm']]
processes=subprocess.check_output(['ps','-eo','pid,ppid,stat,comm,args'],text=True)
assert not [line for line in processes.splitlines() if len(a:=line.split(None,4))==5 and a[3]in ['cargo','rustc','cc','ld'] and not a[2].startswith('Z')]
candidates=[];rows=[]
for root in roots:
    assert root.is_dir()
    for p in sorted(root.rglob('*')):
        if not p.is_file()or p.is_symlink()or p.suffix not in ['.rlib','.rmeta','.so']or not p.name.startswith('lib'):continue
        if p.name.startswith(('libisogeny_algos','libcrypto_lib','libghs','libchained','libdiem','libplane_quartic')):continue
        if str(p)in held or str(p.resolve())in held or str(p.resolve())in subjects:continue
        dep=p.with_name(p.name[3:].rsplit('.',1)[0]+'.d')
        if not dep.is_file():continue
        text=dep.read_text()
        if '/.cargo/registry/src/'not in text or '/workspace/'in text:continue
        st=p.stat();candidates.append(p);rows.append(dict(path=str(p),bytes=st.st_size,allocated_bytes=st.st_blocks*512,mode=st.st_mode,inode=st.st_ino,links=st.st_nlink,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),retained_registry_dependency_file=str(dep),retained_dependency_file_sha256=hashlib.file_digest(dep.open('rb'),'sha256').hexdigest(),classification='registry-source compiler cache; dependency file contains registry source and no workspace source'))
assert len(rows)==302
retained=[p for root in roots for p in root.rglob('*') if p.is_file() and not p.is_symlink() and p.stat().st_mode&0o111 and p not in candidates]
retained += [w/'crypto/target/release/deps/crypto_lib-0f5740d1cfe22c09',scratch/'ct55-g3-root-regression-01-build-cache/release/deps/crypto_lib-0f5740d1cfe22c09']
before_hashes={str(p):hashlib.file_digest(p.open('rb'),'sha256').hexdigest()for p in retained}
statuses={name:subprocess.check_output(['git','status','--porcelain'],cwd=w/name)for name in ['crypto','cryptanalysis','crypto-autoresearcher']}
raw=scratch/'ct94-unheld-temporary-registry-cache-cleanup-12';raw.mkdir();before=os.statvfs(w)
inventory=raw/'whole-removed-cache-inventory.json.xz';inventory.write_bytes(lzma.compress((json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),all_rows=rows,all51583_guard_paths_and_every_PCC_subject_excluded=True,all_retained_executable_hashes=before_hashes,no_active_compiler=True,scope='only registry thirdparty .rlib/.rmeta/compilerplugin.so in four closed old temporary build caches; no source/raw/research executable/field-engine or workspace library/fullpreparedcopy/currentct57-ct80 path removed'),indent=2)+'\n').encode()))
for p in candidates:p.unlink()
assert all(Path(row['retained_registry_dependency_file']).exists()and hashlib.file_digest(Path(row['retained_registry_dependency_file']).open('rb'),'sha256').hexdigest()==row['retained_dependency_file_sha256'] for row in rows)
assert all(hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()==h for p,h in before_hashes.items())
assert all(subprocess.check_output(['git','status','--porcelain'],cwd=w/name)==state for name,state in statuses.items())
after=os.statvfs(w);outcome=dict(at=datetime.now(timezone.utc).isoformat(),removed_paths=len(rows),logical_bytes=sum(row['bytes']for row in rows),allocated_bytes=sum(row['allocated_bytes']for row in rows),actual_available_before=before.f_bavail*before.f_frsize,actual_available_after=after.f_bavail*after.f_frsize,whole_inventory=str(inventory),whole_inventory_bytes=inventory.stat().st_size,whole_inventory_sha256=hashlib.file_digest(inventory.open('rb'),'sha256').hexdigest(),all51583_guard_paths_and_every_PCC_subject_excluded=True,retained_executables_wholebytes_unchanged=len(before_hashes),all_dependency_source_records_unchanged=True,all_three_Git_statuses_unchanged=True,scope='unsigned derived thirdparty compiler cache cleanup; no scientific/cold/cost acceptance change')
(raw/'outcome.json').write_text(json.dumps(outcome,indent=2)+'\n');shutil.copyfile(__file__,raw/'original-command.py');print(json.dumps(outcome),flush=True)
