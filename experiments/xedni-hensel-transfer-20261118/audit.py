"""Independent full-grid, first-axis, and beam-ledger Fraction replay."""
from fractions import Fraction as F
from pathlib import Path
import gzip, hashlib, itertools, json, math

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
compressed=(H/'run-result.json.gz').read_bytes()
raw=gzip.decompress(compressed)
R=json.loads(raw)
S=json.loads((H/'summary.json').read_text())
assert S['run_result_raw_sha256']==hashlib.sha256(raw).hexdigest()
assert S['run_result_gzip_sha256']==hashlib.sha256(compressed).hexdigest()
assert S['run_result_gzip_bytes']==len(compressed)
assert S['protocol_sha256']==R['protocol_sha256']
assert S['status']==R['status']
assert S['queries']==R['queries'] and S['vector_tests']==R['vector_tests']
assert S['public_hits']==len(R['public_hits']) and S['eligible_count']==R['eligible_count']
assert S['comparisons']==R['comparisons']
SOURCE=H.parent/'xedni-height-selected-two-image-20261116'/'protocol.json'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==P['source_protocol_sha256']
BASE=json.loads(SOURCE.read_text())
BH=H.parent/'xedni-height-beam-20261118'
B=json.loads((BH/'run-result.json').read_text()); B.pop('elapsed_wall_seconds')
assert hashlib.sha256(json.dumps(B,sort_keys=True).encode()).hexdigest()==P['beam_result_normalized_sha256']
assert hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()==R['protocol_sha256']
p=0; U=None; V=None; ab=None

def add_mod(P,Q,ell):
    if P is None: return Q
    if Q is None: return P
    x,y=P; u,v=Q
    if x==u and (y+v)%ell==0: return None
    lam=(3*x*x-1)*pow(2*y,-1,ell)%ell if P==Q else (v-y)*pow(u-x,-1,ell)%ell
    X=(lam*lam-x-u)%ell
    return X,(lam*(x-X)-y)%ell
def mul_mod(n,P,ell):
    if n<0: P=(P[0],-P[1]%ell); n=-n
    out=None
    while n:
        if n&1: out=add_mod(out,P,ell)
        P=add_mod(P,P,ell); n//=2
    return out

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

