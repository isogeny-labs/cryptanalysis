"""Independent Sage replay of the first triple witness and full coverage."""
import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PLAN=json.loads((HERE/'inputs.json').read_text())
POST=json.loads((HERE/'post-run.json').read_text())


def pinned(name):
    item=PLAN['frozen'][name]
    raw=(ROOT/item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==item['sha256']
    return json.loads(raw)


def point_list(P,E):
    return None if P==E(0) else [int(P[0]),int(P[1])]


def main():
    raw=(HERE/'result.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==POST['result_sha256']
    result=json.loads(raw)
    assert pinned('result.json')['status']=='NO_RELATION'
    assert pinned('audit.json')['status']=='PASS'
    logs=pinned('class-logs.json')['q_logs']
    public=pinned('public-target.json')
    fixture=pinned('fixture.json')
    cls=next(x for x in pinned('class-result.json')['cases'] if x['p']==PLAN['p'])
    p,q=PLAN['p'],PLAN['q']
    E=EllipticCurve(GF(p),[0,-1,1,-10,-20])
    assert int(E.cardinality())==63275
    points=[E(x,y) for x,y in cls['class_points']]
    base=[PLAN['cofactor']*P for P in points]
    T=E(*public['generator']);Q=E(*public['point'])
    assert int(T.order())==q and all(B==k*T for B,k in zip(base,logs))
    assert public['point']==fixture['point'] and fixture['scalar']*T==Q
    index={}
    for i,j in itertools.combinations(range(40),2):
        for a,b in itertools.product((-1,1),repeat=2):
            index.setdefault(a*base[i]+b*base[j],[]).append((i,a,j,b))
    canonical=[{'point':point_list(P,E),'witnesses':[list(w) for w in ws]}
               for P,ws in sorted(index.items(),key=lambda x:(x[0]!=E(0),
                   (0,0) if x[0]==E(0) else (int(x[0][0]),int(x[0][1]))))]
    index_sha=hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert index_sha==result['pair_index_sha256'] and len(index)==result['pair_index_points']==689
    assert Q not in index
    audited=[];found=None
    for k in range(40):
        for c in (-1,1):
            residual=Q-c*base[k]
            bucket=index.get(residual,[])
            checked=0
            for i,a,j,b in bucket:
                checked+=1
                if k in (i,j):continue
                assert a*base[i]+b*base[j]+c*base[k]==Q
                found=(i,a,j,b,k,c)
                break
            audited.append({'probe_number':len(audited)+1,'third_source':k,'third_sign':c,
                            'residual':point_list(residual,E),'pair_bucket_size':len(bucket),
                            'pair_witnesses_scanned':checked,
                            'status':'MATCH' if found is not None else 'MISS'})
            if found is not None:break
        if found is not None:break
    assert audited==result['probes'] and list(found)==result['witness']
    i,a,j,b,k,c=found
    scalar=(a*logs[i]+b*logs[j]+c*logs[k])%q
    assert scalar==result['recovered_scalar']==fixture['scalar']
    assert scalar*T==Q and len(audited)==result['probe_count']
    group_covered=set()
    scalar_covered=set()
    patterns=0
    for i,j,k in itertools.combinations(range(40),3):
        for a,b,c in itertools.product((-1,1),repeat=3):
            group_covered.add(a*base[i]+b*base[j]+c*base[k])
            scalar_covered.add((a*logs[i]+b*logs[j]+c*logs[k])%q)
            patterns+=1
    table={z*T:z for z in range(q)}
    assert len(table)==q and {table[P] for P in group_covered}==scalar_covered
    assert Q in group_covered and scalar in scalar_covered
    assert result['component_phase_sum_ns']+result['target_interval_overhead_ns']==result['component_online_ns']
    out={'schema':'hecke-d79-p63317-target-triple-audit-v1','status':'PASS',
         'p':p,'q':q,'target':public['point'],'scalar':scalar,
         'first_witness':list(found),'first_probe_count':len(audited),
         'pair_index_points':len(index),'triple_patterns':patterns,
         'triple_coverage_points':len(group_covered),
         'triple_uncovered_points':q-len(group_covered),
         'target_covered':True}
    (HERE/'audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','probe_count':len(audited),
                      'triple_coverage':len(group_covered),'uncovered':q-len(group_covered)}))


if __name__=='__main__':
    main()
