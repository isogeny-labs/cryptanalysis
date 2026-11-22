"""Matched W29 quartic/subspace-GCD comparator on frozen N131 first codes."""
import hashlib,json,resource,time
from pathlib import Path
from sage.all import GF,PolynomialRing
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'n131_gcd_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_N131_GCD_COMPARISON'
for label,item in cfg['sources'].items():assert sha(item['path'])==item['sha256'],label
source=json.loads(Path(cfg['sources']['coefficients']['path']).read_text())
reference=json.loads((HERE/'n131_result.json').read_text())
R=PolynomialRing(GF(2),'u');u=R.gen()
F=GF(2**131,name='u',modulus=u**131+u**13+u**2+u+1)
S=PolynomialRing(F,'z');z=S.gen()
enc=lambda x:sum(int(b)<<i for i,b in enumerate(x.polynomial().list()))
dec=lambda x:F.from_integer(x)
seed_mask=898618;seed=dec(seed_mask<<1)
bits=[i for i in range(29) if i!=seed_mask.bit_length()-1]
def source_product(code,rotation):
    a=sum((dec(1<<(bit+1)) for j,bit in enumerate(bits) if code>>j&1),F.zero())
    return (a*a+seed*a)**(1<<rotation)
qbasis=[source_product(1<<j,18) for j in range(28)]
def eval_linearized(coeffs,value):
    out=F.zero()
    for c in coeffs:
        out+=c*value;value*=value
    return out
start=time.monotonic();coefs=[F.one()]
for basis in qbasis:
    w=eval_linearized(coefs,basis)
    assert w
    nxt=[w*coefs[0]]
    for j in range(1,len(coefs)):nxt.append(coefs[j-1]*coefs[j-1]+w*coefs[j])
    nxt.append(coefs[-1]*coefs[-1]);coefs=nxt
assert len(coefs)==29
assert all(eval_linearized(coefs,b)==0 for b in qbasis)
prepared=time.monotonic()
terms=[[(i,j,dec(c)) for i,j,c in row['terms']] for row in source['rows'][:2]]
rows=[];status='COMPLETE_N131_GCD_PANEL'
for previous in reference['rows']:
    if time.monotonic()-start>=cfg['wall_cap_seconds']:
        status='WALL_CAP_PARTIAL_PANEL';break
    p=source_product(previous['p_code'],0)
    t0=time.monotonic()
    powers=[F.one(),p]
    for _ in range(3):powers.append(powers[-1]*p)
    poly=S.zero()
    for i,j,c in terms[previous['target_index']]:poly+=c*powers[i]*z**j
    assert poly and poly.degree()<=4
    specialized=time.monotonic()
    x=z%poly;remainder=S.zero()
    for c in coefs:
        remainder=(remainder+c*x)%poly
        x=(x*x)%poly
    factor=poly.gcd(remainder)
    checked=time.monotonic()
    reject=(factor.degree()==0)
    assert reject==previous['reject']
    row={'target_index':previous['target_index'],'p_code':previous['p_code'],
         'quartic_degree':int(poly.degree()),'gcd_degree':int(factor.degree()),
         'reject':reject,'specialize_seconds':specialized-t0,'gcd_seconds':checked-specialized}
    rows.append(row)
    print(json.dumps(row,sort_keys=True),flush=True)
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>cfg['rss_cap_bytes']:
        status='RSS_CAP_PARTIAL_PANEL';break
result={'status':status,'candidate_id':None,'rows':rows,'requested_rows':len(reference['rows']),
        'precompute_seconds':prepared-start,'wall_seconds':time.monotonic()-start,
        'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(HERE/'n131_gcd_protocol.json'),'script_sha256':sha(Path(__file__))}
(HERE/'n131_gcd_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('status','precompute_seconds','wall_seconds','peak_rss_raw')},sort_keys=True),flush=True)
