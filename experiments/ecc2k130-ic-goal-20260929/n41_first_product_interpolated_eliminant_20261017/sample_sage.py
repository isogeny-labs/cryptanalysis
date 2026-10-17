#!/usr/bin/env sage -python
"""One isolated target-conditioned resultant specialization."""
import argparse,hashlib,json,resource,time
from pathlib import Path
from sage.all import GF,PolynomialRing
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
GEO=ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json'
PRIOR=ROOT/'n41_w8_three_pair_resultant_20261013/result.json'
OLD=ROOT/'n41_twofree_symbolic_resultant_replay_20261016'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main(panel,pvalue):
    proto=json.loads((HERE/'protocol_v2.json').read_text())
    assert sha(HERE/'sample_sage.py')==proto['source_sha256']['sample_sage']
    assert panel in proto['panel_order']
    assert pvalue in proto['sample_first_products']+proto['holdout_first_products']
    geo=json.loads(GEO.read_text());prior=json.loads(PRIOR.read_text())
    archived=json.loads((OLD/('result.json' if panel=='witness' else 'control_result.json')).read_text())
    poly=PolynomialRing(GF(2),'t');t=poly.gen()
    field=GF(2**41,name='t',modulus=t**41+t**3+1)
    def dec(v):return field(poly([(v>>i)&1 for i in range(41)]))
    def enc(v):return sum(int(bit)<<i for i,bit in enumerate(v.polynomial().list()))
    R=PolynomialRing(field,names=('q','r','z'));q,r,z=R.gens()
    a,b,s3=[dec(v) for v in (geo['blocks'][0]['s'],geo['blocks'][1]['s'],geo['blocks'][2]['s'])]
    target=dec(archived['residual_chart'])
    A=target**2+z*(z+1)*target*(target+1)+(target+1)**2
    B=z*(z+1)*target*(target+1)
    D=(z+1)**2*target**2+z**2*(target+1)**2
    L=1+r;M=L*B+r*A;N=L*D+s3**2*A
    Q=L*N**2+r*N*M+s3**2*M**2
    H=sum((a**ea*b**eb*dec(pvalue)**ep*q**eq*z**ez
           for ea,eb,ep,eq,ez in prior['terms']),R.zero())
    assert Q.degree(z)==4 and H.degree(z)==8
    start=time.monotonic_ns();f=H.resultant(Q,z)
    elapsed=time.monotonic_ns()-start
    assert f and f.degree(z)==0 and f.degree(q)<=16 and f.degree(r)<=24
    terms=sorted((int(exps[0]),int(exps[1]),enc(coef)) for exps,coef in f.dict().items())
    print(json.dumps({'panel':panel,'first_product':pvalue,'terms':terms,
                      'resultant_ns':elapsed,
                      'peak_self_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},sort_keys=True))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('panel',choices=['witness','negative']);ap.add_argument('first_product',type=int)
    args=ap.parse_args();main(args.panel,args.first_product)
