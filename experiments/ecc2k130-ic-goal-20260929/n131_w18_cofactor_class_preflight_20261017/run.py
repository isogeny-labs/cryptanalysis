#!/usr/bin/env sage -python
"""Exact cofactor-four class census on the frozen W18 terminal source."""
import hashlib
import json
import resource
import signal
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'n131_w18_two_terminal_fourfiber_20261017'
R131=680564733841876926932320129493409985129
R41=549756390943


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    return {'script':Path(__file__),'runtime':HERE/'sage_runtime_info.json',
            'pool':PRIOR/'pool.json','public':PRIOR/'query_result.json',
            'public_audit':PRIOR/'public_sage_audit_result.json',
            'control':PRIOR/'control_result.json',
            'n41':PRIOR/'n41_control_result.json'}


def save(name,value):
    with (HERE/name).open('x') as out:
        json.dump(value,out,sort_keys=True,indent=2)
        out.write('\n')


def model(degree,exponents):
    ring=PolynomialRing(GF(2),'t');t=ring.gen()
    field=GF(2**degree,name='t',modulus=sum(t**i for i in exponents))
    curve=EllipticCurve(field,[1,0,0,0,1])
    def dec(value):
        return field(ring([(int(value)>>i)&1 for i in range(degree)]))
    def point(row):
        return curve(0) if row is None else curve([dec(value) for value in row])
    torsion=[curve(0),curve([field(1),field(0)]),
             curve([field(0),field(1)]),curve([field(1),field(1)])]
    assert 2*torsion[1]==torsion[2] and 3*torsion[1]==torsion[3]
    assert 4*torsion[1]==curve(0) and len(set(torsion))==4
    return curve,dec,point,{p:i for i,p in enumerate(torsion)}


def freeze():
    prior=json.loads((PRIOR/'query_result.json').read_text())
    audit=json.loads((PRIOR/'public_sage_audit_result.json').read_text())
    runtime=json.loads((HERE/'sage_runtime_info.json').read_text())
    assert prior['curve_id']=='EC1N131Ckb1heb5f1998f20b'
    assert len(prior['residuals'])==8320
    assert audit['status']=='PASS_INDEPENDENT_SAGE_N131_FOURFIBER_PUBLIC_RESIDUALS'
    assert runtime['status']=='verified'
    save('protocol.json',{'status':'FROZEN_W18_C4_CLASS_CENSUS_BEFORE_RUN',
                          'curve_id':prior['curve_id'],'workload_id':prior['workload_id'],
                          'subgroup_orders':{'n131':R131,'n41':R41},
                          'torsion_generator':[1,0],
                          'class_law':'label [r]P by multiples 0..3 of (1,0)',
                          'worker_count':1,'wall_cap_seconds':300,
                          'rss_observation_cap_bytes':4294967296,
                          'source_sha256':{name:sha(path) for name,path in sources().items()}})


