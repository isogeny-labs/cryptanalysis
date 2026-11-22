"""Freeze source-bound affine W23 selection and RR rank experiment."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
ROOT=D.parent
PARENT=ROOT/'n41_n131_sixpair_rr_root_span_20261016/frozen_panels.json'
COUNT=ROOT/'n131_w23_sixpair_density_20261016/run_result.json'
RR=ROOT/'n41_n131_sixpair_rr_root_span_20261016/run.py'
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
parent=json.loads(PARENT.read_text())['n131']
count=json.loads(COUNT.read_text())['worker_result']
assert parent['edges'][0]['masks']==[3,898617]
assert count['seed_mask']==898618
record={'schema':1,'candidate_id':None,
        'curve_id':'EC1N131Ckb1heb5f1998f20b',
        'seed_mask':898618,'anchor_mask':3,
        'direction_policy':'nonpivot unit directions in ascending bit order, then weight-two directions in ascending mask order; first eligible affine square containing anchor',
        'required':'all four codes source-valid, eight orbit columns distinct and disjoint from fixed five edges, all seven determinant x coordinates distinct for both roots',
        'chart_order':'code order [a,a xor d1,a xor d2,a xor d1 xor d2], then root 0 and root 1 per code',
        'source_sha256':{'parent_panel':sha(PARENT),'w23_count':sha(COUNT),
                         'rr_kernel':sha(RR),'preparer':sha(D/'prepare.py'),
                         'screen':sha(D/'screen.py'),'auditor':sha(D/'audit_sage.py')},
        'worker_count':1,'wall_cap_s':600,'rss_cap_bytes':4*1024**3}
with (D/'protocol.json').open('x') as out:
    json.dump(record,out,sort_keys=True,indent=2);out.write('\n')
print(sha(D/'protocol.json'))
