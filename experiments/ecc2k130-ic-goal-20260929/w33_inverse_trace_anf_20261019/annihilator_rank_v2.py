"""Exact ranks of low-degree polynomials vanishing on valid affine-slice codes."""
import hashlib,itertools,json,time,resource
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((H/'rank_protocol_v2.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_VALID_CODE_ANNIHILATOR_RANK_V2'
for label,s in cfg['sources'].items():assert sha(s['path'])==s['sha256'],label
input=json.loads((H/'result_v3.json').read_text())
assert input['status']=='COMPLETE_INVERSE_TRACE_ANF'
start=time.monotonic();out=[]
def mobius(coeff,k):
    v=coeff[:]
    for bit in range(k):
        for mask in range(1<<k):
            if mask>>bit&1:v[mask]^=v[mask^(1<<bit)]
    return v
for name,f in input['families'].items():
    for row in f['slices']:
        k=len(row['free_code_bits']);size=1<<k
        ta=mobius([(int(row['trace_a']['anf_hex'],16)>>i)&1 for i in range(size)],k)
        ia=mobius([(int(row['trace_inv_a']['anf_hex'],16)>>i)&1 for i in range(size)],k)
        ib=mobius([(int(row['trace_inv_b']['anf_hex'],16)>>i)&1 for i in range(size)],k)
        valid=[i for i in range(size) if (ta[i],ia[i],ib[i])==(0,0,0)]
        assert len(valid)==row['valid_codes']
        ranks=[]
        for degree in cfg['degrees']:
            monomials=[mask for mask in range(size) if mask.bit_count()<=degree]
            basis={};pivot_codes=[]
            for code in valid:
                word=sum(1<<j for j,monomial in enumerate(monomials)
                         if code&monomial==monomial)
                while word:
                    pivot=word.bit_length()-1
                    if pivot in basis:word^=basis[pivot]
                    else:basis[pivot]=word;pivot_codes.append(code);break
            ranks.append({'degree_cap':degree,'monomials':len(monomials),
                          'rank_on_valid_codes':len(basis),
                          'annihilator_dimension':len(monomials)-len(basis),
                          'pivot_codes':pivot_codes if degree==cfg['certificate_degrees'][name] else None})
        out.append({'family':name,'slice':row['name'],'valid_codes':len(valid),'ranks':ranks})
result={'status':'COMPLETE_VALID_CODE_ANNIHILATOR_RANK','candidate_id':None,'rows':out,
        'wall_seconds':time.monotonic()-start,'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(H/'rank_protocol_v2.json'),'script_sha256':sha(Path(__file__))}
(H/'rank_result_v2.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
for r in out:print(r['family'],r['slice'],[(x['degree_cap'],x['rank_on_valid_codes'],x['annihilator_dimension']) for x in r['ranks']])
