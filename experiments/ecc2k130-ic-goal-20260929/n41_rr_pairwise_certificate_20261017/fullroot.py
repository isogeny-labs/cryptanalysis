"""Test one certificate across both x roots of each eligible first-slot code."""
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((HERE/'fullroot_protocol.json').read_text())
for path,digest in protocol['sources'].items():assert sha(path)==digest,path
source=ROOT/'n41_n131_sixpair_rr_root_span_20261016/run.py'
spec=importlib.util.spec_from_file_location('rr',source)
rr=importlib.util.module_from_spec(spec);spec.loader.exec_module(rr)
g=json.loads((ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json').read_text())
hit=json.loads((ROOT/'n41_sixpair_shared_target_20261017/join_audit_result.json').read_text())
base=json.loads((HERE/'result.json').read_text())
F=rr.Field(41,(1<<41)|(1<<3)|1)
def roots(block,mask):
    by_x={}
    for row in block['states']:
        if row['a']==mask:
            x,y=row['raw_sum'];by_x.setdefault(x,set()).add(y)
    assert len(by_x)==2 and all(len(ys)==2 for ys in by_x.values())
    return [[[x,y] for y in sorted(by_x[x])] for x in sorted(by_x)]
fixed=[]
for slot in range(1,6):
    row=hit['pair_rows'][slot]
    options=roots(g['blocks'][slot],row['masks'][0])
    fixed.append(next(root[0] for root in options if row['raw_sum'] in root))
rows=[]
for first in base['charts']:
    point=roots(g['blocks'][0],first['mask'])[1][0]
    points=[point]+fixed
    c=rr.coefficients([p[0] for p in points],[p[1] for p in points],hit['raw_target'],F)
    assert c is not None
    non=[c[k] for k in range(1,64) if rr.popcount(k)<=3]
    ordinary=first['nonconstant']+non+[first['constant'],c[0]]
    labels=[0]*(len(first['nonconstant'])+len(non))+[1,1]
    rank=len(rr.rank_basis(ordinary))
    augmented=len(rr.rank_basis([(v<<1)|bit for v,bit in zip(ordinary,labels)]))
    row={'mask':first['mask'],'root1_point':point,'root1_coefficients':c,
         'root1_coefficient_sha256':hashlib.sha256(json.dumps(c).encode()).hexdigest(),
         'root1_local_rank':len(rr.rank_basis(non)),
         'two_root_nonconstant_rank':len(rr.rank_basis(first['nonconstant']+non)),
         'two_root_rank':rank,'two_root_augmented_rank':augmented,
         'shared_functional_exists':rank==augmented,
         'root1_zero_signs':[s for s in range(64) if rr.evaluate(c,s)==0]}
    rows.append(row)
result={'status':'COMPLETE_N41_BOTH_ROOTS_CERTIFICATE_CENSUS',
        'code_count':len(rows),'certifiable_codes':sum(r['shared_functional_exists'] for r in rows),
        'rank_distribution':dict(sorted(Counter(r['two_root_nonconstant_rank'] for r in rows).items())),
        'rows':rows,'protocol_sha256':sha(HERE/'fullroot_protocol.json')}
with (HERE/'fullroot_result.json').open('x') as out:json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(json.dumps({k:result[k] for k in ('status','code_count','certifiable_codes','rank_distribution')}))
