from pathlib import Path
import shutil,json,hashlib,subprocess,sys
src=Path(__file__).resolve().parent
root=Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929/output_first_fifth_20261019')
root.mkdir(exist_ok=True)
(root/'scratch').mkdir(exist_ok=True)
for p in src.iterdir():
    if p.is_file() and p.name!='canonicalize.py':
        shutil.copy2(p,root/'scratch'/p.name)
for name in ['output_first_math.py','run.py','audit_sage.py','supervise_audit.py','verify_n41.py','OutputFirst.lean']:
    shutil.copy2(src/name,root/name)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def freeze(name):
    d=json.loads((src/name).read_text())
    for k,v in d['sources'].items():
        p=Path(v['path'])
        if p.is_relative_to(src):
            p=root/p.name
        v['path']=str(p)
        assert p.exists(),(name,k,p)
        v['sha256']=sha(p)
    (root/name).write_text(json.dumps(d,sort_keys=True,indent=2)+'\n')
def command(argv,stdout=None):
    r=subprocess.run(argv,cwd=root,text=True,capture_output=True,timeout=620)
    if stdout:
        (root/stdout).write_text(r.stdout)
        (root/stdout.replace('.stdout','.stderr')).write_text(r.stderr)
    print(argv,'exit',r.returncode,r.stdout[-500:],r.stderr[-500:],flush=True)
    if r.returncode:raise RuntimeError(argv)
command(['/Volumes/SSD990/cryptanalysis/sage','--runtime-info'])
# Save fresh checked launcher receipt explicitly, outside timed producer/auditor intervals.
r=subprocess.run(['/Volumes/SSD990/cryptanalysis/sage','--runtime-info'],cwd=root,text=True,capture_output=True,check=True)
(root/'sage_runtime_info.json').write_text(r.stdout)
freeze('n41_protocol.json')
command([sys.executable,str(root/'run.py'),'n41'],'n41.stdout')
freeze('n41_audit_protocol.json')
command([sys.executable,str(root/'supervise_audit.py'),'n41'])
freeze('n41_gate_protocol.json')
command([sys.executable,str(root/'verify_n41.py')])
freeze('n131_protocol.json')
command([sys.executable,str(root/'run.py'),'n131'],'n131.stdout')
freeze('n131_audit_protocol.json')
command([sys.executable,str(root/'supervise_audit.py'),'n131'])
print('CANONICAL_COMPLETE',root)
