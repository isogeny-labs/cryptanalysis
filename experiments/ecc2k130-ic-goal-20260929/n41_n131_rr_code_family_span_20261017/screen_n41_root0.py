"""Screen whether one RR trace separator covers a free N41 pair code."""
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
protocol=json.loads((HERE/'protocol_n41_root0.json').read_text())
for path,digest in protocol['sources'].items():assert sha(path)==digest,path
g=json.loads((ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json').read_text())
hit=json.loads((ROOT/'n41_sixpair_shared_target_20261017/join_audit_result.json').read_text())
target=hit['raw_target']
assert target==protocol['target'] and len(hit['pair_rows'])==6
F=rr.Field(41,(1<<41)|(1<<3)|1)

def roots(block,mask):
    rows=[row for row in block['states'] if row['a']==mask]
    assert len(rows)==4
    by_x={}
    for row in rows:
        x,y=row['raw_sum'];by_x.setdefault(x,set()).add(y)
    assert len(by_x)==2 and all(len(y)==2 for y in by_x.values())
    return [[[x,y] for y in sorted(by_x[x])] for x in sorted(by_x)]

fixed=[]
for slot in range(1,6):
    witness=hit['pair_rows'][slot]
    choices=roots(g['blocks'][slot],witness['masks'][0])
    matching=[root for root in choices if witness['raw_sum'] in root]
    assert len(matching)==1
    fixed.append(matching[0][0])

def insert(basis,value):
    while value:
        p=value.bit_length()-1
        if p in basis:value^=basis[p]
        else:basis[p]=value;break

def rank(basis):return len(basis)
rows=[]
for mask in g['permitted_canonical_a']:
    edge_cols={g['mask_columns'][str(mask)],g['mask_columns'][str(mask^56)]}
    used={col for row in hit['pair_rows'][1:] for col in row['columns']}
    if edge_cols&used:continue
    for root_index,root in enumerate(roots(g['blocks'][0],mask)[:1]):
        points=[root[0]]+fixed
        c=rr.coefficients([p[0] for p in points],[p[1] for p in points],target,F)
        if c is None:
            rows.append({'mask':mask,'root':root_index,'status':'DUPLICATE_X_EXCEPTION'})
            continue
        non=[c[k] for k in range(1,64) if rr.popcount(k)<=3]
        local={};[insert(local,x) for x in non]
        rows.append({'mask':mask,'root':root_index,'status':'VALID_CHART','constant':c[0],
                     'nonconstant':non,'local_rank':rank(local),
                     'zeros':[s for s in range(64) if rr.evaluate(c,s)==0]})
assert len(rows)>0
valid=[row for row in rows if row['status']=='VALID_CHART']
base=[]
for row in valid:
    v={};aug={};nonbasis={}
    for old in base+[row]:
        for x in old['nonconstant']:insert(v,x);insert(aug,x<<1);insert(nonbasis,x)
        insert(v,old['constant']);insert(aug,(old['constant']<<1)|1)
    row['prefix_rank']=rank(v);row['prefix_augmented_rank']=rank(aug)
    row['prefix_nonconstant_rank']=rank(nonbasis)
    row['shared_functional_exists']=rank(v)==rank(aug)
    base.append(row)
result={'status':'COMPLETE_N41_ROOT0_CODE_FAMILY_CERTIFICATE_SCREEN','target':target,
        'valid_charts':len(valid),'exceptional_charts':len(rows)-len(valid),
        'first_failed_prefix':next((i+1 for i,r in enumerate(valid) if not r['shared_functional_exists']),None),
        'first_full_nonconstant_rank':next((i+1 for i,r in enumerate(valid) if r['prefix_nonconstant_rank']==41),None),
        'rows':[{k:v for k,v in row.items() if k not in ('nonconstant','constant')} for row in rows],
        'protocol_sha256':sha(HERE/'protocol_n41_root0.json')}
with (HERE/'result_n41_root0.json').open('x') as out:json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(json.dumps({k:result[k] for k in ('status','valid_charts','exceptional_charts','first_failed_prefix','first_full_nonconstant_rank')}))
