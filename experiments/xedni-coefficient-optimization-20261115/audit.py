"""Independent inverse-map, cost-formula, and checked-Sage public relation audit."""
import hashlib
import json
import math
from pathlib import Path
from sage.all import EllipticCurve, GF, prime_range, is_prime

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/'xedni-coefficient-holdout-20261115'
COVER=HERE.parent/'xedni-finite-family-coverage-20261115'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def mul_cost(k):
    n=abs(k);return n.bit_length()+n.bit_count()

protocol=json.loads((HERE/'protocol.json').read_text())
family=json.loads((HERE/'family-selection.json').read_text())
fields=json.loads((HERE/'field-selection.json').read_text())
result=json.loads((HERE/'result.json').read_text())
for key,path in (
    ('parent_family_protocol_sha256',PARENT/'protocol.json'),
    ('parent_coverage_protocol_sha256',COVER/'protocol.json'),
    ('parent_coverage_result_sha256',COVER/'result.json'),
):assert protocol[key]==sha(path)
assert family['protocol_sha256']==fields['protocol_sha256']==result['protocol_sha256']==sha(HERE/'protocol.json')
assert family['source_sha256']==sha(HERE/'select_family.py')
assert fields['source_sha256']==sha(HERE/'select_fields.py')
assert result['source_sha256']==sha(HERE/'run.py')
assert result['family_selection_sha256']==sha(HERE/'family-selection.json')
assert result['field_selection_sha256']==sha(HERE/'field-selection.json')
assert fields['family_selection_sha256']==sha(HERE/'family-selection.json')
# Reconstruct greedy selection with an independent hit-set formula.
qs=protocol['calibration_orders'];assert qs==[751,883,983,1103]
choices=sorted((a,b) for a in range(1,7) for b in range(-6,7)
               if b!=0 and a+b!=0 and math.gcd(a,abs(b))==1)
assert len(choices)==family['candidate_count']==45
seen={q:set() for q in qs};selected=[]
for step in family['rounds']:
    score=[]
    for a,b in choices:
        if (a,b) in selected:continue
        candidate={q:{(b*t*pow((a+b)%q,-1,q))%q for t in range(1,35)} for q in qs}
        gain=sum(len(candidate[q]-seen[q]) for q in qs)
        score.append((-gain,(a,b),candidate))
    _,best,sets=min(score,key=lambda x:(x[0],x[1]))
    assert list(best)==step['vector']
    selected.append(best)
    for q in qs:seen[q]|=sets[q]
assert [list(x) for x in selected]==family['selected']
old=json.loads((PARENT/'protocol.json').read_text())['coefficient_family']
assert family['baseline']==[x for x in old if sum(x)!=0]
# Reconstruct every candidate field in the frozen p scan.
checked=[];chosen=[]
for p in prime_range(1501,10001):
    E=EllipticCurve(GF(p),[-1,-2]);G=E(2,2);q=int(E.cardinality())
    prime=bool(is_prime(q))
    checked.append({'p':int(p),'q':q,'prime_order':prime})
    if prime and not G.is_zero():
        assert int(G.order())==q
        chosen.append([int(p),q])
        if len(chosen)==8:break
assert checked==fields['checked'] and chosen==fields['selected']
assert len(result['fields'])==len(chosen)==8
out=[]
for row,(p,q) in zip(result['fields'],chosen):
    assert (p,q)==(row['field_prime'],row['subgroup_order'])
    E=EllipticCurve(GF(p),[-1,-2]);G=E(2,2)
    assert all((a+b)%q!=0 for a,b in selected)
    raw=HERE/row['raw_path']
    assert sha(raw)==row['raw_sha256']
    records=[json.loads(line) for line in raw.read_text().splitlines()]
    assert len(records)==row['target_count']==q-1
    totals={name:{'hits':0,'capped':0,'vector_tests':0,'group_add_calls':0}
            for name in ('baseline','selected')}
    for d,record in enumerate(records,start=1):
        assert record['scalar']==d
        for name in totals:
            vectors=[tuple(v) for v in family[name]]
            first=None
            for t in range(1,35):
                if t==d:continue
                for j,(a,b) in enumerate(vectors):
                    if (b*t*pow((a+b)%q,-1,q))%q==d:
                        first=(t,j,a,b);break
                if first:break
            actual=record[name]
            if first:
                t,j,a,b=first
                assert actual['status']=='hit' and actual['query_index']==t+1
                assert actual['offset']==t and actual['vector_index']==j
                assert actual['vector']==[a,b] and actual['recovered_scalar']==d
                Q=d*G;R=Q-t*G
                assert not R.is_zero() and R!=Q and (a*Q+b*R).is_zero()
                until=t
                tests=13*(t-1-int(d<t))+(j+1)
                adds=t + (t-1-int(d<t))*sum(mul_cost(x)+mul_cost(y)+1 for x,y in vectors)
                adds+=sum(mul_cost(x)+mul_cost(y)+1 for x,y in vectors[:j+1])
                totals[name]['hits']+=1
            else:
                assert actual['status']=='capped' and actual['query_index']==35
                assert actual['vector'] is None and actual['recovered_scalar'] is None
                until=34
                tests=13*(34-int(d<=34))
                adds=34+sum(mul_cost(x)+mul_cost(y)+1 for x,y in vectors)*(34-int(d<=34))
                totals[name]['capped']+=1
            assert actual['vector_tests']==tests and actual['group_add_calls']==adds
            assert actual['admitted_queries']==until-int(d<=until)
            totals[name]['vector_tests']+=tests
            totals[name]['group_add_calls']+=adds
    assert totals==row['arms']
    assert all(totals[name]['hits']<=13*34 for name in totals)
    out.append({'field_prime':p,'subgroup_order':q,'arms':totals})
print(json.dumps({'schema':'xedni-coefficient-optimization-audit-v1','status':'PASS',
                  'checked_primes':len(checked),'fields':out},sort_keys=True,indent=2))
