"""Closed unheld root dependency cache cleanup; no source/raw/full-copy removal."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,subprocess
w=Path('/workspace');root=w/'crypto/target/release';held=json.loads((w/'scratch/ct89-whole-closed-science-handoff-24/current-inputs.json').read_text());assert len(held)==49753
subjects=set()
for name in ['crypto','cryptanalysis','crypto-autoresearcher']:
 for q in(w/name/'pcc/claims').glob('*.json'):
  for proof in json.loads(q.read_text()).get('proofs',[]):
   if proof.get('kind')=='attestation':
    v=proof.get('subject',proof);assert'path'in v;path=Path(v['path']);path=path if path.is_absolute()else w/name/path;subjects.add(str(path.resolve()))
processes=subprocess.check_output(['ps','-eo','pid,ppid,stat,comm,args'],text=True);active=[x for x in processes.splitlines()if len(a:=x.split(None,4))==5 and a[3]in ['cargo','rustc']and not a[2].startswith('Z')];assert not active,active
ldd=subprocess.run(['ldd',str(w/'crypto/target/release/deps/crypto_lib-0f5740d1cfe22c09')],capture_output=True,text=True);assert ldd.returncode==0
candidates=[p for p in root.rglob('*')if p.is_file()and not p.is_symlink()and p.suffix in ['.a','.so']and p.stat().st_size>1024*1024 and str(p)not in held and str(p.resolve())not in held and str(p.resolve())not in subjects and not p.name.startswith(('libisogeny_algos','libcrypto_lib'))and p.name not in ldd.stdout]
assert candidates
retained=[w/'crypto/target/release/deps/crypto_lib-0f5740d1cfe22c09',w/'scratch/ct55-g3-root-regression-01-build-cache/release/deps/crypto_lib-0f5740d1cfe22c09'];expected='82029f639d326548a7d44ea0f55477880f0c50cf358edeec3a6827f22591a9bd';retained_rows={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in retained};assert retained_rows[str(retained[1])]==expected;assert all(str(p)not in held or retained_rows[str(p)]==held[str(p)]for p in retained)
statuses={name:subprocess.check_output(['git','status','--porcelain'],cwd=w/name)for name in ['crypto','cryptanalysis','crypto-autoresearcher']}
rows=[dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),mode=p.stat().st_mode,inode=p.stat().st_ino,links=p.stat().st_nlink,allocated_bytes=p.stat().st_blocks*512)for p in sorted(candidates)]
receipt=w/'scratch/ct90-closed-root-compiler-link-cache-cleanup-10.json.xz';assert not receipt.exists();receipt.write_bytes(lzma.compress((json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),scope='Only obsolete unheld Root target/release third-party static dependency and compiler macro shared-library cache, all49753 genuine24 guardpaths/every modern-legacy PCC subject/root isogenylibrary/ldd-required libraries excluded; no active compiler. Source/raw/actual research executables/fullpreparedcopies/currentct57-ct80 untouched; both exact263MB diagnostic executables andall Git statuses retained. Rebuildable dependency cache, no cold orscientific acceptance inference',guard_keys=len(held),subjects_checked=len(subjects),active_compilers=active,all_rows=rows,retained_executables=[str(p)for p in retained],retained_individual_sha256=retained_rows,known_historical_Scratch_sha256=expected),indent=2)+'\n').encode()))
for p in candidates:p.unlink()
assert all(hashlib.sha256(p.read_bytes()).hexdigest()==retained_rows[str(p)] for p in retained);assert all(subprocess.check_output(['git','status','--porcelain'],cwd=w/name)==v for name,v in statuses.items())
print('Removed',len(rows),'unheld derived dependency paths;',sum(x['bytes']for x in rows),'logical bytes; exact executables and Git statuses unchanged')
