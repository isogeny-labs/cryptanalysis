#!/usr/bin/env sage -python
"""Interpolate the target-conditioned resultant over the first product."""
import argparse,hashlib,json,resource,signal,time
from pathlib import Path
from sage.all import GF,PolynomialRing
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
GEO=ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json'
PRIOR=ROOT/'n41_w8_three_pair_resultant_20261013/result.json'
OLD=ROOT/'n41_twofree_symbolic_resultant_replay_20261016'
FILES={'worker':HERE/'worker.py','geometry':GEO,'prior':PRIOR,
       'witness_archived':OLD/'result.json','negative_archived':OLD/'control_result.json',
       'runtime':HERE/'sage_runtime_info.json'}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main(panel):
    signal.alarm(300)
    protocol=json.loads((HERE/'protocol.json').read_text())
    assert protocol['source_sha256']=={name:sha(path) for name,path in FILES.items()}
    assert panel in protocol['panel_order']
    geo=json.loads(GEO.read_text());prior=json.loads(PRIOR.read_text())
    archived=json.loads((OLD/('result.json' if panel=='witness' else 'control_result.json')).read_text())
    poly=PolynomialRing(GF(2),'t');t=poly.gen()
    field=GF(2**41,name='t',modulus=t**41+t**3+1)
    def dec(v):return field(poly([(v>>i)&1 for i in range(41)]))
    def enc(v):return sum(int(bit)<<i for i,bit in enumerate(v.polynomial().list()))
    R=PolynomialRing(field,names=('q','r','z'));q,r,z=R.gens()
    P=PolynomialRing(field,'P');Pvar=P.gen()
    a,b,s3=[dec(v) for v in (geo['blocks'][0]['s'],geo['blocks'][1]['s'],geo['blocks'][2]['s'])]
    target=dec(archived['residual_chart'])
    A=target**2+z*(z+1)*target*(target+1)+(target+1)**2
    B=z*(z+1)*target*(target+1)
    D=(z+1)**2*target**2+z**2*(target+1)**2
    L=1+r;M=L*B+r*A;N=L*D+s3**2*A
    Q=L*N**2+r*N*M+s3**2*M**2
    assert Q.degree(z)==4
    terms=[(ea,eb,ep,eq,ez) for ea,eb,ep,eq,ez in prior['terms']]
    assert max(x[2] for x in terms)==4
    def build_first(pvalue):
        pv=dec(pvalue)
        H=sum((a**ea*b**eb*pv**ep*q**eq*z**ez for ea,eb,ep,eq,ez in terms),R.zero())
        assert H.degree(z)==8
        f=H.resultant(Q,z)
        assert f and f.degree(z)==0 and f.degree(q)<=16 and f.degree(r)<=24
        return {(int(exps[0]),int(exps[1])):coef for exps,coef in f.dict().items()}
    start=time.monotonic_ns();samples=[];sample_ns=[]
    for index,pvalue in enumerate(protocol['sample_first_products']):
        begin=time.monotonic_ns();coeffs=build_first(pvalue)
        sample_ns.append(time.monotonic_ns()-begin)
        samples.append(coeffs)
        print(json.dumps({'panel':panel,'sample':index+1,'terms':len(coeffs),'elapsed_s':sample_ns[-1]/1e9}),flush=True)
    built=time.monotonic_ns()
    support=sorted(set().union(*(set(row) for row in samples)))
    interpolated={}
    for monomial in support:
        values=[(dec(p),row.get(monomial,field.zero()))
                for p,row in zip(protocol['sample_first_products'],samples)]
        polynomial=P.lagrange_polynomial(values)
        if polynomial:interpolated[monomial]=polynomial
    interpolated_ns=time.monotonic_ns()-built
    assert interpolated and max(int(v.degree()) for v in interpolated.values())<=16
    holdout_rows=[]
    for pvalue in protocol['holdout_first_products']:
        begin=time.monotonic_ns()
        predicted={key:value(dec(pvalue)) for key,value in interpolated.items() if value(dec(pvalue))}
        prediction_ns=time.monotonic_ns()-begin
        begin=time.monotonic_ns();direct=build_first(pvalue)
        direct_ns=time.monotonic_ns()-begin
        assert predicted==direct,(panel,pvalue,len(predicted),len(direct))
        if pvalue==protocol['holdout_first_products'][0]:
            expected={(int(exps[0]),int(exps[1])):dec(value)
                      for exps,value in archived['terms']}
            assert predicted==expected
        holdout_rows.append({'first_product':pvalue,'predicted_terms':len(predicted),
                             'prediction_ns':prediction_ns,'direct_resultant_ns':direct_ns,
                             'coefficient_sha256':hashlib.sha256(json.dumps(sorted((i,j,enc(v)) for (i,j),v in predicted.items())).encode()).hexdigest()})
    elapsed=time.monotonic_ns()-start
    encoded=[(i,j,[(k,enc(coef)) for k,coef in enumerate(polynomial.list()) if coef])
             for (i,j),polynomial in sorted(interpolated.items())]
    out={'status':'PASS_FIRST_PRODUCT_INTERPOLATION','panel':panel,'candidate_id':None,
         'curve_id':geo['curve_id'],'protocol_sha256':sha(HERE/'protocol.json'),
         'source_sha256':protocol['source_sha256'],'sample_count':len(samples),
         'sample_resultant_ns':sample_ns,'sample_support_sizes':[len(row) for row in samples],
         'interpolation_ns':interpolated_ns,'universal_terms':len(interpolated),
         'max_first_product_degree':max(int(v.degree()) for v in interpolated.values()),
         'coefficient_terms':encoded,'holdouts':holdout_rows,'worker_ns':elapsed,
         'peak_self_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    with (HERE/f'{panel}_result.json').open('x') as output:json.dump(out,output,sort_keys=True,indent=2);output.write('\n')
    print(json.dumps({'status':out['status'],'panel':panel,'universal_terms':len(interpolated),
                      'max_p_degree':out['max_first_product_degree'],'worker_s':elapsed/1e9}),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('panel',choices=['witness','negative'])
    main(ap.parse_args().panel)
