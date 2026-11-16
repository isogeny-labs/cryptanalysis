"""Exercise actual receipt-validator rejection with complete copied inputs; I/O only."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
r=Path('/workspace/cryptanalysis');study=r/'experiments/chained-transfer-public-target'
raw=Path('/workspace/scratch/ct95-induced-proof-driver-local-01');assert(raw/'actual-driver.exit').read_text().strip()=='0'
base=raw/'whole-output';validator=study/'ci_induced_transfer/validate_receipts_01.py'
tests=[]
for name in ['missing-named-root','missing-structural-declaration','missing-exact-binding','altered-binding-verdict']:
 d=raw/('negative-'+name);shutil.copytree(base,d)
 (d/'whole-proof-coverage-and-bindings.json').unlink()
 if name.startswith('missing-')and name!='missing-exact-binding':
  audit=next((d/'consumer-proofs').rglob('audit.log'))
  target='InducedFullTransfer.induced_reverse_norms'if name=='missing-named-root'else'InducedFullTransfer.Presentation.phi_add'
  lines=audit.read_text().splitlines(keepends=True);removed=[line for line in lines if line.startswith('ok')and target in line];assert len(removed)==1
  audit.write_text(''.join(line for line in lines if line not in removed))
 elif name=='missing-exact-binding':next(d.glob('binding-*.txt')).unlink()
 else:
  f=next(d.glob('binding-*.txt'));row=json.loads(f.read_text());assert row['verdict']=='pass';row['verdict']='fail';f.write_text(json.dumps(row,indent=2)+'\n')
 cmd=['python3',str(validator),str(raw/'cryptanalysis'),str(d)]
 with(raw/(name+'.txt')).open('xb')as log:q=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 (raw/(name+'.exit')).write_text(str(q.returncode)+'\n');assert q.returncode==1 and not(d/'whole-proof-coverage-and-bindings.json').exists()
 tests.append(dict(case=name,actual_exit=q.returncode,no_accepted_output=True,command=cmd));print(name,q.returncode,flush=True)
(raw/'receipt-negative-controls.json').write_text(json.dumps(tests,indent=2)+'\n');shutil.copyfile(__file__,raw/'actual-negative-control-command.py')