def run():
    start=time.monotonic_ns()
    signal.alarm(300)
    protocol=json.loads((HERE/'protocol.json').read_text())
    assert protocol['status']=='FROZEN_W18_C4_CLASS_CENSUS_BEFORE_RUN'
    assert protocol['source_sha256']=={name:sha(path) for name,path in sources().items()}
    pool=json.loads((PRIOR/'pool.json').read_text())
    public=json.loads((PRIOR/'query_result.json').read_text())
    control=json.loads((PRIOR/'control_result.json').read_text())
    n41=json.loads((PRIOR/'n41_control_result.json').read_text())
    curve,dec,point,labels=model(131,(131,13,2,1,0))
    assert R131%4==1
    def chi(row):
        p=point(row)
        assert R131*p in labels
        return labels[R131*p]
    left={row['state_id']:chi(row['rotated_raw_point']) for row in pool['left_states']}
    right={row['state_id']:chi(row['rotated_raw_point']) for row in pool['right_states']}
    assert len(left)==len(right)==48
    raw=[chi(row) for row in public['raw_targets']]
    assert sorted(raw)==[0,1,2,3]
    def trace(row):
        p=point(row)
        return int((1/p[0]).trace())
    for state in pool['left_states']:
        assert left[state['state_id']]%2==trace(state['rotated_raw_point'])
    for state in pool['right_states']:
        assert right[state['state_id']]%2==trace(state['rotated_raw_point'])
    joint_classes={}
    family=defaultdict(set)
    for row in pool['joint_states']:
        i,j=row['left_state_id'],row['right_state_id']
        label=(left[i]+right[j])%4
        joint_classes[i,j]=label
        family[(pool['left_states'][i]['edge_index'],
                pool['right_states'][j]['edge_index'])].add(label)
    assert len(joint_classes)==2080
    direct=[]
    for raw_index in range(4):
        for offset in (0,17,511,1023,2079):
            row=public['residuals'][raw_index*2080+offset]
            expected=(raw[raw_index]-joint_classes[row['left_state_id'],
                                                   row['right_state_id']])%4
            actual=chi(row['point'])
            assert actual==expected
            direct.append({'raw_preimage_index':raw_index,'joint_index':offset,
                           'class':actual})
    edge_hist=Counter(len(values) for values in family.values())
    per_edge={}
    x_buckets=defaultdict(set)
    for side,states,classes in (('left',pool['left_states'],left),
                                ('right',pool['right_states'],right)):
        edge=defaultdict(set)
        for state in states:
            label=classes[state['state_id']]
            edge[state['edge_index']].add(label)
            x_buckets[(side,state['edge_index'],state['rotated_raw_point'][0])].add(label)
        per_edge[side]={'support_size_histogram':dict(Counter(map(len,edge.values()))),
                        'classes':{str(k):sorted(v) for k,v in sorted(edge.items())}}
    ambiguous=Counter(tuple(sorted(values)) for values in x_buckets.values())
    assert all(len(values) in (1,2) for values in x_buckets.values())
    assert all(values in ({0},{2},{1,3}) for values in x_buckets.values())
    # A fixed signed source sum chooses exactly one of the four raw lifts.
    for label in joint_classes.values():
        assert sorted((target-label)%4 for target in raw)==[0,1,2,3]
    c41,_,p41,l41=model(41,(41,3,0))
    def chi41(row):
        p=p41(row)
        assert R41*p in l41
        return l41[R41*p]
    n41_raw=[chi41(row['raw_target']) for row in n41['raw_fibers']]
    n41_free=chi41(n41['free_five_sum'])
    n41_terminal=chi41(n41['terminal_two_sum'])
    assert sorted(n41_raw)==[0,1,2,3]
    assert (n41_free+n41_terminal)%4==n41_raw[0]
    elapsed=time.monotonic_ns()-start
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    receipt={'status':'PASS_W18_C4_CLASS_PREFLIGHT',
             'curve_id':public['curve_id'],'workload_id':public['workload_id'],
             'n131_raw_classes':raw,
             'left_class_counts':dict(Counter(left.values())),
             'right_class_counts':dict(Counter(right.values())),
             'admissible_joint_class_counts':dict(Counter(joint_classes.values())),
             'admissible_edge_pairs':len(family),
             'edge_pair_class_support_size_histogram':dict(edge_hist),
             'edge_pair_classes':{f'{i},{j}':sorted(v) for (i,j),v in sorted(family.items())},
             'per_edge':per_edge,
             'x_bucket_class_patterns':{','.join(map(str,k)):v for k,v in sorted(ambiguous.items())},
             'direct_residual_samples':direct,
             'n41':{'raw_classes':n41_raw,'free_five_class':n41_free,
                    'terminal_two_class':n41_terminal},
             'elapsed_ns':elapsed,
             'peak_self_rss_bytes':rss if sys.platform=='darwin' else rss*1024,
             'source_sha256':protocol['source_sha256'],
             'protocol_sha256':sha(HERE/'protocol.json')}
    save('result.json',receipt)
    signal.alarm(0)
    print(receipt['status'],len(family),dict(edge_hist),flush=True)


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('freeze','run')
    {'freeze':freeze,'run':run}[sys.argv[1]]()
