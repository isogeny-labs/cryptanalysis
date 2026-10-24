"""Factor degree-29 Hecke x-fibers at the four residual orbit classes."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
from sage.all import GF

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'hecke-two-sheet-small-order-20261023/tools'))
import hecke11 as H
def sha(p):return sha256(p.read_bytes()).hexdigest()

def main():
    path=HERE/'residual_factor_protocol.json';raw=path.read_bytes()
    protocol=json.loads(raw);assert protocol['status']=='FROZEN_BEFORE_RESIDUAL_FACTOR_SCREEN'
    frontier_path=ROOT/'hecke-torsion-frontiers-20261024/p20023.result.json'
    functions_path=ROOT/'hecke-degree-next-screen-20261024/l29_functions.json'
    frontier=json.loads(frontier_path.read_text());saved=json.loads(functions_path.read_text())
    F=GF(20023);funcs={}
    for tag,coeff in saved['functions'].items():
        ell,part,k=tag.split(':')
        funcs[(int(ell),part,int(k))]={tuple(map(int,ab.split(','))):F(v) for ab,v in coeff.items()}
    _,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[29])
    T=rd.E([5,5,1]);assert 5*T==rd.E(0)
    rows=[]
    for old_index in protocol['old_ambiguous_orbit_indices']:
        rep=frontier['column_representatives'][old_index]
        P0=rd.E([*rep,1])
        for translate in range(5):
            Q=P0+translate*T
            P=(int(Q[0]),int(Q[1]))
            j=rd.j(Q)
            polynomial=rd.neighbour_x(29,Q)
            factors=polynomial.factor()
            profile=[{'degree':int(f.degree()),'multiplicity':int(m),
                      'coefficients':[int(c) for c in f.list()]}
                     for f,m in factors]
            assert sum(r['degree']*r['multiplicity'] for r in profile)==30
            squarefree=all(r['multiplicity']==1 for r in profile)
            rows.append({'source':P,'old_orbit_index':old_index,'translate':translate,
                         'source_j':None if j is None else int(j),
                         'squarefree':squarefree,
                         'rational_x_root_multiplicity':sum(r['multiplicity'] for r in profile if r['degree']==1),
                         'max_factor_degree':max(r['degree'] for r in profile),
                         'factors':profile})
    summary={'source_points':len(rows),'squarefree_source_points':sum(r['squarefree'] for r in rows),
             'degree_profiles':dict(Counter(str(sorted((f['degree'],f['multiplicity']) for f in r['factors'])) for r in rows)),
             'max_factor_degree_histogram':dict(Counter(str(r['max_factor_degree']) for r in rows))}
    out={'status':'L29_RESIDUAL_FIBER_FACTORS_PRODUCED','protocol_sha256':sha(path),
         'source_sha256':{'frontier':sha(frontier_path),'functions':sha(functions_path)},
         'rows':rows,'summary':summary,'candidate_id':None,'timing_claim':None}
    (HERE/'residual_factor_result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True))

if __name__=='__main__':main()
