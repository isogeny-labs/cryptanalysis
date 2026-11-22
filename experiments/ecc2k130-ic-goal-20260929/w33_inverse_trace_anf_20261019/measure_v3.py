"""Exact affine-slice ANFs of fixed-seed inverse-trace eligibility."""
import hashlib,json,resource,signal,time
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((H/'protocol_v3.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_INVERSE_TRACE_ANF_V3'
for label,s in cfg['sources'].items():assert sha(s['path'])==s['sha256'],label
rlimit_status='UNAVAILABLE_OS_AFTER_V1_VALUEERROR'
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('wall cap')))
signal.alarm(cfg['wall_cap_seconds'])
start=time.monotonic()
class Field:
    def __init__(self,n,taps):self.n=n;self.mod=(1<<n)|sum(1<<i for i in taps)
    def reduce(self,a):
        while a.bit_length()>self.n:a^=self.mod<<(a.bit_length()-self.n-1)
        return a
    def mul(self,a,b):
        v=0
        while b:
            if b&1:v^=a
            b>>=1;a<<=1
            if a>>self.n:a^=self.mod
        return v
    def square(self,a):
        v=0
        while a:
            low=a&-a;v^=1<<(2*(low.bit_length()-1));a^=low
        return self.reduce(v)
    def inv(self,a):
        assert a
        u,v,g,h=a,self.mod,1,0
        while u!=1:
            assert u
            j=u.bit_length()-v.bit_length()
            if j<0:u,v=v,u;g,h=h,g;j=-j
            u^=v<<j;g^=h<<j
        return self.reduce(g)
    def trace_mask(self):
        mask=0
        for i in range(self.n):
            v=1<<i;t=0
            for _ in range(self.n):t^=v;v=self.square(v)
            assert t in (0,1)
            if t:mask|=1<<i
        return mask

def stats(values,k):
    assert len(values)==1<<k
    coeff=values[:]
    for bit in range(k):
        for index in range(1<<k):
            if index>>bit&1:coeff[index]^=coeff[index^(1<<bit)]
    rebuilt=coeff[:]
    for bit in range(k):
        for index in range(1<<k):
            if index>>bit&1:rebuilt[index]^=rebuilt[index^(1<<bit)]
    assert rebuilt==values
    counts=[0]*(k+1)
    for index,value in enumerate(coeff):
        if value:counts[index.bit_count()]+=1
    return {'ones':sum(values),'degree':max((i for i,v in enumerate(counts) if v),default=-1),
            'monomial_counts_by_degree':counts,'truth_hex':hex(sum(v<<i for i,v in enumerate(values))),
            'anf_hex':hex(sum(v<<i for i,v in enumerate(coeff)))}

def family(name,n,taps,seed_mask,width):
    F=Field(n,taps);seed=seed_mask<<1
    bits=[i for i in range(width) if i!=seed_mask.bit_length()-1]
    assert len(bits)==width-1
    base=[1<<(i+1) for i in bits]
    trace=F.trace_mask()
    def compute(code):
        a=0
        for i,b in enumerate(base):
            if code>>i&1:a^=b
        if a==0 or a==seed:return (None,None,None)
        i1,i2=F.inv(a),F.inv(a^seed)
        assert F.mul(a,i1)==1 and F.mul(a^seed,i2)==1
        t0=(a&trace).bit_count()&1
        t1=(i1&trace).bit_count()&1
        t2=(i2&trace).bit_count()&1
        return (t0,t1,t2)
    checks={}
    for code in cfg['known_codes'][name]:checks[str(code)]=compute(code)
    out={'field_degree':n,'field_modulus':F.mod,'seed':seed,
         'free_bits':len(bits),'trace_mask':trace,'known_code_checks':checks,'slices':[]}
    if name=='n41':
        valid=[]
        for code in range(1<<len(bits)):
            values=compute(code)
            if values==(0,0,0):valid.append(code)
        prior=json.loads(Path(cfg['sources']['n41_valid_codes']['path']).read_text())
        assert valid==prior['valid_codes'] and len(valid)==281
        out['full_valid_count']=len(valid)
        out['full_valid_sha256']=hashlib.sha256(json.dumps(valid,separators=(',',':')).encode()).hexdigest()
    for row in cfg['slices'][name]:
        free=row['free_code_bits'];anchor=row['anchor_code'];k=len(free)
        assert anchor and all(not(anchor>>bit&1) for bit in free)
        table=[[],[],[]];valid=0
        for index in range(1<<k):
            code=anchor
            for j,bit in enumerate(free):
                if index>>j&1:code^=1<<bit
            v=compute(code)
            assert all(x is not None for x in v)
            for j in range(3):table[j].append(v[j])
            valid+=int(v==(0,0,0))
        out['slices'].append({'name':row['name'],'free_code_bits':free,'anchor_code':anchor,
                              'valid_codes':valid,'trace_a':stats(table[0],k),
                              'trace_inv_a':stats(table[1],k),
                              'trace_inv_b':stats(table[2],k)})
    return out
families={}
for name,args in [('n41',(41,[0,3],56,11)),('n131',(131,[0,1,2,13],898618,33))]:
    families[name]=family(name,*args)
signal.alarm(0)
result={'status':'COMPLETE_INVERSE_TRACE_ANF','candidate_id':None,'families':families,
        'wall_seconds':time.monotonic()-start,'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'rlimit_status':rlimit_status,
        'protocol_sha256':sha(H/'protocol_v3.json'),'script_sha256':sha(Path(__file__))}
(H/'result_v3.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
for name,f in families.items():
    print(name,'full_valid',f.get('full_valid_count'),'slices',[(r['name'],r['valid_codes'],r['trace_inv_a']['degree'],r['trace_inv_b']['degree']) for r in f['slices']])
