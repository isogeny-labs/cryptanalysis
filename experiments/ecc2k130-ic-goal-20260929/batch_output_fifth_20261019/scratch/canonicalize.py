from pathlib import Path
import shutil,json,hashlib,subprocess,sys
src=Path(__file__).resolve().parent
root=Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929/batch_output_fifth_20261019')
(root/'scratch').mkdir(parents=True,exist_ok=True)
for p in src.iterdir():
 if p.is_file() and p.name!='canonicalize.py':shutil.copyfile(p,root/'scratch'/p.name)
for name in ('batch_output.py','batch_output_fast.py','BatchInverse.lean'):
 shutil.copyfile(src/name,root/name)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def freeze(case,fast=False):
 suffix='_fast_protocol.json' if fast else '_protocol.json'
 name=case+suffix
 d=json.loads((src/name).read_text())
 for k,v in d['sources'].items():
  p=Path(v['path'])
  if p.is_relative_to(src):p=root/p.name
  v['path']=str(p)
  assert p.exists(),(name,k,p)
  v['sha256']=sha(p)
 (root/name).write_text(json.dumps(d,sort_keys=True,indent=2)+'\n')
def run(argv):
 r=subprocess.run(argv,cwd=root,text=True,capture_output=True,timeout=620)
 print(argv,'exit',r.returncode,r.stdout[-500:],r.stderr[-500:],flush=True)
 if r.returncode:raise RuntimeError(argv)
for case in ('n41','n131'):
 freeze(case)
 run([sys.executable,str(root/'batch_output.py'),case])
 freeze(case,True)
 run([sys.executable,str(root/'batch_output_fast.py'),case])
r=subprocess.run(['/Users/adamburan/.elan/toolchains/leanprover--lean4---v4.34.1/bin/lean','BatchInverse.lean'],cwd=root,text=True,capture_output=True)
(root/'lean_check.stdout').write_text(r.stdout)
(root/'lean_check.stderr').write_text(r.stderr)
print('Lean exit',r.returncode,r.stdout,r.stderr,flush=True)
if r.returncode:raise RuntimeError('Lean failed')
print('CANONICAL_COMPLETE')
