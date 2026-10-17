"""Exact N41 pairwise coverage census for RR trace certificates."""
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((HERE/'protocol.json').read_text())
for path,digest in protocol['sources'].items():assert sha(path)==digest,path
source=ROOT/'n41_n131_sixpair_rr_root_span_20261016/run.py'
spec=importlib.util.spec_from_file_location('rr',source)
rr=importlib.util.module_from_spec(spec);spec.loader.exec_module(rr)
g=json.loads((ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json').read_text())
hit=json.loads((ROOT/'n41_sixpair_shared_target_20261017/join_audit_result.json').read_text())
target=hit['raw_target']
assert target==protocol['raw_target']
F=rr.Field(41,(1<<41)|(1<<3)|1)

def roots(block,mask):
    rows=[row for row in block['states'] if row['a']==mask]
    assert len(rows)==4
    by_x={}
    for row in rows:
        x,y=row['raw_sum'];by_x.setdefault(x,set()).add(y)
    assert len(by_x)==2 and all(len(ys)==2 for ys in by_x.values())
    return [[[x,y] for y in sorted(by_x[x])] for x in sorted(by_x)]

def rank(values):return len(rr.rank_basis(values))
def certifiable(charts):
    values=[];labels=[]
    for chart in charts:
        values.extend(chart['nonconstant']);labels.extend([0]*len(chart['nonconstant']))
        values.append(chart['constant']);labels.append(1)
    ordinary=rank(values)
    augmented=rank([(v<<1)|b for v,b in zip(values,labels)])
    return {'nonconstant_rank':rank([v for chart in charts for v in chart['nonconstant']]),
            'ordinary_rank':ordinary,'augmented_rank':augmented,
            'common_functional_exists':ordinary==augmented}

fixed=[]
for slot in range(1,6):
    row=hit['pair_rows'][slot]
    choices=roots(g['blocks'][slot],row['masks'][0])
    matches=[root for root in choices if row['raw_sum'] in root]
    assert len(matches)==1
    fixed.append(matches[0][0])
used={column for row in hit['pair_rows'][1:] for column in row['columns']}
charts=[]
for mask in g['permitted_canonical_a']:
    cols={g['mask_columns'][str(mask)],g['mask_columns'][str(mask^56)]}
    if cols&used:continue
    point=roots(g['blocks'][0],mask)[0][0]
    points=[point]+fixed
    c=rr.coefficients([p[0] for p in points],[p[1] for p in points],target,F)
    assert c is not None
    non=[c[k] for k in range(1,64) if rr.popcount(k)<=3]
    chart={'mask':mask,'point':point,'constant':c[0],'nonconstant':non,
           'zero_signs':[s for s in range(64) if rr.evaluate(c,s)==0],
           'coefficient_sha256':hashlib.sha256(json.dumps(c).encode()).hexdigest()}
    chart.update(certifiable([chart]))
    chart['coefficients']=c
    charts.append(chart)
assert len(charts)==35
pairs=[]
for i,left in enumerate(charts):
    for j in range(i+1,len(charts)):
        row={'masks':[left['mask'],charts[j]['mask']]}
        row.update(certifiable([left,charts[j]]))
        pairs.append(row)
assert len(pairs)==595
result={'status':'COMPLETE_N41_RR_PAIRWISE_CENSUS','candidate_id':None,
        'raw_target':target,'chart_count':len(charts),'pair_count':len(pairs),
        'single_certifiable':sum(row['common_functional_exists'] for row in charts),
        'pair_certifiable':sum(row['common_functional_exists'] for row in pairs),
        'pair_nonconstant_rank_distribution':dict(sorted(Counter(row['nonconstant_rank'] for row in pairs).items())),
        'charts':charts,'pairs':pairs,'protocol_sha256':sha(HERE/'protocol.json')}
with (HERE/'result.json').open('x') as out:json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(json.dumps({k:result[k] for k in ('status','chart_count','pair_count','single_certifiable','pair_certifiable','pair_nonconstant_rank_distribution')}))
