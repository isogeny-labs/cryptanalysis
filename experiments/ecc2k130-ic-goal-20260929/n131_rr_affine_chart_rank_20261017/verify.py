"""Read-only proof, source and exact outcome verification."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
ROOT=D.parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
t=json.loads((D/'terminal.json').read_text())
for name,digest in t['files'].items():
    assert sha(D/name)==digest,name
p=json.loads((D/'protocol.json').read_text())
parent=ROOT/'n41_n131_sixpair_rr_root_span_20261016/frozen_panels.json'
count=ROOT/'n131_w23_sixpair_density_20261016/run_result.json'
rr=ROOT/'n41_n131_sixpair_rr_root_span_20261016/run.py'
assert p['source_sha256']=={
    'parent_panel':sha(parent),'w23_count':sha(count),'rr_kernel':sha(rr),
    'preparer':sha(D/'prepare.py'),'screen':sha(D/'screen.py'),
    'auditor':sha(D/'audit_sage.py')}
assert t['external']==p['source_sha256']
panel=json.loads((D/'panel.json').read_text())
r=json.loads((D/'result.json').read_text())
a=json.loads((D/'audit_result.json').read_text())
gp=json.loads((D/'group_protocol.json').read_text())
g=json.loads((D/'group_audit_result.json').read_text())
cp=json.loads((D/'column_protocol.json').read_text())
c=json.loads((D/'column_audit_result.json').read_text())
assert sha(D/'protocol.json')==panel['protocol_sha256']==r['protocol_sha256']==a['protocol_sha256']
assert sha(D/'panel.json')==r['panel_sha256']==gp['panel_sha256']
assert sha(D/'result.json')==a['producer_sha256']==gp['rank_result_sha256']
assert sha(D/'audit_result.json')==gp['determinant_audit_sha256']
assert sha(D/'group_audit_sage.py')==gp['group_audit_source_sha256']
assert sha(D/'group_protocol.json')==g['group_protocol_sha256']
assert sha(D/'panel.json')==cp['panel_sha256']==c['panel_sha256']
assert sha(D/'column_audit_sage.py')==cp['source_sha256']
assert sha(D/'column_protocol.json')==c['protocol_sha256']
assert [x['pooled_nonconstant_rank'] for x in r['rows']]==[34,68,102,131,131,131,131,131]
assert [x['pooled_nonconstant_rank'] for x in a['rows']]==[34,68,102,131,131,131,131,131]
assert r['first_failed_chart']==3
assert [x['common_linear_certificate'] for x in r['rows']]==[True,True,True,False,False,False,False,False]
assert all(not x['determinant_zero_sign_masks'] for x in r['rows'])
assert all(not x['group_matches'] for x in g['rows']) and g['total_signs_checked']==512
assert len(set(panel['selection']['columns']))==8
assert c['all_distinct_columns'] and c['selected_columns']==panel['selection']['columns']
assert 'constant_in_span_not_separable' in (D/'lean.stdout').read_text()
print('PASS affine source, independent determinant and group replays, rank obstruction, Lean receipt')
