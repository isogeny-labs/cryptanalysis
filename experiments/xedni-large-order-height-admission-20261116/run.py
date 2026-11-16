"""Frozen public-vector search followed by conditional rational witness search."""
from sage.all import EllipticCurve, GF, QQ, inverse_mod
from pathlib import Path
from fractions import Fraction
import hashlib, itertools, json, time

HERE=Path(__file__).resolve().parent
P=json.loads((HERE/'protocol.json').read_text())
SRC=HERE.parent/'xedni-large-order-admission-20261115'/'result.json'
assert hashlib.sha256(SRC.read_bytes()).hexdigest()==P['source_sha256']
START=time.monotonic()

def emit(f,r): f.write(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n')
def coords(T): return None if T.is_zero() else [int(T[0]),int(T[1])]
def center(z,p): return z-p if z>p//2 else z
def rational(z): return Fraction(int(z.numerator()),int(z.denominator()))
def bits(z):
    f=rational(z); return max(abs(f.numerator).bit_length(),f.denominator.bit_length())
def mod(z,p):
    f=rational(z)
    if f.denominator%p==0: raise ValueError('nonintegral_reduction')
    return f.numerator*pow(f.denominator,-1,p)%p

def generator(E,p,q,N):
    for x in range(p):
        for T in sorted(E.lift_x(GF(p)(x),all=True),key=lambda z:int(z[1])):
            G=(N//q)*T
            if not G.is_zero() and (q*G).is_zero(): return G
    raise ValueError('generator_missing')

public_path=HERE/'public.jsonl'; lift_path=HERE/'lifts.jsonl'
count={k:0 for k in ('public_attempts','public_hits','public_nonhits','lift_events','lift_attempts','lift_pass','lift_failure','control_events')}
with public_path.open('w') as public, lift_path.open('w') as lifts:
  for spec in P['fields']:
    p,q,N=spec['p'],spec['q'],spec['order']
    E=EllipticCurve(GF(p),P['curve_coefficients'])
    assert int(E.cardinality())==N
    G=generator(E,p,q,N)
    for j in range(4):
      digest=hashlib.sha256(f'xedni-large-height-v1|{p}|{j}'.encode()).digest()
      w=1+int.from_bytes(digest,'big')%(q-1)
      Q=w*G
      queries=[]
      for t1,t2 in itertools.permutations(P['offsets'],2):
        U,V=Q-t1*G,Q-t2*G
        if not U.is_zero() and not V.is_zero(): queries.append((t1,t2,U,V))
        if len(queries)==16: break
      assert len(queries)==16
      events=[]; control=None
      for qi,(t1,t2,U,V) in enumerate(queries):
        for vi,(a,b) in enumerate(P['vectors']):
          hit=(a*U+b*V).is_zero()
          assert hit==((a*(w-t1)+b*(w-t2))%q==0)
          row={'p':p,'q':q,'order':N,'G':coords(G),'target_index':j,'w':w,
               'query_index':qi,'t1':t1,'t2':t2,'U':coords(U),'V':coords(V),
               'vector_index':vi,'a':a,'b':b,'public_relation':hit}
          emit(public,row); count['public_attempts']+=1
          count['public_hits' if hit else 'public_nonhits']+=1
          if hit: events.append((row,U,False))
          elif control is None: control=(row,U,True)
      assert control is not None
      events.append(control); count['control_events']+=1
      for row,U,is_control in events:
        a,b=row['a'],row['b']
        S=int(inverse_mod(b%q,q))*U
        x0,y0=[center(z,p) for z in coords(S)]
        assert (y0*y0-x0*x0*x0+x0+2)%p==0
        eid=f"p{p}-j{j}-q{row['query_index']}-v{row['vector_index']}"
        count['lift_events']+=1
        for kx,ky,kA in itertools.product((-1,0,1),repeat=3):
          x,y,A=x0+kx*p,y0+ky*p,-1+kA*p
          B=y*y-x*x*x-A*x
          rec={'event_id':eid,'control':is_control,'p':p,'q':q,'target_index':j,
               'query_index':row['query_index'],'vector_index':row['vector_index'],
               'public_relation':row['public_relation'],'a':a,'b':b,
               'shift':[kx,ky,kA],'x':x,'y':y,'A':A,'B':B}
          count['lift_attempts']+=1
          try:
            assert -16*(4*A**3+27*B**2)!=0
            assert (A+1)%p==0 and (B+2)%p==0
            C=EllipticCurve(QQ,[A,B]); T=C(QQ(x),QQ(y)); R1=b*T; R2=-a*T
            assert not R1.is_zero() and not R2.is_zero()
            assert (a*R1+b*R2).is_zero()
            r1=[mod(R1[0],p),mod(R1[1],p)]
            r2=[mod(R2[0],p),mod(R2[1],p)]
            assert r1==row['U']
            match=r2==row['V']
            assert match==row['public_relation']
            score=max(bits(z) for z in (QQ(A),QQ(B),R1[0],R1[1],R2[0],R2[1]))
            rec.update({'status':'pass','second_match':match,'score_bits':score,
                        'P':[str(R1[0]),str(R1[1])],'R':[str(R2[0]),str(R2[1])],
                        'P_reduction':r1,'R_reduction':r2})
            count['lift_pass']+=1
          except Exception as exc:
            rec.update({'status':'failure','error':f'{type(exc).__name__}: {exc}'})
            count['lift_failure']+=1
          emit(lifts,rec)
          if time.monotonic()-START>P['run_cap_seconds']:
            raise TimeoutError('run_cap_seconds exceeded')
assert count['public_attempts']==8*4*16*13
assert count['lift_attempts']==27*count['lift_events']
result={'schema':'xedni-large-order-height-admission-result-v1',
        'status':'complete' if count['lift_failure']==0 else 'failed_attempts',
        'counts':count,'elapsed_wall_seconds':time.monotonic()-START,
        'protocol_sha256':hashlib.sha256((HERE/'protocol.json').read_bytes()).hexdigest(),
        'public_sha256':hashlib.sha256(public_path.read_bytes()).hexdigest(),
        'lifts_sha256':hashlib.sha256(lift_path.read_bytes()).hexdigest()}
(HERE/'run-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2,sort_keys=True))
