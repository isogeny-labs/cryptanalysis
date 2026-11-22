#!/usr/bin/env python3
"""Independent stdlib arithmetic and raw-output auditor for CT131. No producer import."""
import json,sys,math,random,hashlib,copy
p=2147483033;q=536857417; a=622683939;b=2147483024
r=969960860;j=392507391; lam=390258842
G=(911976709,415929193); H=(180482573,1535800095)

def plus(P,Q,aa,bb):
    if P is None:return Q
    if Q is None:return P
    x,y=P;z,w=Q
    if x==z and (y+w)%p==0:return None
    if x==z: t=(3*x*x+2*aa*x+bb)*pow(2*y,-1,p)%p
    else:t=(w-y)*pow(z-x,-1,p)%p
    u=(t*t-aa-x-z)%p
    return(u, (t*(x-u)-y)%p)

def mul(P,n,aa,bb):
    S=None
    while n>0:
        if n&1:S=plus(S,P,aa,bb)
        P=plus(P,P,aa,bb);n>>=1
    return S

def iso(P):
    if P is None or P==(0,0):return None
    x,y=P;z=pow(x,-1,p)
    return(((x+a+b*z)*pow(4,-1,p)+r)%p, (y*(1-b*z*z)*pow(8,-1,p))%p)

def prime(n):
    if n<2:return False
    for d in [2,3,5,7,11,13,17,19,23,29,31]:
        if n%d==0:return n==d
    k=n-1;s=0
    while k%2==0:s+=1;k//=2
    for t in (2,325,9375,28178,450775,9780504,1795265022):
        t%=n
        if not t:continue
        h=pow(t,k,n)
        if h in (1,n-1):continue
        for _ in range(s-1):
            h=h*h%n
            if h==n-1:break
        else:return False
    return True

def check(obj,seed):
    if obj.get('schema')!='ct131-cm-glv-rho/v1':raise ValueError('schema')
    if obj.get('standing')!='[pcc:unverified]':raise ValueError('standing')
    if (obj['field_p'],obj['subgroup_q'],obj['source_a'],obj['source_b'],obj['source_G'],obj['target_H'],obj['seed']) != (p,q,a,b,list(G),list(H),seed):raise ValueError('constants')
    if not (prime(p) and prime(q) and q%4==1):raise ValueError('prime')
    if not (r*r%p==(-9)%p and j*j%p==p-1 and lam*lam%q==q-1):raise ValueError('endomorphism root')
    if mul(G,q,a,b) is not None or mul(H,q,0,9) is not None or iso(G)!=H:raise ValueError('base/order')
    if abs(4*q-(p+1))>2*math.isqrt(p)+1 or 4*q<4*math.isqrt(p):raise ValueError('Hasse uniqueness')
    if mul(H,lam,0,9)!=((-H[0])%p,j*H[1]%p):raise ValueError('GLV eigenvalue')
    rows=obj.get('rows',[])
    if len(rows)!=64:raise ValueError('count')
    rng=random.Random(seed)
    expected=[rng.randrange(q//8,q-1) for _ in rows]
    if obj.get('predefined_scalars')!=expected:raise ValueError('frozen scalar panel')
    totals={'source_neg':0,'target_glv':0}
    counts={'source_neg':0,'target_glv':0}
    for idx,(row,k) in enumerate(zip(rows,expected)):
        if row.get('scalar')!=k:raise ValueError('scalar')
        P=mul(G,k,a,b)
        if row.get('public_Q')!=list(P) or iso(P)!=mul(H,k,0,9):raise ValueError('public log')
        expected_arms=['source_neg','target_glv','target_glv','source_neg'] if idx%2==0 else ['target_glv','source_neg','source_neg','target_glv']
        arms=row.get('arms',[])
        if [x.get('arm') for x in arms]!=expected_arms:raise ValueError('ABBA order')
        same={}
        for arm in arms:
            mode=arm['arm']
            if arm.get('recovered_log')!=k or arm.get('verified') is not True:raise ValueError('recovered log')
            if any(type(arm.get(t)) is not int or arm[t]<=0 for t in ['ns','iterations','add_calls','inverse_calls','stored_states']):raise ValueError('sample positive')
            if type(arm.get('fruitless_cycles')) is not int or arm['fruitless_cycles']<0:raise ValueError('cycle count')
            if arm['inverse_calls']>arm['add_calls'] or arm['add_calls']<arm['iterations']:raise ValueError('ops')
            if arm['stored_states']>arm['iterations']:raise ValueError('memory')
            signature=(arm['iterations'],arm['fruitless_cycles'],arm['stored_states'],arm['add_calls'],arm['inverse_calls'])
            if mode in same and signature!=same[mode]:raise ValueError('A/A deterministic walk')
            same[mode]=signature
            totals[mode]+=arm['ns'];counts[mode]+=1
    if counts!={'source_neg':128,'target_glv':128}:raise ValueError('arm balance')
    if type(obj.get('peak_rss_kb')) is not int or obj['peak_rss_kb']<1024:raise ValueError('rss')
    return dict(seed=seed,paired=64,source_ns=totals['source_neg'],target_ns=totals['target_glv'],time_ratio=totals['source_neg']/totals['target_glv'],rss_kb=obj['peak_rss_kb'])

def run():
    reports=[]
    for seed,path in [(20261116,sys.argv[1]),(20261117,sys.argv[2])]:
        with open(path,'rb') as f:raw=f.read()
        obj=json.loads(raw)
        reports.append(dict(check(obj,seed),sha256=hashlib.sha256(raw).hexdigest()))
        for tag,mut in [
            ('wrong_log',lambda x:x['rows'][0]['arms'][0].__setitem__('recovered_log',3)),
            ('wrong_point',lambda x:x['rows'][0].__setitem__('public_Q',[10,11])),
            ('wrong_q',lambda x:x.__setitem__('subgroup_q',13)),
            ('missing_arm',lambda x:x['rows'][0]['arms'].pop()),
            ('wrong_ops',lambda x:x['rows'][0]['arms'][0].__setitem__('inverse_calls',10**10)),
            ('wrong_AA',lambda x:x['rows'][0]['arms'][3].__setitem__('iterations',1)),
            ('wrong_schedule',lambda x:x['rows'][0]['arms'].__setitem__(slice(0,2), list(reversed(x['rows'][0]['arms'][:2])))),
            ('missing_memory',lambda x:x.__setitem__('peak_rss_kb',0))]:
            v=copy.deepcopy(obj);mut(v)
            try:check(v,seed)
            except (ValueError,KeyError,TypeError,AssertionError):pass
            else:raise RuntimeError(f'fail-open mutation {tag}, seed {seed}')
    print(json.dumps({'arithmetic':'checked independently', 'raw':reports,'synthetic_mutations_rejected':16,'standing':'[pcc:unverified]'},sort_keys=True,indent=2))
if __name__=='__main__':run()
