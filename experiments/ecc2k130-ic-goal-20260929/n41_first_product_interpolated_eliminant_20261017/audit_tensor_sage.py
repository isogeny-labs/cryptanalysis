#!/usr/bin/env sage -python
"""Independently evaluate the interpolant as a polynomial in p last."""
import hashlib,json,resource,signal,time
from pathlib import Path
from sage.all import GF,PolynomialRing
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
GEO=ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    signal.alarm(180)
    proto=json.loads((HERE/'tensor_audit_protocol.json').read_text())
    files={'audit_tensor_sage':HERE/'audit_tensor_sage.py',
           'sweep_result':HERE/'sweep_result.json','geometry':GEO,
           'witness_tensor':HERE/'witness_result_v2.json','negative_tensor':HERE/'negative_result_v2.json',
           'runtime':HERE/'sage_runtime_info.json'}
    assert proto['source_sha256']=={k:sha(p) for k,p in files.items()}
    geo=json.loads(GEO.read_text());sweep=json.loads((HERE/'sweep_result.json').read_text())
    poly=PolynomialRing(GF(2),'t');t=poly.gen()
    field=GF(2**41,name='t',modulus=t**41+t**3+1)
    def dec(v):return field(poly([(v>>i)&1 for i in range(41)]))
    def product(slot,mask):
        v=0
        for i,b in enumerate(geo['blocks'][slot]['product_basis']):
            if mask>>i&1:v^=b
        return v
    source=[sorted((product(slot,m),m) for m in geo['permitted_canonical_a'])
            for slot in range(3)]
    assert all(len(row)==40 and len({x for x,m in row})==40 for row in source)
    source_field=[[(v,m,dec(v)) for v,m in row] for row in source]
    panels=[]
    for recorded in sweep['panels']:
        begin=time.monotonic_ns();name=recorded['name']
        tensor=json.loads((HERE/f'{name}_result_v2.json').read_text())
        terms=[(i,j,[(k,dec(c)) for k,c in coeffs])
               for i,j,coeffs in tensor['coefficient_terms']]
        zero=[];evaluations=0
        for q,mq,qv in source_field[1]:
            qpow=[qv**i for i in range(17)]
            for r,mr,rv in source_field[2]:
                rpow=[rv**i for i in range(25)]
                coeff=[field.zero()]*17
                for i,j,terms_p in terms:
                    scale=qpow[i]*rpow[j]
                    for k,c in terms_p:coeff[k]+=c*scale
                for p,mp,pv in source_field[0]:
                    value=field.zero()
                    for c in reversed(coeff):value=value*pv+c
                    evaluations+=1
                    if value==0:zero.append((p,q,r))
        expected=sorted(tuple(row['products']) for row in recorded['zero_triples'])
        assert evaluations==64000 and sorted(zero)==expected,(name,len(zero),len(expected))
        panels.append({'name':name,'evaluations':evaluations,'zeros':len(zero),
                       'elapsed_ns':time.monotonic_ns()-begin})
    out={'status':'PASS_REVERSE_ORDER_FULL_CUBE_AUDIT','candidate_id':None,
         'curve_id':geo['curve_id'],'protocol_sha256':sha(HERE/'tensor_audit_protocol.json'),
         'source_sha256':proto['source_sha256'],'panels':panels,
         'peak_self_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    with (HERE/'tensor_audit_result.json').open('x') as output:json.dump(out,output,indent=2,sort_keys=True);output.write('\n')
    print(json.dumps({'status':out['status'],'panels':panels}),flush=True)
if __name__=='__main__':main()
