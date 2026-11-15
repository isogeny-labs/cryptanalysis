import random,time,json
from ct130_experiment import Curve,transfer,P,bsgs

def rho(c,G,Q,q,seed,max_steps=400_000,distinguished_bits=9):
    rng=random.Random(seed)
    a_b=[(rng.randrange(0,q),rng.randrange(0,q)) for _ in range(16)]
    jump=[c.add(c.mul(G,a),c.mul(Q,b)) for a,b in a_b]
    a=rng.randrange(0,q);b=rng.randrange(0,q)
    at=c.add(c.mul(G,a),c.mul(Q,b))
    visited={}
    mask=(1<<distinguished_bits)-1
    collisions=0
    for count in range(1,max_steps+1):
        h=(at[0]&15) if at is not None else 0
        at=c.add(at,jump[h]); a=(a+a_b[h][0])%q;b=(b+a_b[h][1])%q
        if at is not None and not at[0]&mask:
            record=visited.get(at)
            if record is not None:
                a0,b0=record
                denom=(b-b0)%q
                if denom:
                    m=((a0-a)*pow(denom,-1,q))%q
                    if c.mul(G,m)==Q:return m,count,len(visited),collisions
                collisions+=1
            else:visited[at]=(a,b)
    raise RuntimeError(('rho run exceeded iteration bound',seed,len(visited),collisions))

def run():
 c=Curve(829286810,1720850223);d=Curve(488910027,790354208)
 G=(340312345,363681553);q=1073779747
 H=transfer(c,d,G)
 rows=[]
 for m in (17,12345,456789):
    Q=c.mul(G,m)
    for name,curve,g,qq in [('source-rho',c,G,Q),('transfer-rho',d,H,transfer(c,d,Q))]:
        elapsed=[];iters=[];mem=[]
        for j in range(2):
            now=time.perf_counter_ns()
            if name=='transfer-rho':
                g=transfer(c,d,G);qq=transfer(c,d,Q)
            try:
                recovered,n,entries,coll=rho(curve,g,qq,q,1000+7*m+j)
            except Exception as exc:
                print('FAIL',m,name,j,str(exc),flush=True);continue
            assert recovered==m and c.mul(G,recovered)==Q
            elapsed.append(time.perf_counter_ns()-now);iters.append(n);mem.append(entries)
        rows.append(dict(scalar=m,arm=name,elapsed_ns=elapsed,walk_steps=iters,stored_distinguished=mem))
 print(json.dumps(rows))
if __name__=='__main__':run()
