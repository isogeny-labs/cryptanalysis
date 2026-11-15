"""Remove one closed, unheld derived Cargo cache object; never raw custody."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,subprocess
w=Path('/workspace');p=w/'crypto/target/release/deps/libcrypto_lib-bd818e59d6c43732.rlib';guardfile=w/'scratch/ct84-whole-closed-science-handoff-22/current-inputs.json';held=json.loads(guardfile.read_text());assert len(held)==44386
packed=w/'scratch/ct84-whole-closed-science-handoff-22/whole-current-inputs.json.xz';assert json.loads(lzma.decompress(packed.read_bytes()))==held
manifest=json.loads((w/'crypto/research/chained_jacobian_transfers_20261110/evidence/public-n4-complete-chain-handoff-22/.artifacts.json').read_text())['files']['whole-current-inputs.json.xz'];assert len(packed.read_bytes())==manifest['bytes']and hashlib.sha256(packed.read_bytes()).hexdigest()==manifest['sha256']
assert str(p)not in held and str(p.resolve())not in held
subjects=[]
for repo in ['crypto','cryptanalysis','crypto-autoresearcher']:
 for q in(w/repo/'pcc/claims').glob('*.json'):
  for proof in json.loads(q.read_text()).get('proofs',[]):
   if proof.get('kind')=='attestation':
    subject=proof.get('subject',proof);assert isinstance(subject,dict)and'path'in subject,str(q);name=subject['path'];v=Path(name);v=v if v.is_absolute()else w/repo/v;subjects.append(str(v));assert v.resolve()!=p.resolve(),str(q)
processes=subprocess.check_output(['ps','-eo','pid,ppid,stat,comm,args'],text=True);active=[line for line in processes.splitlines()if len(x:=line.split(None,4))==5 and x[3]in ['cargo','rustc']and not x[2].startswith('Z')];assert not active,active
original=w/'scratch/ct55-g3-root-regression-01-build-cache/release/deps/crypto_lib-0f5740d1cfe22c09';expected='82029f639d326548a7d44ea0f55477880f0c50cf358edeec3a6827f22591a9bd';assert hashlib.sha256(original.read_bytes()).hexdigest()==expected
before={repo:subprocess.check_output(['git','status','--porcelain'],cwd=w/repo)for repo in ['crypto','cryptanalysis','crypto-autoresearcher']}
assert p.is_file()and p.suffix=='.rlib'and p.stat().st_nlink==1
row=dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),inode=p.stat().st_ino,links=p.stat().st_nlink,allocated_bytes=p.stat().st_blocks*512)
receipt=w/'scratch/ct86-closed-root-derived-rlib-cleanup-08.json';assert not receipt.exists()
record=dict(at=datetime.now(timezone.utc).isoformat(),scope='ONE obsolete root Cargo RLIB cache object from2026-11-11; outside all44386 genuine22 guarded keys and every current PCC attestation subject; full actual source/raw/executables/prepared-library copies/currentct57+ct80 untouched. Static compiled diagnostic executable retained exact. Root library cache is rebuildable from unchanged source; no active compiler.',guard_keys=len(held),guard_sha256=hashlib.sha256(guardfile.read_bytes()).hexdigest(),genuine_manifest_exact=True,attestation_subjects_checked=len(subjects),active_compilers=active,row=row,retained_original_executable=dict(path=str(original),sha256=expected))
receipt.write_text(json.dumps(record,indent=2)+'\n')
p.unlink();assert not p.exists();assert hashlib.sha256(original.read_bytes()).hexdigest()==expected
assert all(subprocess.check_output(['git','status','--porcelain'],cwd=w/repo)==before[repo]for repo in before)
print('Removed one unheld derived cache RLIB:',row['bytes'],'bytes; original executable and all Git statuses exact')
