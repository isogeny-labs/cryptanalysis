#!/usr/bin/env sage -python
"""Screen all 40^3 source-product triples using frozen interpolated tensors."""
import hashlib,json,resource,signal,time
from pathlib import Path
from sage.all import GF,PolynomialRing
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
GEO=ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json'
PRIOR=ROOT/'n41_w8_three_pair_resultant_20261013/result.json'
FILES={'sweep':HERE/'sweep.py','geometry':GEO,'prior':PRIOR,
       'witness_tensor':HERE/'witness_result_v2.json','negative_tensor':HERE/'negative_result_v2.json',
       'runtime':HERE/'sage_runtime_info.json'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    signal.alarm(180)
    proto=json.loads((HERE/'sweep_protocol.json').read_text())
    assert proto['source_sha256']=={k:sha(v) for k,v in FILES.items()}
    geo=json.loads(GEO.read_text());prior=json.loads(PRIOR.read_text())
    poly=PolynomialRing(GF(2),'t');t=poly.gen()
    field=GF(2**41,name='t',modulus=t**41+t**3+1)
    def dec(v):return field(poly([(v>>i)&1 for i in range(41)]))
    def product(slot,mask):
        value=0
        for i,basis in enumerate(geo['blocks'][slot]['product_basis']):
            if mask>>i&1:value^=basis
        return value
    codes=[sorted((product(slot,m),m) for m in geo['permitted_canonical_a']) for slot in range(3)]
    assert all(len(row)==40 and len({p for p,m in row})==40 for row in codes)
    prepared=[[(p,m,dec(p)) for p,m in row] for row in codes]
    panels=[]
    for name in proto['panels']:
        start=time.monotonic_ns()
        tensor=json.loads((HERE/f'{name}_result_v2.json').read_text())
        assert tensor['status']=='PASS_ISOLATED_FIRST_PRODUCT_INTERPOLATION'
        terms=[(i,j,[(k,dec(c)) for k,c in coeffs])
               for i,j,coeffs in tensor['coefficient_terms']]
        pmax=tensor['max_first_product_degree']
        qmax=max(i for i,j,coeffs in terms);rmax=max(j for i,j,coeffs in terms)
        assert len(terms)==213 and pmax<=16 and qmax<=16 and rmax<=24
        powers_q={p:[v**i for i in range(qmax+1)] for p,m,v in prepared[1]}
        values_r=[(p,m,v) for p,m,v in prepared[2]]
        source_zero=[];evaluations=0
        for p0,m0,pv in prepared[0]:
            powers_p=[pv**i for i in range(pmax+1)]
            specialized=[(i,j,sum((c*powers_p[k] for k,c in coeffs),field.zero()))
                         for i,j,coeffs in terms]
            for p1,m1,qv in prepared[1]:
                cp=[field.zero()]*(rmax+1);qpow=powers_q[p1]
                for i,j,c in specialized:cp[j]+=c*qpow[i]
                for p2,m2,rv in values_r:
                    value=field.zero()
                    for coef in reversed(cp):value=value*rv+coef
                    evaluations+=1
                    if value==0:source_zero.append({'products':[p0,p1,p2],
                                                    'masks':[m0,m1,m2]})
        elapsed=time.monotonic_ns()-start
        assert evaluations==64000
        if name=='witness':
            assert prior['witness_pair_products'] in [row['products'] for row in source_zero]
        panel={'name':name,'code_triples':evaluations,'zero_triples':source_zero,
               'zero_count':len(source_zero),'sweep_ns':elapsed,
               'suffix_state_ids':prior['panels'][0 if name=='witness' else 1]['suffix_state_ids'],
               'residual_chart':prior['panels'][0 if name=='witness' else 1]['residual_chart']}
        panels.append(panel)
        print(json.dumps({'panel':name,'zero_count':len(source_zero),'sweep_s':elapsed/1e9}),flush=True)
    out={'status':'PASS_INTERPOLATED_THREE_CODE_SWEEP','candidate_id':None,
         'curve_id':geo['curve_id'],'protocol_sha256':sha(HERE/'sweep_protocol.json'),
         'source_sha256':proto['source_sha256'],'panels':panels,
         'peak_self_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    with (HERE/'sweep_result.json').open('x') as result:json.dump(out,result,sort_keys=True,indent=2);result.write('\n')
if __name__=='__main__':main()
