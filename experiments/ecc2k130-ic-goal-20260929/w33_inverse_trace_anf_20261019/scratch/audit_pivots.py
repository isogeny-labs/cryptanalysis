"""Independently replay full-rank valid-code certificates with exponent inversion."""
import hashlib,json,resource,signal,time
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((H/'audit_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_INDEPENDENT_PIVOT_AUDIT'
for label,s in cfg['sources'].items():assert sha(s['path'])==s['sha256'],label
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('pivot audit wall cap')))
signal.alarm(cfg['wall_cap_seconds']);start=time.monotonic()
class FieldAlt:
    def __init__(self,n,taps):self.n=n;self.mod=(1<<n)|sum(1<<i for i in taps)
    def reduce(self,v):
        while v.bit_length()>self.n:v^=self.mod<<(v.bit_length()-self.n-1)
        return v
    def mul(self,a,b):
        raw=0
        while b:
            low=b&-b;raw^=a<<(low.bit_length()-1);b^=low
        return self.reduce(raw)
    def square(self,a):
        raw=0
        while a:
            low=a&-a;raw^=1<<(2*(low.bit_length()-1));a^=low
        return self.reduce(raw)
    def inverse(self,a):
        assert a
        power=(1<<self.n)-2;out=1
        while power:
            if power&1:out=self.mul(out,a)
            a=self.square(a);power>>=1
        return out
    def trace_mask(self):
        mask=0
        for i in range(self.n):
            value=1<<i;total=0
            for _ in range(self.n):total^=value;value=self.square(value)
            assert total in (0,1)
            if total:mask|=1<<i
        return mask
rank=json.loads((H/'rank_result_v2.json').read_text())
assert rank['status']=='COMPLETE_VALID_CODE_ANNIHILATOR_RANK'
truth=json.loads((H/'result_v3.json').read_text())
rows=[]
for row in rank['rows']:
    name=row['family'];slice_name=row['slice']
    family=truth['families'][name]
    slice_row=next(s for s in family['slices'] if s['name']==slice_name)
    n=family['field_degree'];taps=[0,3] if n==41 else [0,1,2,13]
    F=FieldAlt(n,taps);trace=F.trace_mask()
    assert trace==family['trace_mask']
    width=11 if n==41 else 33;seed_mask=56 if n==41 else 898618
    bits=[i for i in range(width) if i!=seed_mask.bit_length()-1]
    seed=seed_mask<<1;free=slice_row['free_code_bits'];anchor=slice_row['anchor_code']
    degree=cfg['certificate_degrees'][name]
    cert=next(x for x in row['ranks'] if x['degree_cap']==degree)
    pivots=cert['pivot_codes'];assert len(pivots)==cert['monomials']==cert['rank_on_valid_codes']
    monomials=[m for m in range(1<<len(free)) if m.bit_count()<=degree]
    basis={}
    for local in pivots:
        code=anchor
        for j,bit in enumerate(free):
            if local>>j&1:code^=1<<bit
        a=sum((1<<(bits[i]+1) for i in range(len(bits)) if code>>i&1),0)
        assert a and a!=seed
        inv_a=F.inverse(a);inv_b=F.inverse(a^seed)
        assert F.mul(a,inv_a)==1 and F.mul(a^seed,inv_b)==1
        assert (a&trace).bit_count()%2==0
        assert (inv_a&trace).bit_count()%2==0
        assert (inv_b&trace).bit_count()%2==0
        word=sum(1<<j for j,m in enumerate(monomials) if local&m==m)
        while word:
            bit=word.bit_length()-1
            if bit in basis:word^=basis[bit]
            else:basis[bit]=word;break
        else:raise AssertionError(('dependent pivot',name,slice_name,local))
    assert len(basis)==len(monomials)
    rows.append({'family':name,'slice':slice_name,'degree_cap':degree,
                 'valid_pivots_checked':len(pivots),'independent_rank':len(basis),
                 'trace_mask':trace})
signal.alarm(0)
result={'status':'PASS_INDEPENDENT_VALID_PIVOT_AUDIT','candidate_id':None,'rows':rows,
        'valid_pivots_checked':sum(r['valid_pivots_checked'] for r in rows),
        'wall_seconds':time.monotonic()-start,
        'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(H/'audit_protocol.json'),'script_sha256':sha(Path(__file__))}
(H/'audit_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'valid_pivots_checked':result['valid_pivots_checked'],'wall_seconds':result['wall_seconds']},sort_keys=True))
