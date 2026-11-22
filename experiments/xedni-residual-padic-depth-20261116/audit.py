"""Independent Fraction replay of all frozen formal-parameter depths."""
from collections import Counter
from fractions import Fraction
from pathlib import Path
import gzip
import hashlib
import json

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
R=json.loads((H/'run-result.json').read_text())
SOURCE=H.parent/'xedni-wide-shift-defect-20261116'
BASE=H.parent/'xedni-height-selected-two-image-20261116'
assert hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()==R['protocol_sha256']
for name,digest in P['parent_sha256'].items():
    assert hashlib.sha256((SOURCE/name).read_bytes()).hexdigest()==digest
assert json.loads((SOURCE/'audit.json').read_text())['status']=='PASS'
parent=json.loads((SOURCE/'run-result.json').read_text())
queries={r['event_index']:r for r in map(json.loads,gzip.open(BASE/'queries.jsonl.gz','rt'))}
vectors={(r['event_index'],r['vector_index']):r for r in map(json.loads,gzip.open(BASE/'vectors.jsonl.gz','rt'))}

def read_part(folder,meta):
    blob=(folder/meta['path']).read_bytes()
    assert len(blob)==meta['gzip_bytes']
    assert hashlib.sha256(blob).hexdigest()==meta['gzip_sha256']
    raw=gzip.decompress(blob)
    assert hashlib.sha256(raw).hexdigest()==meta['raw_sha256']
    rows=[json.loads(line) for line in raw.splitlines()]
    assert len(rows)==meta['rows']
    return rows

def add(Pt,Qt,A):
    if Pt is None: return Qt
    if Qt is None: return Pt
    x,y=Pt; u,v=Qt
    if x==u and y+v==0: return None
    slope=(3*x*x+A)/(2*y) if Pt==Qt else (v-y)/(u-x)
    X=slope*slope-x-u
    return X,slope*(x-X)-y

def mul(n,Pt,A):
    if n<0: Pt=(Pt[0],-Pt[1]); n=-n
    out=None
    while n:
        if n&1: out=add(out,Pt,A)
        Pt=add(Pt,Pt,A); n//=2
    return out

def center(z,p): return z-p if z>p//2 else z

def v_int(n,p):
    n=abs(n)
    if n==0: return None
    k=0
    while n%p==0: n//=p; k+=1
    return k

def v_rat(z,p):
    z=Fraction(z)
    if z.numerator==0: return None
    return v_int(z.numerator,p)-v_int(z.denominator,p)

counts=Counter(); depth_hist=Counter(); model_depths=[]; prior_depths=[]; oracle_depths=[]
for summary,pmeta,rmeta,rsummary in zip(parent['summaries'],parent['candidate_parts'],R['parts'],R['summaries']):
    event,vi,p,a,b=(summary[k] for k in ('event_index','vector_index','p','a','b'))
    assert (rsummary['event_index'],rsummary['vector_index'],rsummary['p'],rsummary['a'],rsummary['b'])==(event,vi,p,a,b)
    assert vectors[(event,vi)]['public_relation']
    query=queries[event]
    parent_rows=read_part(SOURCE,pmeta)
    rows=read_part(H,rmeta)
    assert len(parent_rows)==len(rows)==625
    scores={tuple(row['shift']):row['model_score_bits'] for row in parent_rows if row['status']=='pass'}
    for parent_row,row in zip(parent_rows,rows):
        assert parent_row['status']=='pass' and row['status']=='pass'
        assert (row['event_index'],row['vector_index'],row['shift'])==(event,vi,parent_row['shift'])
        shift=row['shift']; U,V=query['U'],query['V']
        x1,y1=[center(z,p) for z in U]; x2,y2=[center(z,p) for z in V]
        x1+=shift[0]*p; y1+=shift[1]*p
        x2+=shift[2]*p; y2+=shift[3]*p
        A=Fraction((y1*y1-x1**3)-(y2*y2-x2**3),x1-x2)
        B=Fraction(y1*y1-x1**3)-A*x1
        assert (str(A),str(B))==(parent_row['A'],parent_row['B'])
        P1,P2=(Fraction(x1),Fraction(y1)),(Fraction(x2),Fraction(y2))
        assert P1[1]**2==P1[0]**3+A*P1[0]+B
        assert P2[1]**2==P2[0]**3+A*P2[0]+B
        residual=add(mul(a,P1,A),mul(b,P2,A),A)
        coords=None if residual is None else [str(residual[0]),str(residual[1])]
        digest=hashlib.sha256(json.dumps(coords,separators=(',',':')).encode()).hexdigest()
        assert digest==row['parent_residual_digest']==parent_row['residual_digest']
        if residual is None:
            vx=vy=depth=pattern=None
            counts['identity_residuals']+=1
        else:
            vx,vy=v_rat(residual[0],p),v_rat(residual[1],p)
            depth=v_rat(-residual[0]/residual[1],p)
            pattern=(depth is not None and depth>=1 and vx==-2*depth and vy==-3*depth)
            counts['nonidentity_residuals']+=1
            counts['formal_pattern_pass' if pattern else 'formal_pattern_fail']+=1
            depth_hist[depth]+=1
        assert (vx,vy,depth,pattern)==(row['vx'],row['vy'],row['depth'],row['pattern'])
        counts['candidate_attempts']+=1; counts['candidate_pass']+=1
    byshift={tuple(row['shift']):row for row in rows}
    model=byshift[tuple(summary['model_choice']['shift'])]
    prior=byshift[tuple(query['chosen_shift'])]
    oracle=max(rows,key=lambda row:(float('inf') if row['depth'] is None else row['depth'],
                                    -scores[tuple(row['shift'])],tuple(-z for z in row['shift'])))
    assert rsummary=={'event_index':event,'vector_index':vi,'p':p,'a':a,'b':b,
        'attempts':625,'pass':625,'failures':0,
        'model_depth':model['depth'],'prior_depth':prior['depth'],
        'oracle_depth':oracle['depth'],'oracle_shift':oracle['shift'],
        'depth_ge_2':sum(row['depth'] is not None and row['depth']>=2 for row in rows),
        'depth_ge_3':sum(row['depth'] is not None and row['depth']>=3 for row in rows)}
    model_depths.append(model['depth']); prior_depths.append(prior['depth']); oracle_depths.append(oracle['depth'])
assert all(counts[k]==v for k,v in R['counts'].items())
assert counts['candidate_attempts']==13750 and counts['formal_pattern_fail']==0
summary={'schema':'xedni-residual-padic-depth-audit-v1','status':'PASS',
         'counts':dict(counts),'depth_histogram':{str(k):v for k,v in sorted(depth_hist.items())},
         'model_depth_histogram':{str(k):model_depths.count(k) for k in sorted(set(model_depths))},
         'prior_depth_histogram':{str(k):prior_depths.count(k) for k in sorted(set(prior_depths))},
         'oracle_depth_histogram':{str(k):oracle_depths.count(k) for k in sorted(set(oracle_depths))},
         'oracle_improved_hits':sum(o>m for o,m in zip(oracle_depths,model_depths)),
         'depth_ge_2':sum(v for k,v in depth_hist.items() if k>=2),
         'depth_ge_3':sum(v for k,v in depth_hist.items() if k>=3),
         'uniform_heuristic_depth_ge_2':sum(625/r['p'] for r in R['summaries']),
         'run_result_sha256':hashlib.sha256((H/'run-result.json').read_bytes()).hexdigest()}
(H/'audit.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2,sort_keys=True))
