import random
from pathlib import Path
p = 2**31-1
K = (1965083199,1854403464)
def plus(P,Q):
    if P is None: return Q
    if Q is None: return P
    x,y=P
    u,v=Q
    if x==u and (y+v)%p==0: return None
    m=((3*x*x+1)*pow(2*y,-1,p) if x==u else (v-y)*pow(u-x,-1,p))%p
    z=(m*m-x-u)%p
    return z,(m*(x-z)-y)%p
def answer(x):
    r=(x*x+1)*x%p
    y=pow(r,(p+1)//4,p)
    if y*y%p!=r: return 0,0
    P=(x,min(y,p-y)); seen=set(); bits=0
    for j in range(32):
        if P is None or P[0] in seen: return 1,0
        u=P[0];seen.add(u)
        bits|=(pow((u**3+2*u+14)%p,(p-1)//2,p)!=p-1)<<j
        P=plus(P,K)
    return 2,bits
for seed in (315201,315202):
    rng=random.Random(seed)
    with Path(f'{seed}.txt').open('w') as f:
        for _ in range(8224):
            x=rng.randrange(p); print(x,*answer(x),file=f)
