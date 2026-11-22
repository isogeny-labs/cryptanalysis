"""Check sealed jet receipts, Lean proof, and independent full-grid replay."""
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
actual={str(p.relative_to(H)) for p in H.rglob('*')
        if p.is_file() and '.lake' not in p.parts and p.name!='SEAL.sha256'}
assert set(names)==actual,(set(names)^actual)
P=json.loads((H/'protocol.json').read_text())
R=json.loads((H/'run-result.json').read_text())
assert R['schema']=='xedni-jacobian-jet-result-v1' and R['status']=='complete'
assert R['protocol_sha256']==hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()
assert R['counts']=={'queries':512,'vector_tests':6656,'public_hits':14,
                     'equal_x_hits':0,'candidate_attempts':7303,'candidate_pass':7303,
                     'candidate_failure':0,'jet_attempt_hits':14,'jet_qmultiples':28,
                     'jet_failure_hits':0,'modular_fallback_hits':0,
                     'mod_probe_validation_controls':140,'qprobe_validation_controls':140,
                     'selected_qconfirm_controls':28,'rational_controls':14,
                     'rational_hits':0,'left_pairs':686,'right_pairs':686,
                     'lookup_matches':45,'fallback_hits':3,
                     'selected_prediction_pass':14,'selected_prediction_fail':0}
assert len(R['candidate_parts'])==14
assert (H/'run.stderr').read_bytes()==b'' and (H/'audit.stderr').read_bytes()==b''
assert json.loads((H/'sage-runtime.json').read_text())['status']=='verified'
for field,filename in [('source_protocol_sha256','xedni-height-selected-two-image-20261116'),
                       ('prior_proxy_protocol_sha256','xedni-qdefect-proxy-20261116'),
                       ('prior_leading_protocol_sha256','xedni-leading-defect-selector-20261116'),
                       ('prior_aware_protocol_sha256','xedni-vector-aware-selector-20261116'),
                       ('prior_width_protocol_sha256','xedni-vector-aware-width-20261116'),
                       ('prior_affine_protocol_sha256','xedni-affine-leading-defect-20261116'),
                       ('prior_mitm_protocol_sha256','xedni-affine-mitm-20261118'),
                       ('prior_modp2_protocol_sha256','xedni-modp2-affine-20261118')]:
    path=H.parent/filename/'protocol.json'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==P[field]
run=json.loads((H/'run.stdout').read_text())
assert run['status']=='complete' and run['counts']==R['counts'] and run['stages']==R['stages']
assert run['selected_depth2_hits']==11
assert sum(s['candidate_attempts'] for s in R['summaries'] if not s['fallback'])==100
replay=subprocess.run([sys.executable,str(H/'audit.py')],capture_output=True,text=True,check=True)
assert replay.stderr=='' and replay.stdout==(H/'audit.stdout').read_text()
assert json.loads(replay.stdout)==json.loads((H/'audit.json').read_text())
audit=json.loads(replay.stdout)
assert audit['status']=='PASS' and audit['lookup_mismatches']==0
assert audit['affine_mismatches']==0 and audit['full_grid_models']==33614
assert audit['selected_depth2_hits']==11
assert audit['residual_depth_histogram']=={'1':33569,'2':45}
formal=H/'formal'
build=subprocess.run(['lake','build','FirstOrderJet'],cwd=formal,
                     capture_output=True,text=True,check=True)
axioms=subprocess.run(['lake','env','lean','FirstOrderJet.lean'],cwd=formal,
                      capture_output=True,text=True,check=True)
assert 'Build completed successfully' in build.stdout+build.stderr
assert 'first_order_product' in axioms.stdout+axioms.stderr
assert 'axioms: [propext]' in axioms.stdout+axioms.stderr
assert 'sorryAx' not in axioms.stdout+axioms.stderr
print(json.dumps({'status':'PASS','sealed_files':len(lines),'producer_models':7303,
                  'audit_models':33614,'selected_depth2_hits':11},sort_keys=True))
