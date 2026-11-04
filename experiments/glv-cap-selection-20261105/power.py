import numpy as np, math, collections
rng=np.random.default_rng(1)
SE=0.67/math.sqrt(1400); S=[38,39,40,41,42]; x=np.array(S,float); xc=x-x.mean()
MARGIN=math.log(.995)
def run(mu,nsim=20000):
    c=collections.Counter(); go=0
    for _ in range(nsim):
        L=mu+rng.normal(0,SE,5)
        slope=(L*xc).sum()/(xc**2).sum(); fit=L.mean()+slope*xc
        ok=fit<=MARGIN; T=None
        for i in range(5):
            if ok[i:].all(): T=S[i]; break
        if T is None: c['none']+=1; continue
        k=S.index(T); Sm=L[k:].mean(); se=SE/math.sqrt(5-k)
        if Sm+1.2816*se<0: go+=1; c[T]+=1
        else: c['fail%d'%T]+=1
    return go/nsim, dict(sorted(c.items(),key=str))
for name,mu in [("null all 0",[0]*5),("38-39 0, 40 -0.5%, 41 -1%, 42 -1.5%",[0,0,-.005,-.01,-.015]),("step: 0,0,0,0,-1.1%",[0,0,0,0,-.011]),("38,39 0; 40-42 -1.5%",[0,0,-.015,-.015,-.015]),("all -2%",[-.02]*5),("38:+.03(as #1338) then lin to 42:-1.1%",[.003,-.0,-.004,-.008,-.011])]:
    print(name, run(np.array(mu)))
