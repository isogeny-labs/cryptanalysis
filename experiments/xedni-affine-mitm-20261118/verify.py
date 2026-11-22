"""Check sealed affine lookup receipts and full-grid independent replay."""
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
assert R['schema']=='xedni-affine-mitm-result-v1' and R['status']=='complete'
assert R['protocol_sha256']==hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()
assert R['counts']=={'queries':512,'vector_tests':6656,'public_hits':19,
                     'equal_x_hits':0,'candidate_attempts':2596,'candidate_pass':2596,
                     'candidate_failure':0,'qprobe_controls':190,
                     'selected_qconfirm_controls':38,'rational_controls':19,
                     'rational_hits':0,'left_pairs':931,'right_pairs':931,
                     'lookup_matches':105,'fallback_hits':1,
                     'selected_prediction_pass':19,'selected_prediction_fail':0}
assert len(R['candidate_parts'])==19
assert (H/'run.stderr').read_bytes()==b'' and (H/'audit.stderr').read_bytes()==b''
assert json.loads((H/'sage-runtime.json').read_text())['status']=='verified'
for field,filename in [('source_protocol_sha256','xedni-height-selected-two-image-20261116'),
                       ('prior_proxy_protocol_sha256','xedni-qdefect-proxy-20261116'),
                       ('prior_leading_protocol_sha256','xedni-leading-defect-selector-20261116'),
                       ('prior_aware_protocol_sha256','xedni-vector-aware-selector-20261116'),
                       ('prior_width_protocol_sha256','xedni-vector-aware-width-20261116'),
                       ('prior_affine_protocol_sha256','xedni-affine-leading-defect-20261116')]:
    path=H.parent/filename/'protocol.json'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==P[field]
run=json.loads((H/'run.stdout').read_text())
assert run['status']=='complete' and run['counts']==R['counts'] and run['stages']==R['stages']
assert run['selected_depth2_hits']==18
assert sum(s['candidate_attempts'] for s in R['summaries'] if not s['fallback'])==195
replay=subprocess.run([sys.executable,str(H/'audit.py')],capture_output=True,text=True,check=True)
assert replay.stderr=='' and replay.stdout==(H/'audit.stdout').read_text()
assert json.loads(replay.stdout)==json.loads((H/'audit.json').read_text())
audit=json.loads(replay.stdout)
assert audit['status']=='PASS' and audit['lookup_mismatches']==0
assert audit['affine_mismatches']==0 and audit['full_grid_models']==45619
assert audit['selected_depth2_hits']==18
assert audit['residual_depth_histogram']=={'1':45514,'2':105}
print(json.dumps({'status':'PASS','sealed_files':len(lines),
                  'producer_models':2596,'audit_models':45619,'selected_depth2_hits':18},sort_keys=True))