def audit_axis(record):
    shift=[0,0,0,0]; e,t=exact(shift)
    assert record['steps'][0]==e
    for k,row in enumerate(record['steps'][1:],1):
        assert row['k']==k and row['shift_before']==shift
        M=p**(k+1); before=red(t,M)
        assert row['t_before_mod']==before and before%p**k==0
        if row['status']=='already_deeper':
            assert before==0 and row['shift_after']==shift and row['exact']==e
            continue
        assert row['status']=='accepted'
        chosen=None
        for axis,probe in enumerate(row['probes']):
            trial=shift[:]; trial[axis]+=p**(k-1)
            assert probe['axis']==axis and probe['trial_shift']==trial and probe['status']=='pass'
            _,tp=exact(trial); t1=red(tp,M)
            assert probe['t_probe_mod']==t1 and (t1-before)%p**k==0
            d=((t1-before)//p**k)%p
            assert probe['derivative']==d
            if d:
                digit=-(before//p**k)*pow(d,-1,p)%p
                assert probe['digit']==digit and probe==row['probes'][-1]
                chosen=(axis,digit)
            else: assert 'digit' not in probe
        assert chosen==(row['chosen_axis'],row['digit'])
        shift[chosen[0]]+=p**(k-1)*chosen[1]
        assert row['shift_after']==shift
        e,t=exact(shift)
        assert e==row['exact'] and row['t_after_mod']==red(t,M)==0
        assert e['depth']>=k+1
    assert record['status']=='depth_cap' and len(record['steps'])==8
    assert record['final_model_bits']==e['model_bits']
    assert record['final_depth']==e['depth'] and not record['final_relation']
    return e['model_bits']

def audit_beam(record):
    e,_=exact([0,0,0,0])
    beam=[{'id':'D1:0','parent_id':None,'digits':[0,0,0,0],
           'shift':[0,0,0,0],'exact':e}]
    assert record['stages'][0]['beam']==beam
    total=0
    for k,stage in enumerate(record['stages'][1:],1):
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
                A,Bb,_,_,height=model(trial)
                assert rec['status']=='pass' and rec['model_bits']==height
                assert rec['A']==rat(A) and rec['B']==rat(Bb)
                candidates.append(rec)
        assert index==len(rows)
        assert stage['parent_statuses']=={x['parent_id']:x['status'] for x in parents}
        assert stage['candidate_count']==len(candidates)
        assert stage['valid_candidate_count']==len(candidates)
        dedup={}
        for rec in candidates:
            key=tuple(rec['shift'])
            if key not in dedup or rank(rec)<rank(dedup[key]): dedup[key]=rec
        assert stage['deduplicated_count']==len(dedup)
        selected=sorted(dedup.values(),key=rank)[:P['beam_width']]
        assert stage['selected_candidate_ids']==[x['id'] for x in selected]
        selected_ids=set(x['id'] for x in selected)
        assert all(x['selected']==(x['id'] in selected_ids) for x in candidates)
        new_beam=[]
        for i,rec in enumerate(selected):
            e,t=exact(rec['shift']); tmod=0 if t is None else red(t,M)
            assert tmod==0 and not e['relation'] and e['depth']>=k+1
            new_beam.append({'id':f'D{k+1}:{i}','candidate_id':rec['id'],
                'parent_id':rec['parent_id'],'digits':rec['digits'],
                'shift':rec['shift'],'exact':e,'t_mod':tmod})
        assert stage['beam']==new_beam and stage['status']=='complete'
        beam=new_beam; total+=len(candidates)
    assert record['status']=='depth_cap' and len(record['stages'])==8
    assert record['final_model_bits']==beam[0]['exact']['model_bits']
    assert record['final_depth']==beam[0]['exact']['depth']
    assert not record['final_relation']
    return beam[0]['exact']['model_bits'],total

queries=0; vector_tests=0; hits=[]
for spec in BASE['fields']:
    p,q,N=spec['p'],spec['q'],spec['order']
    G=None
    for x in range(p):
        for y in range(p):
            if (y*y-x**3+x+2)%p: continue
            T=mul_mod(N//q,(x,y),p)
            if T is not None and mul_mod(q,T,p) is None: G=T; break
        if G is not None: break
    assert G is not None
    for target_index in range(4):
        w=1+int.from_bytes(hashlib.sha256(
            f'xedni-hensel-height-v1|{p}|{target_index}'.encode()).digest(),'big')%(q-1)
        Q=mul_mod(w,G,p); pairs=[]
        for t1,t2 in itertools.permutations(BASE['offsets'],2):
            Up=add_mod(Q,mul_mod(-t1,G,p),p)
            Vp=add_mod(Q,mul_mod(-t2,G,p),p)
            if Up is not None and Vp is not None: pairs.append((t1,t2,Up,Vp))
            if len(pairs)==16: break
        assert len(pairs)==16
        for query_index,(t1,t2,Up,Vp) in enumerate(pairs):
            queries+=1
            for vector_index,(a,b) in enumerate(BASE['vectors']):
                vector_tests+=1
                pub=add_mod(mul_mod(a,Up,p),mul_mod(b,Vp,p),p) is None
                assert pub==((a*(w-t1)+b*(w-t2))%q==0)
                if pub:
                    hits.append({'p':p,'q':q,'order':N,'G':list(G),
                        'target_index':target_index,'w':w,'query_index':query_index,
                        't1':t1,'t2':t2,'U':list(Up),'V':list(Vp),
                        'vector_index':vector_index,'a':a,'b':b,
                        'event_index':queries-1,'vector_event_index':vector_tests-1,
                        'status':'eligible' if Up[0]!=Vp[0] else 'equal_x_excluded'})
assert (queries,vector_tests)==(R['queries'],R['vector_tests'])==(512,6656)
assert hits==R['public_hits'] and len(hits)==9
eligible=[x for x in hits if x['status']=='eligible']
assert len(eligible)==R['eligible_count']==len(R['results'])==9
assert {k:v for k,v in eligible[0].items() if k!='status'}==B['selected']
comparisons=[]; total_candidates=0
for hit_index,(hit,row) in enumerate(zip(eligible,R['results'])):
    assert row['hit_index']==hit_index and row['hit']==hit and row['status']=='measured'
    p=hit['p']; U=hit['U']; V=hit['V']; ab=(hit['a'],hit['b'])
    axis_bits=audit_axis(row['first_axis'])
    beam_bits,count=audit_beam(row['beam']); total_candidates+=count
    comparisons.append({'hit_index':hit_index,'comparable':True,
        'first_axis_bits':axis_bits,'beam_bits':beam_bits,
        'beam_minus_axis_bits':beam_bits-axis_bits})
    if hit_index==0:
        assert [s['beam'] for s in row['beam']['stages']]==[s['beam'] for s in B['stages']]
        assert [s['candidate_count'] for s in row['beam']['stages']]==[
            s['candidate_count'] for s in B['stages']]
assert comparisons==R['comparisons'] and R['status']=='complete'
out={'schema':'xedni-hensel-transfer-audit-v1','status':'pass',
     'queries':queries,'vector_tests':vector_tests,'public_hits':len(hits),
     'eligible_hits':len(eligible),'paired_depth_eight':len(comparisons),
     'beam_lower_model_hits':sum(x['beam_minus_axis_bits']<0 for x in comparisons),
     'beam_minus_axis_bits':[x['beam_minus_axis_bits'] for x in comparisons],
     'enumerated_beam_candidates':total_candidates}
(H/'audit-result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
