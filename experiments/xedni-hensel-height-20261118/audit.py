"""Independent pure-Python public-grid and exact-Fraction replay."""
from fractions import Fraction as F
from pathlib import Path
import hashlib, itertools, json

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text()); R=json.loads((H/'run-result.json').read_text())
S=H.parent/'xedni-height-selected-two-image-20261116'/'protocol.json'
assert hashlib.sha256(S.read_bytes()).hexdigest()==P['source_protocol_sha256']
assert hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()==R['protocol_sha256']
B=json.loads(S.read_text())

def add(P,Q,A,m=None):
    if P is None: return Q
    if Q is None: return P
    x,y=P; u,v=Q
    if m is not None:
        if x==u and (y+v)%m==0: return None
        lam=((3*x*x+A)*pow(2*y,-1,m))%m if P==Q else ((v-y)*pow(u-x,-1,m))%m
        X=(lam*lam-x-u)%m
        return X,(lam*(x-X)-y)%m
    if x==u and y+v==0: return None
    lam=(3*x*x+A)/(2*y) if P==Q else (v-y)/(u-x)
    X=lam*lam-x-u
    return X,lam*(x-X)-y

def mul(n,P,A,m=None):
    if n<0:
        P=(P[0],(-P[1])%m if m is not None else -P[1]); n=-n
    out=None
    while n:
        if n&1: out=add(out,P,A,m)
        P=add(P,P,A,m); n//=2
    return out

def center(z,p): return z-p if z>p//2 else z
def v(n,p):
    if n==0: return None
    n=abs(n); k=0
    while n%p==0: n//=p; k+=1
    return k
def rat(z):
    z=F(z)
    return {'num':str(z.numerator),'den':str(z.denominator),
            'bits':max(abs(z.numerator).bit_length(),z.denominator.bit_length())}
def modrat(z,M):
    z=F(z)
    if z.numerator==0: return 0
    if z.denominator%M==0 or __import__('math').gcd(z.denominator,M)!=1:
        raise ValueError('nonintegral_rational_reduction')
    return z.numerator*pow(z.denominator,-1,M)%M
def candidate(p,U,V,shift):
    x1,y1,x2,y2=(center(U[0],p)+p*shift[0],center(U[1],p)+p*shift[1],
                  center(V[0],p)+p*shift[2],center(V[1],p)+p*shift[3])
    f1=y1*y1-x1**3; f2=y2*y2-x2**3
    A=F(f1-f2,x1-x2); Bb=F(f1)-A*x1
    assert 4*A**3+27*Bb**2!=0
    assert (modrat(A,p),modrat(Bb,p))==(p-1,p-2)
    assert (x1%p,y1%p)==tuple(U) and (x2%p,y2%p)==tuple(V)
    assert y1*y1==x1**3+A*x1+Bb and y2*y2==x2**3+A*x2+Bb
    return A,Bb,(F(x1),F(y1)),(F(x2),F(y2))
def exact(p,U,V,ab,shift):
    A,Bb,P1,P2=candidate(p,U,V,shift)
    Rr=add(mul(ab[0],P1,A),mul(ab[1],P2,A),A)
    assert Rr is None or Rr[1]!=0
    t=None if Rr is None else -Rr[0]/Rr[1]
    dep=None if t is None or t==0 else v(t.numerator,p)-v(t.denominator,p)
    return {'shift':shift[:],'A':rat(A),'B':rat(Bb),'P1':[rat(z) for z in P1],
            'P2':[rat(z) for z in P2],'R':None if Rr is None else [rat(z) for z in Rr],
            't':None if t is None else rat(t),'depth':dep,'relation':Rr is None,
            'model_bits':max(rat(z)['bits'] for z in (A,Bb,*P1,*P2)),
            'residual_bits':None if Rr is None else max(rat(z)['bits'] for z in Rr)},t

