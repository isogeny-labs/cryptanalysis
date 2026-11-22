"""Freeze exact unpinned N41 output-first gate before N131 promotion."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((H/'n41_gate_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_UNPINNED_N41_OUTPUT_FIRST_GATE'
for label,s in cfg['sources'].items():assert sha(s['path'])==s['sha256'],label
for name in ('n41_protocol.json','n41_audit_protocol.json'):
    p=json.loads((H/name).read_text())
    for label,s in p['sources'].items():assert sha(s['path'])==s['sha256'],(name,label)
producer=json.loads((H/'n41_result.json').read_text())
audit=json.loads((H/'n41_audit_result.json').read_text())
receipt=json.loads((H/'n41_audit_receipt.json').read_text())
prior=json.loads(Path(cfg['sources']['prior_relation']['path']).read_text())
assert producer['status']=='COMPLETE_OUTPUT_FIRST_FIFTH'
assert producer['boxes_completed']==9 and producer['source_product_rank']==10
assert producer['public_relations']==0
assert all(r['prefix_assignments']==256 for r in producer['rows'])
assert sum(r['status_counts'].get('OUTSIDE_PRODUCT_SUBSPACE',0) for r in producer['rows'])==2303
positive=producer['rows'][0]['verified_relations']
assert len(positive)==1
assert positive[0]['prefix_choice_indices']==[0,1,1,1]
assert positive[0]['first_four_codes']==[96,783,555,253]
assert positive[0]['last_code']==63
assert len(set(positive[0]['factor_columns']))==10
assert prior['status']=='PASS_INDEPENDENT_N41_W11_FIVEPAIR_PUBLIC_RELATION'
assert audit['status']=='PASS_INDEPENDENT_OUTPUT_FIRST_SAGE_AUDIT'
assert audit['residuals_checked']==2304 and audit['verified_relations']==1
assert receipt['status']=='COMPLETE' and receipt['exit_code']==0
assert receipt['stop_reason'] is None and receipt['monitor_error'] is None
assert receipt['wall_seconds']<120 and receipt['sampled_peak_combined_rss_bytes']<4294967296
assert receipt['command'][0]=='/Volumes/SSD990/cryptanalysis/sage'
assert receipt['result_sha256']==sha(H/'n41_audit_result.json')
assert receipt['stdout_sha256']==sha(H/'n41_audit.stdout')
assert receipt['stderr_sha256']==sha(H/'n41_audit.stderr')
assert (H/'n41_audit.stderr').read_bytes()==b''
result={'status':'PASS_UNPINNED_N41_OUTPUT_FIRST_GATE','candidate_id':None,
        'curve_id':producer['curve_id'],'residuals_checked':2304,
        'recovered_last_code':63,'independent_sage_audit':True,
        'protocol_sha256':sha(H/'n41_gate_protocol.json'),
        'verifier_sha256':sha(Path(__file__))}
(H/'n41_gate.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
