import hashlib, json, os, re, subprocess, time
from pathlib import Path
root=Path('/home/ec2-user/cryptanalysis-proof-audit-20261021')
out=Path('/var/tmp/cryptanalysis-core-replay-20261021');out.mkdir(exist_ok=True)
allf=[root/p for p in subprocess.check_output(['git','ls-files','--','*.lean'],cwd=root,text=True).splitlines()]
covered=set()
for rel in subprocess.check_output(['git','ls-files','--','experiments/**/check.py'],cwd=root,text=True).splitlines():
 p=root/rel;receipt=p.parent/'lean-build.txt'
 if receipt.exists():covered.update(re.findall(r'^sha256 (.*\.lean): [0-9a-f]{64}$',receipt.read_text(),re.M))
selected=[]
for p in allf:
 rel=str(p.relative_to(root))
 if rel in covered or 'prime-j0-mixed640-materialized-tree-20261013' in rel or 'orbit-quotient-summation/lean' in rel or 'binary_genus2_cover_20261014/lean' in rel or p.name in ('GaugeTree.lean','OrbitCompression.lean'):continue
 imports=[]
 for line in re.findall(r'^\s*import\s+([^\n]+)',p.read_text(),re.M):imports.extend(line.split())
 if set(imports)<={'Lean','Init.Grind.Ring.Basic'}:selected.append(p)
allowed={'propext','Classical.choice','Quot.sound'};rows=[]
for p in selected:
 rel=str(p.relative_to(root));slug=rel.replace('/','_').replace('.lean','');t=time.monotonic();source=p.read_bytes()
 pin=p.parent
 while pin!=root and not (pin/'lean-toolchain').exists():pin=pin.parent
 env=os.environ.copy();env['ELAN_TOOLCHAIN']=(pin/'lean-toolchain').read_text().strip() if (pin/'lean-toolchain').exists() else 'leanprover/lean4:v4.34.1'
 try:
  r=subprocess.run(['lean','-o',str(out/(slug+'.olean')),str(p)],cwd=root,env=env,capture_output=True,text=True,timeout=300)
  status='PASS' if r.returncode==0 else 'BUILD_FAIL';output=r.stdout+r.stderr
 except subprocess.TimeoutExpired as e:
  status='TIMEOUT';output=str(e);r=None
 lines=re.findall(r"'([^']+)' (?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)",output,re.M)
 expected=len(re.findall(r'^#print axioms ',source.decode(),re.M))
 bad=[]
 for _,values in lines:bad.extend(sorted({v.strip() for v in values.split(',') if v.strip()}-allowed))
 if status=='PASS' and (len(lines)!=expected or bad):status='AUDIT_FAIL'
 row={'source':rel,'sha256':hashlib.sha256(source).hexdigest(),'status':status,'toolchain':env['ELAN_TOOLCHAIN'],'seconds':round(time.monotonic()-t,1),'expected_prints':expected,'actual_prints':len(lines),'bad_axioms':bad,'exit':r.returncode if r else None}
 (out/(slug+'.log')).write_text(output);rows.append(row);(out/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(status,rel,f"{row['seconds']}s",f"{len(lines)}/{expected} axiom prints",flush=True)
print('summary:',len(rows),'of',len(selected),'compiled; pass',sum(x['status']=='PASS' for x in rows),flush=True)
