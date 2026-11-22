"""Frozen, single-hit Hensel coordinate experiment; run with the checked Sage launcher."""
from sage.all import EllipticCurve, GF, QQ
from fractions import Fraction
from pathlib import Path
import hashlib, itertools, json, time

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
S=H.parent/'xedni-height-selected-two-image-20261116'/'protocol.json'
assert hashlib.sha256(S.read_bytes()).hexdigest()==P['source_protocol_sha256']
BASE=json.loads(S.read_text())
start=time.monotonic()

def center(z,p): return z-p if z>p//2 else z
def coords(T): return None if T.is_zero() else [int(T[0]),int(T[1])]
def parts(z):
    z=Fraction(str(z))
    return z.numerator,z.denominator
def rat(z):
    n,d=parts(z); return {'num':str(n),'den':str(d),'bits':max(abs(n).bit_length(),d.bit_length())}
def v(n,p):
    if n==0: return None
    n=abs(n); k=0
    while n%p==0: n//=p; k+=1
    return k
def vre(z,p):
    n,d=parts(z)
    return None if n==0 else v(n,p)-v(d,p)
def mod(z,M):
    n,d=parts(z)
    if d%M==0 or __import__('math').gcd(d,M)!=1: raise ValueError('nonunit_coefficient_denominator')
    return n*pow(d,-1,M)%M
def candidate(p,U,V,shift):
    x1,y1,x2,y2=(center(U[0],p)+p*shift[0],center(U[1],p)+p*shift[1],
                  center(V[0],p)+p*shift[2],center(V[1],p)+p*shift[3])
    f1=y1*y1-x1**3; f2=y2*y2-x2**3
    A=Fraction(f1-f2,x1-x2); B=Fraction(f1)-A*x1
    if 4*A**3+27*B**2==0: raise ValueError('singular_curve')
    if (mod(A,p),mod(B,p))!=(p-1,p-2): raise ValueError('wrong_reduction')
    return A,B,(x1,y1),(x2,y2)
def jdbl(P,A,M):
    X,Y,Z=P
    if Z==0 or Y==0: return (0,1,0)
    XX=X*X%M; YY=Y*Y%M; YYYY=YY*YY%M; ZZ=Z*Z%M
    s=2*((X+YY)**2-XX-YYYY)%M; t=(3*XX+A*ZZ*ZZ)%M
    return ((t*t-2*s)%M,(t*(s-(t*t-2*s)%M)-8*YYYY)%M,((Y+Z)**2-YY-ZZ)%M)
def jadd(P,Q,A,M):
    if P[2]==0: return Q
    if Q[2]==0: return P
    X1,Y1,Z1=P; X2,Y2,Z2=Q
    z1=Z1*Z1%M; z2=Z2*Z2%M
    u1=X1*z2%M; u2=X2*z1%M
    s1=Y1*Z2*z2%M; s2=Y2*Z1*z1%M
    if u1==u2: return jdbl(P,A,M) if s1==s2 else (0,1,0)
    h=(u2-u1)%M; i=(2*h)**2%M; j=h*i%M; r=2*(s2-s1)%M; vv=u1*i%M
    return ((r*r-j-2*vv)%M,(r*(vv-(r*r-j-2*vv)%M)-2*s1*j)%M,
            (((Z1+Z2)**2-z1-z2)*h)%M)
def jmul(n,P,A,M):
    if n<0: P=(P[0],-P[1]%M,P[2]); n=-n
    R=(0,1,0)
    while n:
        if n&1: R=jadd(R,P,A,M)
        P=jdbl(P,A,M); n//=2
    return R
def probe(p,U,V,ab,shift,k):
    A,B,P1,P2=candidate(p,U,V,shift); M=p**(k+1)
    am=mod(A,M)
    R=jadd(jmul(ab[0],(P1[0]%M,P1[1]%M,1),am,M),
           jmul(ab[1],(P2[0]%M,P2[1]%M,1),am,M),am,M)
    X,Y,Z=R
    if Z==0:
        if (X,Y)!=(0,1): raise ValueError('noncanonical_infinity')
        return 0
    if Z%p or Y%p==0: raise ValueError('modular_normal_form_failure')
    return -X*Z*pow(Y,-1,M)%M
def exact(p,U,V,ab,shift):
    A,B,Uq,Vq=candidate(p,U,V,shift)
    C=EllipticCurve(QQ,[QQ(A.numerator)/A.denominator,QQ(B.numerator)/B.denominator])
    P1=C(*Uq); P2=C(*Vq); R=ab[0]*P1+ab[1]*P2
    t=None if R.is_zero() else -R[0]/R[1]
    dep=None if t is None else vre(t,p)
    if not R.is_zero() and R[1]==0: raise ValueError('formal_parameter_pole')
    return {'shift':shift[:], 'A':rat(A),'B':rat(B),'P1':[rat(z) for z in Uq],
            'P2':[rat(z) for z in Vq], 'R':None if R.is_zero() else [rat(R[0]),rat(R[1])],
            't':None if t is None else rat(t), 'depth':dep,
            'relation':bool(R.is_zero()),
            'model_bits':max(rat(z)['bits'] for z in (A,B,*Uq,*Vq)),
            'residual_bits':None if R.is_zero() else max(rat(z)['bits'] for z in (R[0],R[1]))}

