"""Fresh-target affine leading-defect selector using five Qp probes per hit."""
from sage.all import EllipticCurve, GF, Qp, QQ
from fractions import Fraction
from pathlib import Path
import gzip
import hashlib
import itertools
import json
import time

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
SOURCE=H.parent/'xedni-height-selected-two-image-20261116'/'protocol.json'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==P['source_protocol_sha256']
BASE=json.loads(SOURCE.read_text())
PRIOR=H.parent/'xedni-qdefect-proxy-20261116'/'protocol.json'
assert hashlib.sha256(PRIOR.read_bytes()).hexdigest()==P['prior_proxy_protocol_sha256']
LEADING=H.parent/'xedni-leading-defect-selector-20261116'/'protocol.json'
assert hashlib.sha256(LEADING.read_bytes()).hexdigest()==P['prior_leading_protocol_sha256']
AWARE=H.parent/'xedni-vector-aware-selector-20261116'/'protocol.json'
assert hashlib.sha256(AWARE.read_bytes()).hexdigest()==P['prior_aware_protocol_sha256']
WIDTH=H.parent/'xedni-vector-aware-width-20261116'/'protocol.json'
assert hashlib.sha256(WIDTH.read_bytes()).hexdigest()==P['prior_width_protocol_sha256']
START=time.monotonic()

def center(z,p): return z-p if z>p//2 else z

def parts(z):
    n,d=z.numerator,z.denominator
    return int(n() if callable(n) else n),int(d() if callable(d) else d)

def mod(z,p):
    n,d=parts(z)
    if d%p==0: raise ValueError('nonintegral_reduction')
    return n*pow(d,-1,p)%p

def bits(z):
    n,d=parts(z)
    return max(abs(n).bit_length(),d.bit_length())

def coords(point): return None if point.is_zero() else [int(point[0]),int(point[1])]

