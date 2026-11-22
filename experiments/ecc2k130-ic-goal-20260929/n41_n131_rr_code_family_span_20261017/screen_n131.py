"""Rank of exact RR sign coefficients across three first-code variants."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
source=ROOT/'n41_n131_sixpair_rr_root_span_20261016/run.py'
spec=importlib.util.spec_from_file_location('rr',source)
rr=importlib.util.module_from_spec(spec);spec.loader.exec_module(rr)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((HERE/'protocol_n131.json').read_text())
for path,digest in protocol['sources'].items():assert sha(path)==digest,path
panel=json.loads((HERE/'panel_n131.json').read_text())
assert panel['status']=='FROZEN_N131_FIRST_CODE_VARIANTS'
field=rr.Field(panel['field_degree'],panel['field_modulus'])
target=panel['target']
def insert(basis,value):
    while value:
        p=value.bit_length()-1
        if p in basis:value^=basis[p]
        else:basis[p]=value;break

nonbasis={};values={};augmented={};rows=[]
for variant in panel['variants']:
    point=variant['roots'][0][0]
    points=[point]+panel['fixed_points']
    c=rr.coefficients([p[0] for p in points],[p[1] for p in points],target,field)
    if c is None:
        rows.append({'sample_index':variant['sample_index'],'status':'DUPLICATE_X_EXCEPTION'})
        continue
    non=[c[k] for k in range(1,64) if rr.popcount(k)<=3]
    local={}
    for x in non:
        insert(local,x);insert(nonbasis,x);insert(values,x);insert(augmented,x<<1)
    insert(values,c[0]);insert(augmented,(c[0]<<1)|1)
    rows.append({'sample_index':variant['sample_index'],'status':'VALID_CHART',
                 'local_nonconstant_rank':len(local),'pooled_nonconstant_rank':len(nonbasis),
                 'pooled_rank':len(values),'pooled_augmented_rank':len(augmented),
                 'shared_functional_exists':len(values)==len(augmented),
                 'determinant_zero_sign_masks':[s for s in range(64) if rr.evaluate(c,s)==0],
                 'coefficient_sha256':hashlib.sha256(json.dumps(c).encode()).hexdigest()})
result={'status':'COMPLETE_N131_CODE_FAMILY_CERTIFICATE_SCREEN',
        'protocol_sha256':sha(HERE/'protocol_n131.json'),'rows':rows,
        'first_failed_prefix':next((i+1 for i,row in enumerate(rows)
                                    if row['status']=='VALID_CHART' and not row['shared_functional_exists']),None)}
with (HERE/'result_n131.json').open('x') as out:
    json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(json.dumps(result))