hit=None; total_queries=0; total_vectors=0; public_hits=0
for spec in BASE['fields']:
    p,q,N=spec['p'],spec['q'],spec['order']; E=EllipticCurve(GF(p),[-1,-2])
    assert int(E.cardinality())==N
    G=None
    for x in range(p):
        for T in sorted(E.lift_x(GF(p)(x),all=True),key=lambda z:int(z[1])):
            V=(N//q)*T
            if not V.is_zero() and (q*V).is_zero(): G=V; break
        if G is not None: break
    assert G is not None
    for target_index in range(4):
        w=1+int.from_bytes(hashlib.sha256(f'xedni-hensel-height-v1|{p}|{target_index}'.encode()).digest(),'big')%(q-1)
        Q=w*G; queries=[]
        for t1,t2 in itertools.permutations(BASE['offsets'],2):
            U=Q-t1*G; V=Q-t2*G
            if not U.is_zero() and not V.is_zero(): queries.append((t1,t2,U,V))
            if len(queries)==16: break
        assert len(queries)==16
        for query_index,(t1,t2,U,V) in enumerate(queries):
            total_queries+=1
            for vector_index,(a,b) in enumerate(BASE['vectors']):
                total_vectors+=1
                pub=(a*U+b*V).is_zero()
                assert pub==((a*(w-t1)+b*(w-t2))%q==0)
                public_hits+=int(pub)
                if hit is None and pub and int(U[0])!=int(V[0]):
                    hit={'p':p,'q':q,'order':N,'G':coords(G),'target_index':target_index,
                         'w':w,'query_index':query_index,'t1':t1,'t2':t2,
                         'U':coords(U),'V':coords(V),'vector_index':vector_index,'a':a,'b':b,
                         'event_index':total_queries-1,'vector_event_index':total_vectors-1}
            if time.monotonic()-start>P['run_cap_seconds']: raise TimeoutError('run_cap_seconds')
assert (total_queries,total_vectors)==(512,6656)
assert hit is not None
p=hit['p']; U=hit['U']; V=hit['V']; ab=(hit['a'],hit['b']); shift=[0]*4
steps=[exact(p,U,V,ab,shift)]
stop='depth_cap'
for k in range(1,P['maximum_target_depth']):
    prior=steps[-1].get('exact',steps[-1])
    if prior['relation']: stop='exact_relation'; break
    if prior['depth'] is None or prior['depth']<k:
        stop='exact_modular_mismatch'; break
    row={'k':k,'shift_before':shift[:],'axes':[]}
    try: t0=probe(p,U,V,ab,shift,k)
    except Exception as exc:
        row['status']='modular_failure'; row['error']=str(exc); steps.append(row); stop='modular_failure'; break
    row['t_before_mod']=t0
    if t0%p**k: row['status']='unexpected_depth'; steps.append(row); stop='exact_modular_mismatch'; break
    if t0==0:
        row['status']='already_deeper'; row['shift_after']=shift[:]
        row['exact']=exact(p,U,V,ab,shift); steps.append(row); continue
    chosen=None
    for axis in range(4):
        trial=shift[:]; trial[axis]+=p**(k-1)
        rec={'axis':axis,'trial_shift':trial}
        try:
            t1=probe(p,U,V,ab,trial,k)
            d=((t1-t0)//p**k)%p if (t1-t0)%p**k==0 else None
            rec.update({'status':'pass','t_probe_mod':t1,'derivative':d})
            if d:
                delta=-(t0//p**k)*pow(d,-1,p)%p
                chosen=(axis,delta); rec['delta']=delta
        except Exception as exc: rec.update({'status':'failure','error':str(exc)})
        row['axes'].append(rec)
        if chosen is not None: break
    if chosen is None:
        row['status']='derivative_exhausted'; steps.append(row); stop='derivative_exhausted'; break
    axis,delta=chosen; shift[axis]+=p**(k-1)*delta
    row.update({'status':'accepted','chosen_axis':axis,'delta':delta,'shift_after':shift[:]})
    row['t_after_mod']=probe(p,U,V,ab,shift,k)
    row['exact']=exact(p,U,V,ab,shift)
    steps.append(row)
    if row['t_after_mod']!=0 or row['exact']['depth'] is not None and row['exact']['depth']<k+1:
        stop='exact_modular_mismatch'; break
    if time.monotonic()-start>P['run_cap_seconds']: stop='run_cap_seconds'; break
result={'schema':'xedni-hensel-height-result-v1','status':stop,'protocol_sha256':hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest(),
        'source_protocol_sha256':P['source_protocol_sha256'],'queries':total_queries,'vector_tests':total_vectors,
        'public_hits':public_hits,'selected':hit,'steps':steps,'elapsed_wall_seconds':time.monotonic()-start}
(H/'run-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':stop,'selected':hit,'depths':[x['depth'] if 'depth' in x else x.get('exact',{}).get('depth') for x in steps],
                  'model_bits':[x['model_bits'] if 'model_bits' in x else x.get('exact',{}).get('model_bits') for x in steps],
                  'elapsed_wall_seconds':result['elapsed_wall_seconds']},indent=2))
