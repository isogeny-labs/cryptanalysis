"""Independent Sage reconstruction of output-first residual and source-code decisions."""
import hashlib,itertools,json,resource,sys,time
from collections import Counter
from pathlib import Path
from sage.all import EllipticCurve,GF,PolynomialRing
H=Path(__file__).resolve().parent;case=sys.argv[1]
assert case in ('n41','n131')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((H/(case+'_audit_protocol.json')).read_text())
assert cfg['status']=='FROZEN_BEFORE_OUTPUT_FIRST_SAGE_AUDIT_'+case.upper()
for label,s in cfg['sources'].items():assert sha(s['path'])==s['sha256'],label
produced=json.loads((H/(case+'_result.json')).read_text())
assert produced['status']=='COMPLETE_OUTPUT_FIRST_FIFTH'
start=time.monotonic();n=41 if case=='n41' else 131
R=PolynomialRing(GF(2),'u');u=R.gen()
mod=u**41+u**3+1 if n==41 else u**131+u**13+u**2+u+1
F=GF(2**n,name='u',modulus=mod);E=EllipticCurve(F,[1,0,0,0,1]);dec=F.from_integer
enc=lambda v:sum(int(bit)<<i for i,bit in enumerate(v.polynomial().list()))
seed_mask=56 if case=='n41' else 898618;seed=dec(seed_mask<<1)
width=11 if case=='n41' else 33;rotation=24 if case=='n41' else 72
bits=[i for i in range(width) if i!=seed_mask.bit_length()-1]
base=[dec(1<<(i+1)) for i in bits]
pb=[a*a+seed*a for a in base]
def halftrace(v):
    assert v.trace()==0
    out=F.zero();term=v
    for _ in range((n+1)//2):out+=term;term=term**4
    assert out*out+out==v
    return out
h=halftrace(seed);Hc=h*h;Cc=F.one()+Hc
assert enc(Hc)==produced['H'] and enc(Cc)==produced['C'] and Cc
basis={}
for i,value in enumerate(pb):
    word=enc(value);code=1<<i
    while word:
        pivot=word.bit_length()-1
        if pivot not in basis:basis[pivot]=(word,code);break
        v,c=basis[pivot];word^=v;code^=c
    else:raise AssertionError('dependent basis')
assert len(basis)==width-1
def decode(word):
    code=0
    while word:
        pivot=word.bit_length()-1
        if pivot not in basis:return None
        v,c=basis[pivot];word^=v;code^=c
    return code
def source(code):
    a=sum((base[i] for i in range(len(base)) if code>>i&1),F.zero())
    return a,a+seed
def eligible(a,b):
    return bool(a and b and a.trace()==0 and (~a).trace()==0 and (~b).trace()==0)
def column(a):
    x=F.one()+1/halftrace(a)
    return min(enc(x**(1<<k)) for k in range(n))
def pair_points(a,b):
    x1=F.one()+1/halftrace(a);x2=F.one()+1/halftrace(b)
    return [E((p+q)[0]**(1<<rotation),(p+q)[1]**(1<<rotation))
            for p,q in itertools.product(E.lift_x(x1,all=True),E.lift_x(x2,all=True))]
if case=='n41':
    panel=json.loads(Path(cfg['sources']['panel']['path']).read_text())
    states={}
    for line in Path(cfg['sources']['join_input']['path']).read_text().splitlines()[2:]:
        c=line.split()
        if c[0]=='S':
            slot,sid,code,branch,a,b,ca,cb,x,y=map(int,c[1:])
            states[(slot,sid)]={'point':E(dec(x),dec(y)),'code':code,'columns':[ca,cb]}
    boxes=[]
    for box in panel['boxes']:
        choices=[[states[(slot,sid)] for pair in box['root_choices'][slot] for sid in pair]
                 for slot in range(4)]
        boxes.append((box['kind'],choices,E(*(dec(v) for v in panel['target_point']))))
else:
    panel=json.loads(Path(cfg['sources']['panel']['path']).read_text())
    boxes=[]
    for box in panel['boxes']:
        choices=[]
        for slot in range(4):
            choices.append([{'point':E(*(dec(v) for v in xy)),'code':choice['code'],'columns':choice['columns']}
                            for choice in box['choices'][slot] for xy in choice['signed_points']])
        boxes.append((box['kind'],choices,E(*(dec(v) for v in box['target_point']))))
rows=[];checked=0
for index,(kind,choices,target) in enumerate(boxes):
    counts=Counter();hits=[]
    for ids in itertools.product(range(4),repeat=4):
        selected=[choices[j][ids[j]] for j in range(4)]
        prefix=sum((item['point'] for item in selected),E(0))
        residual=target-prefix
        if residual==E(0):status='IDENTITY_RESIDUAL'
        elif residual[0]==0:status='ZERO_X_RESIDUAL'
        else:
            xbase=residual[0]**(1<<((n-rotation)%n))
            p=Hc*xbase+Cc/xbase
            code=decode(enc(p))
            if code is None:status='OUTSIDE_PRODUCT_SUBSPACE'
            else:
                a,b=source(code)
                assert a*b==p
                if not eligible(a,b):status='INELIGIBLE_CODE'
                elif residual not in pair_points(a,b):status='GROUP_MISMATCH'
                else:
                    status='VERIFIED_PAIR_OUTPUT'
                    cols=[col for item in selected for col in item['columns']]+[column(a),column(b)]
                    if len(set(cols))<10 or code in [item['code'] for item in selected]:
                        counts['COLUMN_OR_CODE_COLLISION']+=1
                    else:
                        hits.append({'prefix_choice_indices':list(ids),'last_code':code,
                                     'residual_point':[enc(residual[0]),enc(residual[1])],
                                     'factor_columns':cols})
        counts[status]+=1;checked+=1
    expected=produced['rows'][index]
    assert dict(sorted(counts.items()))==expected['status_counts'],(index,counts,expected['status_counts'])
    assert len(hits)==len(expected['verified_relations'])
    for got,want in zip(hits,expected['verified_relations']):
        assert got['prefix_choice_indices']==want['prefix_choice_indices']
        assert got['last_code']==want['last_code']
        assert got['residual_point']==want['residual_point']
        assert got['factor_columns']==want['factor_columns']
    rows.append({'box_index':index,'status_counts':dict(sorted(counts.items())),
                 'verified_relations':hits})
assert checked==9*256
result={'status':'PASS_INDEPENDENT_OUTPUT_FIRST_SAGE_AUDIT','candidate_id':None,
        'case':case,'curve_id':cfg['curve_id'],'residuals_checked':checked,
        'source_product_rank':len(basis),'boxes_checked':len(rows),
        'verified_relations':sum(len(row['verified_relations']) for row in rows),
        'rows':rows,'wall_seconds':time.monotonic()-start,
        'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(H/(case+'_audit_protocol.json')),'script_sha256':sha(Path(__file__))}
(H/(case+'_audit_result.json')).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('status','case','residuals_checked','verified_relations','wall_seconds')},sort_keys=True),flush=True)
