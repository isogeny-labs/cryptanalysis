"""Independent Sage replay of F2531 class logs, target and signed pair coverage."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, matrix, vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PLAN=json.loads((HERE/'inputs.json').read_text())
PRE=json.loads((HERE/'pre-run.json').read_text())
POST=json.loads((HERE/'post-run.json').read_text())


def parent(name):
    item=PLAN['frozen'][name]
    raw=(ROOT/item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==item['sha256']
    return json.loads(raw)


def local(name):
    raw=(HERE/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==PRE['sha256'][name]
    return json.loads(raw)


def sparse(item):
    return {int(k):int(v) for k,v in item['row'].items() if v}


def main():
    raw=(HERE/'result.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==POST['result_sha256']
    run=json.loads(raw)
    logs=local('class-logs.json')
    public=local('public-target.json')
    fixture=local('fixture.json')
    cls=next(x for x in parent('class-result.json')['cases'] if x['p']==PLAN['p'])
    analysis=next(x for x in parent('analysis.json')['cases'] if x['p']==PLAN['p'])
    assert parent('audit.json')['status']=='PASS'
    p,q=PLAN['p'],PLAN['q']
    E=EllipticCurve(GF(p),[0,-1,1,-10,-20])
    assert int(E.cardinality())==PLAN['curve_order']
    points=[E(x,y) for x,y in cls['class_points']]
    projected=[PLAN['cofactor']*P for P in points]
    anchor=next(i for i,x in enumerate(projected) if x!=E(0))
    T=projected[anchor]
    assert int(T.order())==q and anchor==logs['anchor_index']
    assert [int(T[0]),int(T[1])]==logs['anchor_point']
    table={k*T:k for k in range(q)}
    assert len(table)==q
    enumerated_logs=[table[B] for B in projected]
    assert enumerated_logs==logs['q_logs'] and len(set(projected))==run['actual_distinct_projected_base_points']
    rows=[sparse(x) for x in cls['base_rows']+analysis['direct_candidates']+analysis['hecke_candidates']]
    assert len(rows)==logs['relation_rows']
    A=matrix(GF(q),len(rows),40,lambda i,j:rows[i].get(j,0))
    assert int(A.rank())==39 and A*vector(GF(q),enumerated_logs)==vector(GF(q),[0]*len(rows))
    Q=E(*public['point'])
    assert public['point']==fixture['point'] and Q not in projected and Q!=E(0)
    attempts=[]
    for counter in range(PLAN['target_counter_cap']):
        digest=hashlib.sha256((PLAN['target_seed']+str(counter)).encode()).digest()
        scalar=1+int.from_bytes(digest,'big')%(q-1)
        candidate=scalar*T
        accepted=candidate!=E(0) and candidate not in projected
        attempts.append({'counter':counter,'scalar':scalar,'accepted':accepted})
        if accepted:break
    assert attempts==fixture['attempts'] and scalar==fixture['scalar'] and candidate==Q
    index={}
    for i in range(40):
        for j in range(i+1,40):
            for a in (-1,1):
                for b in (-1,1):
                    index.setdefault(a*projected[i]+b*projected[j],(i,a,j,b))
    assert len(index)==run['index_distinct_points']
    canonical=[{'point':None if P==E(0) else [int(P[0]),int(P[1])],
                'witness':list(w)}
               for P,w in sorted(index.items(),key=lambda x:(x[0]!=E(0),
                   (0,0) if x[0]==E(0) else (int(x[0][0]),int(x[0][1]))))]
    digest=hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert digest==run['index_sha256']
    covered_scalars={table[P] for P in index}
    assert len(covered_scalars)==len(index) and scalar not in covered_scalars
    assert Q not in index and run['status']=='NO_RELATION' and run['witness'] is None
    assert run['recovered_scalar'] is None and run['index_enumerated_patterns']==3120
    assert run['component_phase_sum_ns']+run['target_interval_overhead_ns']==run['component_online_ns']
    neg_closed=all((-x)%q in set(enumerated_logs) for x in enumerated_logs)
    output={'schema':'hecke-d79-p63317-target-pair-audit-v1','status':'PASS',
            'p':p,'q':q,'target':public['point'],'fixture_scalar':scalar,
            'index_points':len(index),'coverage_numerator':len(index),
            'coverage_denominator':q,'target_covered':False,
            'pair_patterns':3120,'class_logs_checked':40,
            'class_log_negation_closed':neg_closed,
            'distinct_log_values':len(set(enumerated_logs))}
    (HERE/'audit.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','index_points':len(index),
                      'target_covered':False,'negation_closed':neg_closed}))


if __name__=='__main__':
    main()
