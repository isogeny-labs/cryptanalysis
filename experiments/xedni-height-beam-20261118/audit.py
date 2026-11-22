"""Independent full-ledger Fraction replay of the width-eight beam."""
from fractions import Fraction as F
from pathlib import Path
import gzip, hashlib, itertools, json, math

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text()); R=json.loads((H/'run-result.json').read_text())
BH=H.parent/'xedni-hensel-height-20261118'
B=json.loads((BH/'run-result.json').read_text()); B.pop('elapsed_wall_seconds')
assert hashlib.sha256(json.dumps(B,sort_keys=True).encode()).hexdigest()==P['baseline_result_normalized_sha256']
SH=H.parent/'xedni-short-digit-height-20261118'
SHORT=json.loads((SH/'run-result.json').read_text()); SHORT.pop('elapsed_wall_seconds')
assert hashlib.sha256(json.dumps(SHORT,sort_keys=True).encode()).hexdigest()==P['short_digit_result_normalized_sha256']
GH=H.parent/'xedni-model-height-digit-20261118'
GREEDY=json.loads((GH/'run-result.json').read_text()); GREEDY.pop('elapsed_wall_seconds')
assert hashlib.sha256(json.dumps(GREEDY,sort_keys=True).encode()).hexdigest()==P['greedy_model_result_normalized_sha256']
assert hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()==R['protocol_sha256']
hit=B['selected']; assert R['selected']==hit==SHORT['selected']==GREEDY['selected']
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
def model(shift):
    x1,y1,x2,y2=(center(U[0])+p*shift[0],center(U[1])+p*shift[1],
                  center(V[0])+p*shift[2],center(V[1])+p*shift[3])
    f1=y1*y1-x1**3; f2=y2*y2-x2**3
    A=F(f1-f2,x1-x2); Bb=F(f1)-A*x1
    assert 4*A**3+27*Bb**2!=0
    assert (red(A,p),red(Bb,p))==(p-1,p-2)
    P1=(F(x1),F(y1)); P2=(F(x2),F(y2))
    assert y1*y1==x1**3+A*x1+Bb and y2*y2==x2**3+A*x2+Bb
    height=max(rat(z)['bits'] for z in (A,Bb,*P1,*P2))
    return A,Bb,P1,P2,height
def exact(shift):
    A,Bb,P1,P2,height=model(shift)
    Rr=add(mul(ab[0],P1,A),mul(ab[1],P2,A),A)
    assert Rr is None or Rr[1]!=0
    t=None if Rr is None else -Rr[0]/Rr[1]
    dep=None if t is None or t==0 else vp(t.numerator)-vp(t.denominator)
    rec={'shift':shift[:],'A':rat(A),'B':rat(Bb),
         'P1':[rat(z) for z in P1],'P2':[rat(z) for z in P2],
         'R':None if Rr is None else [rat(z) for z in Rr],
         't':None if t is None else rat(t),'depth':dep,'relation':Rr is None,
         'model_bits':height,
         'residual_bits':None if Rr is None else max(rat(z)['bits'] for z in Rr)}
    return rec,t

def rank(rec):
    shift=rec['shift']; digits=rec['digits']
    return (rec['model_bits'],max(abs(z) for z in shift),sum(abs(z) for z in shift),
            tuple(shift),rec['parent_id'],tuple(digits))
def ledger(meta):
    blob=(H/meta['path']).read_bytes()
    assert len(blob)==meta['gzip_bytes']
    assert hashlib.sha256(blob).hexdigest()==meta['gzip_sha256']
    raw=gzip.decompress(blob)
    assert hashlib.sha256(raw).hexdigest()==meta['raw_sha256']
    rows=[json.loads(x) for x in raw.splitlines()]
    assert len(rows)==meta['rows']
    return rows

e,_=exact([0,0,0,0]); assert e==B['steps'][0]
beam=[{'id':'D1:0','parent_id':None,'digits':[0,0,0,0],
       'shift':[0,0,0,0],'exact':e}]
