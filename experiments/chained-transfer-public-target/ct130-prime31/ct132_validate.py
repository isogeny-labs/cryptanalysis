#!/usr/bin/env python3
"""Independent CT132 arithmetic/raw schema validator, intentionally no producer imports.
Checks group, isogeny, public known answers, order, deterministic A/A counters,
and fail-closed mutations. It cannot attest reported elapsed nanoseconds.
"""
import copy
import hashlib
import json
import math
import random
import statistics
import sys

P=2147483033; N=536857417; A=622683939; B=2147483024
G=(911976709,415929193); H=(180482573,1535800095)
R=969960860; I=392507391; L=390258842
WIDTH=math.isqrt(N-1)+1
ARMS=('source_bsgs','source_neg','target_glv')
SEEDS=(20261118,20261119)


def prime(n):
    if n<2:return False
    for t in (2,3,5,7,11,13,17,19,23,29,31):
        if n%t==0:return n==t
    d=n-1;s=0
    while d%2==0:
        d//=2;s+=1
    for v in (2,325,9375,28178,450775,9780504,1795265022):
        v%=n
        if v==0:continue
        x=pow(v,d,n)
        if x==1 or x==n-1:continue
        for _ in range(s-1):
            x=(x*x)%n
            if x==n-1:break
        else:return False
    return True


def add(U,V,a,b):
    if U is None:return V
    if V is None:return U
    x,y=U;u,v=V
    if x==u and (y+v)%P==0:return None
    if x==u:
        lam=(3*x*x+2*a*x+b)*pow(2*y,-1,P)%P
    else:
        lam=(v-y)*pow(u-x,-1,P)%P
    X=(lam*lam-a-x-u)%P
    return(X,(lam*(x-X)-y)%P)


def mul(U,k,a,b):
    S=None
    while k:
        if k&1:S=add(S,U,a,b)
        U=add(U,U,a,b);k>>=1
    return S


def iso(U):
    if U is None or U==(0,0):return None
    x,y=U;z=pow(x,-1,P)
    return((R+(x+A+B*z)*pow(4,-1,P))%P, y*(1-B*z*z)*pow(8,-1,P)%P)


def guard(ok, name):
    if not ok:raise ValueError(name)


