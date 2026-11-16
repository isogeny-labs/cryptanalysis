"""Verify sealed two-image shift-grid receipts and rerun the independent audit."""
from pathlib import Path
import hashlib,json,subprocess,sys
H=Path(__file__).resolve().parent
seal=(H/'SEAL.sha256').read_text().splitlines()
for line in seal:
    digest,name=line.split('  ',1)
    assert hashlib.sha256((H/name).read_bytes()).hexdigest()==digest,name
result=json.loads((H/'run-result.json').read_text())
assert result['status']=='complete'
assert result['counts']=={'source_public_attempts':6656,'positive_events':17,'control_events':32,
 'candidate_attempts':3969,'candidate_pass':3969,'candidate_failure':0,
 'rational_hits_positive':0,'rational_hits_control':0,'centered_parent_matches':49}
assert (H/'run.stderr').read_bytes()==b''
replay=subprocess.run([sys.executable,str(H/'audit.py')],capture_output=True,text=True,check=True)
assert replay.stderr=='' and replay.stdout==(H/'audit.stdout').read_text()
assert json.loads(replay.stdout)['status']=='PASS'
assert (H/'audit.stderr').read_bytes()==b''
print(json.dumps({'status':'PASS','sealed_files':len(seal),'public_tests':6656,
                  'candidate_attempts':3969,'rational_hits':0},sort_keys=True))
