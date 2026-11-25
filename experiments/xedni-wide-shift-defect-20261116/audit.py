"""Independent exact-arithmetic replay of every wide-shift candidate residual."""
from collections import Counter
from fractions import Fraction
from pathlib import Path
import gzip
import hashlib
import itertools
import json
import statistics

H = Path(__file__).resolve().parent
P = json.loads((H/'protocol.json').read_text())
R = json.loads((H/'run-result.json').read_text())
SOURCE = H.parent/'xedni-height-selected-two-image-20261116'
assert hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()==R['protocol_sha256']
for name, digest in P['parent_sha256'].items():
    assert hashlib.sha256((SOURCE/name).read_bytes()).hexdigest()==digest
assert json.loads((SOURCE/'audit.json').read_text())['status']=='PASS'

def read_source(name):
    return [json.loads(line) for line in gzip.open(SOURCE/name,'rt')]

def read_part(meta):
    blob=(H/meta['path']).read_bytes()
    assert len(blob)==meta['gzip_bytes']
    assert hashlib.sha256(blob).hexdigest()==meta['gzip_sha256']
    raw=gzip.decompress(blob)
    assert hashlib.sha256(raw).hexdigest()==meta['raw_sha256']
    rows=[json.loads(line) for line in raw.splitlines()]
    assert len(rows)==meta['rows']
    return rows

queries={r['event_index']:r for r in read_source('queries.jsonl.gz')}
hits=[r for r in read_source('vectors.jsonl.gz') if r['public_relation']]
assert len(hits)==P['expected_admitted_hits']==len(R['summaries'])==len(R['candidate_parts'])

def add(Pt,Qt,A,m=None):
    if Pt is None: return Qt
    if Qt is None: return Pt
    x,y=Pt; u,v=Qt
    if m is not None:
        if x==u and (y+v)%m==0: return None
        slope=((3*x*x+A)*pow(2*y,-1,m))%m if Pt==Qt else ((v-y)*pow(u-x,-1,m))%m
        X=(slope*slope-x-u)%m
        return X,(slope*(x-X)-y)%m
    if x==u and y+v==0: return None
    slope=(3*x*x+A)/(2*y) if Pt==Qt else (v-y)/(u-x)
    X=slope*slope-x-u
    return X,slope*(x-X)-y

def mul(n,Pt,A,m=None):
    if n<0:
        Pt=(Pt[0],(-Pt[1])%m if m is not None else -Pt[1]); n=-n
    out=None
    while n:
        if n&1: out=add(out,Pt,A,m)
        Pt=add(Pt,Pt,A,m); n//=2
    return out

def center(z,p): return z-p if z>p//2 else z

def bits(z):
    z=Fraction(z)
    return max(abs(z.numerator).bit_length(),z.denominator.bit_length())

def mod(z,p):
    z=Fraction(z)
    assert z.denominator%p
    return z.numerator*pow(z.denominator,-1,p)%p

def candidate(p,U,V,shift):
    x1,y1=[center(z,p) for z in U]
    x2,y2=[center(z,p) for z in V]
    x1+=shift[0]*p; y1+=shift[1]*p
    x2+=shift[2]*p; y2+=shift[3]*p
    A=Fraction((y1*y1-x1**3)-(y2*y2-x2**3),x1-x2)
    B=Fraction(y1*y1-x1**3)-A*x1
    assert 4*A**3+27*B**2!=0
    assert (mod(A,p),mod(B,p))==(p-1,p-2)
    assert (x1%p,y1%p)==tuple(U) and (x2%p,y2%p)==tuple(V)
    P1,P2=(Fraction(x1),Fraction(y1)),(Fraction(x2),Fraction(y2))
    assert P1[1]**2==P1[0]**3+A*P1[0]+B
    assert P2[1]**2==P2[0]**3+A*P2[0]+B
    return A,B,P1,P2,max(bits(z) for z in (A,B,*P1,*P2))

