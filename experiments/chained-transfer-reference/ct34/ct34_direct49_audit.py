#!/usr/bin/env python3
"""CT34: independently constructed direct 49-Velu map from cyclic kernel K.

Self-contained F101 polynomial/elliptic/BSGS checks; no imports from
the CT33 producer. Unsigned development evidence [pcc:unverified].
"""
import json
from math import isqrt
p=101
def trim(v):
    v=[a%p for a in v]
    while len(v)>1 and v[-1]==0:v.pop()
    return v or [0]
def plus(f,g):return trim([(f[i] if i<len(f) else 0)+(g[i] if i<len(g) else 0) for i in range(max(len(f),len(g)))])
def neg(f):return trim([-x for x in f])
def diff(f,g):return plus(f,neg(g))
def times(f,g):
    v=[0]*(len(f)+len(g)-1)
    for i,a in enumerate(f):
        for j,b in enumerate(g):v[i+j]+=a*b
    return trim(v)
def mult(f,k):return trim([x*k for x in f])
def der(f):return trim([i*f[i] for i in range(1,len(f))])
def sq(f):return times(f,f)
def val(f,x):
    a=0
    for c in reversed(f):a=(a*x+c)%p
    return a
def velu(a,b,K):
    r=len(K)-1; s1=-K[-2]; f=[b,a,0,1]; kp=der(K)
    D=sq(K)
    N=plus(diff(times([-2*s1,2*r+1],D),mult(times(times(der(f),kp),K),2)),
           mult(times(f,diff(sq(kp),times(K,der(kp)))),4))
    return N,D
def codomain(a,b,K):
    r=len(K)-1; s=[r]
    for j in range(1,4):
        z=-j*K[r-j]-sum(K[r-i]*s[j-i] for i in range(1,j))
        s.append(z%p)
    u,v,w=s[1:]
    return [(a-10*(3*v+r*a))%p,(b-14*(5*w+3*a*u+2*r*b))%p],(u,v,w)
def H_pull(h,N,D):
    n2=sq(N);d2=sq(D)
    return plus(plus(times(n2,N),mult(times(n2,D),h[2])),
                plus(mult(times(N,d2),h[1]),mult(times(d2,D),h[0])))
def compose(a,b,h0,h1,mid):
    N0,D0=velu(a,b,h0);N1,_=velu(mid[0],mid[1],h1)
    H=H_pull(h1,N0,D0)
    np=[[1]];dp=[[1]]
    for _ in range(7):
        np.append(times(np[-1],N0));dp.append(times(dp[-1],D0))
    Nc=[0]
    for i,c in enumerate(N1):Nc=plus(Nc,mult(times(np[i],dp[7-i]),c))
    return Nc,sq(times(h0,H)),H
def add(A,B,a):
    if A is None:return B
    if B is None:return A
    x,y=A;u,v=B
    if x==u and (y+v)%p==0:return None
    if A==B:
        if y==0:return None
        slope=(3*x*x+a)*pow(2*y,-1,p)%p
    else:slope=(v-y)*pow((u-x)%p,-1,p)%p
    X=(slope*slope-x-u)%p
    return (X,(slope*(x-X)-y)%p)
def negpt(Q):return (Q[0],(-Q[1])%p) if Q else None
def mulpt(P,k,a):
    R=None
    while k:
        if k&1:R=add(R,P,a)
        P=add(P,P,a);k>>=1
    return R
def points(a,b):
    return [None]+[(x,y) for x in range(p) for y in range(p)
                   if (y*y-x*x*x-a*x-b)%p==0]
def mappt(Q,N,D):
    if Q is None:return None
    x,y=Q;d=val(D,x)
    if d==0:raise ValueError('base-field kernel collision')
    n=val(N,x);iv=pow(d,-1,p)
    dernum=(val(der(N),x)*d-n*val(der(D),x))%p
    return (n*iv%p,y*dernum*iv*iv%p)