queries=0; vectors=0; hits=0; first=None
for spec in B['fields']:
    p,q,N=spec['p'],spec['q'],spec['order']
    G=None
    for x in range(p):
        for y in range(p):
            if (y*y-x**3+x+2)%p: continue
            T=mul(N//q,(x,y),-1,p)
            if T is not None and mul(q,T,-1,p) is None: G=T; break
        if G is not None: break
    assert G is not None
    for j in range(4):
        w=1+int.from_bytes(hashlib.sha256(f'xedni-hensel-height-v1|{p}|{j}'.encode()).digest(),'big')%(q-1)
        Q=mul(w,G,-1,p); pairs=[]
        for t1,t2 in itertools.permutations(B['offsets'],2):
            U=add(Q,mul(-t1,G,-1,p),-1,p); V=add(Q,mul(-t2,G,-1,p),-1,p)
            if U is not None and V is not None: pairs.append((t1,t2,U,V))
            if len(pairs)==16: break
        assert len(pairs)==16
        for qi,(t1,t2,U,V) in enumerate(pairs):
            queries+=1
            for vi,(a,b) in enumerate(B['vectors']):
                vectors+=1
                relation=add(mul(a,U,-1,p),mul(b,V,-1,p),-1,p) is None
                assert relation==((a*(w-t1)+b*(w-t2))%q==0)
                hits+=int(relation)
                if first is None and relation and U[0]!=V[0]:
                    first={'p':p,'q':q,'order':N,'G':list(G),'target_index':j,'w':w,
                           'query_index':qi,'t1':t1,'t2':t2,'U':list(U),'V':list(V),
                           'vector_index':vi,'a':a,'b':b,'event_index':queries-1,
                           'vector_event_index':vectors-1}
assert (queries,vectors,hits,first)==(R['queries'],R['vector_tests'],R['public_hits'],R['selected'])
p=first['p']; U=first['U']; V=first['V']; ab=(first['a'],first['b'])
shift=[0,0,0,0]
e,t=exact(p,U,V,ab,shift)
assert e==R['steps'][0]
assert len(R['steps'])==P['maximum_target_depth']
for k,row in enumerate(R['steps'][1:],1):
    assert row['k']==k and row['shift_before']==shift
    M=p**(k+1)
    assert modrat(t,M)==row['t_before_mod']
    if row['status']=='already_deeper':
        assert modrat(t,M)==0 and row['shift_after']==shift
        assert row['exact']==e
        continue
    assert row['status']=='accepted'
    assert modrat(t,M)%p**k==0
    for rec in row['axes']:
        trial=shift[:]; axis=rec['axis']; trial[axis]+=p**(k-1)
        assert trial==rec['trial_shift'] and rec['status']=='pass'
        _,tp=exact(p,U,V,ab,trial)
        t1=modrat(tp,M)
        assert rec['t_probe_mod']==t1
        d=((t1-row['t_before_mod'])//p**k)%p
        assert rec['derivative']==d
        if d:
            delta=-(row['t_before_mod']//p**k)*pow(d,-1,p)%p
            assert rec['delta']==delta and rec==row['axes'][-1]
            assert (axis,delta)==(row['chosen_axis'],row['delta'])
        else: assert rec==row['axes'][-1] or 'delta' not in rec
    shift[row['chosen_axis']]+=p**(k-1)*row['delta']
    assert row['shift_after']==shift
    e,t=exact(p,U,V,ab,shift)
    assert e==row['exact']
    assert modrat(t,M)==row['t_after_mod']==0
    assert e['depth']>=k+1
assert R['status']=='depth_cap'
out={'schema':'xedni-hensel-height-audit-v1','status':'pass','queries':queries,
     'vector_tests':vectors,'public_hits':hits,'selected_event_index':first['event_index'],
     'selected_vector_event_index':first['vector_event_index'],
     'depths':[x['depth'] if 'depth' in x else x['exact']['depth'] for x in R['steps']],
     'model_bits':[x['model_bits'] if 'model_bits' in x else x['exact']['model_bits'] for x in R['steps']]}
(H/'audit-result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
