"""Exact shared-linear RR certificate rank across affine source-code charts."""
import hashlib
import importlib.util
import json
import resource
import signal
import time
from pathlib import Path

D=Path(__file__).resolve().parent
ROOT=D.parent
RR=ROOT/'n41_n131_sixpair_rr_root_span_20261016/run.py'
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
p=json.loads((D/'protocol.json').read_text())
assert sha(D/'screen.py')==p['source_sha256']['screen']
assert sha(RR)==p['source_sha256']['rr_kernel']
panel=json.loads((D/'panel.json').read_text())
assert panel['status']=='FROZEN_N131_AFFINE_FOUR_CODE_PANEL'
signal.alarm(p['wall_cap_s'])
start=time.monotonic()
spec=importlib.util.spec_from_file_location('rr',RR)
rr=importlib.util.module_from_spec(spec);spec.loader.exec_module(rr)
field=rr.Field(131,(1<<131)|(1<<13)|7)
def insert(basis,value):
    while value:
        k=value.bit_length()-1
        if k in basis:value^=basis[k]
        else:basis[k]=value;break
nonbasis={};values={};augmented={};rows=[]
for code,roots in enumerate(panel['selection']['roots']):
    for root in (0,1):
        points=[roots[root][0]]+panel['fixed_points']
        coefficients=rr.coefficients([x[0] for x in points],
                                      [x[1] for x in points],panel['target'],field)
        assert coefficients is not None
        assert all(coefficients[k]==0 for k in range(64) if rr.popcount(k)>3)
        local={}
        for k in range(1,64):
            if rr.popcount(k)<=3:
                x=coefficients[k]
                insert(local,x);insert(nonbasis,x)
                insert(values,x);insert(augmented,x<<1)
        insert(values,coefficients[0]);insert(augmented,(coefficients[0]<<1)|1)
        rows.append({'code':code,'root':root,
                     'mask':panel['selection']['masks'][code],
                     'local_nonconstant_rank':len(local),
                     'pooled_nonconstant_rank':len(nonbasis),
                     'pooled_value_rank':len(values),
                     'pooled_augmented_rank':len(augmented),
                     'common_linear_certificate':len(values)==len(augmented),
                     'determinant_zero_sign_masks':[s for s in range(64)
                                                    if rr.evaluate(coefficients,s)==0],
                     'coefficients_sha256':hashlib.sha256(
                         json.dumps(coefficients).encode()).hexdigest()})
result={'status':'COMPLETE_N131_AFFINE_RR_RANK_SCREEN','candidate_id':None,
        'rows':rows,
        'first_failed_chart':next((i for i,row in enumerate(rows)
                                   if not row['common_linear_certificate']),None),
        'wall_s':time.monotonic()-start,
        'self_peak_rss_bytes_darwin':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(D/'protocol.json'),
        'panel_sha256':sha(D/'panel.json')}
with (D/'result.json').open('x') as out:
    json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(json.dumps({'status':result['status'],'first_failed_chart':result['first_failed_chart'],
                  'ranks':[row['pooled_nonconstant_rank'] for row in rows]},sort_keys=True))
