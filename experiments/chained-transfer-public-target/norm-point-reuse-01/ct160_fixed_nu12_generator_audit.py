#!/usr/bin/env python3
"""Independent exact q223 fixed-nu12 public generators, Hasse and Frobenius.

No Rust, CT158 Python, or CT160 C++ implementation imported.  The K field is
F_223[z]/(z^3-3), coefficient order [1,z,z^2]. [pcc:unverified]
"""
import json
from math import isqrt
P=223
Q=P**3
O=(0,0,0)
ONE=(1,0,0)
N=2_771_711
ORDER=11_086_844
SOURCE=((167,76,41),(27,91,187))
TARGET=((207,175,148),(175,89,34))
GENERATORS=(((55,126,141),(110,98,213)),((65,114,83),(100,34,29)))

def require(c,reason):
    if not c: raise ValueError(reason)

def add(a,b): return tuple((x+y)%P for x,y in zip(a,b))
def neg(a): return tuple(-x%P for x in a)
def subtract(a,b): return add(a,neg(b))
def multiply(a,b):
    a0,a1,a2=a; b0,b1,b2=b
    return ((a0*b0+3*(a1*b2+a2*b1))%P,
            (a0*b1+a1*b0+3*a2*b2)%P,
            (a0*b2+a1*b1+a2*b0)%P)
def power(x,k):
    require(k>=0,'negative exponent')
    out=ONE
    while k:
        if k&1: out=multiply(out,x)
        x=multiply(x,x);k>>=1
    return out

def inverse(a):
    require(a!=O,'inverse of zero')
    return power(a,Q-2)

def rhs(curve,x):
    a,b=curve
    return add(multiply(x,add(multiply(x,x),a)),b)
def curve_check(curve,G):
    if G is None:return True
    x,y=G
    return multiply(y,y)==rhs(curve,x)

def point_add(curve,G,H):
    if G is None:return H
    if H is None:return G
    x1,y1=G;x2,y2=H
    if x1==x2 and add(y1,y2)==O: return None
    if G==H:
        if y1==O: return None
        lam=multiply(multiply((3,0,0),multiply(x1,x1)), inverse(multiply((2,0,0),y1)))
        lam=add(lam,multiply(curve[0],inverse(multiply((2,0,0),y1))))
    else:
        lam=multiply(subtract(y2,y1),inverse(subtract(x2,x1)))
    x3=subtract(subtract(multiply(lam,lam),x1),x2)
    y3=subtract(multiply(lam,subtract(x1,x3)),y1)
    return x3,y3

def scale(curve,G,k):
    require(k>=0,'scalar must be nonnegative')
    acc=None
    while k:
        if k&1:acc=point_add(curve,acc,G)
        G=point_add(curve,G,G); k>>=1
    return acc

def prime_trial(n):
    if n<2:return False
    for d in range(2,isqrt(n)+1):
        if n%d==0:return False
    return True

def audit():
    require(pow(3,(P-1)//3,P)!=1, 'z^3-3 reducible over Fp')
    require(power((0,1,0),3)==(3,0,0),'wrong field reduction')
    require(power((0,1,0),Q)==(0,1,0),'wrong Frobenius')
    require(power((12,0,0),(Q-1)//2)==(222,0,0),'nu=12 is not nonsquare')
    require(prime_trial(N),'N not prime')
    low=Q+1-isqrt(4*Q)
    high=Q+1+isqrt(4*Q)
    first=(low+N-1)//N; last=high//N
    require(first==last==4 and 4*N==ORDER,'multiple of N in Hasse interval not unique')
    rows=[]
    for name,curve,G in zip(('fixed_source','fixed_target'),(SOURCE,TARGET),GENERATORS):
        a,b=curve
        require(add(multiply((4,0,0),power(a,3)),multiply((27,0,0),power(b,2)))!=O, f'{name}: singular model')
        require(G is not None and curve_check(curve,G),f'{name}: generator not on curve')
        require(scale(curve,G,N) is None,f'{name}: generator missing prime order')
        require(scale(curve,G,1)==G,f'{name}: wrong identity')
        for k in (2,3,13,169,277):
            C=scale(curve,G,k)
            require(curve_check(curve,C),f'{name}: scalar not on curve')
            require(scale(curve,C,N) is None,f'{name}: subgroup check at {k}')
        rows.append({'model':name,'on_curve':True,'generator_prime_order':N,'Hasse_multiple':4,'group_order':ORDER,'public_generator':G})
    tvals=range(-isqrt(4*P),isqrt(4*P)+1)
    gaps=[abs(t**3-3*P*t-(Q+1-ORDER)) for t in tvals if t*t<=4*P]
    require(len(gaps)==59 and min(gaps)==112 and all(g!=0 for g in gaps),'Frobenius base-change gap')
    # Mutant A source and coordinate altered public generators must fail.
    mutated=((168,76,41),SOURCE[1])
    tests=[(mutated,GENERATORS[0]),(SOURCE,(add(GENERATORS[0][0],ONE),GENERATORS[0][1])),(TARGET,(add(GENERATORS[1][0],ONE),GENERATORS[1][1]))]
    for e,p in tests: require(not curve_check(e,p),'mutated model/generator unexpectedly on curve')
    return {'schema':'ct160-actual-nu12-hasse-generator-certificate/v1','status':'[pcc:unverified]','field_size':Q,
            'prime_order_trial_division':True,'Hasse_interval':[low,high], 'unique_subgroup_multiple':4,
            'model_generators':rows,'cubic_trace':Q+1-ORDER,'prime_field_candidates':len(gaps),
            'minimum_trace_gap':min(gaps),'negative_controls_rejected':len(tests)}

if __name__=='__main__': print(json.dumps(audit(),sort_keys=True,separators=(',',':')))
