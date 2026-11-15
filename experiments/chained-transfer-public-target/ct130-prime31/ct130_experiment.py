#!/usr/bin/env python3
"""Independent, bounded affine-curve toy cold ECDLP transfer comparison on p=2**31-1.
Not a new asymptotic attack or independent PCC evidence.
"""
import math, random, time, json, gc, resource
from collections import Counter
P=(1<<31)-1
O=None
class Curve:
    __slots__=('a','b','ops')
    def __init__(self,a,b): self.a=a%P;self.b=b%P;self.ops=Counter()
    def neg(self,R):return None if R is None else (R[0],(-R[1])%P)
    def add(self,R,S):
        self.ops['add_calls']+=1
        if R is None: return S
        if S is None: return R
        x,y=R;u,v=S
        if x==u:
            if (y+v)%P==0:return O
            d=(2*y)%P;z=(3*x*x+2*self.a*x+self.b)%P
        else:
            d=(u-x)%P;z=(v-y)%P
        self.ops['inversions']+=1
        lam=z*pow(d,-1,P)%P
        w=(lam*lam-self.a-x-u)%P
        return (w,(lam*(x-w)-y)%P)
    def mul(self,R,n):
        S=O
        while n:
            if n&1:S=self.add(S,R)
            R=self.add(R,R);n>>=1
        return S
    def on(self,R):
        return R is None or R[1]*R[1]%P==(R[0]**3+self.a*R[0]*R[0]+self.b*R[0])%P
    def point(self,rng):
        for _ in range(10000):
            x=rng.randrange(1,P);r=(x*x*x+self.a*x*x+self.b*x)%P
            y=pow(r,(P+1)//4,P)
            if y*y%P==r:return(x,y)
        raise RuntimeError('No point found')

def isprime(n):
    if n<2:return False
    for t in (2,3,5,7,11,13,17,19,23,29,31,37):
        if n%t==0:return n==t
    s=0;d=n-1
    while d%2==0:s+=1;d//=2
    for a in (2,325,9375,28178,450775,9780504,1795265022):
        a%=n
        if a==0:continue
        x=pow(a,d,n)
        if x in (1,n-1):continue
        for _ in range(s-1):
            x=x*x%n
            if x==n-1:break
        else:return False
    return True

def order_from_hasse(c,R):
    bound=math.isqrt(4*P)
    lo=P+1-bound;hi=P+1+bound
    m=math.isqrt(hi-lo+1)+1
    babies={};V=O
    for j in range(m):
        babies.setdefault(V,j)
        V=c.add(V,R)
    W=c.neg(c.mul(R,lo)); step=c.neg(c.mul(R,m))
    valid=[]
    for i in range((hi-lo)//m+2):
        if W in babies:
            N=lo+i*m+babies[W]
            if lo<=N<=hi and c.mul(R,N) is None:valid.append(N)
        W=c.add(W,step)
    return sorted(set(valid))

def construct(seed=137):
    rng=random.Random(seed)
    for k in range(100):
        a=rng.randrange(1,P);b=rng.randrange(1,P)
        if (a*a-4*b)%P==0:continue
        c=Curve(a,b);R=c.point(rng)
        group=order_from_hasse(c,R)
        for N in group:
            if N%2 or not isprime(N//2):continue
            q=N//2
            if q<10**8:continue
            G=c.mul(R,2)
            if G is None or c.mul(G,q) is not None:continue
            if len(group)!=1:continue
            d=Curve(-2*a,a*a-4*b)
            if not d.on(transfer(c,d,G)):raise AssertionError('isogeny fails curve')
            if c.on((0,0)) is False:raise AssertionError('kernel')
            for u in range(1,50):
                lhs=transfer(c,d,c.mul(G,u));rhs=d.mul(transfer(c,d,G),u)
                if lhs!=rhs:raise AssertionError(('homomorphism',u,lhs,rhs))
            return c,d,G,N,q,k+1,seed
    raise RuntimeError('No prime-cofactor-two ordinary curve found')

def transfer(c,d,R):
    if R is None or R==(0,0):return O
    x,y=R
    if not x:raise ValueError('unexpected 2-torsion')
    inv=pow(x,-1,P)
    U=(x+c.a+c.b*inv)%P
    V=y*(1-c.b*inv*inv)%P
    return(U,V)

def bsgs(c,G,Q,q):
    width=math.isqrt(q-1)+1
    baby={};R=O
    for j in range(width):
        baby.setdefault(R,j)
        R=c.add(R,G)
    step=c.neg(c.mul(G,width));T=Q
    for i in range(width+1):
        j=baby.get(T)
        if j is not None:
            candidate=i*width+j
            if candidate<q and c.mul(G,candidate)==Q:return candidate,len(baby)
        T=c.add(T,step)
    raise AssertionError('BSGS recovery failed')

def timing(c,d,G,q,scalars):
    rows=[];H=transfer(c,d,G)
    rng=random.Random(97)
    for z in scalars:
        Q=c.mul(G,z)
        S=transfer(c,d,Q)
        assert d.on(S) and d.mul(H,z)==S
        block=[]
        for ix in range(4):
            arms=('source','target','target','source') if ix%2==0 else ('target','source','source','target')
            vals=[]
            for arm in arms:
                t0=time.perf_counter_ns();ops0=Counter((c if arm=='source' else d).ops)
                if arm=='source':found,bs=bsgs(c,G,Q,q)
                else:
                    H2=transfer(c,d,G);S2=transfer(c,d,Q)
                    assert H2==H and S2==S
                    found,bs=bsgs(d,H2,S2,q)
                assert found==z and c.mul(G,found)==Q
                delta=time.perf_counter_ns()-t0
                ctr=(c if arm=='source' else d).ops-ops0
                vals.append(dict(arm=arm,ns=delta,baby_entries=bs,
                                 group_add_calls=ctr['add_calls'],field_inversions=ctr['inversions']))
            block.append(dict(order=list(arms),observations=vals))
        rows.append(dict(fixture_scalar=z,source_public=Q,target_public=S,blocks=block))
    return rows

def main():
    start=time.perf_counter_ns()
    c,d,G,N,q,attempts,seed=construct()
    setup_ns=time.perf_counter_ns()-start
    cases=[17,12345,456789]
    rows=timing(c,d,G,q,cases)
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    out=dict(schema='ct130-prime31-isogeny-screen/v1',standing='[pcc:unverified]',
        source_prime=P,curve_coefficients=dict(a=c.a,b=c.b),
        codomain_coefficients=dict(a=d.a,b=d.b),curve_order=N,subgroup_prime=q,
        selection_seed=seed,attempts=attempts,source_generator=G,
        isogeny_degree=2,setup_ns=setup_ns,peak_rss_kb=rss,rows=rows,
        scope='ordinary public prime-cofactor-two toy; complete per-query source BSGS vs isogeny+target BSGS, not strongest optimized rho or IC')
    import statistics as st
    ratios=[]
    for row in rows:
        for b in row['blocks']:
            s=[r['ns'] for r in b['observations'] if r['arm']=='source'];t=[r['ns'] for r in b['observations'] if r['arm']=='target']
            ratios.append(st.mean(s)/st.mean(t))
    out['source_over_transferred_bsgs_median_per_block']=st.median(ratios)
    print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
