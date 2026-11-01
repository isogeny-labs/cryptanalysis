import json, subprocess, sys, time
from pathlib import Path
root=Path('/home/ec2-user/cryptanalysis-proof-audit-20261021')
base=root/'experiments/prime-j0-hex-orbit-materialized-20261013'
rows=[]
for label,fixture,native in [
 ('calibration','experiments/prime-j0-hex-dag-pareto-20261013/holdout.json','experiments/prime-j0-hex-orbit-materialized-20261013/calibration-native.jsonl'),
 ('holdout','experiments/prime-j0-hex-orbit-materialized-20261013/holdout.json','experiments/prime-j0-hex-orbit-materialized-20261013/holdout-native.jsonl')]:
 start=time.monotonic()
 try:
  p=subprocess.run([sys.executable,str(base/'check.py'),str(root/fixture),str(root/native)],cwd=root,capture_output=True,text=True,timeout=300)
  expected=json.loads((base/f'{label}-check.json').read_text())
  actual=json.loads(p.stdout) if p.returncode==0 else None
  same=actual==expected
  row={'label':label,'exit':p.returncode,'matches_frozen_receipt':same,'seconds':round(time.monotonic()-start,1),'stdout':p.stdout,'stderr':p.stderr}
 except Exception as e:
  row={'label':label,'exit':'ERROR','matches_frozen_receipt':False,'seconds':round(time.monotonic()-start,1),'error':repr(e)}
 rows.append(row);Path('/var/tmp/cryptanalysis-hex-orbit-replay-20261021.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(label,row['exit'],same if 'same' in locals() else False,row['seconds'],flush=True)