assert R['stages'][0]['beam']==beam
total_candidates=0
for k,stage in enumerate(R['stages'][1:],1):
    assert stage['depth']==k+1 and stage['parent_count']==len(beam)
    rows=ledger(stage['ledger']); index=0; candidates=[]; parents=[]
    M=p**(k+1)
    for state in beam:
        shift=state['shift']; e,t=exact(shift)
        assert e==state['exact'] and not e['relation'] and e['depth']>=k
        before=red(t,M); assert before%p**k==0
        parent=rows[index]; index+=1
        assert parent['kind']=='parent' and parent['parent_id']==state['id']
        assert parent['shift']==shift and parent['t_before_mod']==before
        assert parent['status']=='expanded'
        deriv=[]
        for axis,probe in enumerate(parent['probes']):
            trial=shift[:]; trial[axis]+=p**(k-1)
            assert probe['axis']==axis and probe['trial_shift']==trial and probe['status']=='pass'
            _,tp=exact(trial); t1=red(tp,M)
            assert t1==probe['t_probe_mod'] and (t1-before)%p**k==0
            d=((t1-before)//p**k)%p
            assert d==probe['derivative']; deriv.append(d)
        assert deriv==parent['derivatives']
        target=-(before//p**k)%p
        assert target==parent['target_digit']
        hmax=parent['radius_search'][-1]['radius']
        assert hmax<=P['minimum_radius_search_limit']
        for h in range(hmax+1):
            count=sum(sum(d*z for d,z in zip(deriv,ds))%p==target
                for ds in itertools.product(range(-h,h+1),repeat=4))
            assert parent['radius_search'][h]=={'radius':h,'solutions_within_radius':count}
            assert (count==0)==(h<hmax)
        cap=min(hmax+P['radius_slack'],(p-1)//2)
        assert cap==parent['candidate_radius_cap']
        parents.append(parent)
        for ds in itertools.product(range(-cap,cap+1),repeat=4):
            if sum(d*z for d,z in zip(deriv,ds))%p!=target: continue
            trial=[z+p**(k-1)*d for z,d in zip(shift,ds)]
            rec=rows[index]; index+=1
            assert rec['kind']=='candidate' and rec['id']==f'D{k+1}:C{len(candidates)}'
            assert rec['parent_id']==state['id'] and rec['digits']==list(ds)
            assert rec['shift']==trial
            try:
                A,Bb,_,_,height=model(trial)
                assert rec['status']=='pass' and rec['model_bits']==height
                assert rec['A']==rat(A) and rec['B']==rat(Bb)
            except (AssertionError,ValueError,ZeroDivisionError) as exc:
                if isinstance(exc,AssertionError): raise
                assert rec['status']=='failure' and rec['model_bits'] is None
                assert rec['error']==f'{type(exc).__name__}: {exc}'
            candidates.append(rec)
    assert index==len(rows)
    assert stage['parent_statuses']=={x['parent_id']:x['status'] for x in parents}
    assert stage['candidate_count']==len(candidates)
    valid=[x for x in candidates if x['status']=='pass']
    assert stage['valid_candidate_count']==len(valid)
    dedup={}
    for rec in valid:
        key=tuple(rec['shift'])
        if key not in dedup or rank(rec)<rank(dedup[key]): dedup[key]=rec
    assert stage['deduplicated_count']==len(dedup)
    selected=sorted(dedup.values(),key=rank)[:P['beam_width']]
    assert stage['selected_candidate_ids']==[x['id'] for x in selected]
    selected_ids=set(x['id'] for x in selected)
    assert all(x['selected']==(x['id'] in selected_ids) for x in candidates)
    new_beam=[]
    for i,rec in enumerate(selected):
        e,t=exact(rec['shift'])
        tmod=0 if t is None else red(t,M)
        assert tmod==0 and (e['relation'] or e['depth']>=k+1)
        state={'id':f'D{k+1}:{i}','candidate_id':rec['id'],
               'parent_id':rec['parent_id'],'digits':rec['digits'],
               'shift':rec['shift'],'exact':e,'t_mod':tmod}
        new_beam.append(state)
    assert stage['beam']==new_beam and stage['status']=='complete'
    beam=new_beam; total_candidates+=len(candidates)
assert R['status']=='depth_cap' and len(R['stages'])==P['maximum_target_depth']
base_bits=[s.get('model_bits',s.get('exact',{}).get('model_bits')) for s in B['steps']]
short_bits=[s.get('model_bits',s.get('exact',{}).get('model_bits')) for s in SHORT['steps']]
greedy_bits=[s.get('model_bits',s.get('exact',{}).get('model_bits')) for s in GREEDY['steps']]
beam_bits=[min(x['exact']['model_bits'] for x in s['beam']) for s in R['stages']]
out={'schema':'xedni-height-beam-audit-v1','status':'pass','depths':list(range(1,9)),
     'baseline_model_bits':base_bits,'short_digit_model_bits':short_bits,
     'greedy_model_bits':greedy_bits,'beam_min_model_bits':beam_bits,
     'delta_vs_baseline':[a-b for a,b in zip(beam_bits,base_bits)],
     'enumerated_candidates':total_candidates,'replayed_steps':len(R['stages'])-1,
     'beam_sizes':[len(x['beam']) for x in R['stages']]}
(H/'audit-result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
