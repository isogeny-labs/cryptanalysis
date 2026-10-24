"""Independent modular-polynomial screen and ambiguity-adjacency replay."""
from collections import Counter,defaultdict
from hashlib import sha256
import json
from pathlib import Path
import sys
from sage.all import GF, PolynomialRing, classical_modular_polynomial

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'hecke-torsion-frontiers-20261024'
MODULE=HERE.parent/'hecke-two-sheet-small-order-20261023/tools/hecke11.py'
sys.path.insert(0,str(MODULE.parent))
import hecke11 as H
def sha(path):return sha256(path.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    protocol=json.loads((HERE/'validation_protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_HIGHER_DEGREE_VALIDATOR'
    sources={'validator':HERE/'validate.py','result':HERE/'result.json',
             'frontier':PRIOR/'p20023.result.json','hecke11':MODULE}
    assert protocol['source_sha256']=={name:sha(path) for name,path in sources.items()}
    data=json.loads(sources['result'].read_text());prior=json.loads(sources['frontier'].read_text())
    funcs,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[2,3]);T=rd.E([5,5,1])
    bad=set(protocol['ambiguous_orbit_indices']);by_j=defaultdict(list);undefined=[];bad_j=set()
    for i,rep in enumerate(prior['column_representatives']):
        P0=rd.E(0) if rep[0]==-1 else rd.E([rep[0],rep[1],1])
        for k in range(5):
            P=P0+k*T;j=rd.j(P)
            if j is None:undefined.append(key(P));continue
            jj=int(j);by_j[jj].append((key(P),i in bad))
            if i in bad:bad_j.add(jj)
    assert sorted(undefined)==sorted(tuple(x) for x in data['undefined_j_sources'])
    assert len(by_j)==data['distinct_j_count']==len(data['records'])
    F=GF(20023);R=PolynomialRing(F,'Y');Y=R.gen()
    phi={l:classical_modular_polynomial(l) for l in (19,23)}
    hist={str(l):Counter() for l in (19,23)};adjacency={str(l):[] for l in (19,23)}
    records={r['j']:r for r in data['records']}
    for jj,sources_for_j in sorted(by_j.items()):
        rec=records[jj]
        assert rec['source_count']==len(sources_for_j)
        assert rec['ambiguous_source_count']==sum(int(flag) for _,flag in sources_for_j)
        assert sorted(tuple(x) for x in rec['source_points'])==sorted(P for P,_ in sources_for_j)
        for l in (19,23):
            polynomial=R(phi[l](F(jj),Y));assert polynomial.degree()==l+1
            roots=polynomial.roots()
            multiplicity=sum(int(m) for _,m in roots)
            assert rec['degrees'][str(l)]=={'rational_root_multiplicity':multiplicity,
                                           'distinct_rational_roots':len(roots)}
            hist[str(l)][multiplicity]+=len(sources_for_j)
            if multiplicity==l+1:
                hits=sorted({int(r) for r,_ in roots}&bad_j)
                adjacency[str(l)].append({'source_j':jj,'source_count':len(sources_for_j),
                                           'ambiguous_neighbor_j':hits})
    for l in (19,23):
        assert {str(k):v for k,v in sorted(hist[str(l)].items())}==data['summary'][str(l)]['source_histogram']
        assert [x['source_j'] for x in adjacency[str(l)]]==data['summary'][str(l)]['fully_split_j']
    assert sum(len(v) for v in by_j.values())+len(undefined)==19745
    out={'status':'PASS_HIGHER_DEGREE_SPLITTING_AND_ADJACENCY_REPLAY',
         'protocol_sha256':sha(HERE/'validation_protocol.json'),
         'result_sha256':sha(HERE/'result.json'),'validator_sha256':sha(HERE/'validate.py'),
         'source_count':19745,'distinct_j_count':len(by_j),'ambiguous_j_count':len(bad_j),
         'source_root_histograms':{l:{str(k):v for k,v in sorted(v.items())} for l,v in hist.items()},
         'fully_split_adjacency':adjacency}
    (HERE/'validation.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'distinct_j_count':len(by_j),
                      'fully_split_adjacency':adjacency},sort_keys=True))

if __name__=='__main__':main()
