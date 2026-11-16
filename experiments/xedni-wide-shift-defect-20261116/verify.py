"""Verify the sealed wide-shift receipts and rerun independent arithmetic."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

H=Path(__file__).resolve().parent
seal=(H/'SEAL.sha256').read_text().splitlines()
names=[]
for line in seal:
    digest,name=line.split('  ',1)
    assert hashlib.sha256((H/name).read_bytes()).hexdigest()==digest,name
    names.append(name)
assert len(names)==len(set(names))
assert set(names)=={p.name for p in H.iterdir() if p.is_file() and p.name!='SEAL.sha256'}
P=json.loads((H/'protocol.json').read_text())
R=json.loads((H/'run-result.json').read_text())
assert R['status']=='complete'
assert R['protocol_sha256']==hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()
assert R['counts']=={'admitted_hits':22,'candidate_attempts':13750,
                     'candidate_failure':0,'candidate_pass':13750,
                     'rational_controls':13750,'rational_relation_hits':0}
assert len(R['candidate_parts'])==22
assert (H/'run.stderr').read_bytes()==b'' and (H/'audit.stderr').read_bytes()==b''
assert json.loads((H/'sage-runtime.json').read_text())['status']=='verified'
run=json.loads((H/'run.stdout').read_text())
assert run['status']=='complete' and run['counts']==R['counts']
assert run['elapsed_wall_seconds']==R['elapsed_wall_seconds']
source=H.parent/'xedni-height-selected-two-image-20261116'
for name,digest in P['parent_sha256'].items():
    assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest
replay=subprocess.run([sys.executable,str(H/'audit.py')],capture_output=True,text=True,check=True)
assert replay.stderr=='' and replay.stdout==(H/'audit.stdout').read_text()
assert json.loads(replay.stdout)==json.loads((H/'audit.json').read_text())
assert json.loads(replay.stdout)['status']=='PASS'
print(json.dumps({'status':'PASS','sealed_files':len(seal),
                  'candidate_attempts':13750,'rational_relation_hits':0},sort_keys=True))