def bsgs(B,Q,n,a):
    m=isqrt(n)+1;cache={};P=None;ops=0
    for j in range(m):
        cache.setdefault(P,j)
        P=add(P,B,a);ops+=1
    step=negpt(mulpt(B,m,a));P=Q
    for i in range(m+1):
        if P in cache:
            k=(i*m+cache[P])%n
            if mulpt(B,k,a)==Q:return k,ops
        P=add(P,step,a);ops+=1
    raise ValueError('BSGS failure')
def chk(ok,why):
    if not ok:raise ValueError('CT34: '+why)
CASES=[
 dict(tag='E109',a=1,b=46,n=109,mid=[26,58],end=[59,27],
      h0=[72,100,35,1],h1=[99,94,75,1],
      H=[9,78,22,78,88,78,90,64,94,74,63,12,66,63,87,78,67,69,81,60,83,1]),
 dict(tag='E113',a=44,b=21,n=113,mid=[69,50],end=[23,7],
      h0=[59,46,8,1],h1=[53,19,40,1],
      H=[69,65,23,53,73,2,51,98,84,33,33,30,95,34,26,89,25,69,19,29,88,1])]
def audit(c):
    a,b,n=c['a'],c['b'],c['n'];h0,h1=c['h0'],c['h1']
    K=times(h0,c['H']);N,D=velu(a,b,K)
    target,sums=codomain(a,b,K)
    chk(target==c['end'],'direct target coefficients')
    Nc,Dc,H=compose(a,b,h0,h1,c['mid'])
    chk(H==c['H'],'independent H comparison')
    chk((N,D)==(Nc,Dc),'direct49 != composed7+7 as polynomials')
    chk(len(N)==50 and len(D)==49,'degree49 map not reduced')
    altered=K[:];altered[0]=(altered[0]+1)%p
    chk(velu(a,b,altered)!=(N,D),'low coefficient negative control')
    altered=K[:];altered[-2]=(altered[-2]+1)%p
    chk(codomain(a,b,altered)[0]!=target,'top coefficient negative control')
    source=points(a,b);dest=set(points(*target))
    chk(len(source)==n and len(dest)==n,'curve point counts')
    chk(codomain(a,b,h0)[0]==c['mid'],'first target')
    chk(codomain(*c['mid'],h1)[0]==target,'second target')
    N0,D0=velu(a,b,h0);N1,D1=velu(*c['mid'],h1)
    mapped={}
    for Q in source:
        T=mappt(Q,N,D)
        chk(T in dest,'image not on target')
        chk(T==mappt(mappt(Q,N0,D0),N1,D1),'pointwise composition mismatch')
        mapped[Q]=T
    chk(len(set(mapped.values()))==n,'not a rational-point bijection')
    G=source[1];T=mapped[G]
    seq=[mulpt(G,k,a) for k in range(n)]
    img=[mapped[v] for v in seq]
    chk(len(set(seq))==len(set(img))==n,'generator order')
    for k in range(n):chk(mulpt(T,k,target[0])==img[k],'scalar image')
    for i in range(n):
        for j in range(n):
            chk(add(img[i],img[j],target[0])==img[(i+j)%n],'homomorphism')
    src_ops=dst_ops=0
    for k in range(n):
        q,cost=bsgs(G,seq[k],n,a)
        r,tc=bsgs(T,img[k],n,target[0])
        chk(q==r==k,'cold known-answer DLP')
        src_ops+=cost;dst_ops+=tc
    return dict(chain=c['tag'],kernel_x_pairs=24, degree=49,
                power_sums=list(sums),target=target,polynomial_equal=True,
                mapped_points=n,additivity_checks=n*n,dlps=n,
                direct_bsgs_additions=src_ops,transport_bsgs_additions=dst_ops,
                negative_controls=2)
if __name__=='__main__':
    for case in CASES:print(json.dumps(audit(case),sort_keys=True))
    print('CT34 PASS [pcc:unverified]')
