from pathlib import Path
import hashlib,json,subprocess,sys
src=Path(__file__).resolve().parent
root=Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929/output_first_fifth_20261019')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def freeze(name):
    d=json.loads((src/name).read_text())
    for k,v in d['sources'].items():
        p=Path(v['path'])
        if p.is_relative_to(src):p=root/p.name
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
freeze('n41_gate_protocol.json')
command([sys.executable,str(root/'verify_n41.py')])
freeze('n131_protocol.json')
command([sys.executable,str(root/'run.py'),'n131'],'n131.stdout')
freeze('n131_audit_protocol.json')
command(['/Volumes/SSD990/cryptanalysis/sage','-python',str(root/'supervise_audit.py'),'n131'])
print('CANONICAL_COMPLETE',root)
