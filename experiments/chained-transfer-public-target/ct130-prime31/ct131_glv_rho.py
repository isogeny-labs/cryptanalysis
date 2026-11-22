#!/usr/bin/env python3
"""CT131 exploratory, bounded CM-isogeny/GLV rho, public known answers only.
This does not establish a fastest-source-rho, IC or Jacobian advantage.
"""
import json,random,resource,sys,time
import ct130_experiment as ec
P=2147483033; Q=536857417; R=969960860; I=392507391; L=390258842
SA=622683939;SB=2147483024
G=(911976709,415929193);H=(180482573,1535800095)
ec.P=P

def mapping(T):
    if T is None or T==(0,0):return None
    x,y=T;z=pow(x,-1,P)
    return (((x+SA+SB*z)*pow(4,-1,P)+R)%P,
            (y*(1-SB*z*z)*pow(8,-1,P))%P)

def fold(T,orbit):
    if T is None:return None,1
    x,y=T
    neg=(x,(-y)%P)
    if orbit==2:return (neg,Q-1) if neg<T else (T,1)
    phi=((-x)%P,I*y%P)
    return min(((T,1),(neg,Q-1),(phi,L),((phi[0],(-phi[1])%P),(-L)%Q)),key=lambda v:v[0])

def solve(curve,base,public,orbit,seed,cap=300000,retries=6):
    rng=random.Random(seed);total=cycles=0
    for _ in range(retries):
        jumps=[]
        for j in range(32):
            a=rng.randrange(1,Q);b=rng.randrange(1,Q)
            jumps.append((curve.add(curve.mul(base,a),curve.mul(public,b)),a,b))
        a=rng.randrange(1,Q);b=rng.randrange(1,Q)
        T=curve.add(curve.mul(base,a),curve.mul(public,b))
        T,u=fold(T,orbit);a=a*u%Q;b=b*u%Q
        seen={};salt=rng.randrange(1,2**32)
        for z in range(cap):
            if T in seen:
                aa,bb=seen[T]
                if bb!=b:
                    result=(aa-a)*pow(b-bb,-1,Q)%Q
                    if curve.mul(base,result)!=public:raise ValueError('bad collision')
                    return result,total+z+1,cycles,len(seen)
                cycles+=1
                x=0 if T is None else T[0];y=0 if T is None else T[1]
                idx=(((x^(y>>5)^salt)*0x9e3779b1)&31)+1+rng.randrange(31)
                idx&=31
            else:
                seen[T]=(a,b)
                x=0 if T is None else T[0];y=0 if T is None else T[1]
                idx=((x^(y>>5)^salt)*0x9e3779b1)&31
            J,da,db=jumps[idx]
            T=curve.add(T,J);a=(a+da)%Q;b=(b+db)%Q
            T,u=fold(T,orbit);a=a*u%Q;b=b*u%Q
        total+=z+1
    raise RuntimeError('bounded walk exhausted')

def run(seed=20261116,count=64):
    if count>64 or count<1:raise ValueError('run limit 64')
    source=ec.Curve(SA,SB);target=ec.Curve(0,9)
    if not (mapping(G)==H and source.mul(G,Q) is None and target.mul(H,Q) is None):raise ValueError('bad public parameters')
    if not (R*R%P==(P-9)%P and I*I%P==P-1 and L*L%Q==Q-1):raise ValueError('bad algebraic parameters')
    if target.mul(H,L)!=((-H[0])%P,I*H[1]%P):raise ValueError('wrong eigenvalue')
    rng=random.Random(seed);keys=[rng.randrange(Q//8,Q-1) for _ in range(count)]
    rows=[]
    for kidx,k in enumerate(keys):
        pub=source.mul(G,k)
        arms=['source_neg','target_glv','target_glv','source_neg'] if kidx%2==0 else ['target_glv','source_neg','source_neg','target_glv']
        items=[]
        for name in arms:
            c=source if name=='source_neg' else target
            t0=time.perf_counter_ns();before=c.ops.copy()
            base,point,orbit=(G,pub,2) if name=='source_neg' else (mapping(G),mapping(pub),4)
            got,its,cycles,stored=solve(c,base,point,orbit,seed+kidx*19)
            if got!=k or source.mul(G,got)!=pub:raise ValueError('wrong public log')
            dt=time.perf_counter_ns()-t0;delta=c.ops-before
            items.append(dict(arm=name,recovered_log=got,ns=dt,iterations=its,fruitless_cycles=cycles,
                              stored_states=stored,add_calls=delta['add_calls'],inverse_calls=delta['inversions'],verified=True))
        rows.append(dict(scalar=k,public_Q=pub,arms=items))
    return dict(schema='ct131-cm-glv-rho/v1',standing='[pcc:unverified]',field_p=P,source_a=SA,
                source_b=SB,source_G=G,target_H=H,subgroup_q=Q,seed=seed,predefined_scalars=keys,
                rows=rows,peak_rss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                scope='known-curve toy cold rho comparator only; no strongest external rho/IC/Jacobian')

if __name__=='__main__':
    seed=int(sys.argv[1]) if len(sys.argv)>1 else 20261116
    count=int(sys.argv[2]) if len(sys.argv)>2 else 64
    print(json.dumps(run(seed,count),sort_keys=True,separators=(',',':')))
