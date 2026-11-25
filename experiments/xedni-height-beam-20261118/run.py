"""Frozen width-eight rational-height beam over four-coordinate Hensel lifts."""
from sage.all import EllipticCurve, QQ
from fractions import Fraction
from pathlib import Path
import gzip, hashlib, itertools, json, time

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
BH=H.parent/'xedni-hensel-height-20261118'
B=json.loads((BH/'run-result.json').read_text())
BN={k:v for k,v in B.items() if k!='elapsed_wall_seconds'}
assert hashlib.sha256(json.dumps(BN,sort_keys=True).encode()).hexdigest()==P['baseline_result_normalized_sha256']
SH=H.parent/'xedni-short-digit-height-20261118'
SHORT=json.loads((SH/'run-result.json').read_text())
SN={k:v for k,v in SHORT.items() if k!='elapsed_wall_seconds'}
assert hashlib.sha256(json.dumps(SN,sort_keys=True).encode()).hexdigest()==P['short_digit_result_normalized_sha256']
GH=H.parent/'xedni-model-height-digit-20261118'
GREEDY=json.loads((GH/'run-result.json').read_text())
GN={k:v for k,v in GREEDY.items() if k!='elapsed_wall_seconds'}
assert hashlib.sha256(json.dumps(GN,sort_keys=True).encode()).hexdigest()==P['greedy_model_result_normalized_sha256']
assert B['status']=='depth_cap' and len(B['steps'])==P['maximum_target_depth']
assert SHORT['selected']==GREEDY['selected']==B['selected']
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
def model(shift):
    x1,y1,x2,y2=(center(U[0])+p*shift[0],center(U[1])+p*shift[1],
                  center(V[0])+p*shift[2],center(V[1])+p*shift[3])
    f1=y1*y1-x1**3; f2=y2*y2-x2**3
    A=Fraction(f1-f2,x1-x2); Bb=Fraction(f1)-A*x1
    if 4*A**3+27*Bb**2==0: raise ValueError('singular_curve')
    if (red(A,p),red(Bb,p))!=(p-1,p-2): raise ValueError('wrong_reduction')
    assert (x1%p,y1%p)==tuple(U) and (x2%p,y2%p)==tuple(V)
    return A,Bb,(x1,y1),(x2,y2),max(rational(z)['bits'] for z in (A,Bb,x1,y1,x2,y2))
def exact(shift):
    A,Bb,(x1,y1),(x2,y2),model_bits=model(shift)
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
         'model_bits':model_bits,
         'residual_bits':None if R.is_zero() else max(rational(z)['bits'] for z in (R[0],R[1]))}
    return rec,t

def minimum_radius(deriv,target):
    """Find the first feasible radius via pair-sum lookup."""
    history=[]
    for h in range(P['minimum_radius_search_limit']+1):
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
            return h,history
    raise ValueError('radius_exhausted')

def rank(rec):
    shift=rec['shift']; digits=rec['digits']
    return (rec['model_bits'],max(abs(z) for z in shift),sum(abs(z) for z in shift),
            tuple(shift),rec['parent_id'],tuple(digits))

