"""Independent saved-row and modular-rank replay of the f=6 trichotomy census."""
from collections import Counter
import hashlib
import json
from math import gcd,isqrt
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
MODULUS=1000000007


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE/name).read_text())


def class_number(disc):
    total=0
    for a in range(1,isqrt((-disc)//3)+2):
        for b in range(-a,a+1):
            numerator=b*b-disc
            if numerator%(4*a):continue
            c=numerator//(4*a)
            if a>c or (b<0 and (abs(b)==a or a==c)):continue
            if gcd(gcd(a,abs(b)),c)==1:total+=1
    return total


def rank_mod(rows,q):
    a=[[value%q for value in row] for row in rows]
    pivot=0
    for col in range(len(a[0])):
        chosen=next((i for i in range(pivot,len(a)) if a[i][col]),None)
        if chosen is None:continue
        a[pivot],a[chosen]=a[chosen],a[pivot]
        inv=pow(a[pivot][col],-1,q)
        a[pivot]=[value*inv%q for value in a[pivot]]
        for i in range(pivot+1,len(a)):
            factor=a[i][col]
            if factor:
                a[i]=[(value-factor*w)%q for value,w in zip(a[i],a[pivot])]
        pivot+=1
        if pivot==len(a):break
    return pivot


def model(kind,n):
    a=[[0]*n for _ in range(n)]
    for i in range(n):
        a[i][i]+=1
        if kind=='split':
            a[i][(i-1)%n]+=1
            a[i][(i+1)%n]+=1
        elif kind=='ramified':a[i][1-i]+=1
        else:assert kind=='inert' and n==1
    return a


def main():
    inputs,revision,initial,audit=(read(name) for name in
        ('inputs.json','revision_protocol.json','audit_initial.json','audit_revised.json'))
    assert inputs['status']=='FROZEN_RETROSPECTIVE_ALL_SAVED_F6_WALKS'
    assert revision['status']=='FROZEN_REVISED_TRICHOTOMY_BEFORE_REPLAY'
    assert revision['inputs_sha256']==sha(HERE/'inputs.json')
    assert revision['initial_audit_sha256']==sha(HERE/'audit_initial.json')
    assert revision['initial_script_sha256']==sha(HERE/'audit_initial.py')
    assert initial['script_sha256']==sha(HERE/'audit_initial.py')
    assert audit['status']=='REVISED_TRICHOTOMY_CENSUS_WITH_ALL_INPUTS_RETAINED'
    assert audit['inputs_sha256']==sha(HERE/'inputs.json')
    assert audit['revision_protocol_sha256']==sha(HERE/'revision_protocol.json')
    assert audit['script_sha256']==sha(HERE/'audit.py')
    assert len(inputs['inputs'])==len(revision['cases'])==len(audit['cases'])==14
    records=[]
    for item,prediction,case in zip(inputs['inputs'],revision['cases'],audit['cases']):
        assert item['path']==prediction['path']==case['path']
        path=ROOT/item['path']
        assert sha(path)==item['sha256']==case['sha256']
        data=json.loads(path.read_text())
        kind={0:'ramified',1:'split',2:'inert'}[data['DK']%3]
        assert kind==prediction['splitting_at_3']==case['splitting_at_3']
        assert data['class_size']==item['class_size']==case['class_size']
        assert data['relations']==item['relations']==case['saved_rows']
        if case['status']=='EMPTY_CLASS':
            assert data['class_size']==data['relations']==0
            records.append({'DK':data['DK'],'p':data['p'],'type':kind,'status':'EMPTY_CLASS'})
            continue
        assert case['a3']==-1
        conductors=case['column_conductors']
        assert len(conductors)==data['class_size']
        c2={i for i,c in enumerate(conductors) if c==2}
        floor={i for i,c in enumerate(conductors) if c==6}
        assert len(c2)==case['conductor2_points']==2*class_number(4*data['DK'])
        assert len(floor)==case['floor_points']
        assert {int(k):v for k,v in case['conductor_counts'].items()}==dict(Counter(conductors))
        if case['status']=='PARTIAL_CYCLE_STRUCTURE':
            assert len(case['shape_errors'])==1
            assert case['shape_errors'][0]['reason']=='neighbor_outside_saved_class'
            assert case['reconstructed_sources']==len(c2)-1
            assert not case['saved_row_missing_sources']
            records.append({'DK':data['DK'],'p':data['p'],'type':kind,
                            'status':case['status'],'missing_source':case['shape_errors'][0]['source']})
            continue
        assert case['status']=='PASS_SAVED_OPERATOR_BRIDGE'
        indices={int(src):int(row) for src,row in case['source_row_indices'].items()}
        assert set(indices)==c2
        assert not case['saved_row_missing_sources'] and not case['shape_errors']
        components=case['component_vertices']
        assert [len(c) for c in components]==[r['length'] for r in case['components']]
        assert sorted(len(c) for c in components)==case['component_lengths']
        assert Counter(src for component in components for src in component)==Counter(c2)
        kernel_sum=0
        for component,record in zip(components,case['components']):
            n=len(component)
            rows=[]
            for src in component:
                raw=data['relation_rows'][indices[src]]
                projected={int(col):int(value) for col,value in raw.items()
                           if int(col) not in floor and value}
                assert projected.get(src)==1 and set(projected)<=c2
                rows.append([projected.get(col,0) for col in component])
            assert rows==model(kind,n)
            rank=rank_mod(rows,MODULUS)
            assert rank==record['rank_QQ']
            assert n-rank==record['kernel_dimension_QQ']
            if kind=='split':assert n-rank==(2 if n%3==0 else 0)
            elif kind=='ramified':assert n==2 and n-rank==1
            else:assert n==1 and n-rank==0
            kernel_sum+=n-rank
        assert kernel_sum==case['total_projected_kernel_QQ']
        records.append({'DK':data['DK'],'p':data['p'],'type':kind,
                        'status':case['status'],'components':len(components),
                        'projected_kernel_QQ':kernel_sum})
    counts=dict(Counter(r['status'] for r in records))
    assert counts=={'PASS_SAVED_OPERATOR_BRIDGE':11,'PARTIAL_CYCLE_STRUCTURE':2,'EMPTY_CLASS':1}
    assert counts==audit['counts']
    result={'status':'PASS_INDEPENDENT_TRICHOTOMY_REPLAY',
            'audit_revised_sha256':sha(HERE/'audit_revised.json'),
            'script_sha256':sha(HERE/'validate.py'),
            'counts':counts,'records':records,
            'modulus':MODULUS,'candidate_id':None,'timing_claim':None}
    (HERE/'validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':result['status'],'counts':counts},sort_keys=True))


if __name__=='__main__':main()
