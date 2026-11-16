#!/usr/bin/env python3
"""CT167: bounded toy ECDLP through a sextic twist, no speedup claim.
E/F223: y^2=x^3+9; K=F223[z]/(z^3+3); L=K[u]/(u^6-(2+z)).
Explicit map (x,y)->(u^2*x,u^3*y) lands on y^2=x^3+9*(2+z).
"""
import argparse
import json
import resource
import subprocess
import math
import sys
import time

P=223
Q=P**3
ZK=(0,0,0)
OK=(1,0,0)
D=(2,1,0)

def ka(a,b): return tuple((a[i]+b[i])%P for i in range(3))
def ks(a,b): return tuple((a[i]-b[i])%P for i in range(3))
def km(a,b):
    v=[0]*5
    for i in range(3):
        for j in range(3): v[i+j]=(v[i+j]+a[i]*b[j])%P
    for i in (4,3):v[i-3]=(v[i-3]-3*v[i])%P
    return tuple(v[:3])
def kp(a,n):
    r=OK
    while n:
        if n&1:r=km(r,a)
        a=km(a,a);n>>=1
    return r
def ki(a):
    if a==ZK:raise ZeroDivisionError
    return kp(a,Q-2)

def lift(a):return (a,)+(ZK,)*5
ZL=(ZK,)*6
OL=lift(OK)
U=(ZK,OK)+(ZK,)*4
def la(a,b):return tuple(ka(a[i],b[i]) for i in range(6))
def ls(a,b):return tuple(ks(a[i],b[i]) for i in range(6))
def lm(a,b):
    v=[ZK]*11
    for i in range(6):
        if a[i]==ZK:continue
        for j in range(6):
            if b[j]!=ZK:v[i+j]=ka(v[i+j],km(a[i],b[j]))
    for i in range(10,5,-1):
        if v[i]!=ZK:v[i-6]=ka(v[i-6],km(D,v[i]))
    return tuple(v[:6])
def lp(a,n):
    r=OL
    while n:
        if n&1:r=lm(r,a)
        a=lm(a,a);n>>=1
    return r
def linv(a):
    if a==ZL:raise ZeroDivisionError
    return lp(a,Q**6-2)

class Field:
    def __init__(self,zero,one,add,sub,mul,inv):
        self.zero,self.one,self.add,self.sub,self.mul,self.inv=zero,one,add,sub,mul,inv
    def neg(self,a):return self.sub(self.zero,a)
    def double(self,a):return self.add(a,a)
    def triple(self,a):return self.add(a,self.double(a))
FP=Field(0,1,lambda a,b:(a+b)%P,lambda a,b:(a-b)%P,
         lambda a,b:a*b%P,lambda a:pow(a,P-2,P))
FK=Field(ZK,OK,ka,ks,km,ki)
FL=Field(ZL,OL,la,ls,lm,linv)
def add(A,B,F):
    if A is None:return B
    if B is None:return A
    x,y=A;u,v=B
    if x==u and F.add(y,v)==F.zero:return None
    if x==u and y!=v:raise AssertionError('invalid same x')
    if A==B:
        if y==F.zero:return None
        slope=F.mul(F.triple(F.mul(x,x)),F.inv(F.double(y)))
    else:slope=F.mul(F.sub(v,y),F.inv(F.sub(u,x)))
    xx=F.sub(F.sub(F.mul(slope,slope),x),u)
    return xx,F.sub(F.mul(slope,F.sub(x,xx)),y)
def mul(A,n,F):
    if n<0:return mul((A[0],F.neg(A[1])),-n,F)
    B=None
    while n:
        if n&1:B=add(B,A,F)
        A=add(A,A,F);n>>=1
    return B
def generator():
    G=(132,63)
    x,y=G
    assert (y*y-x*x*x-9)%P==0 and mul(G,73,FP) is None
    return G
def point_map(A):
    if A is None:return None
    x,y=A
    return lm(lp(U,2),lift((x,0,0))),lm(lp(U,3),lift((y,0,0)))
def bsgs(G,Qpub,F,n):
    m=math.isqrt(n)+1
    baby={}
    cur=None
    for j in range(m):
        baby.setdefault(cur,j)
        cur=add(cur,G,F)
    shift=mul(G,-m,F)
    cur=Qpub
    for i in range(m+1):
        if cur in baby:
            k=(i*m+baby[cur])%n
            if mul(G,k,F)==Qpub:return k
        cur=add(cur,shift,F)
    raise RuntimeError('no logarithm')

