import hashlib, json, os, re, subprocess, time
from pathlib import Path
root = Path('/home/ec2-user/cryptanalysis-proof-audit-20261021')
srcdir = root/'experiments/prime-j0-mixed640-materialized-tree-20261013'
out = Path('/var/tmp/cryptanalysis-mixed640-replay-20261021')
out.mkdir(exist_ok=True)
files = {p.stem:p for p in srcdir.glob('*.lean')}
deps = {name:[x for x in re.findall(r'^import\s+(\S+)',p.read_text(),re.M) if x in files] for name,p in files.items()}
order=[]; seen=set(); active=set()
def visit(name):
 if name in seen:return
 if name in active:raise RuntimeError('dependency cycle at '+name)
 active.add(name)
 for dep in deps[name]:visit(dep)
 active.remove(name);seen.add(name);order.append(name)
for name in sorted(files):visit(name)
env=os.environ.copy();env['ELAN_TOOLCHAIN']='leanprover/lean4:v4.34.1';env['LEAN_PATH']=str(out)
allowed={'propext','Classical.choice','Quot.sound'}
rows=[]
for name in order:
 p=files[name];t=time.monotonic();source=p.read_bytes()
 try:
  r=subprocess.run(['lean','-o',str(out/(name+'.olean')),str(p)],cwd=root,env=env,capture_output=True,text=True,timeout=300)
  status='PASS' if r.returncode==0 else 'BUILD_FAIL'
  output=r.stdout+r.stderr
 except subprocess.TimeoutExpired as e:
  status='TIMEOUT';output=str(e);r=None
 lines=re.findall(r"'([^']+)' (?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)",output,re.M)
 expected=len(re.findall(r'^#print axioms ',source.decode(),re.M))
 bad=[]
 for _,values in lines:
  axioms={v.strip() for v in values.split(',') if v.strip()}
  bad.extend(sorted(axioms-allowed))
 if status=='PASS' and (len(lines)!=expected or bad):status='AUDIT_FAIL'
 row={'source':str(p.relative_to(root)),'sha256':hashlib.sha256(source).hexdigest(),'status':status,'seconds':round(time.monotonic()-t,1),'expected_prints':expected,'actual_prints':len(lines),'bad_axioms':bad,'exit':r.returncode if r else None}
 (out/(name+'.log')).write_text(output)
 rows.append(row);(out/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(status,name,f"{row['seconds']}s",f"{len(lines)}/{expected} axiom prints",flush=True)
 if status!='PASS':break
print('summary:',len(rows),'of',len(files),'compiled; pass',sum(x['status']=='PASS' for x in rows),flush=True)
