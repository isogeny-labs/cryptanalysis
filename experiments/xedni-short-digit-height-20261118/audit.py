"""Independent exact-Fraction replay and brute-force signed-digit optimality audit."""
from fractions import Fraction as F
from pathlib import Path
import hashlib, itertools, json, math

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text()); R=json.loads((H/'run-result.json').read_text())
BH=H.parent/'xedni-hensel-height-20261118'
assert hashlib.sha256((BH/'protocol.json').read_bytes()).hexdigest()==P['baseline_protocol_sha256']
B=json.loads((BH/'run-result.json').read_text()); B.pop('elapsed_wall_seconds')
assert hashlib.sha256(json.dumps(B,sort_keys=True).encode()).hexdigest()==P['baseline_result_normalized_sha256']
assert hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()==R['protocol_sha256']
hit=B['selected']; assert R['selected']==hit
p=hit['p']; U=hit['U']; V=hit['V']; ab=(hit['a'],hit['b'])

def add(P,Q,A):
    if P is None: return Q
    if Q is None: return P
    x,y=P; u,v=Q
    if x==u and y+v==0: return None
    lam=(3*x*x+A)/(2*y) if P==Q else (v-y)/(u-x)
    X=lam*lam-x-u
    return X,lam*(x-X)-y
def mul(n,P,A):
    if n<0: P=(P[0],-P[1]); n=-n
    out=None
    while n:
        if n&1: out=add(out,P,A)
        P=add(P,P,A); n//=2
    return out
def center(z): return z-p if z>p//2 else z
def rat(z):
    z=F(z)
    return {'num':str(z.numerator),'den':str(z.denominator),
            'bits':max(abs(z.numerator).bit_length(),z.denominator.bit_length())}
def vp(n):
    if n==0: return None
    n=abs(n); k=0
    while n%p==0: n//=p; k+=1
    return k
def red(z,M):
    z=F(z)
    assert math.gcd(z.denominator,M)==1
    return z.numerator*pow(z.denominator,-1,M)%M
def exact(shift):
    x1,y1,x2,y2=(center(U[0])+p*shift[0],center(U[1])+p*shift[1],
                  center(V[0])+p*shift[2],center(V[1])+p*shift[3])
    f1=y1*y1-x1**3; f2=y2*y2-x2**3
    A=F(f1-f2,x1-x2); Bb=F(f1)-A*x1
    assert 4*A**3+27*Bb**2!=0
    assert (red(A,p),red(Bb,p))==(p-1,p-2)
    P1=(F(x1),F(y1)); P2=(F(x2),F(y2))
    assert y1*y1==x1**3+A*x1+Bb and y2*y2==x2**3+A*x2+Bb
    Rr=add(mul(ab[0],P1,A),mul(ab[1],P2,A),A)
    assert Rr is None or Rr[1]!=0
    t=None if Rr is None else -Rr[0]/Rr[1]
    dep=None if t is None or t==0 else vp(t.numerator)-vp(t.denominator)
    rec={'shift':shift[:],'A':rat(A),'B':rat(Bb),
         'P1':[rat(z) for z in P1],'P2':[rat(z) for z in P2],
         'R':None if Rr is None else [rat(z) for z in Rr],
         't':None if t is None else rat(t),'depth':dep,'relation':Rr is None,
         'model_bits':max(rat(z)['bits'] for z in (A,Bb,*P1,*P2)),
         'residual_bits':None if Rr is None else max(rat(z)['bits'] for z in Rr)}
    return rec,t

shift=[0]*4; e,t=exact(shift)
assert R['steps'][0]==e
for k,row in enumerate(R['steps'][1:],1):
    assert row['k']==k and row['shift_before']==shift and row['status']=='accepted'
    M=p**(k+1); before=red(t,M)
    assert before==row['t_before_mod'] and before%p**k==0
    derivatives=[]
    for axis,probe in enumerate(row['probes']):
        trial=shift[:]; trial[axis]+=p**(k-1)
        assert probe['axis']==axis and probe['trial_shift']==trial and probe['status']=='pass'
        _,tp=exact(trial); t1=red(tp,M)
        assert t1==probe['t_probe_mod'] and (t1-before)%p**k==0
        d=((t1-before)//p**k)%p
        assert d==probe['derivative']; derivatives.append(d)
    assert derivatives==row['derivatives']
    target=-(before//p**k)%p
    assert target==row['target_digit']
    hmax=row['radius_search'][-1]['radius']; best=None
    for h in range(hmax+1):
        count=0; local=None
        for ds in itertools.product(range(-h,h+1),repeat=4):
            if sum(d*z for d,z in zip(derivatives,ds))%p!=target: continue
            count+=1
            key=(sum(abs(z) for z in ds),ds)
            if local is None or key<local[0]: local=(key,ds)
        assert row['radius_search'][h]=={'radius':h,'solutions_within_radius':count}
        if local is not None:
            assert h==hmax
            best=list(local[1]); break
    assert best==row['digits']
    shift=[z+p**(k-1)*d for z,d in zip(shift,best)]
    assert shift==row['shift_after']
    e,t=exact(shift)
    assert e==row['exact'] and red(t,M)==row['t_after_mod']==0
    assert e['depth']>=k+1
assert R['status']=='depth_cap'
base_bits=[s.get('model_bits',s.get('exact',{}).get('model_bits')) for s in B['steps']]
short_bits=[s.get('model_bits',s.get('exact',{}).get('model_bits')) for s in R['steps']]
out={'schema':'xedni-short-digit-height-audit-v1','status':'pass','depths':list(range(1,9)),
     'baseline_model_bits':base_bits,'short_digit_model_bits':short_bits,
     'delta_bits':[a-b for a,b in zip(short_bits,base_bits)],
     'maximum_digit_radius':max(x['radius_search'][-1]['radius'] for x in R['steps'][1:]),
     'replayed_steps':len(R['steps'])-1}
(H/'audit-result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