def certificate():
    assert lp(U,6)==lift(D)
    c=kp(D,(Q-1)//6)
    # A primitive sixth-power character certifies u^6=d irreducible over K.
    assert c==(40,0,0) and kp(c,6)==OK and kp(c,3)!=OK and kp(c,2)!=OK
    # Candidate discriminant and group-order test are bounded, not a census.
    x=OK;y=(72,131,189)
    b=km((9,0,0),D)
    assert km(y,y)==ka(km(km(x,x),x),b)
    traces=(-6659,-3439,-3220,3220,3439,6659)
    possible=[t for t in traces if mul((x,y),Q+1-t,FK) is None]
    assert possible==[3439]
    return {'twist_character':list(c),'trace_candidates_surviving_one_point':possible,
            'source_trace':5,'not_a_full_point_census':True}

def solve_one(k):
    G=generator();Qpub=mul(G,k,FP)
    a=time.perf_counter_ns()
    ka_=bsgs(G,Qpub,FP,73)
    assert ka_==k and mul(G,ka_,FP)==Qpub
    source_ns=time.perf_counter_ns()-a
    a=time.perf_counter_ns()
    T=point_map(G);V=point_map(Qpub)
    b=lift(km((9,0,0),D))
    for X,Y in (T,V):assert lm(Y,Y)==la(lm(lm(X,X),X),b)
    assert mul(T,73,FL) is None and mul(T,ka_,FL)==V
    kb=bsgs(T,V,FL,73)
    assert kb==k and mul(G,kb,FP)==Qpub and mul(T,kb,FL)==V
    return {'k_for_verifier_only':k,'source_inner_ns':source_ns,
            'target_inner_ns':time.perf_counter_ns()-a,'verified':True}

def arm(name,qx,qy):
    """Cold public-input solve; no verifier scalar reaches either timed arm."""
    t0=time.perf_counter_ns()
    G=generator()
    if type(qx) is not int or type(qy) is not int or not (0<=qx<P and 0<=qy<P):
        raise ValueError('noncanonical public point')
    Qpub=(qx,qy)
    if (qy*qy-qx*qx*qx-9)%P!=0 or mul(Qpub,73,FP) is not None:
        raise ValueError('public point is not in the 73-subgroup')
    if name=='source':
        recovered=bsgs(G,Qpub,FP,73)
        assert mul(G,recovered,FP)==Qpub
    else:
        certificate()  # finite-extension setup charged to target
        T=point_map(G);V=point_map(Qpub)
        b=lift(km((9,0,0),D))
        for X,Y in (T,V):assert lm(Y,Y)==la(lm(lm(X,X),X),b)
        assert mul(T,73,FL) is None
        # No secret-k group multiplication or expected-log oracle in the timed arm.
        recovered=bsgs(T,V,FL,73)
        assert mul(T,recovered,FL)==V and mul(G,recovered,FP)==Qpub
    return {'arm':name,'recovered_log':recovered,'verified':True,
            'process_inner_ns':time.perf_counter_ns()-t0,
            'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'source_G':list(G),'source_Q':list(Qpub)}

def paired():
    records=[]
    for i,k in enumerate((7,31,59,41)):
        order=('source','twist','twist','source') if i%2 else ('twist','source','source','twist')
        for name in order:
            start=time.perf_counter_ns()
            Qpub=mul(generator(),k,FP)  # harness-only verifier secret
            proc=subprocess.run([sys.executable,'-B',__file__,'--arm',name,
                                 '--qx',str(Qpub[0]),'--qy',str(Qpub[1])],
                check=True,capture_output=True,text=True)
            row=json.loads(proc.stdout)
            if type(row.get('recovered_log')) is not int or row['recovered_log']!=k:
                raise AssertionError('harness-only known-answer mismatch')
            row['verifier_k']=k
            row['cold_host_ns']=time.perf_counter_ns()-start
            records.append(row)
    assert len(records)==16 and all(r['verified'] for r in records)
    for k in (7,31,59,41):
        r=[v for v in records if v['verifier_k']==k]
        assert sorted(v['arm'] for v in r)==['source','source','twist','twist']
        assert len({tuple(v['source_Q']) for v in r})==1
    source=sum(r['cold_host_ns'] for r in records if r['arm']=='source')
    twist=sum(r['cold_host_ns'] for r in records if r['arm']=='twist')
    return {'schema':'ct167-cold-paired-v1','standing':'pcc:unverified',
      'records':records,'cold_source_total_ns':source,'cold_twist_total_ns':twist,
      'twist_over_source_ratio':twist/source,
      'scope':'4 toy Q; 2 cold processes per arm per Q; unisolated, no matched rho/IC'}

def self_test():
    cert=certificate()
    for k in (7,31,59):assert solve_one(k)['verified']
    G=generator();T=point_map(G);b=lift(km((9,0,0),D));u2=lp(U,2)
    controls=[
      lp(U,6)!=lift((3,1,0)),
      lm(T[1],T[1])!=la(lm(lm(T[0],T[0]),T[0]),la(b,OL)),
      lm(T[1],T[1])!=la(lm(lm(T[0],T[0]),T[0]),lift((9,0,0))),
      lm(lm(u2,lift((G[1],0,0))),lm(u2,lift((G[1],0,0))))!=la(lm(lm(T[0],T[0]),T[0]),b),
      mul(T,30,FL)!=point_map(mul(G,31,FP)),
      mul(G,30,FP)!=mul(G,31,FP),
    ]
    assert all(controls)
    return {'status':'pass','controls_rejected':len(controls),'certificate':cert,
            'standing':'pcc:unverified'}

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--arm',choices=('source','twist'))
    a.add_argument('--qx',type=int)
    a.add_argument('--qy',type=int)
    a.add_argument('--paired',action='store_true')
    a.add_argument('--self-test',action='store_true')
    x=a.parse_args()
    if x.paired:out=paired()
    elif x.arm:out=arm(x.arm,x.qx,x.qy)
    elif x.self_test:out=self_test()
    else:a.error('specify --self-test, --paired or --arm')
    print(json.dumps(out,sort_keys=True,separators=(',',':')))
