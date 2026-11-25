#!/usr/bin/env sage -python
"""Independent halving-law audit of the cofactor-four character census."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'n131_w18_two_terminal_fourfiber_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model(n,exponents,r):
    ring=PolynomialRing(GF(2),'t');t=ring.gen()
    field=GF(2**n,name='t',modulus=sum(t**i for i in exponents))
    curve=EllipticCurve(field,[1,0,0,0,1])
    def dec(value):
        return field(ring([(int(value)>>i)&1 for i in range(n)]))
    def point(row):
        return curve(0) if row is None else curve([dec(v) for v in row])
    generator=curve([field(1),field(0)])
    two=2*generator
    assert two==curve([field(0),field(1)]) and 4*generator==curve(0)
    def even_class(p):
        if p==curve(0):
            return 0
        if p==two:
            return 2
        x,y=p[0],p[1]
        assert x!=0 and int(x.trace())==0
        h=field(0);v=x
        for _ in range((n+1)//2):
            h+=v;v=v**4
        assert h*h+h==x
        return 2*int((y+(h+1)*x).trace())
    def character(p):
        if p==curve(0):
            return 0
        x=p[0]
        if x==0:
            return 2
        if int((1/x).trace())==0:
            return even_class(p)
        return (even_class(p+generator)-(r%4))%4
    return point,character


def main():
    protocol_path=HERE/'protocol.json'
    result_path=HERE/'result.json'
    protocol=json.loads(protocol_path.read_text())
    result=json.loads(result_path.read_text())
    pool_path=PRIOR/'pool.json'
    pool=json.loads(pool_path.read_text())
    public=json.loads((PRIOR/'query_result.json').read_text())
    n41=json.loads((PRIOR/'n41_control_result.json').read_text())
    assert result['status']=='PASS_W18_C4_CLASS_PREFLIGHT'
    assert protocol['source_sha256']['pool']==sha(pool_path)
    point,chi=model(131,(131,13,2,1,0),680564733841876926932320129493409985129)
    left={row['state_id']:chi(point(row['rotated_raw_point'])) for row in pool['left_states']}
    right={row['state_id']:chi(point(row['rotated_raw_point'])) for row in pool['right_states']}
    raw=[chi(point(p)) for p in public['raw_targets']]
    assert raw==result['n131_raw_classes']
    assert dict(Counter(left.values()))=={int(k):v for k,v in result['left_class_counts'].items()}
    assert dict(Counter(right.values()))=={int(k):v for k,v in result['right_class_counts'].items()}
    families=defaultdict(set)
    family_state_count=Counter()
    class_counts=Counter()
    for row in pool['joint_states']:
        i,j=row['left_state_id'],row['right_state_id']
        label=(left[i]+right[j])%4
        class_counts[label]+=1
        key=(pool['left_states'][i]['edge_index'],pool['right_states'][j]['edge_index'])
        families[key].add(label)
        family_state_count[key]+=1
    assert dict(class_counts)=={int(k):v for k,v in result['admissible_joint_class_counts'].items()}
    assert len(families)==result['admissible_edge_pairs']==130
    assert {f'{i},{j}':sorted(v) for (i,j),v in sorted(families.items())}==result['edge_pair_classes']
    assert all(len(v) in (1,2) and len({c%2 for c in v})==1 for v in families.values())
    singleton_pairs=[key for key,v in families.items() if len(v)==1]
    singleton_states=sum(family_state_count[key] for key in singleton_pairs)
    assert len(singleton_pairs)==12
    # With a hypothetically known free-part class, trace leaves two raw
    # classes; the mod-four class removes one more only in singleton families.
    extra_raw_choices_by_family=len(singleton_pairs)
    extra_raw_choices_weighted=singleton_states
    p41,c41=model(41,(41,3,0),549756390943)
    n41raw=[c41(p41(row['raw_target'])) for row in n41['raw_fibers']]
    free=c41(p41(n41['free_five_sum']))
    terminal=c41(p41(n41['terminal_two_sum']))
    assert n41raw==result['n41']['raw_classes']
    assert free==result['n41']['free_five_class']
    assert terminal==result['n41']['terminal_two_class']
    assert (free+terminal)%4==n41raw[0]
    receipt={'status':'PASS_INDEPENDENT_HALVING_C4_CLASS_AUDIT',
             'n131_terminal_states_checked':96,
             'n131_joint_families_checked':130,
             'n131_joint_state_choices_checked':2080,
             'families_with_one_class':len(singleton_pairs),
             'families_with_two_classes':len(families)-len(singleton_pairs),
             'state_choices_in_singleton_families':singleton_states,
             'extra_raw_choice_reduction_given_known_free_class':{
                 'unweighted_edge_families':extra_raw_choices_by_family,
                 'weighted_terminal_state_choices':extra_raw_choices_weighted},
             'n41_raw_classes':n41raw,
             'sha256':{'script':sha(Path(__file__)),'protocol':sha(protocol_path),
                       'producer':sha(result_path),'pool':sha(pool_path),
                       'public':sha(PRIOR/'query_result.json'),
                       'n41':sha(PRIOR/'n41_control_result.json')}}
    (HERE/'audit_result.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(receipt['status'],len(singleton_pairs),singleton_states,flush=True)


if __name__=='__main__':
    main()
