"""Check sealed paired-width receipts and replay the full candidate panel."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

H=Path(__file__).resolve().parent
lines=(H/'SEAL.sha256').read_text().splitlines()
names=[]
for line in lines:
    digest,name=line.split('  ',1)
    assert hashlib.sha256((H/name).read_bytes()).hexdigest()==digest,name
    names.append(name)
assert len(names)==len(set(names))
assert set(names)=={p.name for p in H.iterdir() if p.is_file() and p.name!='SEAL.sha256'}

P=json.loads((H/'protocol.json').read_text())
R=json.loads((H/'run-result.json').read_text())
assert R['schema']=='xedni-vector-aware-width-result-v1' and R['status']=='complete'
assert R['protocol_sha256']==hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()
assert R['counts']=={'queries':512,'vector_tests':6656,'public_hits':27,
                     'candidate_attempts':64827,'candidate_pass':64827,
                     'candidate_failure':0,'rational_controls':64827,
                     'qproxy_controls':129654,'rational_hits':0,
                     'proxy_selection_events':27,'equal_x_hits':0,
                     'prediction_pass':64827,'prediction_fail':0}
assert len(R['candidate_parts'])==27
assert (H/'run.stderr').read_bytes()==b'' and (H/'audit.stderr').read_bytes()==b''
assert json.loads((H/'sage-runtime.json').read_text())['status']=='verified'
for field,filename in [('source_protocol_sha256','xedni-height-selected-two-image-20261116'),
                       ('prior_proxy_protocol_sha256','xedni-qdefect-proxy-20261116'),
                       ('prior_leading_protocol_sha256','xedni-leading-defect-selector-20261116'),
                       ('prior_aware_protocol_sha256','xedni-vector-aware-selector-20261116')]:
    path=H.parent/filename/'protocol.json'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==P[field]
run=json.loads((H/'run.stdout').read_text())
assert run['status']=='complete' and run['counts']==R['counts'] and run['stages']==R['stages']
assert run['wide_vs_narrow_improvements']==4
assert R['stages']['narrow_qproxy_seconds']<R['stages']['qproxy_seconds']
replay=subprocess.run([sys.executable,str(H/'audit.py')],capture_output=True,text=True,check=True)
assert replay.stderr=='' and replay.stdout==(H/'audit.stdout').read_text()
assert json.loads(replay.stdout)==json.loads((H/'audit.json').read_text())
audit=json.loads(replay.stdout)
assert audit['status']=='PASS' and audit['wide_vs_narrow_improvements']==4
assert audit['wide_vs_narrow_worsenings']==0
assert audit['narrow_no_cancellation_hits']==7 and audit['wide_no_cancellation_hits']==3
print(json.dumps({'status':'PASS','sealed_files':len(lines),
                  'candidate_attempts':64827,'wide_improved_hits':4},sort_keys=True))
