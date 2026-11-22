"""Paired first-axis and width-eight Hensel paths on every eligible public hit."""
from sage.all import EllipticCurve, GF, QQ
from fractions import Fraction
from pathlib import Path
import gzip, hashlib, itertools, json, time

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
SOURCE=H.parent/'xedni-height-selected-two-image-20261116'/'protocol.json'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==P['source_protocol_sha256']
BASE=json.loads(SOURCE.read_text())
BH=H.parent/'xedni-height-beam-20261118'
B=json.loads((BH/'run-result.json').read_text())
BN={k:v for k,v in B.items() if k!='elapsed_wall_seconds'}
assert hashlib.sha256(json.dumps(BN,sort_keys=True).encode()).hexdigest()==P['beam_result_normalized_sha256']
p=0; U=None; V=None; ab=None
start=time.monotonic()

def coords(T): return None if T.is_zero() else [int(T[0]),int(T[1])]
def generator(E,p,q,N):
    for x in range(p):
        for T in sorted(E.lift_x(GF(p)(x),all=True),key=lambda z:int(z[1])):
            G=(N//q)*T
            if not G.is_zero() and (q*G).is_zero(): return G
    raise ValueError('generator_missing')

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

def pack(hit_index,depth,rows):
    raw=(''.join(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n' for row in rows)).encode()
    blob=gzip.compress(raw,compresslevel=9,mtime=0)
    name=f'hit{hit_index:02d}.depth{depth}.jsonl.gz'
    (H/name).write_bytes(blob)
    return {'path':name,'rows':len(rows),'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'gzip_sha256':hashlib.sha256(blob).hexdigest(),'gzip_bytes':len(blob)}

def run_first_axis():
    shift=[0,0,0,0]; initial,t=exact(shift)
    steps=[initial]; stop='depth_cap'
    for k in range(1,P['maximum_target_depth']):
        previous=steps[-1].get('exact',steps[-1])
        if previous['relation']: stop='exact_relation'; break
        if previous['depth'] is None or previous['depth']<k: stop='depth_mismatch'; break
        M=p**(k+1); before=red(t,M)
        row={'k':k,'shift_before':shift[:],'t_before_mod':before,'probes':[]}
        if before%p**k: row['status']='depth_mismatch'; steps.append(row); stop=row['status']; break
        if before==0:
            row.update({'status':'already_deeper','shift_after':shift[:],'exact':previous})
            steps.append(row); continue
        chosen=None
        for axis in range(4):
            trial=shift[:]; trial[axis]+=p**(k-1)
            probe={'axis':axis,'trial_shift':trial}
            try:
                _,tp=exact(trial); t1=red(tp,M)
                if (t1-before)%p**k: raise ValueError('nonlinear_probe')
                d=((t1-before)//p**k)%p
                probe.update({'status':'pass','t_probe_mod':t1,'derivative':d})
                if d:
                    digit=-(before//p**k)*pow(d,-1,p)%p
                    probe['digit']=digit; chosen=(axis,digit)
            except Exception as exc:
                probe.update({'status':'failure','error':f'{type(exc).__name__}: {exc}'})
            row['probes'].append(probe)
            if chosen is not None: break
        if chosen is None:
            row['status']='derivative_exhausted'; steps.append(row); stop=row['status']; break
        axis,digit=chosen; shift[axis]+=p**(k-1)*digit
        row.update({'status':'accepted','chosen_axis':axis,'digit':digit,'shift_after':shift[:]})
        try:
            row['exact'],t=exact(shift)
            row['t_after_mod']=0 if t is None else red(t,M)
            if row['t_after_mod']!=0 or not row['exact']['relation'] and (
                row['exact']['depth'] is None or row['exact']['depth']<k+1):
                row['status']='exact_depth_mismatch'; stop=row['status']
        except Exception as exc:
            row.update({'status':'exact_failure','error':f'{type(exc).__name__}: {exc}'})
            stop=row['status']
        steps.append(row)
        if stop!='depth_cap': break
        if time.monotonic()-start>P['run_cap_seconds']: stop='run_cap_seconds'; break
    final=steps[-1].get('exact',steps[-1])
    return {'status':stop,'steps':steps,'final_model_bits':final.get('model_bits'),
            'final_depth':final.get('depth'),'final_relation':final.get('relation')}

def run_beam(hit_index):
    first,_=exact([0,0,0,0])
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
                     'parent_id':state['id'],'digits':list(digits),
                     'shift':shift,'selected':False}
                try:
                    A,Bb,_,_,height=model(shift)
                    rec.update({'status':'pass','model_bits':height,
                                'A':rational(A),'B':rational(Bb)})
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
               'parent_count':len(beam),
               'parent_statuses':{x['parent_id']:x['status'] for x in parent_rows},
               'candidate_count':len(candidates),'valid_candidate_count':len(valid),
               'deduplicated_count':len(dedup),
               'selected_candidate_ids':[r['id'] for r in selected],
               'beam':new_beam,'ledger':pack(hit_index,k+1,ledger)}
        stages.append(stage); beam=new_beam
        if stage['status']!='complete': stop=stage['status']; break
        if any(s['exact']['relation'] for s in beam): stop='exact_relation'; break
        if time.monotonic()-start>P['run_cap_seconds']: stop='run_cap_seconds'; break
    final=beam[0]['exact'] if beam else {}
    return {'status':stop,'stages':stages,'final_model_bits':final.get('model_bits'),
            'final_depth':final.get('depth'),'final_relation':final.get('relation')}

queries=0; vector_tests=0; public_hits=[]
for spec in BASE['fields']:
    p,q,N=spec['p'],spec['q'],spec['order']
    E=EllipticCurve(GF(p),BASE['curve_coefficients'])
    assert int(E.cardinality())==N
    G=generator(E,p,q,N)
    for target_index in range(4):
        w=1+int.from_bytes(hashlib.sha256(
            f'xedni-hensel-height-v1|{p}|{target_index}'.encode()).digest(),'big')%(q-1)
        Q=w*G; pairs=[]
        for t1,t2 in itertools.permutations(BASE['offsets'],2):
            Up=Q-t1*G; Vp=Q-t2*G
            if not Up.is_zero() and not Vp.is_zero(): pairs.append((t1,t2,Up,Vp))
            if len(pairs)==16: break
        assert len(pairs)==16
        for query_index,(t1,t2,Up,Vp) in enumerate(pairs):
            queries+=1
            for vector_index,(a,b) in enumerate(BASE['vectors']):
                vector_tests+=1
                pub=(a*Up+b*Vp).is_zero()
                assert pub==((a*(w-t1)+b*(w-t2))%q==0)
                if pub:
                    u,v=coords(Up),coords(Vp)
                    public_hits.append({'p':p,'q':q,'order':N,'G':coords(G),
                        'target_index':target_index,'w':w,'query_index':query_index,
                        't1':t1,'t2':t2,'U':u,'V':v,'vector_index':vector_index,
                        'a':a,'b':b,'event_index':queries-1,
                        'vector_event_index':vector_tests-1,
                        'status':'eligible' if u[0]!=v[0] else 'equal_x_excluded'})
assert (queries,vector_tests)==(512,6656)
eligible=[x for x in public_hits if x['status']=='eligible']
assert {k:v for k,v in eligible[0].items() if k!='status'}==B['selected']
results=[]
for hit_index,hit in enumerate(eligible):
    p=hit['p']; U=hit['U']; V=hit['V']; ab=(hit['a'],hit['b'])
    if time.monotonic()-start>P['run_cap_seconds']:
        results.append({'hit_index':hit_index,'hit':hit,'status':'not_run_cap'})
        continue
    try:
        axis=run_first_axis(); beam=run_beam(hit_index)
        results.append({'hit_index':hit_index,'hit':hit,
                        'first_axis':axis,'beam':beam,'status':'measured'})
    except Exception as exc:
        results.append({'hit_index':hit_index,'hit':hit,'status':'run_failure',
                        'error':f'{type(exc).__name__}: {exc}'})
comparisons=[]
for row in results:
    if row['status']!='measured': continue
    axis,beam=row['first_axis'],row['beam']
    comparable=(axis['status']=='depth_cap' and beam['status']=='depth_cap'
                and axis['final_depth'] is not None and axis['final_depth']>=8
                and beam['final_depth'] is not None and beam['final_depth']>=8)
    comparisons.append({'hit_index':row['hit_index'],'comparable':comparable,
        'first_axis_bits':axis['final_model_bits'],'beam_bits':beam['final_model_bits'],
        'beam_minus_axis_bits':beam['final_model_bits']-axis['final_model_bits']
        if comparable else None})
result={'schema':'xedni-hensel-transfer-result-v1','status':'complete' if len(results)==len(eligible)
        and all(x['status']=='measured' for x in results) else 'incomplete',
        'protocol_sha256':hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest(),
        'source_protocol_sha256':P['source_protocol_sha256'],
        'beam_result_normalized_sha256':P['beam_result_normalized_sha256'],
        'queries':queries,'vector_tests':vector_tests,'public_hits':public_hits,
        'eligible_count':len(eligible),'results':results,'comparisons':comparisons,
        }
raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode()
blob=gzip.compress(raw,compresslevel=9,mtime=0)
(H/'run-result.json.gz').write_bytes(blob)
summary={'schema':'xedni-hensel-transfer-summary-v1','status':result['status'],
         'protocol_sha256':result['protocol_sha256'],'queries':queries,
         'vector_tests':vector_tests,'public_hits':len(public_hits),
         'eligible_count':len(eligible),'comparisons':comparisons,
         'run_result_raw_sha256':hashlib.sha256(raw).hexdigest(),
         'run_result_gzip_sha256':hashlib.sha256(blob).hexdigest(),
         'run_result_gzip_bytes':len(blob),
         'elapsed_wall_seconds':time.monotonic()-start}
(H/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'public_hits':len(public_hits),
    'eligible_count':len(eligible),'excluded_count':len(public_hits)-len(eligible),
    'arm_statuses':[(x['hit_index'],x['first_axis']['status'] if x['status']=='measured' else x['status'],
                    x['beam']['status'] if x['status']=='measured' else x['status']) for x in results],
    'comparisons':comparisons,'elapsed_wall_seconds':summary['elapsed_wall_seconds']},indent=2))
