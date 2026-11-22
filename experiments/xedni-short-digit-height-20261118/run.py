"""Four-coordinate minimum signed-digit lift of the frozen public relation."""
from sage.all import EllipticCurve, QQ
from fractions import Fraction
from pathlib import Path
import hashlib, json, time

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
BH=H.parent/'xedni-hensel-height-20261118'
assert hashlib.sha256((BH/'protocol.json').read_bytes()).hexdigest()==P['baseline_protocol_sha256']
B=json.loads((BH/'run-result.json').read_text())
BN={k:v for k,v in B.items() if k!='elapsed_wall_seconds'}
assert hashlib.sha256(json.dumps(BN,sort_keys=True).encode()).hexdigest()==P['baseline_result_normalized_sha256']
assert B['status']=='depth_cap' and len(B['steps'])==P['maximum_target_depth']
hit=B['selected']; p=hit['p']; U=hit['U']; V=hit['V']; ab=(hit['a'],hit['b'])
start=time.monotonic()

def center(z): return z-p if z>p//2 else z
def parts(z):
    z=Fraction(str(z)); return z.numerator,z.denominator
def rational(z):
    n,d=parts(z)
    return {'num':str(n),'den':str(d),'bits':max(abs(n).bit_length(),d.bit_length())}
def vp(n):
    if not n: return None
    n=abs(n); k=0
    while n%p==0: n//=p; k+=1
    return k
def red(z,M):
    n,d=parts(z)
    if __import__('math').gcd(d,M)!=1: raise ValueError('nonunit_denominator')
    return n*pow(d,-1,M)%M
def exact(shift):
    x1,y1,x2,y2=(center(U[0])+p*shift[0],center(U[1])+p*shift[1],
                  center(V[0])+p*shift[2],center(V[1])+p*shift[3])
    f1=y1*y1-x1**3; f2=y2*y2-x2**3
    A=Fraction(f1-f2,x1-x2); Bb=Fraction(f1)-A*x1
    if 4*A**3+27*Bb**2==0: raise ValueError('singular_curve')
    if (red(A,p),red(Bb,p))!=(p-1,p-2): raise ValueError('wrong_reduction')
    assert (x1%p,y1%p)==tuple(U) and (x2%p,y2%p)==tuple(V)
    C=EllipticCurve(QQ,[QQ(A.numerator)/A.denominator,QQ(Bb.numerator)/Bb.denominator])
    P1=C(x1,y1); P2=C(x2,y2)
    R=ab[0]*P1+ab[1]*P2
    if not R.is_zero() and R[1]==0: raise ValueError('formal_parameter_pole')
    t=None if R.is_zero() else -R[0]/R[1]
    n,d=(0,1) if t is None else parts(t)
    depth=None if not n else vp(n)-vp(d)
    rec={'shift':shift[:],'A':rational(A),'B':rational(Bb),
         'P1':[rational(z) for z in (x1,y1)],'P2':[rational(z) for z in (x2,y2)],
         'R':None if R.is_zero() else [rational(R[0]),rational(R[1])],
         't':None if t is None else rational(t),'depth':depth,'relation':bool(R.is_zero()),
         'model_bits':max(rational(z)['bits'] for z in (A,Bb,x1,y1,x2,y2)),
         'residual_bits':None if R.is_zero() else max(rational(z)['bits'] for z in (R[0],R[1]))}
    return rec,t

def digits(deriv,target):
    """Minimize (radius, L1, signed tuple) via pair-sum lookup."""
    history=[]
    for h in range((p-1)//2+1):
        best_pair={}; pair_count={}
        for u in range(-h,h+1):
            for v in range(-h,h+1):
                residue=(deriv[2]*u+deriv[3]*v)%p
                pair_count[residue]=pair_count.get(residue,0)+1
                key=(abs(u)+abs(v),u,v)
                if residue not in best_pair or key<best_pair[residue][0]:
                    best_pair[residue]=(key,(u,v))
        best=None; solutions=0
        for x in range(-h,h+1):
            for y in range(-h,h+1):
                residue=(target-deriv[0]*x-deriv[1]*y)%p
                solutions+=pair_count.get(residue,0)
                if residue in best_pair:
                    u,v=best_pair[residue][1]
                    tup=(x,y,u,v)
                    key=(sum(abs(z) for z in tup),tup)
                    if best is None or key<best[0]: best=(key,tup)
        history.append({'radius':h,'solutions_within_radius':solutions})
        if best is not None:
            assert sum(d*z for d,z in zip(deriv,best[1]))%p==target
            return list(best[1]),history
    raise ValueError('digit_exhausted')

shift=[0,0,0,0]; first,t=exact(shift)
assert first==B['steps'][0]
steps=[first]; stop='depth_cap'
for k in range(1,P['maximum_target_depth']):
    prior=steps[-1].get('exact',steps[-1])
    if prior['relation']: stop='exact_relation'; break
    if prior['depth'] is None or prior['depth']<k: stop='depth_mismatch'; break
    M=p**(k+1); before=red(t,M)
    row={'k':k,'shift_before':shift[:],'t_before_mod':before,'probes':[]}
    if before%p**k: stop='depth_mismatch'; row['status']=stop; steps.append(row); break
    if before==0:
        row.update({'status':'already_deeper','shift_after':shift[:],'exact':prior})
        steps.append(row); continue
    deriv=[]
    for axis in range(4):
        trial=shift[:]; trial[axis]+=p**(k-1)
        rec={'axis':axis,'trial_shift':trial}
        try:
            _,probe_t=exact(trial)
            t1=red(probe_t,M)
            if (t1-before)%p**k: raise ValueError('nonlinear_probe')
            d=((t1-before)//p**k)%p
            rec.update({'status':'pass','t_probe_mod':t1,'derivative':d})
            deriv.append(d)
        except Exception as exc:
            rec.update({'status':'failure','error':f'{type(exc).__name__}: {exc}'})
        row['probes'].append(rec)
    if len(deriv)!=4:
        row['status']='probe_failure'; steps.append(row); stop='probe_failure'; break
    target=-(before//p**k)%p
    row.update({'derivatives':deriv,'target_digit':target})
    try: chosen,history=digits(deriv,target)
    except Exception as exc:
        row.update({'status':'digit_exhausted','error':str(exc)}); steps.append(row)
        stop='digit_exhausted'; break
    row['radius_search']=history; row['digits']=chosen
    shift=[z+p**(k-1)*d for z,d in zip(shift,chosen)]
    row['shift_after']=shift[:]
    row['exact'],t=exact(shift)
    row['t_after_mod']=red(t,M) if t is not None else 0
    row['status']='accepted'
    steps.append(row)
    if row['t_after_mod']!=0 or row['exact']['depth'] is not None and row['exact']['depth']<k+1:
        stop='exact_modular_mismatch'; break
    if time.monotonic()-start>P['run_cap_seconds']: stop='run_cap_seconds'; break
result={'schema':'xedni-short-digit-height-result-v1','status':stop,
        'protocol_sha256':hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest(),
        'baseline_result_normalized_sha256':P['baseline_result_normalized_sha256'],
        'selected':hit,'steps':steps,'elapsed_wall_seconds':time.monotonic()-start}
(H/'run-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':stop,'digits':[s.get('digits') for s in steps[1:]],
                  'depths':[s.get('depth',s.get('exact',{}).get('depth')) for s in steps],
                  'model_bits':[s.get('model_bits',s.get('exact',{}).get('model_bits')) for s in steps],
                  'elapsed_wall_seconds':result['elapsed_wall_seconds']},indent=2))
