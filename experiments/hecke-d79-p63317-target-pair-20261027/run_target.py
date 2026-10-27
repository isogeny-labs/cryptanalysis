"""Target-independent signed pair index followed by one public-point query."""
import hashlib
import json
import resource
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PLAN=json.loads((HERE/'inputs.json').read_text())
PRE=json.loads((HERE/'pre-run.json').read_text())
POSTLOG=json.loads((HERE/'post-logs.json').read_text())


def pinned(name):
    item=PLAN['frozen'][name]
    raw=(ROOT/item['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=item['sha256']:
        raise ValueError('PARENT_PIN_MISMATCH:'+name)
    return json.loads(raw)


def local(name):
    raw=(HERE/name).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PRE['sha256'][name]:
        raise ValueError('LOCAL_PIN_MISMATCH:'+name)
    return json.loads(raw)


def neg(P,p):
    return None if P is None else (P[0],(-P[1]-1)%p)


def add(A,B,p):
    if A is None:return B
    if B is None:return A
    x,y=A;u,v=B
    if x==u and (y+v+1)%p==0:return None
    if A==B:top,bottom=3*x*x-2*x-10,2*y+1
    else:top,bottom=v-y,u-x
    lam=top*pow(bottom%p,-1,p)%p
    b=(y-lam*x)%p
    X=(lam*lam+1-x-u)%p
    Y=(-lam*X-b-1)%p
    return X,Y


def mul(n,P,p):
    if n<0:return mul(-n,neg(P,p),p)
    total=None
    while n:
        if n&1:total=add(total,P,p)
        P=add(P,P,p);n>>=1
    return total


def main():
    p,q=PLAN['p'],PLAN['q']
    public=local('public-target.json')
    cls=pinned('class-result.json')['cases'][0]
    log_raw=(HERE/'class-logs.json').read_bytes()
    if hashlib.sha256(log_raw).hexdigest()!=POSTLOG['sha256']['class-logs.json']:
        raise ValueError('CLASS_LOG_PIN_MISMATCH')
    anchored=json.loads(log_raw)
    if anchored['status']!='PASS':
        raise ValueError('CLASS_LOGS_NOT_READY')
    T=tuple(anchored['anchor_point'])
    Q=tuple(public['point'])
    if tuple(public['generator'])!=T or public['q']!=q or public['scalar_present']:
        raise ValueError('PUBLIC_TARGET_MISMATCH')
    logs=anchored['q_logs']
    points=[tuple(x) for x in cls['class_points']]
    prep_start=time.perf_counter_ns()
    base=[mul(PLAN['cofactor'],P,p) for P in points]
    if any(B!=mul(log,T,p) for B,log in zip(base,logs)):
        raise ValueError('CLASS_LOG_REPLAY_FAIL')
    if Q in base or Q is None:
        raise ValueError('TARGET_NOT_UNSEEN')
    index={}
    enumerated=0
    for i in range(40):
        for j in range(i+1,40):
            for a in (-1,1):
                for b in (-1,1):
                    value=add(base[i] if a==1 else neg(base[i],p),
                              base[j] if b==1 else neg(base[j],p),p)
                    index.setdefault(value,(i,a,j,b))
                    enumerated+=1
    prep_ns=time.perf_counter_ns()-prep_start
    index_canonical=[{'point':None if pt is None else list(pt),'witness':list(witness)}
                     for pt,witness in sorted(index.items(),key=lambda x:(x[0] is not None,x[0] or (0,0)))]
    index_digest=hashlib.sha256(json.dumps(index_canonical,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    online_start=time.perf_counter_ns()
    query_start=time.perf_counter_ns()
    witness=index.get(Q)
    query_ns=time.perf_counter_ns()-query_start
    status='NO_RELATION' if witness is None else 'VERIFIED_PAIR'
    check_ns=0;replay_ns=0;recovered=None
    if witness is not None:
        i,a,j,b=witness
        t=time.perf_counter_ns()
        relation=add(base[i] if a==1 else neg(base[i],p),
                     base[j] if b==1 else neg(base[j],p),p)
        if relation!=Q or i>=j:
            raise ValueError('PAIR_RELATION_FAIL')
        recovered=(a*logs[i]+b*logs[j])%q
        check_ns=time.perf_counter_ns()-t
        t=time.perf_counter_ns()
        if mul(recovered,T,p)!=Q:
            raise ValueError('SCALAR_REPLAY_FAIL')
        replay_ns=time.perf_counter_ns()-t
    online_ns=time.perf_counter_ns()-online_start
    out={'schema':'hecke-d79-p73757-target-pair-run-v1','status':status,
         'p':p,'q':q,'target':list(Q),'generator':list(T),
         'class_points':40,'actual_distinct_projected_base_points':len(set(base)),
         'index_enumerated_patterns':enumerated,'index_distinct_points':len(index),
         'index_sha256':index_digest,'index_build_and_base_projection_ns':prep_ns,
         'witness':None if witness is None else list(witness),
         'recovered_scalar':recovered,
         'target_query_ns':query_ns,'target_relation_check_ns':check_ns,
         'target_scalar_replay_ns':replay_ns,'component_online_ns':online_ns,
         'component_phase_sum_ns':query_ns+check_ns+replay_ns,
         'target_interval_overhead_ns':online_ns-query_ns-check_ns-replay_ns,
         'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'candidate_id':None,'target_online_ms':None}
    (HERE/'result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':status,'witness':out['witness'],
                      'distinct_index_points':len(index)}))


if __name__=='__main__':
    main()
