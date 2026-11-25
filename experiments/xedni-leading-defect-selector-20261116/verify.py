"""Check frozen receipts, rebuild Lean, and replay every public/candidate row."""
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
actual={str(path.relative_to(H)) for path in H.rglob('*')
        if path.is_file() and '.lake' not in path.parts and path.name!='SEAL.sha256'}
assert set(names)==actual,(set(names)^actual)

P=json.loads((H/'protocol.json').read_text())
R=json.loads((H/'run-result.json').read_text())
assert R['schema']=='xedni-leading-defect-selector-result-v1' and R['status']=='complete'
assert R['protocol_sha256']==hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()
assert R['counts']=={'queries':512,'vector_tests':6656,'public_hits':18,
                     'candidate_attempts':11250,'candidate_pass':11250,
                     'candidate_failure':0,'rational_controls':11250,
                     'qproxy_controls':22500,'rational_hits':0,
                     'proxy_selection_events':18,'equal_x_hits':0,
                     'prediction_pass':11250,'prediction_fail':0}
assert len(R['candidate_parts'])==18
assert (H/'run.stderr').read_bytes()==b'' and (H/'audit.stderr').read_bytes()==b''
assert json.loads((H/'sage-runtime.json').read_text())['status']=='verified'
for field,filename in [('source_protocol_sha256','xedni-height-selected-two-image-20261116'),
                       ('prior_proxy_protocol_sha256','xedni-qdefect-proxy-20261116')]:
    path=H.parent/filename/'protocol.json'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==P[field]
run=json.loads((H/'run.stdout').read_text())
assert run['status']=='complete' and run['counts']==R['counts'] and run['stages']==R['stages']
assert run['family_depth_improvements']==1

replay=subprocess.run([sys.executable,str(H/'audit.py')],capture_output=True,text=True,check=True)
assert replay.stderr=='' and replay.stdout==(H/'audit.stdout').read_text()
assert json.loads(replay.stdout)==json.loads((H/'audit.json').read_text())
assert json.loads(replay.stdout)['status']=='PASS'

formal=H/'formal'
build=subprocess.run(['lake','build','LeadingDefect'],cwd=formal,capture_output=True,text=True,check=True)
axioms=subprocess.run(['lake','env','lean','LeadingDefect.lean'],cwd=formal,capture_output=True,text=True,check=True)
assert 'Build completed successfully' in build.stdout+build.stderr
assert 'leading_linear_combination' in axioms.stdout+axioms.stderr
assert 'leading_cancellation_iff_kernel' in axioms.stdout+axioms.stderr
assert 'propext, Quot.sound' in axioms.stdout+axioms.stderr
assert 'sorryAx' not in axioms.stdout+axioms.stderr
print(json.dumps({'status':'PASS','sealed_files':len(lines),'candidate_attempts':11250,
                  'prediction_matches':11250,'family_improved_hits':1},sort_keys=True))
