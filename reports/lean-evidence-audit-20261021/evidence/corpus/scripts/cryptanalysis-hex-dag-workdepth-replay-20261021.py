import json, subprocess, sys, time
from pathlib import Path
root=Path('/home/ec2-user/cryptanalysis-proof-audit-20261021')
rows=[]
cases=[
 ('dag-calibration','experiments/prime-j0-hex-dag-pareto-20261013/check.py','experiments/prime-j0-hex-workdepth-20261013/holdout.json','experiments/prime-j0-hex-dag-pareto-20261013/calibration-native.jsonl','experiments/prime-j0-hex-dag-pareto-20261013/calibration-check.json'),
 ('dag-holdout','experiments/prime-j0-hex-dag-pareto-20261013/check.py','experiments/prime-j0-hex-dag-pareto-20261013/holdout.json','experiments/prime-j0-hex-dag-pareto-20261013/holdout-native.jsonl','experiments/prime-j0-hex-dag-pareto-20261013/holdout-check.json'),
 ('workdepth-calibration','experiments/prime-j0-hex-workdepth-20261013/check.py','experiments/prime-j0-hex-tree-20261013/holdout.json','experiments/prime-j0-hex-workdepth-20261013/calibration-native.jsonl','experiments/prime-j0-hex-workdepth-20261013/calibration-receipt.json'),
 ('workdepth-holdout','experiments/prime-j0-hex-workdepth-20261013/check.py','experiments/prime-j0-hex-workdepth-20261013/holdout.json','experiments/prime-j0-hex-workdepth-20261013/holdout-native.jsonl','experiments/prime-j0-hex-workdepth-20261013/holdout-receipt.json')]
for label,checker,fixture,native,receipt in cases:
 t=time.monotonic()
 try:
  p=subprocess.run([sys.executable,str(root/checker),str(root/fixture),str(root/native),*([str(root/receipt)] if label.startswith('workdepth') else [])],cwd=root,capture_output=True,text=True,timeout=300)
  same=p.returncode==0 and (json.loads(p.stdout)==json.loads((root/receipt).read_text()) if label.startswith('dag') else True)
  row={'label':label,'exit':p.returncode,'matches_frozen_receipt':same,'seconds':round(time.monotonic()-t,1),'stdout':p.stdout,'stderr':p.stderr}
 except Exception as e:
  row={'label':label,'exit':'ERROR','matches_frozen_receipt':False,'seconds':round(time.monotonic()-t,1),'error':repr(e)}
 rows.append(row);Path('/var/tmp/cryptanalysis-hex-dag-workdepth-replay-20261021.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(label,row['exit'],row['matches_frozen_receipt'],row['seconds'],flush=True)
