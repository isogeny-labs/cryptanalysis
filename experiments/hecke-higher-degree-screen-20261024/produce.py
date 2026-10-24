"""Direct modular-polynomial splitting screen for degrees 19 and 23."""
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
    raw=(HERE/'protocol.json').read_bytes();protocol=json.loads(raw)
    assert protocol['status']=='FROZEN_BEFORE_HIGHER_DEGREE_SCREEN'
    sources={'producer':HERE/'produce.py','frontier':PRIOR/'p20023.result.json','hecke11':MODULE}
    assert protocol['source_sha256']=={name:sha(path) for name,path in sources.items()}
    prior=json.loads(sources['frontier'].read_text());old=[tuple(x) for x in prior['column_representatives']]
    assert len(old)==3949
    funcs,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[2,3]);T=rd.E([5,5,1])
    assert 5*T==rd.E(0)
    ambiguous=set(protocol['ambiguous_orbit_indices'])
    R=PolynomialRing(GF(20023),'Y');Y=R.gen()
    modpolys={l:classical_modular_polynomial(l) for l in (19,23)}
    j_sources=defaultdict(list);undefined=[]
    for i,rep in enumerate(old):
        P0=rd.E(0) if rep==(-1,-1) else rd.E([rep[0],rep[1],1])
        for k in range(5):
            P=P0+k*T;j=rd.j(P)
            if j is None:undefined.append(key(P));continue
            j_sources[int(j)].append((key(P),i in ambiguous))
    records=[];summary={str(l):{'j_histogram':Counter(),'source_histogram':Counter(),
                            'ambiguous_source_histogram':Counter(),
                            'fully_split_j':[],'fully_split_sources':[]} for l in (19,23)}
    for jj,sources_for_j in sorted(j_sources.items()):
        rec={'j':jj,'source_count':len(sources_for_j),
             'ambiguous_source_count':sum(int(flag) for _,flag in sources_for_j),
             'source_points':[P for P,_ in sources_for_j], 'degrees':{}}
        for l in (19,23):
            polynomial=R(modpolys[l](GF(20023)(jj),Y))
            assert polynomial.degree()==l+1
            roots=polynomial.roots()
            multiplicity=sum(int(m) for _,m in roots)
            rec['degrees'][str(l)]={'rational_root_multiplicity':multiplicity,
                                    'distinct_rational_roots':len(roots)}
            s=summary[str(l)]
            s['j_histogram'][multiplicity]+=1
            s['source_histogram'][multiplicity]+=len(sources_for_j)
            s['ambiguous_source_histogram'][multiplicity]+=rec['ambiguous_source_count']
            if multiplicity==l+1:
                s['fully_split_j'].append(jj)
                s['fully_split_sources'].extend(P for P,_ in sources_for_j)
        records.append(rec)
        if len(records)%500==0:print(json.dumps({'j_checked':len(records)}),flush=True)
    for s in summary.values():
        for field in ('j_histogram','source_histogram','ambiguous_source_histogram'):
            s[field]={str(k):v for k,v in sorted(s[field].items())}
    assert sum(x['source_count'] for x in records)+len(undefined)==19745
    out={'status':'HIGHER_DEGREE_MODPOLY_SCREEN_PRODUCED',
         'protocol_sha256':sha256(raw).hexdigest(),
         'source_sha256':{name:sha(path) for name,path in sources.items()},
         'p':20023,'degrees':[19,23],'source_point_count':19745,
         'undefined_j_sources':undefined,'distinct_j_count':len(records),
         'records':records,'summary':summary,
         'candidate_id':None,'timing_claim':None}
    (HERE/'result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'distinct_j_count':len(records),'undefined_j_count':len(undefined),
                      'summary':{k:{'fully_split_j_count':len(v['fully_split_j']),
                                     'fully_split_source_count':len(v['fully_split_sources']),
                                     'ambiguous_fully_split_source_count':v['ambiguous_source_histogram'].get(str(int(k)+1),0)}
                                 for k,v in summary.items()}},sort_keys=True))

if __name__=='__main__':main()
