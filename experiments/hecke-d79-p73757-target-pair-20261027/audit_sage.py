"""Independent Sage replay of frozen target, pair index and scalar recovery."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PLAN=json.loads((HERE/'inputs.json').read_text())
PRE=json.loads((HERE/'pre-run.json').read_text())
POST=json.loads((HERE/'post_run.json').read_text())


def local(name):
    raw=(HERE/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==PRE['sha256'][name]
    return json.loads(raw)


def parent(name):
    item=PLAN['frozen'][name]
    raw=(ROOT/item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==item['sha256']
    return json.loads(raw)


def main():
    raw=(HERE/'result.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==POST['result_sha256']
    result=json.loads(raw)
    public=local('public-target.json')
    fixture=local('fixture.json')
    cls=parent('class-result.json')['cases'][0]
    anchored=parent('anchor-solve.json')
    kernel=parent('result.json')
    p,q=PLAN['p'],PLAN['q']
    E=EllipticCurve(GF(p),[0,-1,1,-10,-20])
    assert int(E.cardinality())==73630
    points=[E(x,y) for x,y in cls['class_points']]
    T=E(*public['generator']);Q=E(*public['point'])
    assert int(T.order())==q and list(map(int,T.xy()))==kernel['anchor_point']
    assert public['point']==fixture['point'] and public['selected_counter']==fixture['selected_counter']
    projected=[PLAN['cofactor']*P for P in points]
    assert Q not in projected and Q!=E(0)
    attempts=[]
    for counter in range(PLAN['target_counter_cap']):
        digest=hashlib.sha256((PLAN['target_seed']+str(counter)).encode()).digest()
        scalar=1+int.from_bytes(digest,'big')%(q-1)
        point=scalar*T
        accepted=point!=E(0) and point not in projected
        attempts.append({'counter':counter,'scalar':scalar,'accepted':accepted})
        if accepted:break
    assert attempts==fixture['attempts'] and scalar==fixture['scalar'] and point==Q
    logs=anchored['recovered_q_logs']
    assert all(B==log*T for B,log in zip(projected,logs))
    index={}
    for i in range(40):
        for j in range(i+1,40):
            for a in (-1,1):
                for b in (-1,1):
                    index.setdefault(a*projected[i]+b*projected[j],(i,a,j,b))
    assert len(index)==result['index_distinct_points']==199
    index_canonical=[{'point':None if P==E(0) else [int(P[0]),int(P[1])],
                      'witness':list(w)}
                     for P,w in sorted(index.items(),key=lambda x:(x[0]!=E(0),
                         (0,0) if x[0]==E(0) else (int(x[0][0]),int(x[0][1]))))]
    index_sha=hashlib.sha256(json.dumps(index_canonical,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert index_sha==result['index_sha256']
    witness=index[Q]
    assert list(witness)==result['witness']
    i,a,j,b=witness
    recovered=(a*logs[i]+b*logs[j])%q
    independent=next(k for k in range(q) if k*T==Q)
    assert recovered==result['recovered_scalar']==independent==scalar
    assert a*projected[i]+b*projected[j]==Q
    assert result['component_phase_sum_ns']+result['target_interval_overhead_ns']==result['component_online_ns']
    out={'schema':'hecke-d79-p73757-target-pair-audit-v1','status':'PASS',
         'p':p,'q':q,'target':public['point'],'scalar':independent,
         'index_points':len(index),'enumerated_patterns':3120,
         'witness':list(witness),'independent_scalar_replay':True}
    (HERE/'audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','target':out['target'],'index_points':len(index)}))


if __name__=='__main__':
    main()
