"""Checked-Sage producer for exact p-adic valuations of frozen rational residuals."""
from sage.all import EllipticCurve, QQ
from fractions import Fraction
from pathlib import Path
import gzip
import hashlib
import json
import time

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
SOURCE=H.parent/'xedni-wide-shift-defect-20261116'
BASE=H.parent/'xedni-height-selected-two-image-20261116'
for name,digest in P['parent_sha256'].items():
    assert hashlib.sha256((SOURCE/name).read_bytes()).hexdigest()==digest
parent=json.loads((SOURCE/'run-result.json').read_text())
assert parent['status']=='complete' and parent['counts']['candidate_attempts']==P['expected_candidate_attempts']
assert json.loads((SOURCE/'audit.json').read_text())['status']=='PASS'
queries={r['event_index']:r for r in map(json.loads,gzip.open(BASE/'queries.jsonl.gz','rt'))}
vectors={(r['event_index'],r['vector_index']):r for r in map(json.loads,gzip.open(BASE/'vectors.jsonl.gz','rt'))}
START=time.monotonic()

def read_part(meta):
    blob=(SOURCE/meta['path']).read_bytes()
    assert hashlib.sha256(blob).hexdigest()==meta['gzip_sha256']
    raw=gzip.decompress(blob)
    assert hashlib.sha256(raw).hexdigest()==meta['raw_sha256']
    rows=[json.loads(line) for line in raw.splitlines()]
    assert len(rows)==meta['rows']
    return rows

def packed(path,rows):
    raw=''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in rows).encode()
    blob=gzip.compress(raw,compresslevel=9,mtime=0)
    (H/path).write_bytes(blob)
    return {'path':path,'rows':len(rows),'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'gzip_sha256':hashlib.sha256(blob).hexdigest(),'gzip_bytes':len(blob)}

def v_int(n,p):
    n=abs(int(n))
    if n==0: return None
    k=0
    while n%p==0:
        n//=p; k+=1
    return k

def v_rat(z,p):
    num,den=z.numerator(),z.denominator()
    if num==0: return None
    return v_int(num,p)-v_int(den,p)

def center(z,p): return z-p if z>p//2 else z

parts=[]; summaries=[]
counts={k:0 for k in ('candidate_attempts','candidate_pass','candidate_failure',
                      'nonidentity_residuals','identity_residuals','formal_pattern_pass','formal_pattern_fail')}
for summary,meta in zip(parent['summaries'],parent['candidate_parts']):
    event,vi,p,a,b=(summary[k] for k in ('event_index','vector_index','p','a','b'))
    query=queries[event]
    assert vectors[(event,vi)]['public_relation']
    rows=[]
    parent_rows=read_part(meta)
    score_by_shift={tuple(r['shift']):r['model_score_bits'] for r in parent_rows if r['status']=='pass'}
    for row in parent_rows:
        counts['candidate_attempts']+=1
        rec={'event_index':event,'vector_index':vi,'shift':row['shift']}
        if row['status']!='pass':
            rec.update({'status':'parent_failure','parent_error':row['error'],
                        'vx':None,'vy':None,'depth':None,'pattern':None})
            counts['candidate_failure']+=1
            rows.append(rec)
            continue
        shift=row['shift']; U,V=query['U'],query['V']
        x1,y1=[center(z,p) for z in U]
        x2,y2=[center(z,p) for z in V]
        x1+=shift[0]*p; y1+=shift[1]*p
        x2+=shift[2]*p; y2+=shift[3]*p
        C=EllipticCurve(QQ,[QQ(row['A']),QQ(row['B'])])
        P1,P2=C(QQ(x1),QQ(y1)),C(QQ(x2),QQ(y2))
        R=a*P1+b*P2
        if R.is_zero():
            vx=vy=depth=pattern=None
            counts['identity_residuals']+=1
        else:
            vx,vy=v_rat(R[0],p),v_rat(R[1],p)
            depth=v_rat(-R[0]/R[1],p)
            pattern=(depth is not None and depth>=1 and vx==-2*depth and vy==-3*depth)
            counts['nonidentity_residuals']+=1
            counts['formal_pattern_pass' if pattern else 'formal_pattern_fail']+=1
        rec.update({'status':'pass','vx':vx,'vy':vy,'depth':depth,'pattern':pattern,
                    'parent_residual_digest':row['residual_digest']})
        counts['candidate_pass']+=1
        rows.append(rec)
    passed=[r for r in rows if r['status']=='pass']
    assert len(passed)==summary['pass']
    byshift={tuple(r['shift']):r for r in passed}
    model=byshift[tuple(summary['model_choice']['shift'])]
    prior=byshift[tuple(query['chosen_shift'])]
    oracle=max(passed,key=lambda r:(float('inf') if r['depth'] is None else r['depth'],
                                    -score_by_shift[tuple(r['shift'])],
                                    tuple(-z for z in r['shift'])))
    summaries.append({'event_index':event,'vector_index':vi,'p':p,'a':a,'b':b,
                      'attempts':len(rows),'pass':len(passed),'failures':len(rows)-len(passed),
                      'model_depth':model['depth'],'prior_depth':prior['depth'],
                      'oracle_depth':oracle['depth'],'oracle_shift':oracle['shift'],
                      'depth_ge_2':sum(r['depth'] is not None and r['depth']>=2 for r in passed),
                      'depth_ge_3':sum(r['depth'] is not None and r['depth']>=3 for r in passed)})
    parts.append(packed(f'valuations.event{event:03d}.jsonl.gz',rows))
    if time.monotonic()-START>P['run_cap_seconds']:
        raise TimeoutError('frozen run cap exceeded')
assert counts['candidate_attempts']==P['expected_candidate_attempts']
result={'schema':'xedni-residual-padic-depth-result-v1','status':'complete',
        'protocol_sha256':hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest(),
        'counts':counts,'summaries':summaries,'parts':parts,
        'elapsed_wall_seconds':time.monotonic()-START}
(H/'run-result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'counts':counts,
                  'depth_ge_2':sum(s['depth_ge_2'] for s in summaries),
                  'depth_ge_3':sum(s['depth_ge_3'] for s in summaries)},sort_keys=True))