def pack(depth,rows):
    raw=(''.join(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n' for row in rows)).encode()
    blob=gzip.compress(raw,compresslevel=9,mtime=0)
    name=f'ledger.depth{depth}.jsonl.gz'
    (H/name).write_bytes(blob)
    return {'path':name,'rows':len(rows),'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'gzip_sha256':hashlib.sha256(blob).hexdigest(),'gzip_bytes':len(blob)}

first,_=exact([0,0,0,0])
assert first==B['steps'][0]
beam=[{'id':'D1:0','parent_id':None,'digits':[0,0,0,0],
       'shift':[0,0,0,0],'exact':first}]
stages=[{'depth':1,'status':'initial','beam':beam,'candidate_count':1}]
stop='depth_cap'
for k in range(1,P['maximum_target_depth']):
    M=p**(k+1); ledger=[]; candidates=[]; parent_rows=[]
    for state in beam:
        s=state['shift']; prior=state['exact']
        parent={'kind':'parent','parent_id':state['id'],'shift':s[:],'probes':[]}
        if prior['relation']:
            parent['status']='exact_relation'; parent_rows.append(parent); ledger.append(parent)
            continue
        if prior['depth'] is None or prior['depth']<k:
            parent['status']='depth_mismatch'; parent_rows.append(parent); ledger.append(parent)
            continue
        tmeta=prior['t']; t=Fraction(int(tmeta['num']),int(tmeta['den']))
        before=red(t,M); parent['t_before_mod']=before
        if before%p**k:
            parent['status']='depth_mismatch'; parent_rows.append(parent); ledger.append(parent)
            continue
        deriv=[]
        for axis in range(4):
            trial=s[:]; trial[axis]+=p**(k-1)
            probe={'axis':axis,'trial_shift':trial}
            try:
                _,tp=exact(trial); t1=red(tp,M)
                if (t1-before)%p**k: raise ValueError('nonlinear_probe')
                d=((t1-before)//p**k)%p
                probe.update({'status':'pass','t_probe_mod':t1,'derivative':d})
                deriv.append(d)
            except Exception as exc:
                probe.update({'status':'failure','error':f'{type(exc).__name__}: {exc}'})
            parent['probes'].append(probe)
        if len(deriv)!=4:
            parent['status']='probe_failure'; parent_rows.append(parent); ledger.append(parent)
            continue
        target=-(before//p**k)%p
        parent.update({'derivatives':deriv,'target_digit':target})
        try: h,history=minimum_radius(deriv,target)
        except Exception as exc:
            parent.update({'status':'radius_exhausted','error':str(exc)})
            parent_rows.append(parent); ledger.append(parent); continue
        cap=min(h+P['radius_slack'],(p-1)//2)
        parent.update({'status':'expanded','radius_search':history,'candidate_radius_cap':cap})
        parent_rows.append(parent); ledger.append(parent)
        for digits in itertools.product(range(-cap,cap+1),repeat=4):
            if sum(d*z for d,z in zip(deriv,digits))%p!=target: continue
            shift=[z+p**(k-1)*d for z,d in zip(s,digits)]
            rec={'kind':'candidate','id':f'D{k+1}:C{len(candidates)}',
                 'parent_id':state['id'],'digits':list(digits),'shift':shift,'selected':False}
            try:
                A,Bb,_,_,height=model(shift)
                rec.update({'status':'pass','model_bits':height,'A':rational(A),'B':rational(Bb)})
            except Exception as exc:
                rec.update({'status':'failure','model_bits':None,
                            'error':f'{type(exc).__name__}: {exc}'})
            candidates.append(rec); ledger.append(rec)
    valid=[rec for rec in candidates if rec['status']=='pass']
    dedup={}
    for rec in valid:
        key=tuple(rec['shift'])
        if key not in dedup or rank(rec)<rank(dedup[key]): dedup[key]=rec
    selected=sorted(dedup.values(),key=rank)[:P['beam_width']]
    for rec in selected: rec['selected']=True
    new_beam=[]; exact_failure=None
    for i,rec in enumerate(selected):
        try:
            e,t=exact(rec['shift']); tmod=0 if t is None else red(t,M)
            state={'id':f'D{k+1}:{i}','candidate_id':rec['id'],
                   'parent_id':rec['parent_id'],'digits':rec['digits'],
                   'shift':rec['shift'],'exact':e,'t_mod':tmod}
            new_beam.append(state)
            if tmod!=0 or not e['relation'] and (e['depth'] is None or e['depth']<k+1):
                exact_failure='exact_depth_mismatch'
        except Exception as exc:
            exact_failure=f'exact_failure: {type(exc).__name__}: {exc}'
            break
    stage={'depth':k+1,'status':'complete' if selected and exact_failure is None else
           (exact_failure or 'no_valid_candidate'),
           'parent_count':len(beam),'parent_statuses':{x['parent_id']:x['status'] for x in parent_rows},
           'candidate_count':len(candidates),'valid_candidate_count':len(valid),
           'deduplicated_count':len(dedup),'selected_candidate_ids':[r['id'] for r in selected],
           'beam':new_beam,'ledger':pack(k+1,ledger)}
    stages.append(stage); beam=new_beam
    if stage['status']!='complete': stop=stage['status']; break
    if any(s['exact']['relation'] for s in beam): stop='exact_relation'; break
    if time.monotonic()-start>P['run_cap_seconds']: stop='run_cap_seconds'; break
result={'schema':'xedni-height-beam-result-v1','status':stop,
        'protocol_sha256':hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest(),
        'baseline_result_normalized_sha256':P['baseline_result_normalized_sha256'],
        'short_digit_result_normalized_sha256':P['short_digit_result_normalized_sha256'],
        'greedy_model_result_normalized_sha256':P['greedy_model_result_normalized_sha256'],
        'selected':hit,'stages':stages,'elapsed_wall_seconds':time.monotonic()-start}
(H/'run-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':stop,'beam_min_model_bits':[min(x['exact']['model_bits'] for x in s['beam'])
    if s['beam'] else None for s in stages],
    'beam_sizes':[len(s['beam']) for s in stages],
    'candidate_counts':[s['candidate_count'] for s in stages],
    'elapsed_wall_seconds':result['elapsed_wall_seconds']},indent=2))