def verify(raw,seed):
    d=json.loads(raw)
    guard(d.get('schema')=='ct132-three-arm/v1', 'schema')
    guard(d.get('standing')=='[pcc:unverified]', 'standing')
    guard((d.get('seed'),d.get('source_prime'),d.get('source_a'),d.get('source_b'),
           d.get('source_G'),d.get('target_H'),d.get('subgroup_prime'),d.get('baby_width')) ==
          (seed,P,A,B,list(G),list(H),N,WIDTH),'constants')
    guard(prime(P) and prime(N) and (A*A-4*B)%P!=0, 'prime/nonsingular')
    guard(R*R%P==(-9)%P and I*I%P==P-1 and L*L%N==N-1,'CM')
    guard(mul(G,N,A,B) is None and mul(H,N,0,9) is None and iso(G)==H,'generator/isogeny')
    guard(mul(H,L,0,9)==((-H[0])%P,I*H[1]%P),'eigen')
    guard(abs(4*N-(P+1))<=2*math.isqrt(P)+1,'Hasse')
    guard(type(d.get('peak_rss_kb')) is int and d['peak_rss_kb']>=1024,'RSS')
    rows=d.get('rows')
    guard(type(rows) is list and len(rows)==24,'count')
    rng=random.Random(seed)
    keys=[rng.randrange(N//8,N-1) for _ in range(24)]
    guard(len(set(keys))==24 and d.get('predefined_scalars')==keys,'panel')
    totals={n:0 for n in ARMS}
    adds={n:0 for n in ARMS}
    ratios={n:[] for n in ARMS}
    for ix,(row,k) in enumerate(zip(rows,keys)):
        point=mul(G,k,A,B)
        guard(row.get('scalar')==k and row.get('public_Q')==list(point),'public scalar')
        guard(iso(point)==mul(H,k,0,9),'mapped public')
        expected=list(ARMS+tuple(reversed(ARMS))) if ix%2==0 else list(tuple(reversed(ARMS))+ARMS)
        arm_rows=row.get('observations')
        guard(type(arm_rows) is list and [x.get('arm') for x in arm_rows]==expected and row.get('schedule')==expected,'schedule')
        by_name={n:[] for n in ARMS}
        for x in arm_rows:
            n=x['arm']
            guard(x.get('recovered_log')==k and x.get('source_verified') is True,'recovered scalar')
            for field in ['ns','add_calls','inverse_calls','solver_add_calls','iterations','fruitless_cycles','stored_states']:
                guard(type(x.get(field)) is int,'field type '+field)
            guard(x['ns']>0 and x['add_calls']>0 and x['inverse_calls']>=0 and x['inverse_calls']<=x['add_calls'],'clock/ops')
            guard(0<x['solver_add_calls']<=x['add_calls'],'solver ops')
            if n=='source_bsgs':
                guard(x['stored_states']==WIDTH and x['iterations']==0 and x['fruitless_cycles']==0,'baby table')
            else:
                guard(0<x['iterations']<=1800000 and x['stored_states']>0 and
                      x['stored_states']<=x['iterations'] and 0<=x['fruitless_cycles']<=x['iterations'],'rho bounds')
            by_name[n].append(x)
            totals[n]+=x['ns'];adds[n]+=x['add_calls']
        for n in ARMS:
            guard(len(by_name[n])==2, 'repeats')
            for col in ('recovered_log','add_calls','inverse_calls','solver_add_calls','iterations','fruitless_cycles','stored_states'):
                guard(by_name[n][0][col]==by_name[n][1][col],'A/A deterministic '+col)
            ratios[n].append(max(z['ns'] for z in by_name[n])/min(z['ns'] for z in by_name[n]))
    return dict(seed=seed,targets=24,solves_per_arm=48,total_ns=totals,total_add_calls=adds,
                best_source_over_transfer=min(totals['source_bsgs'],totals['source_neg'])/totals['target_glv'],
                source_bsgs_over_transfer=totals['source_bsgs']/totals['target_glv'],
                source_neg_over_transfer=totals['source_neg']/totals['target_glv'],
                median_AA={n:statistics.median(ratios[n]) for n in ARMS},rss_kb=d['peak_rss_kb'],
                raw_sha256=hashlib.sha256(raw).hexdigest())


def self_test(blob):
    seed=20261118
    original=json.loads(blob)
    if verify(blob,seed)['targets']!=24:raise ValueError('positive failed')
    operations=[
        lambda o:o.__setitem__('subgroup_prime',13),
        lambda o:o.__setitem__('peak_rss_kb',0),
        lambda o:o['rows'][0].__setitem__('public_Q',[10,11]),
        lambda o:o['rows'][0].__setitem__('scalar',42),
        lambda o:o['rows'][0]['observations'][0].__setitem__('recovered_log',3),
        lambda o:o['rows'][0]['observations'][0].__setitem__('source_verified',False),
        lambda o:o['rows'][0]['observations'][0].__setitem__('ns',0),
        lambda o:o['rows'][0]['observations'][0].__setitem__('add_calls',-2),
        lambda o:o['rows'][0]['observations'][0].__setitem__('stored_states',1),
        lambda o:o['rows'][0]['observations'][1].__setitem__('iterations',0),
        lambda o:o['rows'][0]['observations'][5].__setitem__('add_calls',1),
        lambda o:o['rows'][0]['observations'].pop(),
        lambda o:o['rows'][0]['observations'].__setitem__(0,o['rows'][0]['observations'][1]),
        lambda o:o['rows'][0].__setitem__('schedule',list(reversed(o['rows'][0]['schedule'][:-1]))),
    ]
    for i,mutation in enumerate(operations):
        x=copy.deepcopy(original);mutation(x)
        try:verify(json.dumps(x).encode(),seed)
        except (ValueError,KeyError,TypeError,ZeroDivisionError):pass
        else:raise RuntimeError(f'mutation {i} fail-open')
    return len(operations)

if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('usage: ct132_validate.py raw_seed18.json raw_seed19.json')
    with open(sys.argv[1],'rb') as f:r1=f.read()
    with open(sys.argv[2],'rb') as f:r2=f.read()
    result=[verify(r1,20261118),verify(r2,20261119)]
    print(json.dumps({'standing':'[pcc:unverified]','results':result,
                      'synthetic_mutations_rejected':self_test(r1),
                      'scope':'independently rederived arithmetic and raw schema only, not signed execution or timing provenance'},
                     indent=2,sort_keys=True))
