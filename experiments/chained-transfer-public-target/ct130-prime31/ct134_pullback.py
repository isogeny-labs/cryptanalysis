#!/usr/bin/env python3
"""CT134 source-side CM conjugation: finite-subgroup checks and bounded map-only cost.
Producer-only research diagnostic. Never a full cold ECDLP solve.
"""
import json, random, resource, statistics, time
P=2147483033; Q=536857417; A=622683939; B=2147483024
R=969960860; I=392507391; L=390258842; INV2=(Q+1)//2
G=(911976709,415929193); H=(180482573,1535800095)
A2=(-2*A)%P; B2=(A*A-4*B)%P; I4=pow(4,-1,P); I8=pow(8,-1,P)

def check(condition, label):
    if not condition: raise ValueError(label)

class Curve:
    def __init__(self,a,b): self.a=a;self.b=b;self.adds=0;self.invs=0
    def on(self,t):
        return t is None or (t[1]*t[1]-t[0]**3-self.a*t[0]**2-self.b*t[0])%P==0
    def neg(self,t): return None if t is None else (t[0],(-t[1])%P)
    def add(self,u,v):
        self.adds+=1
        if u is None:return v
        if v is None:return u
        x,y=u;z,w=v
        if x==z and (y+w)%P==0:return None
        if x==z: num=3*x*x+2*self.a*x+self.b;den=2*y
        else:num=w-y;den=z-x
        self.invs+=1
        slope=num*pow(den%P,-1,P)%P
        xx=(slope*slope-self.a-x-z)%P
        return (xx,(slope*(x-xx)-y)%P)
    def mul(self,u,n):
        out=None
        while n:
            if n&1:out=self.add(out,u)
            u=self.add(u,u);n>>=1
        return out

def phi(t):
    if t is None or t==(0,0):return None
    x,y=t;z=pow(x,-1,P)
    return (((x+A+B*z)*I4+R)%P,y*(1-B*z*z)*I8%P)

def psi(t):
    if t is None:return None
    X,Y=t;x=4*(X-R)%P;y=8*Y%P
    if not x:return None
    z=pow(x,-1,P)
    return ((x+A2+B2*z)*I4%P,y*(1-B2*z*z)*I8%P)

def alpha(t):return None if t is None else ((-t[0])%P,I*t[1]%P)
def beta(t):return psi(alpha(phi(t)))
def src_alpha(t,c):return c.mul(beta(t),INV2)

def run():
    c=Curve(A,B);d=Curve(0,9)
    check(c.on(G) and d.on(H) and phi(G)==H,'curve/generator')
    check(c.mul(G,Q) is None and d.mul(H,Q) is None,'subgroup')
    check(pow(I,2,P)==P-1 and pow(L,2,Q)==Q-1 and d.mul(H,L)==alpha(H),'eigenline')
    rng=random.Random(20261115)
    scalars=[1,2,3,17,12345,456789,Q-1]+[rng.randrange(1,Q) for _ in range(16)]
    pairs=[]
    check(phi((0,0)) is None and psi(None) is None,'kernels')
    for k in scalars:
        u=c.mul(G,k);v=d.mul(H,k);pairs.append((u,v))
        check(c.on(u) and d.on(v) and phi(u)==v,'phi')
        check(psi(v)==c.mul(u,2) and phi(psi(v))==d.mul(v,2),'dual')
        check(beta(u)==c.mul(u,(2*L)%Q),'beta eigenvalue')
        check(beta(beta(u))==c.mul(u,Q-4),'beta square')
        check(src_alpha(u,c)==c.mul(u,L),'source conjugation')
        check(src_alpha(src_alpha(u,c),c)==c.neg(u),'order four')
    # Check all images before timing; timing excludes scalar verification on BOTH arms.
    samples=[]
    for block in range(4):
        order=('source','target','target','source') if block%2==0 else ('target','source','source','target')
        for arm in order:
            a0=c.adds;i0=c.invs;t0=time.perf_counter_ns()
            acc=0
            for rep in range(16):
                for u,v in pairs:
                    w=src_alpha(u,c) if arm=='source' else alpha(v)
                    check(w is not None,'map returned identity')
                    acc^=w[0]
            elapsed=time.perf_counter_ns()-t0
            calls=16*len(pairs)
            samples.append(dict(block=block,arm=arm,ns=elapsed,calls=calls,
                curve_adds=c.adds-a0,field_inversions=c.invs-i0+(2*calls if arm=='source' else 0),checksum=acc))
    ratios=[]
    for block in range(4):
        group=[e for e in samples if e['block']==block]
        a=statistics.mean(x['ns'] for x in group if x['arm']=='source')
        b=statistics.mean(x['ns'] for x in group if x['arm']=='target')
        ratios.append(a/b)
    check(all(x['curve_adds']==0 and x['field_inversions']==0 for x in samples if x['arm']=='target'),'target counted cost')
    check(all(x['curve_adds']>0 and x['field_inversions']>0 for x in samples if x['arm']=='source'),'source counted cost')
    return dict(schema='ct134-source-cm-pullback/v1',standing='[pcc:unverified]',
                p=P,q=Q,source_j=287496,target_j=1728,validated_scalars=len(scalars),
                beta_eigenvalue=2*L%Q,beta_squared_eigenvalue=Q-4,source_alpha_eigenvalue=L,
                inversed_two=INV2,seed=20261115,repetitions=16,peak_rss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                samples=samples,block_source_over_target_map_ratios=ratios,
                scope='microbenchmark of one subgroup symmetry action only, not cold rho/BSGS/IC or full Jacobian transfer')
if __name__=='__main__':print(json.dumps(run(),sort_keys=True))
