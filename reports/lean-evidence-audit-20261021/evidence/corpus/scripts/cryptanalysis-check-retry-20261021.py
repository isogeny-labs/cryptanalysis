import json, subprocess, sys, time
from pathlib import Path
root=Path('/home/ec2-user/cryptanalysis-proof-audit-20261021')
prior=json.load(open('/var/tmp/cryptanalysis-check-replay-20261021.json'))
paths=[r['path'] for r in prior if r['exit']!=0]
paths += ['experiments/prime-j0-hex-dag-pareto-20261013/check.py','experiments/prime-j0-hex-workdepth-20261013/check.py']
rows=[];out=Path('/var/tmp/cryptanalysis-check-retry-20261021.json')
for rel in paths:
 p=root/rel;start=time.monotonic()
 try:
  r=subprocess.run([sys.executable,str(p),'--check'],cwd=root,capture_output=True,text=True,timeout=600)
  row={'path':rel,'exit':r.returncode,'seconds':round(time.monotonic()-start,1),'stdout':r.stdout,'stderr':r.stderr}
 except subprocess.TimeoutExpired as e:
  row={'path':rel,'exit':'TIMEOUT','seconds':round(time.monotonic()-start,1),'stdout':(e.stdout or b'').decode(errors='replace') if isinstance(e.stdout,bytes) else e.stdout or '', 'stderr':(e.stderr or b'').decode(errors='replace') if isinstance(e.stderr,bytes) else e.stderr or ''}
 rows.append(row);out.write_text(json.dumps(rows,indent=2)+'\n')
 print(f"{row['exit']} {row['seconds']}s {rel}",flush=True)
print(f"completed {len(rows)} checks; {sum(r['exit']==0 for r in rows)} passed",flush=True)