def generator(E,p,q,N):
    for x in range(p):
        for T in sorted(E.lift_x(GF(p)(x),all=True),key=lambda z:int(z[1])):
            G=(N//q)*T
            if not G.is_zero() and (q*G).is_zero(): return G
    raise ValueError('generator_missing')

def candidate(p,U,V,shift):
    x1c,y1c=[center(z,p) for z in U]
    x2c,y2c=[center(z,p) for z in V]
    if shift is None:
        if U[0]!=V[0] or (U[1]+V[1])%p!=0: raise ValueError('invalid_equal_x')
        x1,y1,x2,y2=x1c,y1c,x1c,-y1c
        A,B=Fraction(-1),Fraction(y1*y1-x1**3+x1)
    else:
        x1,y1=x1c+shift[0]*p,y1c+shift[1]*p
        x2,y2=x2c+shift[2]*p,y2c+shift[3]*p
        f1,f2=y1*y1-x1**3,y2*y2-x2**3
        A=Fraction(f1-f2,x1-x2); B=Fraction(f1)-A*x1
    if 4*A**3+27*B**2==0: raise ValueError('singular_curve')
    if (mod(A,p),mod(B,p))!=(p-1,p-2): raise ValueError('wrong_coefficient_reduction')
    if (x1%p,y1%p)!=tuple(U) or (x2%p,y2%p)!=tuple(V):
        raise ValueError('wrong_point_reduction')
    return A,B,x1,y1,x2,y2,max(bits(z) for z in (A,B,x1,y1,x2,y2))

def v_int(n,p):
    n=abs(int(n))
    if n==0: return None
    k=0
    while n%p==0: n//=p; k+=1
    return k

def v_rat(z,p):
    n,d=parts(z)
    if n==0: return None
    return v_int(n,p)-v_int(d,p)

def qlead(P1,P2,q,p):
    out=[]
    for point in (P1,P2):
        R=q*point
        if R.is_zero(): raise ValueError('q_multiple_precision_zero')
        t=-R[0]/R[1]
        k=int(t.valuation())
        if k<1: raise ValueError('q_multiple_not_in_kernel')
        lead=int((t/p).residue())
        out.append((k,lead))
    return out

def packed(path,rows):
    raw=''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in rows).encode()
    blob=gzip.compress(raw,compresslevel=9,mtime=0)
    (H/path).write_bytes(blob)
    return {'path':path,'rows':len(rows),'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'gzip_sha256':hashlib.sha256(blob).hexdigest(),'gzip_bytes':len(blob)}

def padic_leads(A,B,x1,y1,x2,y2,K,q,p):
    C=EllipticCurve(K,[K(QQ(A.numerator)/QQ(A.denominator)),
                         K(QQ(B.numerator)/QQ(B.denominator))])
    D1,D2=C(K(x1),K(y1)),C(K(x2),K(y2))
    return qlead(D1,D2,q,p)

def rational_outcome(model,a,b,p,u,v):
    rec,A,B,x1,y1,x2,y2=model
    C=EllipticCurve(QQ,[QQ(A.numerator)/QQ(A.denominator),
                         QQ(B.numerator)/QQ(B.denominator)])
    P1,P2=C(QQ(x1),QQ(y1)),C(QQ(x2),QQ(y2))
    assert [mod(P1[0],p),mod(P1[1],p)]==u
    assert [mod(P2[0],p),mod(P2[1],p)]==v
    assert (P1+(-P1)).is_zero()
    R=a*P1+b*P2
    depth=None if R.is_zero() else v_rat(-R[0]/R[1],p)
    assert depth is None or depth>=1
    return {'rational_relation':R.is_zero(),'residual_depth':depth}

queries=[]; vectors=[]; parts_meta=[]; summaries=[]
counts={k:0 for k in ('queries','vector_tests','public_hits','candidate_attempts','candidate_pass',
                      'candidate_failure','affine_predictions','affine_cancellation_candidates',
                      'qprobe_controls','selected_qconfirm_controls','rational_controls',
                      'selected_prediction_pass','selected_prediction_fail','rational_hits',
                      'equal_x_hits')}
stages={k:0.0 for k in ('model_seconds','qprobe_seconds','affine_eval_seconds',
                       'selected_qconfirm_seconds','rational_unique_seconds',
                       'selected_rational_seconds','baseline_rational_seconds')}
for spec in BASE['fields']:
    p,q,N=spec['p'],spec['q'],spec['order']
    E=EllipticCurve(GF(p),BASE['curve_coefficients'])
    assert int(E.cardinality())==N
    G=generator(E,p,q,N)
    K=Qp(p,prec=P['proxy_precision'])
    for j in range(4):
        w=1+int.from_bytes(hashlib.sha256(f'xedni-affine-defect-v1|{p}|{j}'.encode()).digest(),'big')%(q-1)
        Q=w*G
        pairs=[]
        for t1,t2 in itertools.permutations(BASE['offsets'],2):
            U,V=Q-t1*G,Q-t2*G
            if not U.is_zero() and not V.is_zero(): pairs.append((t1,t2,U,V))
            if len(pairs)==16: break
        assert len(pairs)==16
        for qi,(t1,t2,U,V) in enumerate(pairs):
            event=len(queries); u,v=coords(U),coords(V)
            query={'event_index':event,'p':p,'q':q,'order':N,'G':coords(G),
                   'target_index':j,'w':w,'query_index':qi,'t1':t1,'t2':t2,
                   'U':u,'V':v,'branch':'equal_x_opposite' if u[0]==v[0] else 'distinct_x'}
            queries.append(query); counts['queries']+=1
            for vi,(a,b) in enumerate(BASE['vectors']):
                pub=(a*U+b*V).is_zero()
                assert pub==((a*(w-t1)+b*(w-t2))%q==0)
                vectors.append({'event_index':event,'vector_index':vi,'a':a,'b':b,'public_relation':pub})
                counts['vector_tests']+=1; counts['public_hits']+=int(pub)
                if not pub: continue
                equal_x=u[0]==v[0]
                counts['equal_x_hits']+=int(equal_x)
                shifts=[None] if equal_x else itertools.product(P['shift_values'],repeat=4)
                rows=[]; models={}
                for shift in shifts:
                    shift=None if shift is None else tuple(shift)
                    rec={'event_index':event,'vector_index':vi,'shift':None if shift is None else list(shift)}
                    counts['candidate_attempts']+=1
                    t0=time.monotonic()
                    try:
                        A,B,x1,y1,x2,y2,score=candidate(p,u,v,shift)
                        rec.update({'status':'pass','A':str(A),'B':str(B),'model_score_bits':score})
                        models[shift]=(rec,A,B,x1,y1,x2,y2)
                        counts['candidate_pass']+=1
                    except Exception as exc:
                        rec.update({'status':'candidate_failure','error':f'{type(exc).__name__}: {exc}'})
                        counts['candidate_failure']+=1
                    stages['model_seconds']+=time.monotonic()-t0
                    rows.append(rec)
                assert models
                probes=[]; intercept=None; slopes=None
                if equal_x:
                    keys=[None]
                else:
                    keys=[tuple(s) for s in P['probe_shifts']]
                for shift in keys:
                    assert shift in models
                    rec,A,B,x1,y1,x2,y2=models[shift]
                    t0=time.monotonic()
                    (k1,c1),(k2,c2)=padic_leads(A,B,x1,y1,x2,y2,K,q,p)
                    stages['qprobe_seconds']+=time.monotonic()-t0
                    counts['qprobe_controls']+=2
                    probe={'shift':None if shift is None else list(shift),
                           'qdepth1':k1,'qdepth2':k2,'lead1':c1,'lead2':c2}
                    probes.append(probe)
                    rec['probe_measurement']=probe
                if not equal_x:
                    intercept=(probes[0]['lead1'],probes[0]['lead2'])
                    slopes=[((probe['lead1']-intercept[0])%p,
                             (probe['lead2']-intercept[1])%p) for probe in probes[1:]]
                else:
                    intercept=(probes[0]['lead1'],probes[0]['lead2'])
                    slopes=[]
                t0=time.monotonic()
                for rec in rows:
                    if rec['status']!='pass': continue
                    shift=rec['shift']
                    c1=(intercept[0]+sum(shift[i]*slopes[i][0] for i in range(4)))%p if shift is not None else intercept[0]
                    c2=(intercept[1]+sum(shift[i]*slopes[i][1] for i in range(4)))%p if shift is not None else intercept[1]
                    cancel=(a*c1+b*c2)%p==0
                    rec.update({'predicted_lead1':c1,'predicted_lead2':c2,
                                'predicted_cancellation':cancel})
                    counts['affine_predictions']+=1
                    counts['affine_cancellation_candidates']+=int(cancel)
                stages['affine_eval_seconds']+=time.monotonic()-t0
                eligible=[r for r in rows if r['status']=='pass']
                order=lambda r:(r['model_score_bits'],() if r['shift'] is None else r['shift'])
                baseline=min(eligible,key=order)
                cancel_rows=[r for r in eligible if r['predicted_cancellation']]
                selected=min(cancel_rows,key=order) if cancel_rows else baseline
                chosen_key=None if selected['shift'] is None else tuple(selected['shift'])
                t0=time.monotonic()
                _,A,B,x1,y1,x2,y2=models[chosen_key]
                (sk1,sc1),(sk2,sc2)=padic_leads(A,B,x1,y1,x2,y2,K,q,p)
                stages['selected_qconfirm_seconds']+=time.monotonic()-t0
                counts['selected_qconfirm_controls']+=2
                assert (sc1,sc2)==(selected['predicted_lead1'],selected['predicted_lead2'])
                for rec in (selected,baseline) if selected is not baseline else (selected,):
                    key=None if rec['shift'] is None else tuple(rec['shift'])
                    t0=time.monotonic()
                    outcome=rational_outcome(models[key],a,b,p,u,v)
                    dt=time.monotonic()-t0
                    stages['rational_unique_seconds']+=dt
                    if rec is selected: stages['selected_rational_seconds']+=dt
                    if rec is baseline: stages['baseline_rational_seconds']+=dt
                    rec.update(outcome)
                    counts['rational_controls']+=1
                    counts['rational_hits']+=int(outcome['rational_relation'])
                actual=(selected['residual_depth'] is None or selected['residual_depth']>=2)
                counts['selected_prediction_pass' if selected['predicted_cancellation']==actual else 'selected_prediction_fail']+=1
                summaries.append({'event_index':event,'vector_index':vi,'p':p,'a':a,'b':b,
                                  'candidate_attempts':len(rows),'eligible':len(eligible),
                                  'probe_results':probes,'intercept':list(intercept),
                                  'slopes':[list(x) for x in slopes],
                                  'predicted_candidates':len(cancel_rows),
                                  'baseline_shift':baseline['shift'],
                                  'selected_shift':selected['shift'],
                                  'selected_qdepth1':sk1,'selected_qdepth2':sk2,
                                  'selected_lead1':sc1,'selected_lead2':sc2,
                                  'baseline_residual_depth':baseline['residual_depth'],
                                  'selected_residual_depth':selected['residual_depth'],
                                  'baseline_relation':baseline['rational_relation'],
                                  'selected_relation':selected['rational_relation']})
                parts_meta.append(packed(f'candidates.hit{len(summaries)-1:03d}.jsonl.gz',rows))
                if time.monotonic()-START>P['run_cap_seconds']:
                    raise TimeoutError('frozen run cap exceeded')
assert counts['queries']==P['expected_queries'] and counts['vector_tests']==P['expected_public_vector_tests']
result={'schema':'xedni-affine-leading-defect-result-v1','status':'complete',
        'protocol_sha256':hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest(),
        'counts':counts,'stages':stages,'summaries':summaries,
        'queries':packed('queries.jsonl.gz',queries),'vectors':packed('vectors.jsonl.gz',vectors),
        'candidate_parts':parts_meta,'elapsed_wall_seconds':time.monotonic()-START}
(H/'run-result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':'complete','counts':counts,'stages':stages,
                  'selected_depth2_hits':sum(s['selected_residual_depth'] is not None and
                      s['selected_residual_depth']>=2 for s in summaries)},sort_keys=True))