counts=Counter(); model_scores=[]; oracle_scores=[]; prior_scores=[]
model_residuals=[]; oracle_residuals=[]; prior_residuals=[]
for hit,summary,meta in zip(hits,R['summaries'],R['candidate_parts']):
    event,vi,a,b=(hit[k] for k in ('event_index','vector_index','a','b'))
    query=queries[event]
    p,U,V=query['p'],query['U'],query['V']
    assert summary['event_index']==event and summary['vector_index']==vi
    assert summary['p']==p and summary['a']==a and summary['b']==b
    assert query['branch']=='distinct_x'
    assert add(mul(a,tuple(U),-1,p),mul(b,tuple(V),-1,p),-1,p) is None
    rows=read_part(meta)
    shifts=list(itertools.product(P['shift_values'],repeat=4))
    assert len(rows)==len(shifts)==625
    for row,shift in zip(rows,shifts):
        assert row['event_index']==event and row['vector_index']==vi and row['shift']==list(shift)
        A,B,P1,P2,score=candidate(p,U,V,shift)
        assert add(P1,(P1[0],-P1[1]),A) is None
        residual=add(mul(a,P1,A),mul(b,P2,A),A)
        coords=None if residual is None else [str(residual[0]),str(residual[1])]
        digest=hashlib.sha256(json.dumps(coords,separators=(',',':')).encode()).hexdigest()
        residual_bits=0 if residual is None else max(bits(residual[0]),bits(residual[1]))
        assert row['status']=='pass'
        assert (row['A'],row['B'],row['model_score_bits'])==(str(A),str(B),score)
        assert (row['relation_zero'],row['residual_score_bits'],row['residual_digest'])==(
            residual is None,residual_bits,digest)
        if residual is not None:
            assert residual[0].denominator % p == 0
            counts['kernel_denominator_pass']+=1
        counts['candidate_attempts']+=1
        counts['candidate_pass']+=1
        counts['rational_controls']+=1
        counts['rational_relation_hits']+=int(residual is None)
    model_choice=min(rows,key=lambda r:(r['model_score_bits'],r['shift']))
    oracle_choice=min(rows,key=lambda r:(r['residual_score_bits'],r['model_score_bits'],r['shift']))
    centered=next(r for r in rows if r['shift']==[0,0,0,0])
    prior=next(r for r in rows if r['shift']==query['chosen_shift'])
    assert prior['model_score_bits']==query['score_bits']
    assert summary=={'event_index':event,'vector_index':vi,'p':p,'a':a,'b':b,
        'attempts':625,'pass':625,'failures':0,
        'rational_relation_hits':sum(r['relation_zero'] for r in rows),
        'model_choice':{'shift':model_choice['shift'],'model_score_bits':model_choice['model_score_bits'],
                        'residual_score_bits':model_choice['residual_score_bits']},
        'oracle_choice':{'shift':oracle_choice['shift'],'model_score_bits':oracle_choice['model_score_bits'],
                         'residual_score_bits':oracle_choice['residual_score_bits']},
        'centered_residual_score_bits':centered['residual_score_bits'],
        'prior_residual_score_bits':prior['residual_score_bits']}
    model_scores.append(model_choice['model_score_bits'])
    oracle_scores.append(oracle_choice['model_score_bits'])
    prior_scores.append(prior['model_score_bits'])
    model_residuals.append(model_choice['residual_score_bits'])
    oracle_residuals.append(oracle_choice['residual_score_bits'])
    prior_residuals.append(prior['residual_score_bits'])
    counts['admitted_hits']+=1
assert all(counts[k]==v for k,v in R['counts'].items())
assert set(counts)-{'kernel_denominator_pass'}<=set(R['counts'])
assert counts['candidate_attempts']==13750 and counts['rational_relation_hits']==0
result={'schema':'xedni-wide-shift-defect-audit-v1','status':'PASS','counts':dict(counts),
        'model_score_median':statistics.median(model_scores),
        'prior_model_score_median':statistics.median(prior_scores),
        'oracle_model_score_median':statistics.median(oracle_scores),
        'model_choice_residual_median':statistics.median(model_residuals),
        'prior_choice_residual_median':statistics.median(prior_residuals),
        'oracle_choice_residual_median':statistics.median(oracle_residuals),
        'wider_model_improvements':sum(x<y for x,y in zip(model_scores,prior_scores)),
        'oracle_residual_improvements':sum(x<y for x,y in zip(oracle_residuals,model_residuals)),
        'run_result_sha256':hashlib.sha256((H/'run-result.json').read_bytes()).hexdigest()}
(H/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2,sort_keys=True))
