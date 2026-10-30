"""Pair-index-plus-one search on the exact retained p63317 target."""
import hashlib
import json
import resource
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PLAN=json.loads((HERE/'inputs.json').read_text())


def pinned(name):
    item=PLAN['frozen'][name]
    raw=(ROOT/item['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=item['sha256']:
        raise ValueError('PARENT_PIN_MISMATCH:'+name)
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
    slope=top*pow(bottom%p,-1,p)%p
    intercept=(y-slope*x)%p
    X=(slope*slope+1-x-u)%p
    Y=(-slope*X-intercept-1)%p
    return X,Y


def mul(n,P,p):
    if n<0:return mul(-n,neg(P,p),p)
    total=None
    while n:
        if n&1:total=add(total,P,p)
        P=add(P,P,p);n>>=1
    return total


def point_list(P):
    return None if P is None else list(P)


def main():
    if pinned('result.json')['status']!='NO_RELATION' or pinned('audit.json')['status']!='PASS':
        raise ValueError('PARENT_MISS_NOT_AUDITED')
    p,q=PLAN['p'],PLAN['q']
    cls=next(x for x in pinned('class-result.json')['cases'] if x['p']==p)
    logs=pinned('class-logs.json')
    public=pinned('public-target.json')
    T=tuple(logs['anchor_point']);Q=tuple(public['point'])
    if public['q']!=q or tuple(public['generator'])!=T:
        raise ValueError('TARGET_IDENTITY_MISMATCH')
    source_points=[tuple(x) for x in cls['class_points']]
    prep_start=time.perf_counter_ns()
    base=[mul(PLAN['cofactor'],P,p) for P in source_points]
    if any(B!=mul(k,T,p) for B,k in zip(base,logs['q_logs'])):
        raise ValueError('CLASS_LOG_MISMATCH')
    index={}
    count=0
    for i in range(40):
        for j in range(i+1,40):
            for a in (-1,1):
                for b in (-1,1):
                    S=add(base[i] if a==1 else neg(base[i],p),
                          base[j] if b==1 else neg(base[j],p),p)
                    index.setdefault(S,[]).append((i,a,j,b))
                    count+=1
    prep_ns=time.perf_counter_ns()-prep_start
    if len(index)!=pinned('sumset-audit.json')['distinct_covered_scalars'] or Q in index:
        raise ValueError('PARENT_PAIR_MISS_OR_INDEX_MISMATCH')
    canonical=[{'point':point_list(P),'witnesses':[list(w) for w in ws]}
               for P,ws in sorted(index.items(),key=lambda x:(x[0] is not None,x[0] or (0,0)))]
    index_sha=hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    online_start=time.perf_counter_ns()
    probe_ns=0;scan_ns=0;replay_ns=0;probes=[]
    witness=None;scalar=None
    for k in range(40):
        for c in (-1,1):
            t=time.perf_counter_ns()
            residual=add(Q,neg(base[k],p) if c==1 else base[k],p)
            bucket=index.get(residual,[])
            probe_ns+=time.perf_counter_ns()-t
            t=time.perf_counter_ns()
            checked=0
            for i,a,j,b in bucket:
                checked+=1
                if k==i or k==j:continue
                candidate=add(add(base[i] if a==1 else neg(base[i],p),
                                  base[j] if b==1 else neg(base[j],p),p),
                              base[k] if c==1 else neg(base[k],p),p)
                if candidate!=Q:
                    raise ValueError('TRIPLE_RELATION_FAIL')
                scalar=(a*logs['q_logs'][i]+b*logs['q_logs'][j]+c*logs['q_logs'][k])%q
                witness=(i,a,j,b,k,c)
                break
            scan_ns+=time.perf_counter_ns()-t
            probes.append({'probe_number':len(probes)+1,'third_source':k,'third_sign':c,
                           'residual':point_list(residual),'pair_bucket_size':len(bucket),
                           'pair_witnesses_scanned':checked,
                           'status':'MATCH' if witness is not None else 'MISS'})
            if witness is not None:break
        if witness is not None:break
    if witness is not None:
        t=time.perf_counter_ns()
        if mul(scalar,T,p)!=Q:
            raise ValueError('SCALAR_REPLAY_FAIL')
        replay_ns=time.perf_counter_ns()-t
    online_ns=time.perf_counter_ns()-online_start
    status='VERIFIED_TRIPLE' if witness is not None else 'CAP80_NO_RELATION'
    out={'schema':'hecke-d79-p63317-target-triple-run-v1','status':status,
         'p':p,'q':q,'target':list(Q),'generator':list(T),
         'class_points':40,'distinct_projected_base_points':len(set(base)),
         'pair_index_patterns':count,'pair_index_points':len(index),
         'pair_index_sha256':index_sha,'pair_index_build_ns':prep_ns,
         'probe_cap':80,'probes':probes,'probe_count':len(probes),
         'witness':None if witness is None else list(witness),
         'recovered_scalar':scalar,'target_probe_ns':probe_ns,
         'target_pair_scan_and_check_ns':scan_ns,
         'target_scalar_replay_ns':replay_ns,
         'component_online_ns':online_ns,
         'component_phase_sum_ns':probe_ns+scan_ns+replay_ns,
         'target_interval_overhead_ns':online_ns-probe_ns-scan_ns-replay_ns,
         'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'candidate_id':None,'target_online_ms':None}
    (HERE/'result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':status,'probe_count':len(probes),'witness':out['witness']}))


if __name__=='__main__':
    main()
