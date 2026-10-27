"""Construct a single public point under the frozen seeded input law."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PLAN=json.loads((HERE/'inputs.json').read_text())


def pinned(name):
    item=PLAN['frozen'][name]
    raw=(ROOT/item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==item['sha256']
    return json.loads(raw)


def negate(P,p):
    return None if P is None else (P[0],(-P[1]-1)%p)


def add(A,B,p):
    if A is None:return B
    if B is None:return A
    x,y=A;u,v=B
    if x==u and (y+v+1)%p==0:return None
    if A==B:top,bottom=3*x*x-2*x-10,2*y+1
    else:top,bottom=v-y,u-x
    slope=top*pow(bottom%p,-1,p)%p
    b=(y-slope*x)%p
    X=(slope*slope+1-x-u)%p
    Y=(-slope*X-b-1)%p
    return X,Y


def mul(n,P,p):
    if n<0:return mul(-n,negate(P,p),p)
    total=None
    while n:
        if n&1:total=add(total,P,p)
        P=add(P,P,p);n>>=1
    return total


def main():
    p,q=PLAN['p'],PLAN['q']
    cls=pinned('class-result.json')['cases'][0]
    kernel=pinned('result.json')
    T=tuple(kernel['anchor_point'])
    points=[tuple(x) for x in cls['class_points']]
    assert mul(PLAN['cofactor'],points[0],p)==T and mul(q,T,p) is None
    projected={mul(PLAN['cofactor'],P,p) for P in points}
    attempts=[]
    for counter in range(PLAN['target_counter_cap']):
        digest=hashlib.sha256((PLAN['target_seed']+str(counter)).encode()).digest()
        scalar=1+int.from_bytes(digest,'big')%(q-1)
        Q=mul(scalar,T,p)
        accepted=Q is not None and Q not in projected
        attempts.append({'counter':counter,'scalar':scalar,'accepted':accepted})
        if accepted:break
    else:
        raise ValueError('TARGET_COUNTER_CAP')
    fixture={'schema':'hecke-d79-p73757-target-fixture-v1','status':'FROZEN',
             'seed':PLAN['target_seed'],'attempts':attempts,
             'selected_counter':counter,'scalar':scalar,'point':list(Q),
             'generator':list(T),'q':q}
    public={'schema':'hecke-d79-p73757-public-target-v1','status':'FROZEN',
            'point':list(Q),'generator':list(T),'q':q,
            'selected_counter':counter,'scalar_present':False}
    (HERE/'fixture.json').write_text(json.dumps(fixture,indent=2,sort_keys=True)+'\n')
    (HERE/'public-target.json').write_text(json.dumps(public,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'FROZEN','counter':counter,'point':list(Q)}))


if __name__=='__main__':
    main()
